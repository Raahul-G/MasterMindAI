"""
Recommendation service — manages per-user topic graph (topic_nodes + topic_edges).

Key functions:
  create_or_update_topic_node  — called at module start (in_progress)
  complete_topic_node          — called at module completion (learned)
  generate_and_save_recommendations — called after completion; writes recommended nodes + edges
  backfill_for_user            — rebuilds graph for users with old data
"""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import Module, Passage, TopicEdge, TopicNode
from app.models.user import User
from app.services import ai_service

logger = logging.getLogger(__name__)


async def create_or_update_topic_node(
    user_id: uuid.UUID,
    topic: str,
    module_id: uuid.UUID,
    status: str,
    db: AsyncSession,
) -> TopicNode:
    """
    Normalises the topic name via AI, then upserts a topic_nodes row.
    Returns the TopicNode (either newly created or existing).
    """
    existing_result = await db.execute(
        select(TopicNode.canonical_name).where(TopicNode.user_id == user_id)
    )
    existing_topics = list(existing_result.scalars().all())

    normalised = await ai_service.normalize_topic(topic, existing_topics)
    canonical_name: str = normalised.get("canonical_name") or topic
    domain: str | None = normalised.get("domain")

    # Check if node already exists (by canonical_name + user)
    node_result = await db.execute(
        select(TopicNode).where(
            TopicNode.user_id == user_id,
            TopicNode.canonical_name == canonical_name,
        )
    )
    node = node_result.scalar_one_or_none()

    if node:
        # Update source_module_id if not set; only upgrade status (in_progress → learned)
        if node.source_module_id is None:
            node.source_module_id = module_id
        if status == "learned":
            node.status = "learned"
        await db.commit()
        await db.refresh(node)
    else:
        node = TopicNode(
            user_id=user_id,
            canonical_name=canonical_name,
            display_name=topic,
            domain=domain,
            source_module_id=module_id,
            status=status,
        )
        db.add(node)
        try:
            await db.commit()
            await db.refresh(node)
        except IntegrityError:
            # Another concurrent request already created the same node — fetch it
            await db.rollback()
            node_result = await db.execute(
                select(TopicNode).where(
                    TopicNode.user_id == user_id,
                    TopicNode.canonical_name == canonical_name,
                )
            )
            node = node_result.scalar_one()
            logger.info("Topic node race condition resolved for user=%s canonical='%s'", user_id, canonical_name)

    logger.info("Topic node upserted: user=%s canonical='%s' status=%s", user_id, canonical_name, status)
    return node


async def complete_topic_node(
    user_id: uuid.UUID,
    canonical_name: str,
    db: AsyncSession,
) -> None:
    """Marks the topic node as learned."""
    result = await db.execute(
        select(TopicNode).where(
            TopicNode.user_id == user_id,
            TopicNode.canonical_name == canonical_name,
        )
    )
    node = result.scalar_one_or_none()
    if node:
        node.status = "learned"
        await db.commit()


async def generate_and_save_recommendations(
    user_id: uuid.UUID,
    source_module_id: uuid.UUID,
    topic: str,
    canonical_name: str,
    domain: str | None,
    level: str,
    learned_concepts: list[str],
    user_interests: list[str],
    db: AsyncSession,
) -> None:
    """
    After a module is completed:
    1. Fetches all existing canonical topic names for this user
    2. Calls AI to suggest 1-2 next modules (recommended nodes)
    3. Upserts recommended topic_nodes (skips if already exists)
    4. Calls AI to detect cross-topic connections
    5. Upserts topic_edges (ON CONFLICT DO NOTHING equivalent)
    """
    existing_result = await db.execute(
        select(TopicNode.canonical_name).where(TopicNode.user_id == user_id)
    )
    all_existing: list[str] = list(existing_result.scalars().all())
    # Exclude the just-completed topic from "other topics" sent to connections AI
    other_topics = [t for t in all_existing if t != canonical_name]

    # --- Module recommendations ---
    try:
        recommendations = await ai_service.generate_module_recommendations(
            canonical_name=canonical_name,
            domain=domain,
            level=level,
            learned_concepts=learned_concepts,
            user_interests=user_interests,
            existing_topics=all_existing,
        )
    except Exception as exc:
        logger.warning("AI module recommendations failed: %s", exc)
        recommendations = []

    for rec in recommendations:
        rec_canonical = rec.get("canonical_name") or rec.get("topic", "")
        if not rec_canonical:
            continue

        # Skip if user already has this topic (learned or in_progress)
        if rec_canonical in all_existing:
            continue

        hints_raw = rec.get("concept_hints") or []
        node = TopicNode(
            user_id=user_id,
            canonical_name=rec_canonical,
            display_name=rec.get("topic") or rec_canonical,
            domain=rec.get("domain"),
            source_module_id=None,
            status="recommended",
            concept_hints=hints_raw[:2] if hints_raw else None,
            reason=rec.get("reason"),
        )
        db.add(node)

    try:
        await db.flush()
    except Exception:
        await db.rollback()
        logger.warning("Flush failed saving recommended nodes for user %s", user_id)
        return

    # --- Topic connections ---
    try:
        connections = await ai_service.detect_topic_connections(
            canonical_name=canonical_name,
            domain=domain,
            existing_topics=other_topics,
        )
    except Exception as exc:
        logger.warning("AI topic connections failed: %s", exc)
        connections = []

    for conn in connections:
        src_name = conn.get("source", "")
        tgt_name = conn.get("target", "")
        rel = conn.get("relationship", "related")
        if not src_name or not tgt_name:
            continue

        # Resolve source and target to node IDs
        src_result = await db.execute(
            select(TopicNode).where(TopicNode.user_id == user_id, TopicNode.canonical_name == src_name)
        )
        src_node = src_result.scalar_one_or_none()

        tgt_result = await db.execute(
            select(TopicNode).where(TopicNode.user_id == user_id, TopicNode.canonical_name == tgt_name)
        )
        tgt_node = tgt_result.scalar_one_or_none()

        if not src_node or not tgt_node:
            continue

        # Check for existing edge to avoid unique constraint violation
        edge_result = await db.execute(
            select(TopicEdge).where(
                TopicEdge.user_id == user_id,
                TopicEdge.source_node_id == src_node.id,
                TopicEdge.target_node_id == tgt_node.id,
            )
        )
        if edge_result.scalar_one_or_none() is None:
            db.add(TopicEdge(
                user_id=user_id,
                source_node_id=src_node.id,
                target_node_id=tgt_node.id,
                relationship_type=rel,
            ))

    await db.commit()
    logger.info(
        "Saved %d recommendations, %d connections for user %s on '%s'",
        len(recommendations),
        len(connections),
        user_id,
        canonical_name,
    )


async def backfill_for_user(user_id: uuid.UUID, db: AsyncSession) -> int:
    """
    Rebuilds topic_nodes + topic_edges for all completed modules that don't
    yet have a topic_node. Returns the number of modules backfilled.
    """
    modules_result = await db.execute(
        select(Module).where(Module.user_id == user_id, Module.status == "completed")
    )
    completed_modules = modules_result.scalars().all()
    if not completed_modules:
        return 0

    # Which module IDs already have a topic_node
    existing_nodes_result = await db.execute(
        select(TopicNode.source_module_id).where(
            TopicNode.user_id == user_id,
            TopicNode.source_module_id.isnot(None),
        )
    )
    already_done: set[uuid.UUID] = set(existing_nodes_result.scalars().all())

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    user_interests = user.interest_topics or [] if user else []

    backfilled = 0
    for module in completed_modules:
        if module.id in already_done:
            continue

        passages_result = await db.execute(
            select(Passage).where(Passage.module_id == module.id).order_by(Passage.order_index)
        )
        learned_concepts = [p.concept_title for p in passages_result.scalars().all()]
        if not learned_concepts:
            continue

        try:
            node = await create_or_update_topic_node(
                user_id=user_id,
                topic=module.topic,
                module_id=module.id,
                status="learned",
                db=db,
            )
            await generate_and_save_recommendations(
                user_id=user_id,
                source_module_id=module.id,
                topic=module.topic,
                canonical_name=node.canonical_name,
                domain=node.domain,
                level=module.level,
                learned_concepts=learned_concepts,
                user_interests=user_interests,
                db=db,
            )
            backfilled += 1
        except Exception as exc:
            logger.warning("Backfill failed for module %s: %s", module.id, exc)

    return backfilled
