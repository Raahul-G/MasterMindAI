from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.learning import Module, Passage
from app.models.user import User
from app.schemas.gamification import AchievementResponse, StreakResponse
from app.services import achievement_service, streak_service

router = APIRouter(prefix="/gamification", tags=["gamification"])


@router.get("/streak", response_model=StreakResponse)
async def get_streak(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns the user's current streak and total concepts learned across all modules."""
    streak = await streak_service.get_streak(current_user.id, db)

    total_result = await db.execute(
        select(func.count(Passage.id))
        .join(Module, Passage.module_id == Module.id)
        .where(Module.user_id == current_user.id, Passage.status == "completed")
    )
    total_concepts = total_result.scalar() or 0

    if streak is None:
        return StreakResponse(
            current_streak=0, longest_streak=0,
            last_activity_date=None, total_concepts=total_concepts,
        )
    return StreakResponse(
        current_streak=streak.current_streak,
        longest_streak=streak.longest_streak,
        last_activity_date=streak.last_activity_date,
        total_concepts=total_concepts,
    )


@router.get("/achievements", response_model=list[AchievementResponse])
async def get_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns all achievements earned by the user, ordered by when they were earned."""
    achievements = await achievement_service.get_user_achievements(current_user.id, db)
    return achievements
