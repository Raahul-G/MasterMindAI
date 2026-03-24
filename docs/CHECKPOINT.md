# Project Checkpoint Log

This file is auto-updated by Claude whenever a checkpoint is triggered.
Entries are ordered newest first.

---

## Devlog — 24 Mar 2026 at 20:15
> Trigger: milestone — post-launch bug fixes + full gamified UI retheme

### 🎯 What Was Planned
Fix all bugs found during live testing (module review, streak, achievements, save interests, invalid date), then apply a full Duolingo-inspired visual retheme: custom color palette, Nunito font, 3D buttons, gamified progress bar, card depth system, and success/error animations.

### ✅ What Was Built / Changed

| File | Type | What It Does |
|------|------|--------------|
| `backend/app/routers/modules.py` | Modified | Fixed `AttributeError` on review endpoint — `q.concept_title` doesn't exist on `Question` model; replaced with `passage_id_to_title` map built from fetched passages |
| `backend/app/schemas/learning.py` | Modified | Added `completed_at` and `created_at` to `ModuleReviewResponse` and `ModuleListItem` schemas |
| `backend/app/services/streak_service.py` | Modified | Replaced `date.today()` with `datetime.now(timezone.utc).date()` to prevent double-increment when modules complete near UTC midnight |
| `backend/app/routers/auth.py` | Modified | Replaced `POST /auth/interests` (bare list body) with `PUT /auth/interests` (`UpdateInterestsRequest` Pydantic model); updates `current_user` directly with `flag_modified()` to force SQLAlchemy ARRAY dirty detection |
| `backend/app/services/achievement_service.py` | Modified | No code change — root cause was frontend slug mismatch |
| `frontend-web/src/types/index.ts` | Modified | Added `completed_at` to `ModuleReview`; added `created_at` to `Module` interface |
| `frontend-web/src/pages/ModuleReview.tsx` | Modified | Added completed date in header; simplified quiz to show only correct answer green ✓ (removed red/grey logic) |
| `frontend-web/src/pages/Dashboard.tsx` | Modified | Fixed Review button (`/modules/:id/review`), Continue button (loads existing module into store); fixed `Invalid Date` from missing `created_at` |
| `frontend-web/src/pages/Profile.tsx` | Modified | Added `getMe()` fallback on mount to restore user after reload; fixed achievement slug mapping; added `saved` state (green tags + "Saved!" button); added error display for save failures |
| `frontend-web/src/index.css` | Modified | Added `@theme` with full custom color palette (green/purple/forest/mint/orange/red overrides) + Nunito font + bounce-success and shake-error keyframe animations |
| `frontend-web/index.html` | Modified | Added Nunito Google Fonts preconnect + stylesheet link; changed title to MasterMind |
| `frontend-web/src/components/ProgressBar.tsx` | Modified | Increased to `h-5` (20px); added white shine overlay `div` for gel/3D effect |
| `frontend-web/src/components/QuizCard.tsx` | Modified | Replaced `shadow-sm` with `border-2 border-gray-200`; selected option uses `border-green-600 border-b-4` raised card style |
| `frontend-web/src/pages/QuizResults.tsx` | Modified | Added `animate-bounce-success` on pass, `animate-shake-error` on fail to result status box |
| 20 frontend files | Modified | Full color retheme: indigo → green primary, purple brand, forest-900 headings, blue ELI5 box, mint correct answers, Duolingo-style level badges; all `bg-green-600` buttons get `border-b-4 border-green-700 active:translate-y-[2px] active:border-b-2` 3D press effect |

#### Code Summary

**`get_module_review()` — `backend/app/routers/modules.py`**
What it does: Builds `passage_id_to_title` dict from already-fetched passages, uses it to populate `concept_title` per question instead of accessing the non-existent `q.concept_title` attribute.
Why this way: `Question` model has no `concept_title` column — it lives on `Passage`. Same pattern used in `generate_quiz_for_module`.

**`update_streak()` — `backend/app/services/streak_service.py`**
What it does: Uses `datetime.now(timezone.utc).date()` instead of `date.today()` for UTC-consistent date comparison, preventing double-increment when two completions straddle UTC midnight.
Why this way: Railway runs UTC; `date.today()` uses server local time which could differ.

**`update_interests()` — `backend/app/routers/auth.py`**
What it does: Accepts `{ interest_topics: [...] }` via PUT, mutates `current_user.interest_topics` directly, calls `flag_modified()` to force SQLAlchemy to detect ARRAY column change, commits, returns updated `UserResponse`.
Why this way: SQLAlchemy `ARRAY(Text)` reassignment is not reliably detected as dirty without `flag_modified`.

**Gamified button system — all page files**
What it does: `border-b-4 border-green-700` creates physical depth; `active:translate-y-[2px] active:border-b-2` simulates button being pressed down; `transition-[transform,border-bottom-width] duration-75` makes it snappy.
Why this way: Spec required `border-bottom` depth (not `box-shadow`) to match Duolingo's chunky button feel.

### 🔄 Logic Changes
- **Streak update**: was `date.today()` (server local) → now `datetime.now(timezone.utc).date()` (always UTC)
- **Interests endpoint**: was `POST` with bare `list[str]` body returning `{"message":"..."}` → now `PUT` with Pydantic model returning `UserResponse`
- **Achievement display**: frontend `ALL_ACHIEVEMENTS` slugs (`on_a_roll`, `no_hints`, etc.) had zero overlap with backend slugs (`streak_starter`, `clean_sweep`, etc.) — replaced entirely
- **3D buttons**: previous session used `box-shadow` approach → replaced with `border-bottom` approach per design spec

### 🐛 Errors Encountered & Fixes

| Error | What Caused It | Fix Applied |
|-------|---------------|-------------|
| "Network Error" on review page | `q.concept_title` accessed on `Question` ORM object which has no such column → `AttributeError` crashed endpoint before response sent | Built `passage_id_to_title` map from fetched passages; used `passage_id_to_title.get(q.passage_id, "")` |
| "Invalid Date" on dashboard cards | `ModuleListItem` schema missing `created_at` field so `mod.created_at` was `undefined` in frontend | Added `created_at: datetime` to `ModuleListItem` schema |
| Streak counting 2 for same-day completions | `date.today()` on Railway (UTC) vs user's local timezone crossing midnight UTC | Switched to `datetime.now(timezone.utc).date()` |
| Save Interests silently failing | Three stacked mismatches: wrong HTTP method (PUT vs POST), wrong body shape, wrong response type | Fixed all three; also added `flag_modified()` for SQLAlchemy ARRAY detection |
| Achievements never highlighting | Frontend slugs (`on_a_roll`, `no_hints`, `social_butterfly`) had zero match with backend slugs (`streak_starter`, `clean_sweep`, `comeback_kid`) | Replaced entire `ALL_ACHIEVEMENTS` array with correct backend slugs |
| Profile shows "?" after reload | `user` not persisted in Zustand (only `token` in localStorage); Profile page never called `getMe()` | Added `getMe()` fallback in Profile's `useEffect`, same pattern as Dashboard |

### 📋 Planned vs Built
Significantly more bug-fixing than planned — the review page, streak, achievements, interests save, and profile reload all had independent bugs discovered during live testing. The gamified retheme matched the spec closely; the one addition was removing `box-shadow` from the previous (incorrect) 3D implementation and replacing it with the `border-bottom` approach from the design spec.

---

## Devlog — 23 Mar 2026 at 14:00
> Trigger: milestone — Milestone 7 complete (Web Frontend, Chunks 1–7)

### 🎯 What Was Planned
Build the full React web frontend: scaffold Vite + Tailwind v4 + React Router, write the TypeScript type layer, API modules, and Zustand stores, then implement all pages (auth, dashboard, learning flow, profile, friends) and deploy to Vercel.

### ✅ What Was Built / Changed

| File | Type | What It Does |
|------|------|--------------|
| `frontend-web/vite.config.ts` | Modified | Added `@tailwindcss/vite` plugin for Tailwind v4 build integration |
| `frontend-web/src/index.css` | Modified | Replaced Vite default CSS with single `@import "tailwindcss"` for Tailwind v4 |
| `frontend-web/.env` / `.env.example` | Created | Points `VITE_API_BASE_URL` at live Railway backend; `.env` gitignored |
| `frontend-web/src/types/index.ts` | Created | All 17 TypeScript interfaces: User, Passage, Question, Module, Streak, Achievement, and social types |
| `frontend-web/src/api/axiosClient.ts` | Created | Single Axios instance; request interceptor reads JWT from `localStorage` and attaches `Authorization` header |
| `frontend-web/src/api/{auth,learning,modules,social,gamification}.ts` | Created | Five typed API modules covering every backend endpoint; all calls go through `axiosClient` |
| `frontend-web/src/store/authStore.ts` | Created | Zustand store: `user`, `token`, `setAuth()` (persists to localStorage), `clearAuth()` |
| `frontend-web/src/store/learningStore.ts` | Created | Zustand store: holds the full in-progress learning session state (module, passages, quiz, result, remediations) |
| `frontend-web/src/components/{LoadingSpinner,Navbar,ProtectedRoute,StreakCounter,PassageCard,ProgressBar,QuizCard,AchievementBadge}.tsx` | Created | 8 shared components used across all pages |
| `frontend-web/src/pages/Landing.tsx` | Created | Hero page with headline, feature cards, and Login/Register CTA buttons |
| `frontend-web/src/pages/{Login,Register}.tsx` | Created | Auth forms; on success call API → `getMe()` → `setAuth()` → redirect to `/dashboard` |
| `frontend-web/src/pages/Dashboard.tsx` | Created | Fetches modules + streak in parallel on mount; shows module grid with level/status badges and a "Start New Module" button |
| `frontend-web/src/pages/TopicSelection.tsx` | Created | Free-text topic input + 3-way level selector (Kid/Intermediate/Expert); calls `startModule()`, saves to store, navigates to `/learn` |
| `frontend-web/src/pages/Learning.tsx` | Created | Shows ELI5 box (yellow) and passage cards; "Take the Quiz" calls `generateQuiz()` and navigates |
| `frontend-web/src/pages/Quiz.tsx` | Created | One question at a time with progress bar; collects answers, submits on final question, saves result, navigates to results |
| `frontend-web/src/pages/QuizResults.tsx` | Created | Shows score, pass/fail state, failed concept list; routes to `/complete` or triggers `remediate()` |
| `frontend-web/src/pages/Remediation.tsx` | Created | Shows revised explanations with "Revised" badge; "Retake Quiz" generates a new quiz for the same module |
| `frontend-web/src/pages/ModuleComplete.tsx` | Created | Celebration screen with score stats, earned achievements, Download Markdown button, and back to Dashboard |
| `frontend-web/src/pages/Profile.tsx` | Created | Shows initials avatar, StreakCounter, 8-badge achievement grid (earned/locked), and editable interest_topics saved via `PUT /auth/interests` |
| `frontend-web/src/pages/Friends.tsx` | Created | Debounced user search, incoming friend request list with Accept button, friends list with streak, and activity feed with `timeAgo` formatting |
| `frontend-web/src/App.tsx` | Modified | Full React Router v6 route table: 13 routes, all protected routes wrapped in `ProtectedRoute` |

#### Code Summary

**`axiosClient` interceptor — `src/api/axiosClient.ts`**
What it does: Reads `access_token` from `localStorage` on every request and injects it as `Authorization: Bearer <token>`. No manual header passing in any page or component.
Why this way: Centralised once — every API call in the app gets auth headers automatically.

**`useAuthStore` — `src/store/authStore.ts`**
What it does: `setAuth()` writes the token to both `localStorage` and Zustand state. `clearAuth()` removes it from both. `token` initialises from `localStorage` so the user stays logged in across page refreshes.
Why this way: `localStorage` as the persistence layer keeps things simple without needing a library like `zustand/middleware/persist`.

**`useLearningStore` — `src/store/learningStore.ts`**
What it does: Holds the entire learning session (module, passages, quiz, result, remediations). `reset()` clears all fields when the user returns to dashboard after completing a module.
Why this way: Single store shared across 5 pages — no prop drilling, no URL state, no re-fetching already-loaded data.

**`ProtectedRoute` — `src/components/ProtectedRoute.tsx`**
What it does: Reads `token` from `useAuthStore`. If present, renders children; if not, redirects to `/login` with `replace` so the back button doesn't loop.
Why this way: Thin wrapper applied once per route in `App.tsx` — no per-page auth checks.

**Pages in `src/pages/`** (13 total)
Group: auth pages (`Landing`, `Login`, `Register`) handle form submission + auth store update. Learning pages (`TopicSelection` → `ModuleComplete`) read/write `learningStore` and chain API calls via navigate on success. Social pages (`Profile`, `Friends`) fetch in parallel with `Promise.all` on mount and operate independently of the learning store.

### 🔄 Logic Changes
None — this is an entirely new codebase. No existing files from previous milestones were modified.

### 🐛 Errors Encountered & Fixes

| Error | What Caused It | Fix Applied |
|-------|---------------|-------------|
| None | — | — |

### 📋 Planned vs Built
Matched plan for Chunks 1–7. One small addition not in the plan: `src/api/gamification.ts` was created as a dedicated API module for streak and achievement calls (the plan had these inline in component `useEffect` calls using `axiosClient` directly). Extracted for consistency with the other API modules. The `PassageCard` component gained an optional `revised` prop to show the "Revised" badge when rendered in `Remediation.tsx`. Build produces 0 TypeScript errors across 105 modules. Chunks 8–9 (Vercel deploy + e2e browser test) pending.

---

## Devlog — 20 Mar 2026 at 21:45
> Trigger: milestone — Milestone 6 complete (Backend Polish + Railway Deploy)

### 🎯 What Was Planned
Polish the backend with a global exception handler, add Railway deployment config files, run Alembic migrations against Supabase, deploy to Railway, and verify the live API with a smoke test.

### ✅ What Was Built / Changed

| File | Type | What It Does |
|------|------|--------------|
| `backend/main.py` | Modified | Added global exception handler — unhandled errors return clean JSON instead of stack traces |
| `backend/Procfile` | Created | Tells Railway/Railpack the uvicorn start command |
| `backend/railway.toml` | Created | Railway build config — switched through Railpack → Nixpacks → Dockerfile before landing on Dockerfile |
| `Dockerfile` | Created | Multi-stage Docker build at repo root: installs from `backend/requirements.txt`, copies `backend/`, starts uvicorn on `$PORT` |
| `railway.toml` | Created | Repo-root Railway config pointing to the Dockerfile builder with health check on `/health` |
| `start.sh` | Created | Repo-root shell script for Railpack detection (later superseded by Dockerfile approach) |

#### Code Summary

**`unhandled_exception_handler()` — `backend/main.py`**
What it does: Catches any unhandled `Exception`, logs the full traceback server-side, and returns `{"error": {"code": "internal_error", "message": "..."}}` with a 500 status. Without this, FastAPI returns raw tracebacks to the client.
Why this way: Central handler at the app level means every route gets safe error responses automatically.

**`Dockerfile` — repo root**
What it does: Builds from `python:3.12-slim`, copies and installs `backend/requirements.txt`, copies the backend source, then starts uvicorn using `${PORT:-8000}` so Railway's injected `$PORT` is picked up automatically.
Why this way: Railpack's auto-detection repeatedly failed in the monorepo structure; a Dockerfile gives full explicit control over build and start with no guessing.

### 🔄 Logic Changes
None to application logic. Deploy strategy changed significantly: started with Railpack + `railway.toml` at `backend/`, moved `start.sh` and `railway.toml` to repo root, then switched entirely to Dockerfile after Railpack continued failing to detect the Python app.

### 🐛 Errors Encountered & Fixes

| Error | What Caused It | Fix Applied |
|-------|---------------|-------------|
| `Railpack could not determine how to build the app` | Railpack couldn't detect Python in monorepo with Root Directory set | Tried `start.sh`, moving config to repo root, then switched to Dockerfile builder entirely |
| Health check failing after Dockerfile worked | `DATABASE_URL` was deleted from Railway Variables during an edit | Re-added `DATABASE_URL` as a new variable |
| `[Errno 101] Network is unreachable` on register | Railway couldn't reach Supabase direct connection (IPv6, port 5432 blocked) | Switched to Supabase connection pooler (`aws-1-us-east-1.pooler.supabase.com:6543`) |
| `password authentication failed` | `DATABASE_URL` pasted with line breaks, truncating password to `Fr` | Deleted and re-entered variable as a single unbroken line |
| `asyncpg TimeoutError` on pooler port 5432 | Railway blocks outbound port 5432 | Switched to Supabase transaction pooler port 6543 |
| `DATABASE_URL Field required` on startup | Railway variable edit accidentally deleted the field | Re-added it as a new variable |

### 📋 Planned vs Built
Core goal matched: backend is live and all smoke test checks pass. The deploy path was significantly more complex than planned — Railpack's monorepo detection failed repeatedly, and Supabase connectivity required three iterations (direct → session pooler port 5432 → transaction pooler port 6543) before finding a path Railway could reach. The `statement_cache_size: 0` already set in `database.py` meant transaction mode worked without any code changes.

---

## Devlog — 20 Mar 2026 at 20:10
> Trigger: milestone — Milestone 5 complete (Social Features API)

### 🎯 What Was Planned
Build the full Social Features API: a friend graph (search, send request, accept), an activity feed showing events from the user and their friends, and automatic feed event posting wired into the existing quiz and achievement services.

### ✅ What Was Built / Changed

| File | Type | What It Does |
|------|------|--------------|
| `backend/app/models/social.py` | Created | `Friendship` and `ActivityFeed` ORM models; `event_metadata` used as the Python attribute name due to SQLAlchemy reserved name conflict |
| `backend/app/models/__init__.py` | Modified | Added `Friendship` and `ActivityFeed` imports so Alembic detects the new tables |
| `backend/alembic/versions/dc8bd001fd56_add_social_tables.py` | Created | Migration that creates the `friendships` and `activity_feed` tables |
| `backend/app/schemas/social.py` | Created | Six Pydantic schemas: `FriendRequestBody`, `FriendAcceptBody`, `UserSummary`, `FriendResponse`, `FriendRequestResponse`, `ActivityFeedItem`, `UserSearchResult` |
| `backend/app/services/social_service.py` | Created | Five async functions covering the full friend graph: send, accept, list friends, list requests, search users |
| `backend/app/services/feed_service.py` | Created | `post_activity()` writes feed events; `get_feed()` returns the 50 most recent events for a user and their friends |
| `backend/app/services/quiz_service.py` | Modified | Captures `topic` and `level` before `db.commit()`, then calls `feed_service.post_activity()` for `module_completed` after streak and achievement updates |
| `backend/app/services/achievement_service.py` | Modified | Added `feed_service` import; after committing new badges, loops through newly earned slugs and posts an `achievement_earned` event for each |
| `backend/app/routers/social.py` | Created | Six endpoints: GET friends, GET requests, POST send request, POST accept, GET feed, GET search — all JWT-protected; `ValueError` from services mapped to HTTP 400 |
| `backend/main.py` | Modified | Registered the social router |
| `backend/tests/test_social.py` | Created | 13 pure unit tests covering friend ID resolution, request validation (self/duplicate), feed visibility, and metadata structure |

#### Code Summary

**`send_friend_request()` / `accept_friend_request()` — `services/social_service.py`**
What it does: `send_friend_request` checks both directions of an existing friendship row before inserting to prevent duplicates and self-requests. `accept_friend_request` verifies the caller is the addressee and status is still `pending` before flipping it to `accepted`.
Why this way: `ValueError` is raised on validation failure so the router can catch it cleanly and return a 400 — no HTTP concerns in the service layer.

**`get_friends()` — `services/social_service.py`**
What it does: Fetches accepted friendships, resolves the friend's ID from whichever side of the row the current user is on, then joins users and streaks in two separate queries. Returns a list of dicts with name, avatar, and streak.
Why this way: The user can appear as either `requester_id` or `addressee_id`, so friend ID resolution must check both sides.

**`post_activity()` / `get_feed()` — `services/feed_service.py`**
What it does: `post_activity` inserts one `ActivityFeed` row — called internally, never from a router. `get_feed` finds friend IDs, fetches the 50 most recent events for the combined set of IDs, then joins user details in one final query.
Why this way: Three queries total (friendships → events → users) is more predictable than JOINs, and the 50-row limit keeps the feed light.

**Activity wiring — `quiz_service.py` + `achievement_service.py`**
What it does: `quiz_service` captures `topic` and `level` before `db.commit()` (SQLAlchemy expires objects post-commit), then posts a `module_completed` event. `achievement_service` loops through newly earned slugs post-commit, re-fetches each Achievement row, and posts an `achievement_earned` event.
Why this way: Side effects added without changing any return values or existing call sites — existing callers see no difference.

### 🔄 Logic Changes
`quiz_service.score_quiz()` previously captured only `completing_user_id`, `completing_module_id`, and `is_first_attempt_perfect` before commit. Added `completing_topic`, `completing_level`, `completing_score`, and `completing_total` to the pre-commit capture block to support the feed event payload.

### 🐛 Errors Encountered & Fixes

| Error | What Caused It | Fix Applied |
|-------|---------------|-------------|
| `InvalidRequestError: Attribute name 'metadata' is reserved` | SQLAlchemy's Declarative API reserves `metadata` on all mapped classes | Renamed Python attribute to `event_metadata` with `mapped_column("metadata", ...)` to keep the DB column name unchanged |
| `KeyError: 'access_token'` in test script | Login endpoint takes JSON body, test used `data=` (form-encoded) | Changed to `json={"email": ..., "password": ...}` |
| `KeyError: 'correct_answer'` in feed test | Quiz question responses intentionally omit `correct_answer` (not exposed to clients) | Fetched correct answers directly from DB via SQLAlchemy for the automated test script |

### 📋 Planned vs Built
Matched the plan. The only deviation was the `metadata` → `event_metadata` rename in the ORM model, forced by SQLAlchemy's reserved attribute name. The DB column is still called `metadata` so the schema and migration are unaffected. 50/50 tests passing (up from 38 before this milestone).

---

## Devlog — 19 Mar 2026 at 10:15
> Trigger: manual /devlog — session wrap-up (Milestone 4 shipped, Milestone 5 drafted)

### 🎯 What Was Planned
Resume mid-Milestone 4 (schemas were the last thing written). Finish the gamification router and tests, commit and push, then draft Milestone 5.

### ✅ What Was Built / Changed

| File | Type | What It Does |
|------|------|--------------|
| `backend/app/routers/gamification.py` | Created | Two GET endpoints: `/gamification/streak` and `/gamification/achievements` |
| `backend/main.py` | Modified | Registered the gamification router alongside existing routers |
| `backend/tests/test_gamification.py` | Created | 18 pure unit tests covering all streak and achievement condition logic |
| `milestones/milestone-05-social.md` | Created | Full 10-chunk plan for the Social Features API milestone |

#### Code Summary

**`get_streak()` — `backend/app/routers/gamification.py`**
What it does: Calls `streak_service.get_streak()` and returns a zero-state `StreakResponse` if no modules have been completed yet, so the frontend never receives a 404 for new users.
Why this way: Returning zeros is safer than a 404 — the frontend can render a streak counter at 0 without special-casing a missing response.

**`get_achievements()` — `backend/app/routers/gamification.py`**
What it does: Delegates to `achievement_service.get_user_achievements()` and returns the list directly. Returns an empty list for users with no achievements yet.
Why this way: No logic in the router — straight delegation to the service layer, consistent with all other endpoints.

**18 test functions — `backend/tests/test_gamification.py`**
What it does: Tests streak date arithmetic (new/consecutive/broken/same-day) and achievement condition evaluation (all 8 badges) using pure in-memory logic — no database or HTTP needed.
Why this way: Pure functions make the core logic testable in isolation. Same pattern used for auth and quiz tests in earlier milestones.

**`milestone-05-social.md` — `milestones/`**
What it does: 10-chunk plan covering `Friendship` + `ActivityFeed` models, `social_service.py`, `feed_service.py`, activity wiring into quiz and achievement services, the social router, and 13 new unit tests.
Why this way: Follows the same chunk-by-chunk format as previous milestones so each step can be built and verified independently.

### 🔄 Logic Changes
None. This session only finished pre-planned Milestone 4 chunks and planned Milestone 5 — no existing logic was changed.

### 🐛 Errors Encountered & Fixes

| Error | What Caused It | Fix Applied |
|-------|---------------|-------------|
| None | — | — |

### 📋 Planned vs Built
Matched plan. Router and tests completed as designed. 38/38 tests passing. Milestone 5 document written in full before the session ended.

---

## Devlog — 18 Mar 2026 at 15:30
> Trigger: milestone — Milestone 4 complete (Gamification API)

### 🎯 What Was Planned
Build the full Gamification API: streaks, achievements catalogue, automatic award triggers on module completion, and two read endpoints (`GET /gamification/streak` and `GET /gamification/achievements`).

### ✅ What Was Built / Changed

| File | Type | What It Does |
|------|------|--------------|
| `backend/app/models/gamification.py` | Created | Defines `Streak`, `Achievement`, and `UserAchievement` ORM models |
| `backend/app/models/__init__.py` | Modified | Imports the three gamification models so Alembic detects them |
| `backend/app/services/streak_service.py` | Created | Updates and reads the user's streak record |
| `backend/app/services/achievement_service.py` | Created | Awards achievements by slug and reads all earned achievements |
| `backend/app/services/quiz_service.py` | Modified | Fires streak + achievement updates when a module is first completed |
| `backend/app/schemas/gamification.py` | Created | `StreakResponse` and `AchievementResponse` Pydantic schemas |
| `backend/app/routers/gamification.py` | Created | Two GET endpoints: `/gamification/streak` and `/gamification/achievements` |
| `backend/main.py` | Modified | Registers the gamification router |
| `backend/scripts/seed_achievements.py` | Created | Seeds 8 achievement definitions; idempotent |
| `backend/tests/test_gamification.py` | Created | 18 unit tests covering streak logic and achievement conditions |

#### Code Summary

**`update_streak()` — `services/streak_service.py`**
What it does: Fetches or creates the user's streak, then applies 3-case logic: same-day is a no-op, yesterday increments, anything older resets to 1. Always updates `longest_streak` if the new value is higher.
Why this way: All cases collapse into one function called automatically after module completion — no manual calls needed.

**`check_and_award_achievements()` — `services/achievement_service.py`**
What it does: Counts the user's completed modules, then evaluates 8 slug/condition pairs (milestones, perfect score, remediation used, streak thresholds). Calls `_award_if_not_earned()` for each passing condition and commits only if something new was awarded.
Why this way: Single function covers all 8 badges — easy to extend by adding a row to the `checks` list.

**`_award_if_not_earned()` — `services/achievement_service.py`**
What it does: Looks up an achievement by slug, checks the `user_achievements` join table, and inserts a row if the user hasn't earned it yet. Returns True if newly awarded.
Why this way: Idempotent by design — safe to call on every module completion without risk of duplicates.

**`score_quiz()` update — `services/quiz_service.py`**
What it does: Saves `completing_user_id`, `completing_module_id`, and `is_first_attempt_perfect` to local variables before `db.commit()` (SQLAlchemy expires ORM objects after commit), then calls streak and achievement services post-commit.
Why this way: Variables must be captured before commit because SQLAlchemy expires all attributes on flushed objects.

**`GET /gamification/streak` — `routers/gamification.py`**
What it does: Returns current streak, longest streak, and last activity date. Returns zeros and null date if the user has never completed a module.
Why this way: Graceful zero-state means the frontend never needs to handle a 404 for new users.

**`GET /gamification/achievements` — `routers/gamification.py`**
What it does: Returns the full list of earned achievements with slug, name, description, icon, and earned timestamp, ordered by `earned_at`.
Why this way: Direct delegation to `achievement_service.get_user_achievements()` — no logic in the router.

### 🔄 Logic Changes
`quiz_service.score_quiz()` previously only updated `module.status` and committed. Now it also fires streak and achievement updates. The pre-commit variable capture pattern was added specifically to avoid the SQLAlchemy post-commit expiry issue.

### 🐛 Errors Encountered & Fixes

| Error | What Caused It | Fix Applied |
|-------|---------------|-------------|
| None | — | — |

### 📋 Planned vs Built
Matched plan exactly. 38/38 tests passing (up from 20 before Milestone 4).

---

## Devlog — 18 Mar 2026 at 14:15
> Trigger: milestone — Milestone 3 complete (Export, Storage, Notion Integration)

### 🎯 What Was Planned
Build the export pipeline: generate a Markdown summary of any completed module, upload it to Supabase Storage for download, and push it as a formatted Notion page. Also expose `/modules` endpoints for browsing past modules.

### ✅ What Was Built / Changed

| File | Type | What It Does |
|------|------|--------------|
| `backend/app/services/markdown_service.py` | Created | Compiles a module's ELI5, passages, quiz Q&A, and remediations into a single Markdown string |
| `backend/app/services/storage_service.py` | Created | Uploads a Markdown string to the Supabase `modules` storage bucket and returns the public URL |
| `backend/app/services/notion_service.py` | Created | Creates a formatted Notion sub-page from module content using an internal integration token |
| `backend/app/routers/modules.py` | Created | Four endpoints: list modules, get module detail, export to download, export to Notion |
| `backend/app/routers/notion.py` | Created | Three endpoints: connect token, check status, disconnect |
| `backend/app/schemas/learning.py` | Modified | Added `ModuleDetail`, `ExportDownloadResponse`, `ExportNotionResponse` schemas |
| `backend/app/services/quiz_service.py` | Modified | Auto-marks module as `completed` when a quiz is fully passed |
| `backend/main.py` | Modified | Registered `modules` and `notion` routers |
| `backend/tests/test_export.py` | Created | 7 tests for the Markdown-to-Notion block converter |

#### Code Summary

**`generate_module_markdown()` — `backend/app/services/markdown_service.py`**
What it does: Queries the DB for a module's full data (module, passages, most recent passed quiz, questions, answers, remediations) and assembles them into a structured Markdown document with headings, quiz results with ✓/✗ markers, and remediation sections.
Why this way: Keeps all document assembly logic in one place; the same output is used for both download and Notion export.

**`upload_markdown()` — `backend/app/services/storage_service.py`**
What it does: POSTs a Markdown string to the Supabase Storage REST API using the service role key with `x-upsert: true` so re-exports overwrite the existing file. Returns the public URL.
Why this way: Direct httpx call to the Supabase Storage REST API — no extra SDK dependency needed.

**`create_page()` + `_get_parent_page_id()` — `backend/app/services/notion_service.py`**
What it does: `_get_parent_page_id()` calls `/v1/search` to find the first page shared with the integration. `create_page()` then creates a child page under it with Notion block objects converted from the Markdown.
Why this way: Internal integrations cannot create workspace-root pages — they require a shared parent page. The search approach means the user only needs to share any one page once.

**`_markdown_to_notion_blocks()` — `backend/app/services/notion_service.py`**
What it does: Iterates markdown lines, maps `##` → `heading_2`, `###` → `heading_3`, `---` → `divider`, everything else → `paragraph`. Strips `**` bold markers.
Why this way: Pure function with no external calls — easy to test in isolation and covers all block types used in the module Markdown.

**`score_quiz()` update — `backend/app/services/quiz_service.py`**
What it does: After saving quiz results, if `passed=True` it fetches the parent module and sets `status="completed"` and `completed_at=now()` in the same DB commit.
Why this way: Keeps the state transition in the service layer alongside the quiz scoring — no need for a separate "complete module" endpoint.

### 🔄 Logic Changes
Notion integration was originally planned as a full public OAuth flow (redirect URL, code exchange). Changed to an **internal integration token** approach (`POST /notion/connect` with a `secret_` or `ntn_` token) because Notion's developer portal no longer offers a simple public integration option for new apps. The migration path to OAuth is documented in comments — the `create_page()` function and DB column are unchanged.

The `create_page()` parent was originally `{"type": "workspace", "workspace": True}`. Changed to use `_get_parent_page_id()` which searches for a shared page first, because internal integrations cannot write at workspace root level.

### 🐛 Errors Encountered & Fixes

| Error | What Caused It | Fix Applied |
|-------|---------------|-------------|
| Notion export 500 error | `create_page()` used `workspace` as parent — not allowed for internal integrations | Added `_get_parent_page_id()` to find a shared page first; changed parent to `page_id` |
| Notion 401 "API token is invalid" | Token validator required `secret_` prefix but new Notion tokens start with `ntn_` | Updated validator to accept both `secret_` and `ntn_` prefixes |
| Previous token stored as `secret_ntn_...` | Old validator forced `secret_` prefix so user prepended it manually | Fixed validator, user re-connected with correct `ntn_...` token |

### 📋 Planned vs Built
Core functionality matched the plan. Two unplanned deviations: (1) Notion OAuth replaced with internal token flow due to Notion portal limitations — a simpler and more appropriate approach for solo dev use; (2) `_get_parent_page_id()` was added as a helper not in the original plan, required to work around the internal integration workspace restriction.

---

## Devlog — 17 Mar 2026 at 00:00
> Trigger: manual /devlog — Milestones 1 and 2 complete

### 🎯 What Was Planned
Build the full backend foundation: auth API (Milestone 1) and AI service + learning API (Milestone 2), covering user registration/login, all Claude-powered content generation, and the learn → quiz → remediate flow wired to the database.

### ✅ What Was Built / Changed

| File | Type | What It Does |
|------|------|--------------|
| `backend/main.py` | Created | FastAPI entry point with CORS middleware and auth + learn routers registered |
| `backend/app/core/config.py` | Created | Pydantic Settings class loading all env vars including LLM_PROVIDER, Anthropic/OpenAI keys |
| `backend/app/core/database.py` | Created | SQLAlchemy async engine + session factory pointing at Supabase Postgres |
| `backend/app/core/security.py` | Created | bcrypt password hashing (`hash_password`, `verify_password`) and JWT create/decode |
| `backend/app/core/llm.py` | Created | LLM factory returning ChatAnthropic or ChatOpenAI depending on `LLM_PROVIDER` env var |
| `backend/app/models/user.py` | Created | SQLAlchemy `User` model with all columns including `interest_topics TEXT[]` for ELI5 personalisation |
| `backend/app/models/learning.py` | Created | Six learning models: `Module`, `Passage`, `Quiz`, `Question`, `Answer`, `Remediation` |
| `backend/app/schemas/auth.py` | Created | Pydantic v2 schemas for register/login requests and token responses; password min-length validated |
| `backend/app/schemas/learning.py` | Created | Pydantic v2 schemas for all four learning endpoints (start, generate quiz, submit quiz, remediate) |
| `backend/app/services/auth_service.py` | Created | register, login, Google OAuth, get user, update interests — all async, no logic in router |
| `backend/app/services/ai_service.py` | Created | LangGraph StateGraph with four nodes (ELI5, passages, quiz, remediation); four public async functions |
| `backend/app/services/learning_service.py` | Created | Orchestrates start_module, generate_quiz, remediate flows — calls AI service and persists to DB |
| `backend/app/services/quiz_service.py` | Created | Scores submitted answers, identifies failed concepts, saves Quiz + Answer rows |
| `backend/app/routers/auth.py` | Created | Five auth endpoints: register, login, Google OAuth, /me, update interests |
| `backend/app/routers/learning.py` | Created | Four learning endpoints: POST /learn/start, /learn/quiz/generate, /learn/quiz/submit, /learn/remediate |
| `backend/app/dependencies.py` | Created | `get_current_user` FastAPI dependency that decodes JWT and returns the User ORM object |
| `backend/alembic/` | Created | Alembic configured with async engine; migrations for users table, learning tables, timestamp fixes |
| `backend/tests/test_auth.py` | Created | 5 security unit tests (password hashing, JWT round-trip, token expiry) |
| `backend/tests/test_ai_service.py` | Created | 4 integration tests for all four AI functions — all run against live Claude API |
| `backend/tests/test_quiz.py` | Created | 4 unit tests for quiz scoring logic (correct, wrong, mixed, all-fail scenarios) |

#### Code Summary

**`get_llm()` — `backend/app/core/llm.py`**
What it does: Returns a LangChain chat model configured with the given temperature and max_tokens. Reads `LLM_PROVIDER` from settings and returns `ChatAnthropic` (default) or `ChatOpenAI`. All AI nodes call this instead of instantiating the client directly.
Why this way: Single env-var swap to change provider — no code changes needed anywhere else in the system.

**`generate_eli5()`, `generate_passages()`, `generate_quiz()`, `generate_remediation()` — `backend/app/services/ai_service.py`**
What it does: Each function builds a minimal LangGraph `StateGraph` with one or two nodes, invokes it with the relevant state fields, parses the LLM's response (plain string or JSON), and returns the result. `LearningState` is a shared TypedDict that flows through every node.
Why this way: LangGraph enforces a structured async pipeline per operation; each function is independently testable and the state schema documents exactly what data each node needs.

**`start_module()` — `backend/app/services/learning_service.py`**
What it does: Calls `generate_eli5` then `generate_passages`, creates a `Module` row and `Passage` rows in the DB via `db.flush()` + `db.commit()`, and returns the assembled `StartModuleResponse` Pydantic schema.
Why this way: Keeps all DB writes inside the service layer so the router stays thin; flush-before-commit lets passage rows reference the module ID within one transaction.

**`score_quiz()` — `backend/app/services/quiz_service.py`**
What it does: Accepts a list of submitted answers, compares each against the stored `correct_answer`, creates `Answer` rows, updates the `Quiz` row with score and passed status, and returns the list of unique failed concept titles for the remediation step.
Why this way: Centralises all scoring logic so the router only passes through results; failed concepts drive the remediation call without any additional DB query.

**`get_current_user()` — `backend/app/dependencies.py`**
What it does: FastAPI dependency that reads the Bearer token from `Authorization`, decodes it with `decode_access_token`, and fetches the matching User row from the DB. Raises 401 if token is missing or invalid.
Why this way: Standard FastAPI dependency injection pattern — any protected route simply declares `user: User = Depends(get_current_user)` with no repeated auth logic.

### 🔄 Logic Changes
Milestone 1 originally planned a standalone Anthropic SDK integration. During Milestone 2 this was replaced with a LangChain + LangGraph approach so the provider can be swapped via env var and each AI function runs as a typed graph node. The four public functions (`generate_eli5`, etc.) retain the same signatures, so learning_service is unaffected.

Additionally, the `alembic/env.py` was updated in Milestone 2 to import all six learning models alongside the User model so Alembic can auto-detect the full schema — the original version only imported User.

### 🐛 Errors Encountered & Fixes

| Error | What Caused It | Fix Applied |
|-------|---------------|-------------|
| Alembic `autogenerate` missing learning tables | `env.py` only imported `User` model, so SQLAlchemy metadata didn't include the new tables | Added imports for all six learning models in `alembic/env.py` |
| Timestamp columns missing `timezone=True` | Original `User` model used `DateTime` without timezone; Postgres stores UTC but comparisons failed | Added migration `fix_timestamp_timezone.py` to `ALTER COLUMN` all timestamps to `TIMESTAMP WITH TIME ZONE` |
| Blank migration generated on second `alembic revision --autogenerate` | First migration already captured the schema; env.py wasn't loading the DB URL from `.env` before running | Fixed `env.py` to call `load_dotenv()` before building the engine URL |

### 📋 Planned vs Built
Both milestones matched the plan from ROADMAP.md. One unplanned addition in Milestone 2: the LLM factory (`llm.py`) and LangGraph pipeline were not in the original design — the plan specified the Anthropic SDK directly. This was a deliberate upgrade during implementation to support provider switching. All 13 tests pass (5 auth + 4 AI + 4 quiz).

---
