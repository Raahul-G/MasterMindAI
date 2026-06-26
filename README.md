# MasterMind AI

**Adaptive AI-powered learning — teaches any topic step by step until you master it.**

MasterMind uses a large language model to generate personalised learning content, adaptive quizzes, and intelligent remediation loops. It doesn't just present information — it teaches you until you genuinely understand, using your own interests as the lens for every explanation.

**Live app:** [mastermind-ai.vercel.app](https://mastermind-ai.vercel.app)
**API docs:** [mastermindai-production.up.railway.app/docs](https://mastermindai-production.up.railway.app/docs)

---

## Screenshots

| Login | Home | Start Learning |
|---|---|---|
| ![Login](screenshots/01-login.png) | ![Home](screenshots/02-home.png) | ![Start Learning](screenshots/03-start-learning.png) |

| Concept Cards | Quiz | Profile & Achievements |
|---|---|---|
| ![Concepts](screenshots/05-concept.png) | ![Quiz](screenshots/06-quiz.png) | ![Profile](screenshots/04-profile.png) |

---

## How It Works

MasterMind runs a structured adaptive learning loop for any topic:

```
Topic + Difficulty Level
         │
         ▼
  Big Idea (ELI5)
  2–4 sentences, personalised analogy
  drawn from your own interests
         │
         ▼
  2 Concept Cards
  Each card has: summary analogy · explanation · real-world use cases
         │
         ▼
  4 Quiz Questions  (2 per concept — true/false or multiple choice)
         │
         ├─ All 4 passed ────────────────────────────▶ Module Complete
         │                                                    │
         └─ Any failed ──▶ Remediation                       │
                           (fresh analogies per concept) ────┘
                                  │
                                  └─ Re-quiz (failed concepts only)
                                         │
                                         └─ Loop until mastery
```

Every completed module auto-generates a Markdown summary (Big Idea + concept cards + quiz Q&A + remediations) which can be downloaded or pushed directly to Notion.

---

## Features

### Agentic AI Learning Engine
Built on **LangGraph** — each AI function is a compiled state graph with dedicated nodes. The LLM provider (Anthropic or OpenAI) is configured via environment variable, making the stack provider-agnostic.

- **Personalised Big Idea** — The LLM generates an analogy grounded in the user's own interest topics (e.g. football, cooking). Interest-to-analogy mapping is enforced at the prompt level with the user's stored interests passed directly into each call.
- **2 Concept Cards per session** — Each card has three structured parts: a one-sentence summary analogy, a 2–4 sentence explanation, and 2–3 sentences of real-world use cases. The LLM skips any concepts the user already knows (prerequisite awareness).
- **4 Quiz Questions per module** — Exactly 2 questions per concept (true/false or multiple choice), tagged to the concept they test. Questions reference only content the user actually read.
- **Smart Remediation** — For each failed concept, the LLM generates a fresh explanation using entirely different analogies. The original passage is provided as negative context ("do not use these comparisons") to guarantee novelty.
- **Infinite Remediation Loop** — No attempt limit. The system loops until every concept is passed.

### Gamification
- **Daily Streaks** — Consecutive-day completion tracking with longest-streak record
- **8 Achievements** — Auto-awarded on milestones: First Steps, Knowledge Seeker, Scholar, Clean Sweep, Comeback Kid, Streak Starter, Hot Streak, Dedicated Learner
- Achievement checks run automatically inside the quiz scoring pipeline — no extra API calls

### Social Learning
- **Friend System** — Search users, send and accept friend requests
- **Activity Feed** — See when friends complete modules or earn achievements, with topic, score, and emoji badges
- Feed is scoped to the user + accepted friends only

### Export
- **Markdown Export** — Full module summary uploaded to Supabase Storage, returned as a public download URL
- **Notion Integration** — OAuth 2.0 flow connects a user's Notion workspace. Module content is pushed as a structured Notion page with heading hierarchy and dividers preserved

### Auth
- Email/password (bcrypt-hashed, JWT-issued)
- Google OAuth (ID token verification)
- Interest onboarding (3–5 topics) stored on the user profile, used to personalise every Big Idea

---

## Tech Stack

### Backend
| Layer | Technology |
|---|---|
| Framework | FastAPI (async-native, Python 3.12) |
| AI Orchestration | LangGraph (one compiled graph per function) |
| LLM | Provider-agnostic via `get_llm()` — Anthropic or OpenAI |
| ORM | SQLAlchemy 2.0 + asyncpg |
| Migrations | Alembic |
| Database | PostgreSQL via Supabase |
| Auth | python-jose (JWT) + passlib/bcrypt |
| Storage | Supabase Storage (public bucket) |
| HTTP Client | httpx (async — Notion API + OAuth flows) |
| Package Manager | uv |
| Tests | pytest + pytest-asyncio (54 tests, all passing) |
| Deploy | Railway |

### Frontend (Web)
| Layer | Technology |
|---|---|
| Framework | React 18 + TypeScript (strict mode) |
| Build Tool | Vite |
| Styling | TailwindCSS |
| Routing | React Router v6 |
| State | Zustand (fully typed stores) |
| HTTP | Axios (single client with JWT interceptor) |
| E2E Tests | Playwright (54/54 passing) |
| Deploy | Vercel |

### Infrastructure
| Service | Role |
|---|---|
| Supabase | PostgreSQL + file storage |
| Railway | FastAPI deployment |
| Vercel | React frontend deployment |
| Google Cloud | OAuth 2.0 credentials |
| Notion API | Export destination |

---

## Architecture

```
┌──────────────────────────────────────────────────┐
│                  React Frontend                   │
│  Zustand Stores ──▶ Axios Client ──▶ REST API    │
└─────────────────────────┬────────────────────────┘
                          │ HTTPS / JWT
┌─────────────────────────▼────────────────────────┐
│              FastAPI Backend  (Railway)           │
│                                                   │
│  Routers ──▶ Services ──▶ SQLAlchemy ORM         │
│                 │                │                │
│           AI Service         PostgreSQL           │
│          (LangGraph)        (Supabase)            │
│                 │                                 │
│         LLM Provider        Supabase Storage      │
└──────────────────────────────────────────────────┘
```

### LangGraph AI Architecture
Each AI operation is an independent compiled `StateGraph` sharing a common `LearningState` TypedDict. At import time, four graphs are compiled once and reused across all requests:

```
_eli5_graph      START ──▶ eli5_node      ──▶ END
_passages_graph  START ──▶ passages_node  ──▶ END
_quiz_graph      START ──▶ quiz_node      ──▶ END
_remediation_graph START ──▶ remediation_node ──▶ END
```

All prompts live exclusively in `ai_service.py` — no prompt strings exist anywhere else in the codebase.

### Quiz Scoring Pipeline
The quiz submission endpoint is the integration point for all downstream side effects:

```
POST /learn/quiz/submit
    │
    ├─▶ quiz_service.score_quiz()
    │       ├─ Score answers, update Quiz record
    │       ├─ If passed: mark Module as completed
    │       ├─ streak_service.update_streak()
    │       ├─ achievement_service.check_and_award_achievements()
    │       └─ feed_service.post_activity("module_completed")
    │               └─ (per badge) post_activity("achievement_earned")
    │
    └─▶ SubmitQuizResponse { score, total, passed, failed_concepts }
```

### Database Schema (13 tables)

```
users ──────────┬──▶ modules ──▶ passages ──▶ questions ──▶ answers
                │         └──▶ quizzes ──────────────────────────┘
                │         └──▶ remediations
                │
                ├──▶ streaks
                ├──▶ user_achievements ──▶ achievements
                ├──▶ friendships  (self-referential)
                └──▶ activity_feed
```

All primary keys are UUID. `interest_topics` is a PostgreSQL `TEXT[]` array. Quiz `options` is stored as `JSONB`.

---

## API Reference

Base URL: `https://mastermindai-production.up.railway.app`
Auth header: `Authorization: Bearer <jwt>`
Interactive docs: `/docs`

### Auth
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | No | Register with email + password |
| POST | `/auth/login` | No | Login, receive JWT |
| POST | `/auth/google` | No | Google OAuth login |
| GET | `/auth/me` | Yes | Current user profile |
| PUT | `/auth/interests` | Yes | Update interest topics |

### Learning
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/learn/start` | Yes | Generate Big Idea + 2 concept cards |
| POST | `/learn/quiz/generate` | Yes | Generate 4 quiz questions for a module |
| POST | `/learn/quiz/submit` | Yes | Submit answers, receive score + failed concepts |
| POST | `/learn/remediate` | Yes | Generate remediation for failed concepts |

### Modules
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/modules` | Yes | List all user modules |
| GET | `/modules/{id}` | Yes | Full module detail with concept cards |
| POST | `/modules/{id}/export/download` | Yes | Generate Markdown, upload to storage, return URL |
| POST | `/modules/{id}/export/notion` | Yes | Push module to Notion |

### Gamification
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/gamification/streak` | Yes | Current + longest streak |
| GET | `/gamification/achievements` | Yes | All earned achievements |

### Social
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/social/friends` | Yes | Friends list with streaks |
| GET | `/social/friends/requests` | Yes | Incoming friend requests |
| POST | `/social/friends/request` | Yes | Send friend request |
| POST | `/social/friends/accept` | Yes | Accept a request |
| GET | `/social/feed` | Yes | Activity feed (self + friends) |
| GET | `/social/users/search?q=` | Yes | Search users by name |

### Notion
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/notion/auth-url` | Yes | Get Notion OAuth URL |
| GET | `/notion/callback` | No | OAuth callback handler |
| DELETE | `/notion/disconnect` | Yes | Remove Notion credentials |

---

## Local Development

### Prerequisites
- Python 3.12+
- Node.js 20+
- [uv](https://docs.astral.sh/uv) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- A [Supabase](https://supabase.com) project
- An LLM API key (Anthropic or OpenAI)

### Backend

```bash
cd backend
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt

cp .env.example .env
# Fill in all values in .env

alembic upgrade head
python -m scripts.seed_achievements

uvicorn main:app --reload --port 8000
```

Swagger UI: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend-web
npm install

# Create .env:
# VITE_API_BASE_URL=http://localhost:8000
# VITE_GOOGLE_CLIENT_ID=your-google-client-id

npm run dev
```

App: `http://localhost:5173`

### Tests

```bash
# Backend unit tests (54 tests)
cd backend && pytest tests/ -v

# Frontend E2E tests (54 tests)
cd frontend-web && npx playwright test
```

---

## Environment Variables

### `backend/.env`

```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DB_NAME
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SECRET_KEY=generate-with-openssl-rand-hex-32
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ANTHROPIC_API_KEY=sk-ant-your-key
ANTHROPIC_MODEL=claude-sonnet-4-20250514
LLM_PROVIDER=anthropic
GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret
NOTION_CLIENT_ID=your-notion-client-id
NOTION_CLIENT_SECRET=your-notion-client-secret
NOTION_REDIRECT_URI=http://localhost:8000/notion/callback
ENVIRONMENT=development
FRONTEND_URL=http://localhost:5173
```

### `frontend-web/.env`

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com
```

---

## Project Structure

```
MasterMindAI/
├── backend/
│   ├── main.py                        # FastAPI entry point + global exception handler
│   ├── app/
│   │   ├── core/
│   │   │   ├── llm.py                 # get_llm() — provider-agnostic LangChain LLM factory
│   │   │   ├── config.py              # Pydantic settings
│   │   │   ├── database.py            # SQLAlchemy async engine
│   │   │   └── security.py            # JWT + bcrypt
│   │   ├── models/                    # SQLAlchemy ORM (user, learning, gamification, social)
│   │   ├── schemas/                   # Pydantic request/response schemas
│   │   ├── routers/                   # auth, learning, modules, gamification, social, notion
│   │   ├── services/
│   │   │   ├── ai_service.py          # All LLM prompts + LangGraph compiled graphs
│   │   │   ├── quiz_service.py        # Scoring + streak / achievement / feed side effects
│   │   │   ├── learning_service.py    # Module orchestration
│   │   │   ├── streak_service.py      # Daily streak logic
│   │   │   ├── achievement_service.py # Badge evaluation and award
│   │   │   ├── feed_service.py        # Activity feed read/write
│   │   │   ├── social_service.py      # Friends graph
│   │   │   ├── notion_service.py      # OAuth + Notion page creation
│   │   │   ├── markdown_service.py    # Module → Markdown assembly
│   │   │   └── storage_service.py     # Supabase Storage upload
│   │   └── dependencies.py            # get_current_user JWT dependency
│   ├── alembic/                       # DB migrations (one file per schema change)
│   ├── scripts/seed_achievements.py   # One-time achievement catalogue seeder
│   └── tests/                         # 54 pytest unit tests
│
├── frontend-web/
│   └── src/
│       ├── pages/                     # 13 pages: Landing, Login, Register, Dashboard,
│       │                              #   TopicSelection, Learning, Quiz, QuizResults,
│       │                              #   Remediation, ModuleComplete, Profile, Friends,
│       │                              #   ModuleReview, KnowledgeGraph
│       ├── components/                # Navbar, ProtectedRoute, QuizCard, PassageCard,
│       │                              #   ProgressBar, AchievementBadge, StreakCounter,
│       │                              #   LoadingSpinner
│       ├── store/                     # authStore, learningStore (Zustand, fully typed)
│       ├── api/                       # axiosClient + per-domain API modules
│       └── types/index.ts             # All TypeScript interfaces (no `any`)
│
└── screenshots/                       # App screenshots
```

---

## Build Progress

| Stage | Description | Status |
|---|---|---|
| 1 | Environment Setup | ✅ Complete |
| 2 | Supabase Database | ✅ Complete |
| 3 | Authentication API | ✅ Complete |
| 4 | Core AI Service (LangGraph) | ✅ Complete |
| 5 | Learning Module API | ✅ Complete |
| 6 | Cloud Storage + Markdown Export | ✅ Complete |
| 7 | Notion Integration | ✅ Complete |
| 8 | Gamification API | ✅ Complete |
| 9 | Social Features API | ✅ Complete |
| 10 | Backend Deploy (Railway) | ✅ Complete |
| 11 | Web Frontend — 13 pages (Vercel) | ✅ Complete |
| 12 | Android App (React Native + Expo) | ⬜ Next |

---

## Engineering Principles

- **No logic in routers** — routers delegate to services only
- **All I/O is async** — `async def` + `await` throughout the entire stack
- **Pydantic for all shapes** — no raw SQLAlchemy objects returned to clients
- **Prompts in one place** — all LLM prompt strings live exclusively in `ai_service.py`
- **Provider-agnostic LLM** — swap between Anthropic and OpenAI via `LLM_PROVIDER` env var
- **One migration per change** — existing Alembic files are never edited
- **TypeScript strict mode** — no `any`, all interfaces in `src/types/index.ts`
- **UUID PKs everywhere** — no auto-increment integers
- **Secrets never committed** — `.env` in `.gitignore`, `.env.example` only

---

Built by [Raahul G](https://github.com/Raahul-G)
