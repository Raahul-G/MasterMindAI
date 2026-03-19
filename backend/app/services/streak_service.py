import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gamification import Streak


async def update_streak(user_id: uuid.UUID, db: AsyncSession) -> Streak:
    """
    Updates the user's streak when they complete a module.
    - No record yet        → creates streak at 1
    - Last activity today  → no change (already counted today)
    - Last activity yesterday → increments by 1
    - Last activity older  → resets to 1
    Always updates longest_streak if current exceeds it.
    """
    result = await db.execute(select(Streak).where(Streak.user_id == user_id))
    streak = result.scalar_one_or_none()
    today = date.today()

    if not streak:
        streak = Streak(
            user_id=user_id,
            current_streak=1,
            longest_streak=1,
            last_activity_date=today,
        )
        db.add(streak)
        await db.commit()
        await db.refresh(streak)
        return streak

    if streak.last_activity_date == today:
        return streak  # Already updated today — no change

    yesterday = date.fromordinal(today.toordinal() - 1)
    if streak.last_activity_date == yesterday:
        streak.current_streak += 1
    else:
        streak.current_streak = 1

    if streak.current_streak > streak.longest_streak:
        streak.longest_streak = streak.current_streak

    streak.last_activity_date = today
    await db.commit()
    await db.refresh(streak)
    return streak


async def get_streak(user_id: uuid.UUID, db: AsyncSession) -> Streak | None:
    """Returns the user's streak record, or None if no modules completed yet."""
    result = await db.execute(select(Streak).where(Streak.user_id == user_id))
    return result.scalar_one_or_none()
