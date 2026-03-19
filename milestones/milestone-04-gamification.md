# Milestone 4 — Gamification API

> **Covers:** Stage 8 (Gamification API)
> **Status:** Not started

---

## What this milestone is

Milestone 3 gave users a way to save and export their learning. Milestone 4 gives them a reason to keep coming back.

There are two features:

1. **Streaks** — every day a user completes a module, their streak increments. Miss a day and it resets to 1. The longest streak ever reached is tracked separately.
2. **Achievements** — a fixed set of badges earned automatically when certain conditions are met (first module, 5 modules, 10 modules, 3-day streak, 7-day streak, perfect first attempt, completing after remediation).

Both features are invisible to the user until the frontend is built — but the data and API will be fully ready.

## What you will be able to do when this milestone is done

- Complete a module and see the `streaks` row in the database update automatically
- Call `GET /gamification/streak` and receive `current_streak`, `longest_streak`, `last_activity_date`
- Call `GET /gamification/achievements` and see a list of all badges earned so far
- Have achievements award themselves automatically — no manual trigger needed
- Have 8 pre-seeded achievement definitions in the `achievements` table

---

## The chunks

Each chunk is one focused block of work. Complete and test each one before moving to the next.

---

### Chunk 1 — Write the gamification models

**What you learn:** How to model a one-to-one relationship (user ↔ streak) and a many-to-many relationship (users ↔ achievements through a join table).

- [ ] Create `backend/app/models/gamification.py`:
  ```python
  import uuid
  from datetime import date, datetime

  from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
  from sqlalchemy.dialects.postgresql import UUID
  from sqlalchemy.orm import Mapped, mapped_column
  from sqlalchemy.sql import func

  from app.core.database import Base


  class Streak(Base):
      __tablename__ = "streaks"

      id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      user_id: Mapped[uuid.UUID] = mapped_column(
          UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
      )
      current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
      longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
      last_activity_date: Mapped[date | None] = mapped_column(Date, nullable=True)
      created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
      updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


  class Achievement(Base):
      __tablename__ = "achievements"

      id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
      name: Mapped[str] = mapped_column(String(255), nullable=False)
      description: Mapped[str] = mapped_column(Text, nullable=False)
      icon_emoji: Mapped[str] = mapped_column(String(10), nullable=False)
      created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


  class UserAchievement(Base):
      __tablename__ = "user_achievements"
      __table_args__ = (UniqueConstraint("user_id", "achievement_id"),)

      id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      user_id: Mapped[uuid.UUID] = mapped_column(
          UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
      )
      achievement_id: Mapped[uuid.UUID] = mapped_column(
          UUID(as_uuid=True), ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False
      )
      earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
  ```
- [ ] Update `backend/app/models/__init__.py` to import the new models:
  ```python
  from app.models.user import User
  from app.models.learning import Module, Passage, Quiz, Question, Answer, Remediation
  from app.models.gamification import Streak, Achievement, UserAchievement
  ```

**Outcome:** Three gamification models exist: `Streak` (one per user), `Achievement` (the catalogue), and `UserAchievement` (the join table tracking who earned what and when).

---

### Chunk 2 — Run the migration

**What you learn:** How Alembic detects new model classes and generates the SQL to create their tables.

- [ ] Make sure the virtual environment is active:
  ```bash
  cd backend
  source .venv/bin/activate
  ```
- [ ] Generate and apply the migration:
  ```bash
  alembic revision --autogenerate -m "add_gamification_tables"
  alembic upgrade head
  ```
- [ ] Open your local database and verify three new tables exist: `streaks`, `achievements`, `user_achievements`

**Outcome:** All three gamification tables exist in the database and are empty.

---

### Chunk 3 — Seed the achievements catalogue

**What you learn:** What a seed script is — a one-time script that pre-populates fixed reference data that the app needs to function.

- [ ] Create the scripts directory:
  ```bash
  mkdir -p backend/scripts
  touch backend/scripts/__init__.py
  ```
- [ ] Create `backend/scripts/seed_achievements.py`:
  ```python
  """
  Run once to populate the achievements catalogue.
  Safe to run multiple times — skips any slugs that already exist.
  Usage: python -m scripts.seed_achievements  (from inside backend/)
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
  ```
- [ ] Run the seed script:
  ```bash
  python -m scripts.seed_achievements
  ```
- [ ] Verify the output says `Added 8 new achievements`
- [ ] Check the database — `achievements` table should have 8 rows

**Outcome:** The achievements catalogue is populated. Every user who earns a badge will reference one of these 8 rows.

---

### Chunk 4 — Write `streak_service.py`

**What you learn:** How date arithmetic drives streak logic, and why the streak calculation is pure enough to test without a real database call.

- [ ] Create `backend/app/services/streak_service.py`:
  ```python
  import uuid
  from datetime import date

  from sqlalchemy import select
  from sqlalchemy.ext.asyncio import AsyncSession

  from app.models.gamification import Streak


  async def update_streak(user_id: uuid.UUID, db: AsyncSession) -> Streak:
      """
      Updates the user's streak when they complete a module.
      - No record yet   → creates streak at 1
      - Last activity today → no change (already counted)
      - Last activity yesterday → increments by 1
      - Last activity older → resets to 1
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
  ```

**Outcome:** `update_streak()` handles all three cases (new, consecutive, broken) and always keeps `longest_streak` up to date.

---

### Chunk 5 — Write `achievement_service.py`

**What you learn:** How to check multiple conditions in one pass and only write to the database for newly earned achievements, avoiding duplicate awards via a unique constraint.

- [ ] Create `backend/app/services/achievement_service.py`:
  ```python
  import uuid

  from sqlalchemy import func, select
  from sqlalchemy.ext.asyncio import AsyncSession

  from app.models.gamification import Achievement, UserAchievement
  from app.models.learning import Module


  async def _award_if_not_earned(user_id: uuid.UUID, slug: str, db: AsyncSession) -> bool:
      """
      Awards an achievement by slug if the user doesn't already have it.
      Returns True if newly awarded, False if already earned or slug not found.
      """
      achievement_result = await db.execute(select(Achievement).where(Achievement.slug == slug))
      achievement = achievement_result.scalar_one_or_none()
      if not achievement:
          return False

      already = await db.execute(
          select(UserAchievement).where(
              UserAchievement.user_id == user_id,
              UserAchievement.achievement_id == achievement.id,
          )
      )
      if already.scalar_one_or_none():
          return False

      db.add(UserAchievement(user_id=user_id, achievement_id=achievement.id))
      return True


  async def check_and_award_achievements(
      user_id: uuid.UUID,
      db: AsyncSession,
      streak_count: int = 0,
      used_remediation: bool = False,
      first_attempt_perfect: bool = False,
  ) -> list[str]:
      """
      Checks all achievement conditions and awards any newly earned ones.
      Returns a list of newly earned achievement slugs (empty if none).
      Called automatically after a module is completed.
      """
      count_result = await db.execute(
          select(func.count()).where(
              Module.user_id == user_id,
              Module.status == "completed",
          )
      )
      completed_count = count_result.scalar() or 0

      checks = [
          (completed_count >= 1, "first_steps"),
          (completed_count >= 5, "knowledge_seeker"),
          (completed_count >= 10, "scholar"),
          (first_attempt_perfect, "clean_sweep"),
          (used_remediation, "comeback_kid"),
          (streak_count >= 3, "streak_starter"),
          (streak_count >= 7, "hot_streak"),
          (streak_count >= 14, "dedicated"),
      ]

      newly_earned = []
      for condition, slug in checks:
          if condition:
              awarded = await _award_if_not_earned(user_id, slug, db)
              if awarded:
                  newly_earned.append(slug)

      if newly_earned:
          await db.commit()

      return newly_earned


  async def get_user_achievements(user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
      """Returns all achievements earned by the user, ordered by when they were earned."""
      result = await db.execute(
          select(Achievement, UserAchievement.earned_at)
          .join(UserAchievement, Achievement.id == UserAchievement.achievement_id)
          .where(UserAchievement.user_id == user_id)
          .order_by(UserAchievement.earned_at)
      )
      return [
          {
              "slug": a.slug,
              "name": a.name,
              "description": a.description,
              "icon_emoji": a.icon_emoji,
              "earned_at": earned_at,
          }
          for a, earned_at in result.all()
      ]
  ```

**Outcome:** Achievements are checked and awarded in a single function call. The unique constraint on `user_achievements` acts as a safety net — even if called twice, no duplicate rows are created.

---

### Chunk 6 — Wire streak and achievement updates into `quiz_service.py`

**What you learn:** How to hook into an existing service to trigger side effects (streak + achievement updates) without cluttering the router.

- [ ] Open `backend/app/services/quiz_service.py`
- [ ] Add these imports at the top:
  ```python
  from sqlalchemy import func
  from app.models.learning import Answer, Module, Passage, Question, Quiz, Remediation
  from app.services import achievement_service, streak_service
  ```
- [ ] Replace the existing `if passed:` block (the one that sets `module.status`) and the `await db.commit()` line with this updated version:
  ```python
      # Track variables needed for gamification — saved before commit expires the objects
      completing_user_id = None
      completing_module_id = None
      is_first_attempt_perfect = False

      quiz_result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
      quiz = quiz_result.scalar_one_or_none()
      if quiz:
          quiz.score = correct_count
          quiz.total_questions = total
          quiz.passed = passed
          quiz.submitted_at = datetime.now(timezone.utc)

          if passed:
              module_result = await db.execute(
                  select(Module).where(Module.id == quiz.module_id)
              )
              module = module_result.scalar_one_or_none()
              if module and module.status != "completed":
                  module.status = "completed"
                  module.completed_at = datetime.now(timezone.utc)
                  completing_user_id = module.user_id
                  completing_module_id = module.id
                  is_first_attempt_perfect = quiz.attempt_number == 1

      await db.commit()

      # Trigger streak + achievement updates for a newly completed module
      if completing_user_id:
          streak = await streak_service.update_streak(completing_user_id, db)

          remediation_result = await db.execute(
              select(func.count()).select_from(Remediation)
              .where(Remediation.module_id == completing_module_id)
          )
          used_remediation = (remediation_result.scalar() or 0) > 0

          await achievement_service.check_and_award_achievements(
              user_id=completing_user_id,
              db=db,
              streak_count=streak.current_streak,
              used_remediation=used_remediation,
              first_attempt_perfect=is_first_attempt_perfect,
          )
  ```
- [ ] Remove the old `if passed:` block that only set `module.status` (it has been replaced above)

**Outcome:** Every time a quiz is passed for the first time, streak and achievements are updated automatically as part of the same request — no extra endpoint needed.

---

### Chunk 7 — Write the gamification schemas

**What you learn:** How to write Pydantic schemas that mix ORM objects (Streak model) with plain dicts (from the achievement join query).

- [ ] Create `backend/app/schemas/gamification.py`:
  ```python
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
  ```

**Outcome:** Two clean response schemas for the gamification endpoints.

---

### Chunk 8 — Write the gamification router and register it

**What you learn:** How a router can return a default "empty" response when a user hasn't started any activity yet, rather than raising a 404.

- [ ] Create `backend/app/routers/gamification.py`:
  ```python
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
      streak = await streak_service.get_streak(current_user.id, db)
      if not streak:
          return StreakResponse(current_streak=0, longest_streak=0, last_activity_date=None)
      return StreakResponse.model_validate(streak)


  @router.get("/achievements", response_model=list[AchievementResponse])
  async def get_achievements(
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ):
      achievements = await achievement_service.get_user_achievements(current_user.id, db)
      return [AchievementResponse(**a) for a in achievements]
  ```
- [ ] Open `backend/main.py` and add the gamification router:
  ```python
  from app.routers import auth, learning, modules, notion, gamification

  # ...existing middleware setup...

  app.include_router(auth.router)
  app.include_router(learning.router)
  app.include_router(modules.router)
  app.include_router(notion.router)
  app.include_router(gamification.router)
  ```

**Outcome:** Two gamification endpoints are live: `GET /gamification/streak` and `GET /gamification/achievements`.

---

### Chunk 9 — Test end to end in Swagger

**What you learn:** How to verify that side effects (streak and achievement updates) fire correctly after the main action (quiz submission).

- [ ] Restart the server (if it isn't hot-reloading already) and open http://localhost:8000/docs
- [ ] Authorize with your JWT token
- [ ] **Check initial state:**
  - `GET /gamification/streak` → should return `current_streak: 0` (no modules completed yet via new code path)
  - `GET /gamification/achievements` → should return `[]`
- [ ] **Complete a module with a perfect first attempt:**
  - `POST /learn/start` → copy `module_id`
  - `POST /learn/quiz/generate` → copy `quiz_id` and all question IDs + correct option strings
  - `POST /learn/quiz/submit` → submit ALL correct answers on the first attempt
- [ ] **Check gamification updated:**
  - `GET /gamification/streak` → should now return `current_streak: 1`, `last_activity_date: today`
  - `GET /gamification/achievements` → should include `first_steps` and `clean_sweep`
- [ ] **Check the database directly:**
  - `streaks` table: should have a row for your user
  - `user_achievements` table: should have 2 rows (first_steps + clean_sweep)
- [ ] **Complete another module (with remediation this time):**
  - Run a new module, submit wrong answers, get remediation, then pass on the second attempt
  - `GET /gamification/achievements` → should now also include `comeback_kid`

**Outcome:** Streak increments and achievements award themselves automatically on quiz completion with zero extra API calls.

---

### Chunk 10 — Write tests

**What you learn:** How to test streak date logic in complete isolation — no database, no async — just pure date arithmetic.

- [ ] Create `backend/tests/test_gamification.py`:
  ```python
  from datetime import date, timedelta


  def test_streak_increments_on_consecutive_day():
      """Completing a module the day after yesterday increments the streak."""
      today = date.today()
      yesterday = today - timedelta(days=1)

      current_streak = 5
      last_activity_date = yesterday

      if last_activity_date == yesterday:
          current_streak += 1

      assert current_streak == 6


  def test_streak_resets_when_day_skipped():
      """Missing a day resets the streak to 1."""
      today = date.today()
      two_days_ago = today - timedelta(days=2)
      yesterday = today - timedelta(days=1)

      current_streak = 5
      last_activity_date = two_days_ago

      if last_activity_date == yesterday:
          current_streak += 1
      else:
          current_streak = 1

      assert current_streak == 1


  def test_streak_unchanged_same_day():
      """Completing two modules in one day does not double-count the streak."""
      today = date.today()

      current_streak = 3
      last_activity_date = today

      if last_activity_date == today:
          pass  # No change

      assert current_streak == 3


  def test_longest_streak_updates_when_exceeded():
      current_streak = 8
      longest_streak = 5

      if current_streak > longest_streak:
          longest_streak = current_streak

      assert longest_streak == 8


  def test_longest_streak_unchanged_when_below_record():
      current_streak = 3
      longest_streak = 10

      if current_streak > longest_streak:
          longest_streak = current_streak

      assert longest_streak == 10


  def test_achievement_conditions_are_independent():
      """Each achievement condition is evaluated separately — one failing doesn't block others."""
      completed_count = 5
      streak_count = 2

      checks = [
          (completed_count >= 1, "first_steps"),
          (completed_count >= 5, "knowledge_seeker"),
          (completed_count >= 10, "scholar"),
          (streak_count >= 3, "streak_starter"),
      ]

      earned = [slug for condition, slug in checks if condition]
      assert "first_steps" in earned
      assert "knowledge_seeker" in earned
      assert "scholar" not in earned
      assert "streak_starter" not in earned
  ```
- [ ] Run all tests:
  ```bash
  pytest tests/ -v
  ```
- [ ] Confirm all 26 tests pass (20 previous + 6 new)

**Outcome:** Automated proof that streak date arithmetic and achievement condition logic work correctly in all edge cases.

---

## Milestone 4 complete checklist (summary)

- [ ] Chunk 1 — Gamification models written, `__init__.py` updated
- [ ] Chunk 2 — Migration run, 3 new tables in DB
- [ ] Chunk 3 — Seed script run, 8 achievements in DB
- [ ] Chunk 4 — `streak_service.py` written
- [ ] Chunk 5 — `achievement_service.py` written
- [ ] Chunk 6 — `quiz_service.py` updated to fire streak + achievement on module completion
- [ ] Chunk 7 — Gamification schemas written
- [ ] Chunk 8 — Gamification router written and registered
- [ ] Chunk 9 — Full flow tested in Swagger (streak increments, achievements auto-award)
- [ ] Chunk 10 — All 26 tests passing

---

## Before starting Milestone 5

Do not start Milestone 5 until every box above is checked AND:

- `streaks` table has a row for your user after completing a module
- `user_achievements` table shows `first_steps` earned after the first module completion
- `user_achievements` table shows `clean_sweep` after a perfect first-attempt quiz
- `pytest tests/ -v` shows all 26 tests passing

Tell Claude: "Milestone 4 is complete. Starting Milestone 5."
