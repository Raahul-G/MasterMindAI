"""
Recommendation service — generates and persists next-concept suggestions.

Called automatically after every module completion (fire-and-forget).
Also exposes backfill_for_user() for users whose old modules pre-date this feature.
"""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import ConceptGraph, Module, Passage
from app.models.user import User
from app.services import ai_service

logger = logging.getLogger(__name__)


async def generate_and_save_recommendations(
    user_id: uuid.UUID,
    source_module_id: uuid.UUID,
    topic: str,
    level: str,
    learned_concepts: list[str],
    user_interests: list[str],
    db: AsyncSession,
) -> None:
    """
    Generates 2 next-concept recommendations for the completed module
    and saves them to the concept_graph table.
    """
    if not learned_concepts:
        return

    raw = await ai_service.generate_concept_recommendations(
        topic=topic,
        level=level,
        learned_concepts=learned_concepts,
        user_interests=user_interests,
    )

    entry = ConceptGraph(
        user_id=user_id,
        source_module_id=source_module_id,
        topic=topic,
        learned_concepts=learned_concepts,
        recommended_concepts=raw,
    )
    db.add(entry)
    await db.commit()
    logger.info(
        "Saved %d recommendations for user %s on topic '%s'",
        len(raw),
        user_id,
        topic,
    )


async def backfill_for_user(user_id: uuid.UUID, db: AsyncSession) -> int:
    """
    Generates recommendations for all completed modules that don't yet have
    a concept_graph entry. Returns the number of modules backfilled.
    """
    # All completed modules for this user
    modules_result = await db.execute(
        select(Module).where(Module.user_id == user_id, Module.status == "completed")
    )
    completed_modules = modules_result.scalars().all()
    if not completed_modules:
        return 0

    # Which modules already have concept_graph entries
    existing_result = await db.execute(
        select(ConceptGraph.source_module_id).where(ConceptGraph.user_id == user_id)
    )
    already_done: set[uuid.UUID] = set(existing_result.scalars().all())

    # User interests
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    user_interests = user.interest_topics or [] if user else []

    backfilled = 0
    for module in completed_modules:
        if module.id in already_done:
            continue

        passages_result = await db.execute(
            select(Passage)
            .where(Passage.module_id == module.id)
            .order_by(Passage.order_index)
        )
        learned_concepts = [p.concept_title for p in passages_result.scalars().all()]
        if not learned_concepts:
            continue

        try:
            await generate_and_save_recommendations(
                user_id=user_id,
                source_module_id=module.id,
                topic=module.topic,
                level=module.level,
                learned_concepts=learned_concepts,
                user_interests=user_interests,
                db=db,
            )
            backfilled += 1
        except Exception as exc:
            logger.warning("Backfill failed for module %s: %s", module.id, exc)

    return backfilled
