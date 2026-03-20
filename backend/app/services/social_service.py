import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gamification import Streak
from app.models.social import Friendship
from app.models.user import User


async def send_friend_request(
    requester_id: uuid.UUID, addressee_id: uuid.UUID, db: AsyncSession
) -> Friendship:
    """
    Creates a pending friend request.
    Raises ValueError if:
    - requester tries to add themselves
    - a friendship row already exists in either direction
    """
    if requester_id == addressee_id:
        raise ValueError("You cannot send a friend request to yourself.")

    existing = await db.execute(
        select(Friendship).where(
            or_(
                (Friendship.requester_id == requester_id) & (Friendship.addressee_id == addressee_id),
                (Friendship.requester_id == addressee_id) & (Friendship.addressee_id == requester_id),
            )
        )
    )
    if existing.scalar_one_or_none():
        raise ValueError("A friendship or pending request already exists between these users.")

    friendship = Friendship(requester_id=requester_id, addressee_id=addressee_id)
    db.add(friendship)
    await db.commit()
    await db.refresh(friendship)
    return friendship


async def accept_friend_request(
    friendship_id: uuid.UUID, current_user_id: uuid.UUID, db: AsyncSession
) -> Friendship:
    """
    Accepts a pending friend request.
    Raises ValueError if the friendship doesn't exist or the current user is not the addressee.
    """
    result = await db.execute(select(Friendship).where(Friendship.id == friendship_id))
    friendship = result.scalar_one_or_none()

    if not friendship:
        raise ValueError("Friend request not found.")
    if friendship.addressee_id != current_user_id:
        raise ValueError("You can only accept requests sent to you.")
    if friendship.status != "pending":
        raise ValueError("This request has already been resolved.")

    friendship.status = "accepted"
    await db.commit()
    await db.refresh(friendship)
    return friendship


async def get_friends(user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    """
    Returns all accepted friends with their current streak.
    Each friend can be either the requester or the addressee in the friendship row.
    """
    result = await db.execute(
        select(Friendship).where(
            Friendship.status == "accepted",
            or_(
                Friendship.requester_id == user_id,
                Friendship.addressee_id == user_id,
            ),
        )
    )
    friendships = result.scalars().all()

    friend_ids = [
        f.addressee_id if f.requester_id == user_id else f.requester_id
        for f in friendships
    ]
    if not friend_ids:
        return []

    users_result = await db.execute(select(User).where(User.id.in_(friend_ids)))
    users = {u.id: u for u in users_result.scalars().all()}

    streaks_result = await db.execute(select(Streak).where(Streak.user_id.in_(friend_ids)))
    streaks = {s.user_id: s.current_streak for s in streaks_result.scalars().all()}

    return [
        {
            "id": uid,
            "full_name": users[uid].full_name,
            "avatar_url": users[uid].avatar_url,
            "current_streak": streaks.get(uid, 0),
        }
        for uid in friend_ids
        if uid in users
    ]


async def get_friend_requests(user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    """Returns all incoming pending friend requests for the current user."""
    result = await db.execute(
        select(Friendship).where(
            Friendship.addressee_id == user_id,
            Friendship.status == "pending",
        )
    )
    friendships = result.scalars().all()
    if not friendships:
        return []

    requester_ids = [f.requester_id for f in friendships]
    users_result = await db.execute(select(User).where(User.id.in_(requester_ids)))
    users = {u.id: u for u in users_result.scalars().all()}

    return [
        {
            "id": f.id,
            "requester": {
                "id": f.requester_id,
                "full_name": users[f.requester_id].full_name,
                "avatar_url": users[f.requester_id].avatar_url,
            },
            "created_at": f.created_at,
        }
        for f in friendships
        if f.requester_id in users
    ]


async def search_users(
    query: str, current_user_id: uuid.UUID, db: AsyncSession
) -> list[dict]:
    """
    Returns users whose full_name contains the search term (case-insensitive).
    Excludes the current user from results.
    Limited to 20 results.
    """
    result = await db.execute(
        select(User)
        .where(
            User.full_name.ilike(f"%{query}%"),
            User.id != current_user_id,
        )
        .limit(20)
    )
    users = result.scalars().all()
    return [
        {"id": u.id, "full_name": u.full_name, "avatar_url": u.avatar_url}
        for u in users
    ]
