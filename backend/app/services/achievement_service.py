import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gamification import Achievement, UserAchievement
from app.models.learning import Module, Passage
from app.services import feed_service

# ---------------------------------------------------------------------------
# Mastery bar tier definitions (threshold within a 100-concept level cycle)
# ---------------------------------------------------------------------------
_MASTERY_TIERS = [
    (1,   "seed",   "Seed",   "🌱"),
    (25,  "sprout", "Sprout", "🌿"),
    (50,  "leaf",   "Leaf",   "🍃"),
    (75,  "tree",   "Tree",   "🌳"),
    (100, "forest", "Forest", "🌲"),
]

# ---------------------------------------------------------------------------
# Streak milestone definitions  (days, slug_key, name, emoji)
# ---------------------------------------------------------------------------
_STREAK_TIERS = [
    (3,   "dew_3",     "Dew",    "💧"),
    (7,   "mist_7",    "Mist",   "🌫️"),
    (14,  "rain_14",   "Rain",   "🌧️"),
    (21,  "sun_21",    "Sun",    "☀️"),
    (30,  "moon_30",   "Moon",   "🌙"),
    (60,  "star_60",   "Star",   "⭐"),
    (90,  "cloud_90",  "Cloud",  "☁️"),
    (100, "peak_100",  "Peak",   "🏔️"),
    (150, "ridge_150", "Ridge",  "🏔️"),
    (200, "river_200", "River",  "🌊"),
    (250, "meadow_250","Meadow", "🌾"),
    (300, "valley_300","Valley", "🏞️"),
    (350, "summit_350","Summit", "🗻"),
    (365, "aurora_365","Aurora", "🌌"),
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _award_if_not_earned(user_id: uuid.UUID, slug: str, db: AsyncSession) -> bool:
    """Awards a pre-seeded achievement if the user doesn't already have it."""
    ach_result = await db.execute(select(Achievement).where(Achievement.slug == slug))
    achievement = ach_result.scalar_one_or_none()
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


async def _award_dynamic(
    user_id: uuid.UUID,
    slug: str,
    name: str,
    description: str,
    icon_emoji: str,
    db: AsyncSession,
) -> bool:
    """
    Like _award_if_not_earned but creates the Achievement row if it doesn't exist yet.
    Used for higher-level mastery milestones (Lv.2+) that aren't pre-seeded.
    """
    ach_result = await db.execute(select(Achievement).where(Achievement.slug == slug))
    achievement = ach_result.scalar_one_or_none()

    if achievement is None:
        achievement = Achievement(
            slug=slug, name=name, description=description, icon_emoji=icon_emoji
        )
        db.add(achievement)
        await db.flush()

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


async def _max_concepts_in_any_module(user_id: uuid.UUID, db: AsyncSession) -> int:
    """Returns the highest completed-passage count across all of the user's modules."""
    subq = (
        select(func.count(Passage.id).label("cnt"))
        .join(Module, Passage.module_id == Module.id)
        .where(Module.user_id == user_id, Passage.status == "completed")
        .group_by(Passage.module_id)
        .subquery()
    )
    result = await db.execute(select(func.max(subq.c.cnt)))
    return result.scalar() or 0


async def _modules_with_any_concept(user_id: uuid.UUID, db: AsyncSession) -> int:
    """Returns the count of modules that have at least 1 completed passage."""
    result = await db.execute(
        select(func.count(func.distinct(Passage.module_id)))
        .join(Module, Passage.module_id == Module.id)
        .where(Module.user_id == user_id, Passage.status == "completed")
    )
    return result.scalar() or 0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def check_and_award_achievements(
    user_id: uuid.UUID,
    db: AsyncSession,
    streak_count: int = 0,
    total_concepts: int = 0,
) -> list[str]:
    """
    Checks all achievement conditions and awards any newly earned ones.
    Returns a list of newly earned achievement slugs (empty if none).
    Called automatically after each concept (passage) is completed.
    """
    newly_earned: list[str] = []

    # ------------------------------------------------------------------
    # 1. Mastery bar milestones (level-based, infinite levels)
    # ------------------------------------------------------------------
    if total_concepts > 0:
        max_level = (total_concepts - 1) // 100 + 1
        for n in range(1, max_level + 1):
            base = (n - 1) * 100
            for threshold, tier_key, tier_name, emoji in _MASTERY_TIERS:
                required = base + threshold
                if total_concepts >= required:
                    slug = f"mastery_{tier_key}_lv{n}"
                    lv_label = f" (Lv.{n})" if n > 1 else ""
                    awarded = await _award_dynamic(
                        user_id, slug,
                        f"{tier_name}{lv_label}",
                        f"{required} concept{'s' if required > 1 else ''} mastered",
                        emoji, db,
                    )
                    if awarded:
                        newly_earned.append(slug)

    # ------------------------------------------------------------------
    # 2. Badge locker
    # ------------------------------------------------------------------

    # First Leaf — first concept ever
    if total_concepts >= 1:
        if await _award_if_not_earned(user_id, "badge_first_leaf", db):
            newly_earned.append("badge_first_leaf")

    # Deep Root (10 in one module) + Wildwood (25 in one module)
    max_in_module = await _max_concepts_in_any_module(user_id, db)
    if max_in_module >= 10:
        if await _award_if_not_earned(user_id, "badge_deep_root", db):
            newly_earned.append("badge_deep_root")
    if max_in_module >= 25:
        if await _award_if_not_earned(user_id, "badge_wildwood", db):
            newly_earned.append("badge_wildwood")

    # Planter (3 modules each with ≥1 concept) + Explorer (10 concepts across 3 modules)
    modules_with_concepts = await _modules_with_any_concept(user_id, db)
    if modules_with_concepts >= 3:
        if await _award_if_not_earned(user_id, "badge_planter", db):
            newly_earned.append("badge_planter")
    if total_concepts >= 10 and modules_with_concepts >= 3:
        if await _award_if_not_earned(user_id, "badge_explorer", db):
            newly_earned.append("badge_explorer")

    # ------------------------------------------------------------------
    # 3. Streak milestones
    # ------------------------------------------------------------------
    for days, key, name, emoji in _STREAK_TIERS:
        if streak_count >= days:
            if await _award_if_not_earned(user_id, f"streak_{key}", db):
                newly_earned.append(f"streak_{key}")

    # ------------------------------------------------------------------
    # Commit + post feed events
    # ------------------------------------------------------------------
    if newly_earned:
        await db.commit()

    for slug in newly_earned:
        ach_result = await db.execute(select(Achievement).where(Achievement.slug == slug))
        achievement = ach_result.scalar_one_or_none()
        if achievement:
            await feed_service.post_activity(
                user_id=user_id,
                activity_type="achievement_earned",
                metadata={
                    "slug": achievement.slug,
                    "name": achievement.name,
                    "icon_emoji": achievement.icon_emoji,
                },
                db=db,
            )

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
