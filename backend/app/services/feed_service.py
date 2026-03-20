import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.social import ActivityFeed, Friendship
from app.models.user import User


async def post_activity(
    user_id: uuid.UUID,
    activity_type: str,
    metadata: dict,
    db: AsyncSession,
) -> None:
    """
    Inserts one event into the activity feed.
    Called internally after module completion or achievement award — never from a router.
    """
    db.add(ActivityFeed(user_id=user_id, activity_type=activity_type, event_metadata=metadata))
    await db.commit()


async def get_feed(user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    """
    Returns the 50 most recent activity events from the user and their accepted friends.
    Each item includes a user summary so the frontend can display names and avatars.
    """
    friendships_result = await db.execute(
        select(Friendship).where(
            Friendship.status == "accepted",
            or_(
                Friendship.requester_id == user_id,
                Friendship.addressee_id == user_id,
            ),
        )
    )
    friendships = friendships_result.scalars().all()
    friend_ids = [
        f.addressee_id if f.requester_id == user_id else f.requester_id
        for f in friendships
    ]

    visible_ids = friend_ids + [user_id]

    feed_result = await db.execute(
        select(ActivityFeed)
        .where(ActivityFeed.user_id.in_(visible_ids))
        .order_by(ActivityFeed.created_at.desc())
        .limit(50)
    )
    events = feed_result.scalars().all()
    if not events:
        return []

    event_user_ids = list({e.user_id for e in events})
    users_result = await db.execute(select(User).where(User.id.in_(event_user_ids)))
    users = {u.id: u for u in users_result.scalars().all()}

    return [
        {
            "id": e.id,
            "user": {
                "id": e.user_id,
                "full_name": users[e.user_id].full_name if e.user_id in users else "Unknown",
                "avatar_url": users[e.user_id].avatar_url if e.user_id in users else None,
            },
            "activity_type": e.activity_type,
            "metadata": e.event_metadata,
            "created_at": e.created_at,
        }
        for e in events
    ]
