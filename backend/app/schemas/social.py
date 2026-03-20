import uuid
from datetime import datetime

from pydantic import BaseModel


class FriendRequestBody(BaseModel):
    addressee_id: uuid.UUID


class FriendAcceptBody(BaseModel):
    friendship_id: uuid.UUID


class UserSummary(BaseModel):
    id: uuid.UUID
    full_name: str
    avatar_url: str | None


class FriendResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    avatar_url: str | None
    current_streak: int


class FriendRequestResponse(BaseModel):
    id: uuid.UUID
    requester: UserSummary
    created_at: datetime


class ActivityFeedItem(BaseModel):
    id: uuid.UUID
    user: UserSummary
    activity_type: str
    metadata: dict
    created_at: datetime


class UserSearchResult(BaseModel):
    id: uuid.UUID
    full_name: str
    avatar_url: str | None
