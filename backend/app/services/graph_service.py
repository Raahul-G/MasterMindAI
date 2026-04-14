import asyncio
import logging
import uuid

import numpy as np
from openai import AsyncOpenAI
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from umap import UMAP

from app.core.config import settings
from app.models.learning import ConceptEmbedding, Module, Passage
from app.models.social import Friendship
from app.schemas.learning import GraphNode, GraphResponse

logger = logging.getLogger(__name__)

_openai_client: AsyncOpenAI | None = None


def _get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


async def _get_embedding(text: str) -> list[float]:
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured — cannot generate embeddings")
    client = _get_openai_client()
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=text[:8000],
    )
    return response.data[0].embedding


async def embed_and_upsert(
    user_id: uuid.UUID,
    concept_title: str,
    content: str,
    module_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    canonical = concept_title.strip().lower()
    if not canonical:
        logger.warning("Skipping embed_and_upsert: empty concept_title for user %s", user_id)
        return

    result = await db.execute(
        select(ConceptEmbedding).where(
            and_(
                ConceptEmbedding.user_id == user_id,
                ConceptEmbedding.canonical_concept == canonical,
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        if module_id not in (existing.module_ids or []):
            existing.module_ids = (existing.module_ids or []) + [module_id]
            existing.hub_score = len(existing.module_ids)
            await db.commit()
        return

    embedding = await _get_embedding(content)

    node = ConceptEmbedding(
        user_id=user_id,
        canonical_concept=canonical,
        embedding=embedding,
        hub_score=1,
        module_ids=[module_id],
    )
    db.add(node)
    await db.commit()
    await db.refresh(node)

    await compute_positions_for_user(user_id, db)


async def compute_positions_for_user(user_id: uuid.UUID, db: AsyncSession) -> None:
    result = await db.execute(
        select(ConceptEmbedding).where(ConceptEmbedding.user_id == user_id)
    )
    all_nodes = [n for n in result.scalars().all() if n.embedding is not None]

    if not all_nodes:
        return

    unpositioned = [n for n in all_nodes if n.pos_x is None]
    if not unpositioned:
        return

    if len(all_nodes) == 1:
        all_nodes[0].pos_x = 0.0
        all_nodes[0].pos_y = 0.0
        all_nodes[0].pos_z = 0.0
        await db.commit()
        return

    embeddings = np.array([n.embedding for n in all_nodes], dtype=np.float32)
    n_neighbors = max(1, min(15, len(all_nodes) - 1))

    try:
        positions = await asyncio.to_thread(
            lambda: UMAP(n_components=3, random_state=42, n_neighbors=n_neighbors).fit_transform(embeddings)
        )
    except Exception as exc:
        logger.warning("UMAP position computation failed for user %s: %s", user_id, exc)
        return

    unpositioned_ids = {n.id for n in unpositioned}
    for i, node in enumerate(all_nodes):
        if node.id in unpositioned_ids:
            node.pos_x = float(positions[i][0])
            node.pos_y = float(positions[i][1])
            node.pos_z = float(positions[i][2])

    await db.commit()


async def get_graph(user_id: uuid.UUID, db: AsyncSession) -> GraphResponse:
    result = await db.execute(
        select(ConceptEmbedding).where(ConceptEmbedding.user_id == user_id)
    )
    nodes = result.scalars().all()

    return GraphResponse(
        nodes=[
            GraphNode(
                id=n.id,
                label=n.canonical_concept,
                pos_x=n.pos_x,
                pos_y=n.pos_y,
                pos_z=n.pos_z,
                hub_score=n.hub_score,
                module_ids=n.module_ids or [],
            )
            for n in nodes
        ]
    )


async def get_friend_graph(
    current_user_id: uuid.UUID,
    friend_user_id: uuid.UUID,
    db: AsyncSession,
) -> GraphResponse:
    friendship = await db.execute(
        select(Friendship).where(
            Friendship.status == "accepted",
            or_(
                and_(Friendship.requester_id == current_user_id, Friendship.addressee_id == friend_user_id),
                and_(Friendship.requester_id == friend_user_id, Friendship.addressee_id == current_user_id),
            ),
        )
    )
    if not friendship.scalar_one_or_none():
        raise PermissionError("You are not friends with this user.")

    return await get_graph(friend_user_id, db)


async def retroactive_populate(user_id: uuid.UUID, db: AsyncSession) -> int:
    result = await db.execute(
        select(Passage)
        .join(Module, Passage.module_id == Module.id)
        .where(
            and_(
                Module.user_id == user_id,
                Passage.status == "completed",
            )
        )
    )
    passages = result.scalars().all()

    count = 0
    for passage in passages:
        canonical = passage.concept_title.strip().lower()
        if not canonical:
            continue

        existing_result = await db.execute(
            select(ConceptEmbedding).where(
                and_(
                    ConceptEmbedding.user_id == user_id,
                    ConceptEmbedding.canonical_concept == canonical,
                )
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            if passage.module_id not in (existing.module_ids or []):
                existing.module_ids = (existing.module_ids or []) + [passage.module_id]
                existing.hub_score = len(existing.module_ids)
                await db.commit()
            continue

        try:
            embedding = await _get_embedding(passage.content)
            node = ConceptEmbedding(
                user_id=user_id,
                canonical_concept=canonical,
                embedding=embedding,
                hub_score=1,
                module_ids=[passage.module_id],
            )
            db.add(node)
            await db.commit()
            count += 1
        except Exception as exc:
            logger.warning("Failed to embed passage %s: %s", passage.id, exc)
            continue

    if count > 0:
        await compute_positions_for_user(user_id, db)

    return count
