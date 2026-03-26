"""
Recommendation service — generates and persists next-concept suggestions.

Called automatically after every module completion (fire-and-forget).
"""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import ConceptGraph
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
