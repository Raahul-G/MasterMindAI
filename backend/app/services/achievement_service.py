import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gamification import Achievement, UserAchievement
from app.models.learning import Module


async def _award_if_not_earned(user_id: uuid.UUID, slug: str, db: AsyncSession) -> bool:
    """
    Awards an achievement by slug if the user doesn't already have it.
    Returns True if newly awarded, False if already earned or slug not found.
    """
    achievement_result = await db.execute(select(Achievement).where(Achievement.slug == slug))
    achievement = achievement_result.scalar_one_or_none()
    if not achievement:
        return False

    already = await db.execute(
        select(UserAchievement).where(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement.id,
        )
    )
    if already.scalar_one_or_none():
        return False

    db.add(UserAchievement(user_id=user_id, achievement_id=achievement.id))
    return True


async def check_and_award_achievements(
    user_id: uuid.UUID,
    db: AsyncSession,
    streak_count: int = 0,
    used_remediation: bool = False,
    first_attempt_perfect: bool = False,
) -> list[str]:
    """
    Checks all 8 achievement conditions and awards any newly earned ones.
    Returns a list of newly earned achievement slugs (empty list if none).
    Called automatically after a module is completed.
    """
    count_result = await db.execute(
        select(func.count()).where(
            Module.user_id == user_id,
            Module.status == "completed",
        )
    )
    completed_count = count_result.scalar() or 0

    checks = [
        (completed_count >= 1, "first_steps"),
        (completed_count >= 5, "knowledge_seeker"),
        (completed_count >= 10, "scholar"),
        (first_attempt_perfect, "clean_sweep"),
        (used_remediation, "comeback_kid"),
        (streak_count >= 3, "streak_starter"),
        (streak_count >= 7, "hot_streak"),
        (streak_count >= 14, "dedicated"),
    ]

    newly_earned = []
    for condition, slug in checks:
        if condition:
            awarded = await _award_if_not_earned(user_id, slug, db)
            if awarded:
                newly_earned.append(slug)

    if newly_earned:
        await db.commit()

    return newly_earned


async def get_user_achievements(user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    """Returns all achievements earned by the user, ordered by when they were earned."""
    result = await db.execute(
        select(Achievement, UserAchievement.earned_at)
        .join(UserAchievement, Achievement.id == UserAchievement.achievement_id)
        .where(UserAchievement.user_id == user_id)
        .order_by(UserAchievement.earned_at)
    )
    return [
        {
            "slug": a.slug,
            "name": a.name,
            "description": a.description,
            "icon_emoji": a.icon_emoji,
            "earned_at": earned_at,
        }
        for a, earned_at in result.all()
    ]
