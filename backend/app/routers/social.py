import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.social import (
    ActivityFeedItem,
    FriendAcceptBody,
    FriendRequestBody,
    FriendRequestResponse,
    FriendResponse,
    UserSearchResult,
)
from app.services import feed_service, social_service

router = APIRouter(prefix="/social", tags=["social"])


@router.get("/friends", response_model=list[FriendResponse])
async def get_friends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns all accepted friends with their current streak."""
    return await social_service.get_friends(current_user.id, db)


@router.get("/friends/requests", response_model=list[FriendRequestResponse])
async def get_friend_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns all incoming pending friend requests."""
    return await social_service.get_friend_requests(current_user.id, db)


@router.post("/friends/request", status_code=201)
async def send_friend_request(
    body: FriendRequestBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sends a friend request to another user."""
    try:
        await social_service.send_friend_request(current_user.id, body.addressee_id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"data": {"message": "Friend request sent."}}


@router.post("/friends/accept")
async def accept_friend_request(
    body: FriendAcceptBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Accepts a pending friend request."""
    try:
        await social_service.accept_friend_request(body.friendship_id, current_user.id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"data": {"message": "Friend request accepted."}}


@router.get("/feed", response_model=list[ActivityFeedItem])
async def get_feed(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns the 50 most recent activity events from the user and their friends."""
    return await feed_service.get_feed(current_user.id, db)


@router.get("/users/search", response_model=list[UserSearchResult])
async def search_users(
    q: str = Query(min_length=2, description="Search term (minimum 2 characters)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Searches users by name. Returns up to 20 results, excluding the current user."""
    return await social_service.search_users(q, current_user.id, db)
