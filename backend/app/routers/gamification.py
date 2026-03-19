from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.gamification import AchievementResponse, StreakResponse
from app.services import achievement_service, streak_service

router = APIRouter(prefix="/gamification", tags=["gamification"])


@router.get("/streak", response_model=StreakResponse)
async def get_streak(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns the user's current streak. Returns zeros if no modules completed yet."""
    streak = await streak_service.get_streak(current_user.id, db)
    if streak is None:
        return StreakResponse(current_streak=0, longest_streak=0, last_activity_date=None)
    return streak


@router.get("/achievements", response_model=list[AchievementResponse])
async def get_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns all achievements earned by the user, ordered by when they were earned."""
    achievements = await achievement_service.get_user_achievements(current_user.id, db)
    return achievements
