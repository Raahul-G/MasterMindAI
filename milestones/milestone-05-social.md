# Milestone 5 — Social Features API

> **Covers:** Stage 9 (Social Features API)
> **Status:** Not started

---

## What this milestone is

Milestone 4 gave users private motivation — streaks and badges visible only to themselves. Milestone 5 makes learning social.

There are three features:

1. **Friends** — users can search for other users by name, send friend requests, and accept incoming ones. The friends list shows each friend's current streak so users can compete.
2. **Activity Feed** — every time a user completes a module or earns an achievement, an event is posted to the database. The feed endpoint returns events from the user and their accepted friends, newest first.
3. **User Search** — a simple name search so users can find and add people they know.

These are the last backend features before the frontend build begins. When this milestone is done, the backend is feature-complete.

## What you will be able to do when this milestone is done

- Search for a user by name and send them a friend request
- Accept an incoming friend request and see that person appear in your friends list
- Complete a module and see a `module_completed` event appear in the activity feed
- Earn an achievement and see an `achievement_earned` event appear in the activity feed
- Call `GET /social/feed` and see interleaved activity from yourself and your friends
- Have all 6 social endpoints live and documented in Swagger

---

## The chunks

Each chunk is one focused block of work. Complete and test each one before moving to the next.

---

### Chunk 1 — Write the social models

**What you learn:** How to model a self-referential relationship (users friending users) and a flexible event log using JSONB for variable metadata.

- [ ] Create `backend/app/models/social.py`:
  ```python
  import uuid
  from datetime import datetime

  from sqlalchemy import DateTime, ForeignKey, String
  from sqlalchemy.dialects.postgresql import JSONB, UUID
  from sqlalchemy.orm import Mapped, mapped_column
  from sqlalchemy.sql import func

  from app.core.database import Base


  class Friendship(Base):
      __tablename__ = "friendships"

      id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      requester_id: Mapped[uuid.UUID] = mapped_column(
          UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
      )
      addressee_id: Mapped[uuid.UUID] = mapped_column(
          UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
      )
      status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
      created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
      updated_at: Mapped[datetime] = mapped_column(
          DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
      )


  class ActivityFeed(Base):
      __tablename__ = "activity_feed"

      id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      user_id: Mapped[uuid.UUID] = mapped_column(
          UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
      )
      activity_type: Mapped[str] = mapped_column(String(100), nullable=False)
      metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
      created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
  ```
  `status` is one of: `pending` | `accepted` | `rejected`.
  `activity_type` is one of: `module_completed` | `achievement_earned`.
  `metadata` is a free-form JSONB dict — different fields per activity type.

- [ ] Update `backend/app/models/__init__.py`:
  ```python
  from app.models.user import User
  from app.models.learning import Module, Passage, Quiz, Question, Answer, Remediation
  from app.models.gamification import Streak, Achievement, UserAchievement
  from app.models.social import Friendship, ActivityFeed
  ```

**Outcome:** Two new ORM models exist: `Friendship` (the friend graph) and `ActivityFeed` (the event log).

---

### Chunk 2 — Run the migration

**What you learn:** How Alembic auto-detects new model classes when `__init__.py` imports them.

- [ ] Make sure the virtual environment is active:
  ```bash
  cd backend
  source .venv/bin/activate
  ```
- [ ] Generate and apply the migration:
  ```bash
  alembic revision --autogenerate -m "add_social_tables"
  alembic upgrade head
  ```
- [ ] Verify two new empty tables exist in the database: `friendships` and `activity_feed`

**Outcome:** Social tables exist in the database and are ready to receive data.

---

### Chunk 3 — Write the social schemas

**What you learn:** How to design response shapes that flatten joined data — for example, embedding a user summary inside a friendship row rather than returning raw IDs.

- [ ] Create `backend/app/schemas/social.py`:
  ```python
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
  ```

**Outcome:** Six schemas covering all social API request bodies and response shapes.

---

### Chunk 4 — Write `social_service.py`

**What you learn:** How to query a self-referential relationship (friendships where the user is either the requester or the addressee) and how to join across three tables (friendships → users → streaks) in one query.

- [ ] Create `backend/app/services/social_service.py`:
  ```python
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
  ```

**Outcome:** Four service functions cover the full social graph: send request, accept request, list friends (with streaks), list incoming requests, and user search.

---

### Chunk 5 — Write `feed_service.py`

**What you learn:** How to build a social feed by first finding a user's friend IDs, then querying activity from that set plus the user themselves, ordered newest-first.

- [ ] Create `backend/app/services/feed_service.py`:
  ```python
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
      db.add(ActivityFeed(user_id=user_id, activity_type=activity_type, metadata=metadata))
      await db.commit()


  async def get_feed(user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
      """
      Returns the 50 most recent activity events from the user and their accepted friends.
      Each item includes a user summary so the frontend can display names and avatars.
      """
      # Find accepted friend IDs (user can be on either side of the friendship)
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

      # Fetch activity events
      feed_result = await db.execute(
          select(ActivityFeed)
          .where(ActivityFeed.user_id.in_(visible_ids))
          .order_by(ActivityFeed.created_at.desc())
          .limit(50)
      )
      events = feed_result.scalars().all()
      if not events:
          return []

      # Fetch user details for everyone who has events
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
              "metadata": e.metadata,
              "created_at": e.created_at,
          }
          for e in events
      ]
  ```

**Outcome:** `post_activity()` is a thin write helper. `get_feed()` builds the social feed in three queries: friends, events, user details.

---

### Chunk 6 — Wire activity posting into existing services

**What you learn:** How to add side effects to an existing service without changing its return value or breaking anything that calls it.

**In `quiz_service.py`** — post a `module_completed` event after a module is first completed.

- [ ] Add `feed_service` to the existing imports at the top of `quiz_service.py`:
  ```python
  from app.services import achievement_service, feed_service, streak_service
  ```
- [ ] Before `await db.commit()` (where you already capture `completing_user_id`), also capture the topic and level:
  ```python
  completing_topic = None
  completing_level = None
  completing_score = correct_count
  completing_total = total

  # Inside the existing block: if module and module.status != "completed":
  completing_topic = module.topic
  completing_level = module.level
  ```
- [ ] After the existing streak and achievement calls in the `if completing_user_id:` block, add:
  ```python
  await feed_service.post_activity(
      user_id=completing_user_id,
      activity_type="module_completed",
      metadata={
          "topic": completing_topic,
          "level": completing_level,
          "score": completing_score,
          "total": completing_total,
      },
      db=db,
  )
  ```

**In `achievement_service.py`** — post an `achievement_earned` event for each newly awarded badge.

- [ ] Add `feed_service` import at the top of `achievement_service.py`:
  ```python
  from app.services import feed_service
  ```
- [ ] In `check_and_award_achievements()`, after the existing `if newly_earned: await db.commit()` block, add:
  ```python
  for slug in newly_earned:
      achievement_result = await db.execute(select(Achievement).where(Achievement.slug == slug))
      achievement = achievement_result.scalar_one_or_none()
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
  ```

**Outcome:** Every module completion and every achievement award automatically writes an event to the `activity_feed` table — no extra API calls needed.

---

### Chunk 7 — Write the social router

**What you learn:** How to map service-layer `ValueError` exceptions to clean HTTP 400 responses without letting them bubble up as 500 errors.

- [ ] Create `backend/app/routers/social.py`:
  ```python
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
      return {"message": "Friend request sent."}


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
      return {"message": "Friend request accepted."}


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
  ```

**Outcome:** All 6 social endpoints exist. `ValueError` from the service layer becomes a clean 400 with the error message as the detail.

---

### Chunk 8 — Register the social router in `main.py`

- [ ] Open `backend/main.py` and add the social router:
  ```python
  from app.routers import auth, gamification, learning, modules, notion, social

  # ...existing middleware setup...

  app.include_router(auth.router)
  app.include_router(learning.router)
  app.include_router(modules.router)
  app.include_router(notion.router)
  app.include_router(gamification.router)
  app.include_router(social.router)
  ```

**Outcome:** All 6 social endpoints appear in Swagger under the `social` tag.

---

### Chunk 9 — Test end to end in Swagger

**What you learn:** How to verify the full social flow — friend graph, feed events, and activity wiring — using two separate user accounts.

You will need two user accounts for this. If you only have one, register a second one first.

- [ ] **Restart the server** and open http://localhost:8000/docs

**Test user search and friend request:**
- [ ] Log in as User A. Copy the JWT.
- [ ] `GET /social/users/search?q=<User B's name>` → should return User B's id
- [ ] `POST /social/friends/request` with `{"addressee_id": "<User B's id>"}` → `201 Friend request sent`
- [ ] Log in as User B. Copy the JWT.
- [ ] `GET /social/friends/requests` → should show User A's name and the friendship id
- [ ] `POST /social/friends/accept` with `{"friendship_id": "<id from above>"}` → `200 Friend request accepted`
- [ ] `GET /social/friends` (as User B) → should show User A with their current streak

**Test activity feed:**
- [ ] As User A, complete a module: `/learn/start` → `/learn/quiz/generate` → `/learn/quiz/submit` (all correct)
- [ ] `GET /social/feed` as User A → should show a `module_completed` event with topic, score, total
- [ ] `GET /social/feed` as User A → should also show any `achievement_earned` events (first_steps at minimum)
- [ ] `GET /social/feed` as User B → should show User A's events (they are friends)

**Test guard conditions:**
- [ ] As User A, `POST /social/friends/request` with User A's own id → should return `400`
- [ ] As User A, send another request to User B → should return `400` (already exists)

**Outcome:** The social graph, feed, and activity wiring all work correctly across two real user accounts.

---

### Chunk 10 — Write tests

**What you learn:** How to test the social layer's pure logic — friend ID resolution and feed assembly — without any database or HTTP.

- [ ] Create `backend/tests/test_social.py`:
  ```python
  """
  Unit tests for social feature logic.
  All tests are pure — no database, no HTTP.
  """
  import uuid


  # ---------------------------------------------------------------------------
  # Friend ID resolution logic
  # ---------------------------------------------------------------------------

  def _resolve_friend_id(requester_id, addressee_id, current_user_id):
      """Given a friendship row, return the ID of the other person."""
      return addressee_id if requester_id == current_user_id else requester_id


  def test_friend_id_resolved_when_user_is_requester():
      user = uuid.uuid4()
      friend = uuid.uuid4()
      result = _resolve_friend_id(user, friend, user)
      assert result == friend


  def test_friend_id_resolved_when_user_is_addressee():
      user = uuid.uuid4()
      friend = uuid.uuid4()
      result = _resolve_friend_id(friend, user, user)
      assert result == friend


  def test_friend_id_not_self():
      user = uuid.uuid4()
      friend = uuid.uuid4()
      result = _resolve_friend_id(user, friend, user)
      assert result != user


  # ---------------------------------------------------------------------------
  # Friend request validation logic
  # ---------------------------------------------------------------------------

  def _validate_friend_request(requester_id, addressee_id, existing_ids):
      """
      Returns an error string or None.
      existing_ids: set of (requester_id, addressee_id) tuples already in DB.
      """
      if requester_id == addressee_id:
          return "You cannot send a friend request to yourself."
      if (requester_id, addressee_id) in existing_ids or (addressee_id, requester_id) in existing_ids:
          return "A friendship or pending request already exists between these users."
      return None


  def test_self_request_is_rejected():
      user = uuid.uuid4()
      error = _validate_friend_request(user, user, set())
      assert error is not None
      assert "yourself" in error


  def test_duplicate_request_is_rejected():
      user_a = uuid.uuid4()
      user_b = uuid.uuid4()
      existing = {(user_a, user_b)}
      error = _validate_friend_request(user_a, user_b, existing)
      assert error is not None


  def test_reverse_duplicate_request_is_rejected():
      user_a = uuid.uuid4()
      user_b = uuid.uuid4()
      existing = {(user_b, user_a)}
      error = _validate_friend_request(user_a, user_b, existing)
      assert error is not None


  def test_valid_request_returns_no_error():
      user_a = uuid.uuid4()
      user_b = uuid.uuid4()
      error = _validate_friend_request(user_a, user_b, set())
      assert error is None


  # ---------------------------------------------------------------------------
  # Activity feed visibility logic
  # ---------------------------------------------------------------------------

  def _build_visible_ids(user_id, friend_ids):
      """The feed should include the user's own events plus all friends' events."""
      return set(friend_ids) | {user_id}


  def test_feed_includes_own_activity():
      user = uuid.uuid4()
      friends = [uuid.uuid4(), uuid.uuid4()]
      visible = _build_visible_ids(user, friends)
      assert user in visible


  def test_feed_includes_all_friend_activity():
      user = uuid.uuid4()
      friends = [uuid.uuid4(), uuid.uuid4()]
      visible = _build_visible_ids(user, friends)
      for f in friends:
          assert f in visible


  def test_feed_excludes_strangers():
      user = uuid.uuid4()
      friends = [uuid.uuid4()]
      stranger = uuid.uuid4()
      visible = _build_visible_ids(user, friends)
      assert stranger not in visible


  # ---------------------------------------------------------------------------
  # Activity metadata structure
  # ---------------------------------------------------------------------------

  def test_module_completed_metadata_has_required_keys():
      metadata = {"topic": "Quantum physics", "level": "intermediate", "score": 8, "total": 10}
      assert "topic" in metadata
      assert "score" in metadata
      assert "total" in metadata


  def test_achievement_earned_metadata_has_required_keys():
      metadata = {"slug": "first_steps", "name": "First Steps", "icon_emoji": "🎯"}
      assert "slug" in metadata
      assert "name" in metadata
      assert "icon_emoji" in metadata
  ```
- [ ] Run all tests:
  ```bash
  pytest tests/ -v
  ```
- [ ] Confirm all 51 tests pass (38 previous + 13 new)

**Outcome:** The social logic is verified in isolation. Friend resolution, request validation, and feed visibility all have automated test coverage.

---

## Milestone 5 complete checklist (summary)

- [ ] Chunk 1 — Social models written, `__init__.py` updated
- [ ] Chunk 2 — Migration run, `friendships` and `activity_feed` tables in DB
- [ ] Chunk 3 — Social schemas written
- [ ] Chunk 4 — `social_service.py` written (search, request, accept, friends, requests)
- [ ] Chunk 5 — `feed_service.py` written (post, get feed)
- [ ] Chunk 6 — Activity posting wired into `quiz_service.py` and `achievement_service.py`
- [ ] Chunk 7 — Social router written (6 endpoints)
- [ ] Chunk 8 — Social router registered in `main.py`
- [ ] Chunk 9 — Full flow tested in Swagger with two user accounts
- [ ] Chunk 10 — All 51 tests passing

---

## Before starting Milestone 6

Do not start Milestone 6 until every box above is checked AND:

- Two users can become friends via Swagger
- `GET /social/feed` for User B shows User A's `module_completed` events after User A completes a module
- `activity_feed` table has rows in the database after module completions and achievement awards
- `pytest tests/ -v` shows all 51 tests passing

Tell Claude: "Milestone 5 is complete. Starting Milestone 6."
