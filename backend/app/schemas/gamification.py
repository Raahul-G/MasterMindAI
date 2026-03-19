from datetime import date, datetime

from pydantic import BaseModel


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    last_activity_date: date | None

    model_config = {"from_attributes": True}


class AchievementResponse(BaseModel):
    slug: str
    name: str
    description: str
    icon_emoji: str
    earned_at: datetime
