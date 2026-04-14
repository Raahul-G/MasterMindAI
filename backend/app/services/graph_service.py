import asyncio
import logging
import uuid

import numpy as np
from openai import AsyncOpenAI
from sqlalchemy import and_, or_, select, text as sa_text
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


def _vec_str(embedding: list[float]) -> str:
    """Format a Python list as a PostgreSQL vector literal."""
    return "[" + ",".join(str(float(x)) for x in embedding) + "]"


def _parse_vec(val) -> list[float]:
    """Parse a vector value whether returned as list, numpy array, or text string."""
    if isinstance(val, str):
        return [float(x) for x in val.strip("[]").split(",")]
    return [float(x) for x in val]


async def _insert_embedding(
    db: AsyncSession,
    user_id: uuid.UUID,
    canonical: str,
    embedding: list[float],
    module_id: uuid.UUID,
) -> None:
    """Insert a new concept embedding row using raw SQL to avoid asyncpg codec issues.

    The vector literal is inlined directly into the SQL string (not passed as a parameter)
    because asyncpg rejects string parameters for the vector type even with CAST.
    The value is safe to inline — it is a list of floats from OpenAI with no user input.
    """
    vec_literal = _vec_str(embedding)
    await db.execute(
        sa_text(f"""
            INSERT INTO concept_embeddings
                (id, user_id, canonical_concept, embedding, hub_score, module_ids, created_at, updated_at)
            VALUES
                (gen_random_uuid(), :uid, :canonical, '{vec_literal}'::vector, 1, :mids, now(), now())
        """),
        {
            "uid": user_id,
            "canonical": canonical,
            "mids": [module_id],
        },
    )
    await db.commit()


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
    await _insert_embedding(db, user_id, canonical, embedding, module_id)
    await compute_positions_for_user(user_id, db)


async def compute_positions_for_user(user_id: uuid.UUID, db: AsyncSession) -> None:
    # Select embeddings as text to avoid asyncpg codec issues with the vector type
    rows = (
        await db.execute(
            sa_text("""
                SELECT id, embedding::text, pos_x
                FROM concept_embeddings
                WHERE user_id = :uid AND embedding IS NOT NULL
            """),
            {"uid": user_id},
        )
    ).fetchall()

    if not rows:
        return

    unpositioned = [r for r in rows if r.pos_x is None]
    if not unpositioned:
        return

    if len(rows) == 1:
        await db.execute(
            sa_text("""
                UPDATE concept_embeddings SET pos_x = 0, pos_y = 0, pos_z = 0
                WHERE user_id = :uid
            """),
            {"uid": user_id},
        )
        await db.commit()
        return

    embeddings = np.array([_parse_vec(r.embedding) for r in rows], dtype=np.float32)
    n_neighbors = max(1, min(15, len(rows) - 1))

    positions = None
    try:
        positions = await asyncio.to_thread(
            lambda: UMAP(n_components=3, random_state=42, n_neighbors=n_neighbors).fit_transform(embeddings)
        )
    except Exception as exc:
        logger.warning("UMAP position computation failed for user %s: %s — using random fallback positions", user_id, exc)

    unpositioned_ids = {str(r.id) for r in unpositioned}
    rng = np.random.default_rng(42)
    for i, row in enumerate(rows):
        if str(row.id) in unpositioned_ids:
            if positions is not None:
                x, y, z = float(positions[i][0]), float(positions[i][1]), float(positions[i][2])
            else:
                x, y, z = [float(v) for v in rng.uniform(-50, 50, 3)]
            await db.execute(
                sa_text("""
                    UPDATE concept_embeddings
                    SET pos_x = :x, pos_y = :y, pos_z = :z
                    WHERE id = :id
                """),
                {"x": x, "y": y, "z": z, "id": row.id},
            )

    await db.commit()


async def get_graph(user_id: uuid.UUID, db: AsyncSession) -> GraphResponse:
    # Explicitly exclude the embedding column — we never need it for display,
    # and it avoids asyncpg codec issues when the vector type codec isn't registered.
    rows = (
        await db.execute(
            sa_text("""
                SELECT id, canonical_concept, pos_x, pos_y, pos_z, hub_score, module_ids
                FROM concept_embeddings
                WHERE user_id = :uid
            """),
            {"uid": user_id},
        )
    ).fetchall()

    return GraphResponse(
        nodes=[
            GraphNode(
                id=row.id,
                label=row.canonical_concept,
                pos_x=row.pos_x,
                pos_y=row.pos_y,
                pos_z=row.pos_z,
                hub_score=row.hub_score,
                module_ids=row.module_ids or [],
            )
            for row in rows
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
            await _insert_embedding(db, user_id, canonical, embedding, passage.module_id)
            count += 1
        except Exception as exc:
            logger.warning("Failed to embed passage %s: %s", passage.id, exc)
            continue

    if count > 0:
        await compute_positions_for_user(user_id, db)

    return count
