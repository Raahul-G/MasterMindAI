"""
Populates the achievements catalogue with all 8 badge definitions.
Safe to run multiple times — skips any slugs that already exist.

Usage (from inside backend/):
    python -m scripts.seed_achievements
"""
import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.gamification import Achievement

ACHIEVEMENTS = [
    {
        "slug": "first_steps",
        "name": "First Steps",
        "description": "Complete your first learning module.",
        "icon_emoji": "🎯",
    },
    {
        "slug": "knowledge_seeker",
        "name": "Knowledge Seeker",
        "description": "Complete 5 learning modules.",
        "icon_emoji": "📚",
    },
    {
        "slug": "scholar",
        "name": "Scholar",
        "description": "Complete 10 learning modules.",
        "icon_emoji": "🎓",
    },
    {
        "slug": "clean_sweep",
        "name": "Clean Sweep",
        "description": "Pass a quiz on your first attempt with a perfect score.",
        "icon_emoji": "✨",
    },
    {
        "slug": "comeback_kid",
        "name": "Comeback Kid",
        "description": "Pass a module after going through remediation.",
        "icon_emoji": "💪",
    },
    {
        "slug": "streak_starter",
        "name": "Streak Starter",
        "description": "Maintain a 3-day learning streak.",
        "icon_emoji": "🔥",
    },
    {
        "slug": "hot_streak",
        "name": "Hot Streak",
        "description": "Maintain a 7-day learning streak.",
        "icon_emoji": "⚡",
    },
    {
        "slug": "dedicated",
        "name": "Dedicated Learner",
        "description": "Maintain a 14-day learning streak.",
        "icon_emoji": "🏆",
    },
]


async def seed():
    async with AsyncSessionLocal() as db:
        added = 0
        for data in ACHIEVEMENTS:
            result = await db.execute(select(Achievement).where(Achievement.slug == data["slug"]))
            if not result.scalar_one_or_none():
                db.add(Achievement(**data))
                added += 1
        await db.commit()
        print(f"Done. Added {added} new achievements ({len(ACHIEVEMENTS) - added} already existed).")


asyncio.run(seed())
