# Milestone 6 — Backend Polish + Railway Deploy

> **Covers:** Stage 10 (Backend Polish + Railway Deploy)
> **Status:** Not started

---

## What this milestone is

The backend is feature-complete. This milestone makes it production-ready and deploys it to Railway so the frontend (Milestone 7) can talk to a live URL instead of `localhost:8000`.

There are four areas of work:

1. **Polish** — Add a global exception handler so unhandled errors return clean JSON (not stack traces). Review `.env.example` to make sure every variable is documented.
2. **Railway setup** — Add the configuration files Railway needs to detect, build, and start the app.
3. **Supabase switch** — The dev database is local Postgres. Production will use Supabase. This means updating `DATABASE_URL` and running Alembic migrations against Supabase before the first deploy.
4. **Deploy + smoke test** — Push to Railway, set all environment variables, and verify the live API responds correctly.

When this milestone is done, `https://<your-app>.up.railway.app/health` returns `{"status": "ok"}` and all endpoints work against the Supabase database.

---

## What you will be able to do when this milestone is done

- Hit `https://<your-app>.up.railway.app/docs` and see the full Swagger UI
- Register a user, complete a module, and earn achievements — all persisted in Supabase
- Have a stable backend URL to use as `VITE_API_BASE_URL` in the web frontend

---

## The chunks

---

### Chunk 1 — Add a global exception handler

**What you learn:** How FastAPI's exception handler hook lets you intercept any unhandled error and return a consistent JSON shape instead of a raw 500 stack trace.

- [ ] Open `backend/main.py` and add the handler after the middleware setup:
  ```python
  import logging
  from fastapi import Request
  from fastapi.responses import JSONResponse

  logger = logging.getLogger(__name__)

  @app.exception_handler(Exception)
  async def unhandled_exception_handler(request: Request, exc: Exception):
      logger.error("Unhandled error on %s: %s", request.url.path, exc, exc_info=True)
      return JSONResponse(
          status_code=500,
          content={"error": {"code": "internal_error", "message": "An unexpected error occurred."}},
      )
  ```

**Outcome:** Any unhandled exception returns `{"error": {"code": "internal_error", "message": "..."}}` instead of a raw traceback. The full traceback is still logged server-side.

---

### Chunk 2 — Review and update `.env.example`

**What you learn:** `.env.example` is the only env file committed to the repo. It must stay in sync with every variable the app actually reads.

- [ ] Open `backend/.env.example` and make sure every variable in `app/core/config.py` is listed with a placeholder value and a one-line comment explaining what it is. The final file should look like this:
  ```env
  # Database
  DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DB_NAME

  # Supabase (for file storage)
  SUPABASE_URL=https://your-project-ref.supabase.co
  SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

  # Auth
  SECRET_KEY=generate-with-openssl-rand-hex-32
  JWT_ALGORITHM=HS256
  ACCESS_TOKEN_EXPIRE_MINUTES=60

  # Claude AI
  ANTHROPIC_API_KEY=sk-ant-your-key
  ANTHROPIC_MODEL=claude-sonnet-4-20250514
  LLM_PROVIDER=anthropic

  # Google OAuth
  GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com
  GOOGLE_CLIENT_SECRET=your-secret

  # Notion (optional)
  NOTION_CLIENT_ID=
  NOTION_CLIENT_SECRET=
  NOTION_REDIRECT_URI=http://localhost:8000/notion/callback

  # App
  ENVIRONMENT=development
  FRONTEND_URL=http://localhost:5173
  ```

**Outcome:** Anyone cloning the repo knows exactly which variables to fill in.

---

### Chunk 3 — Add Railway configuration files

**What you learn:** Railway detects Python apps automatically but needs a `Procfile` to know the exact start command. `railway.toml` lets you pin the build config so Railway doesn't guess.

- [ ] Create `backend/Procfile`:
  ```
  web: uvicorn main:app --host 0.0.0.0 --port $PORT
  ```
  Railway injects `$PORT` automatically — never hard-code it.

- [ ] Create `backend/railway.toml`:
  ```toml
  [build]
  builder = "nixpacks"

  [deploy]
  startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
  healthcheckPath = "/health"
  healthcheckTimeout = 30
  restartPolicyType = "on_failure"
  ```

**Outcome:** Railway knows how to build and start the app, and uses `/health` to confirm it's alive.

---

### Chunk 4 — Run Alembic migrations against Supabase

**What you learn:** Alembic runs against whatever `DATABASE_URL` is set in your shell — you can point it at Supabase from your local machine without deploying anything.

You need your Supabase connection string. Get it from the Supabase dashboard:
**Project → Settings → Database → Connection string → URI** (use the `postgresql+asyncpg://` version, not the `psql` one).

- [ ] In your terminal, temporarily set `DATABASE_URL` to the Supabase URL and run migrations:
  ```bash
  cd backend
  source .venv/bin/activate
  export DATABASE_URL="postgresql+asyncpg://postgres:YOUR_PASSWORD@db.YOUR_REF.supabase.co:5432/postgres"
  alembic upgrade head
  ```
- [ ] Verify in the Supabase Table Editor that all 13 tables appear: `users`, `modules`, `passages`, `quizzes`, `questions`, `answers`, `remediations`, `streaks`, `achievements`, `user_achievements`, `friendships`, `activity_feed`, `alembic_version`
- [ ] Run the achievements seed script against Supabase:
  ```bash
  python scripts/seed_achievements.py
  ```

**Outcome:** Supabase has the full schema and seeded achievements. The app can connect to it immediately on first deploy.

---

### Chunk 5 — Deploy to Railway

**What you learn:** Railway deploys from a GitHub repo. You point it at the `backend/` subfolder, set env vars, and it builds automatically on every push to `main`.

- [ ] Go to https://railway.app → New Project → Deploy from GitHub repo → select `MasterMindAI`
- [ ] In Railway project settings, set **Root Directory** to `backend`
- [ ] Add all environment variables from `.env.example` — use your real Supabase values for `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`:

  | Variable | Value |
  |---|---|
  | `DATABASE_URL` | Supabase `postgresql+asyncpg://...` URI |
  | `SUPABASE_URL` | `https://your-ref.supabase.co` |
  | `SUPABASE_SERVICE_ROLE_KEY` | From Supabase → Settings → API |
  | `SECRET_KEY` | Run `openssl rand -hex 32` to generate |
  | `JWT_ALGORITHM` | `HS256` |
  | `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` |
  | `ANTHROPIC_API_KEY` | Your key from console.anthropic.com |
  | `ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` |
  | `LLM_PROVIDER` | `anthropic` |
  | `GOOGLE_CLIENT_ID` | From Google Cloud Console |
  | `GOOGLE_CLIENT_SECRET` | From Google Cloud Console |
  | `ENVIRONMENT` | `production` |
  | `FRONTEND_URL` | Set to `*` for now (update after Vercel deploy) |

- [ ] Trigger a deploy (Railway auto-deploys on push, or use "Deploy now" in the UI)
- [ ] Watch the build logs — confirm `uvicorn` starts and Railway marks the service as healthy

**Outcome:** The app is live at `https://<your-app>.up.railway.app`.

---

### Chunk 6 — Smoke test the live API

**What you learn:** A smoke test is a minimal pass over the critical paths to confirm the deployed app is wired up correctly — not a full regression test.

- [ ] Open `https://<your-app>.up.railway.app/health` in the browser → should return `{"status": "ok"}`
- [ ] Open `https://<your-app>.up.railway.app/docs` → Swagger UI should load with all 6 tag groups
- [ ] Register a user via Swagger → should return an `access_token`
- [ ] `GET /auth/me` with the token → should return the user profile
- [ ] `POST /learn/start` with a topic → should return ELI5 + passages (confirms Claude API key is working)
- [ ] `GET /gamification/streak` → should return `{"current_streak": 0, ...}` (confirms Supabase connection)

**Outcome:** The live Railway API is fully functional against Supabase. You have a stable backend URL for the frontend milestone.

---

## Milestone 6 complete checklist (summary)

- [ ] Chunk 1 — Global exception handler added to `main.py`
- [ ] Chunk 2 — `.env.example` updated with all variables and comments
- [ ] Chunk 3 — `Procfile` and `railway.toml` created in `backend/`
- [ ] Chunk 4 — Alembic migrations and achievements seed run against Supabase
- [ ] Chunk 5 — App deployed to Railway with all env vars set
- [ ] Chunk 6 — Smoke test passes on the live URL

---

## Before starting Milestone 7

Do not start Milestone 7 until every box above is checked AND:

- `https://<your-app>.up.railway.app/health` returns `{"status": "ok"}`
- `/learn/start` works on the live URL (Claude API key confirmed working)
- You have copied the Railway URL — this becomes `VITE_API_BASE_URL` in the web frontend

Tell Claude: "Milestone 6 is complete. Starting Milestone 7."
