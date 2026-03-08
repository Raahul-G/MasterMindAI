# CLAUDE.md — MasterMind Project Memory File

> Read this file at the start of every session. It contains the full project context.
> Last updated: 2026-02-28

---

## Section 1 — Project Overview and Full Learning Flow

**MasterMind** is an adaptive, AI-powered learning app. It teaches users any topic they choose, step by step, using Claude AI. The experience is personalised, gamified, and repeats remediation until the user actually understands — not just memorises.

### The Full Learning Flow (in order)

1. **Topic Selection** — The user types any topic (e.g. "Black holes", "Supply and demand", "React hooks") and picks a difficulty level: `Kid`, `Intermediate`, or `Expert`.

2. **ELI5 Generation** — The app calls Claude and generates an ELI5 (Explain Like I'm 5). Before a user's very first session, the app asks them to enter 3 to 5 personal topics of interest (e.g. "football", "cooking", "video games"). These interests are stored on the user's profile and used every time an ELI5 is generated — the analogy is drawn specifically from one of the user's own interests, making it immediately relatable. The explanation is always simple regardless of the chosen level. It acts as a personalised mental hook before the real content.

3. **Passage Generation** — Claude generates 2 to 3 core concept passages written at the user's chosen level. Each passage covers one distinct concept within the topic.

4. **Quiz Generation** — Claude generates a quiz of 5 to 10 questions (true/false or multiple choice) based directly on the passages. Each question is tagged to the concept it tests.

5. **Quiz Scoring** — The app scores the quiz and identifies exactly which concepts the user answered incorrectly.

6. **Remediation** — For every failed concept, Claude generates a brand new explanation using entirely different analogies. This is NOT a repeat of the original passage. The user reads the remediation and retakes the quiz for those concepts only.

7. **Remediation Loop** — Steps 5 and 6 repeat until the user passes all questions. There is no limit on attempts.

8. **Module Complete** — When the user passes, the app auto-generates a Markdown summary of everything learned in that module: the ELI5, all passages, the quiz questions and correct answers, and any remediation explanations used.

9. **Export** — The user can download the Markdown file or push it directly to their Notion workspace via the Notion API.

---

## Section 2 — Confirmed Product Decisions

| Decision | Choice |
|---|---|
| Platforms | Web (React) + Android (React Native with Expo) |
| Monetisation | Completely free, no payments or subscriptions |
| Authentication | Email + password, plus Google OAuth |
| Target Users | Students, working professionals, general curious learners of all ages |
| Language | English only (for now) |
| Offline Mode | Not needed |
| Team Size | Solo developer |
| Second Brain Integration | Notion via the official Notion API |
| UI Design Style | Simple and clean like Duolingo — friendly, colourful, not overwhelming |
| Backend Language | Python — non-negotiable |
| AI Model | claude-sonnet-4-20250514 via the Anthropic Python SDK |

---

## Section 3 — Full Tech Stack

### Backend

| Technology | What it is | Problem it solves | Why we chose it |
|---|---|---|---|
| **uv** | A modern Python package manager and virtual environment tool written in Rust | Replaces both `pip` and `python -m venv` with one tool that is 10–100x faster | Handles all Python installs via `uv pip install` and environment creation via `uv venv`; drop-in replacement with no workflow changes |
| **FastAPI** | A Python web framework for building APIs | Lets the frontend talk to the backend over HTTP | Extremely fast, modern, async-native, auto-generates Swagger docs, and has great Python type hint support |
| **Pydantic v2** | A Python library for defining and validating data shapes | Ensures that data coming into and out of the API is always the right type and format | Required by FastAPI, the v2 version is significantly faster than v1 |
| **SQLAlchemy 2.0** | A Python library for talking to a database using Python code instead of raw SQL | Lets us query and write to the database without writing SQL strings everywhere | Industry standard ORM, works perfectly with FastAPI and Alembic |
| **Alembic** | A database migration tool that works with SQLAlchemy | Tracks changes to the database schema over time so we can evolve it safely | Pairs directly with SQLAlchemy, essential for keeping the database in sync as the schema changes |
| **PostgreSQL on Supabase** | PostgreSQL is a powerful open-source relational database. Supabase hosts it in the cloud with a web dashboard | Stores all user data, learning progress, quiz results, streaks, friendships | Supabase gives us a free hosted Postgres with a visual dashboard and built-in Storage — no need to manage a server |
| **Anthropic Python SDK** | The official Python library for calling Claude AI | Handles authentication, request formatting, and response parsing for Claude API calls | Official SDK, the simplest and most reliable way to call Claude |
| **python-jose** | A Python library for creating and verifying JWT tokens | Lets us issue login tokens that prove who a user is without checking the database on every request | Lightweight and standard for JWT in Python ecosystems |
| **passlib + bcrypt** | Libraries for hashing and verifying passwords | Securely stores passwords so that even if the database is stolen, no passwords are exposed | bcrypt is the industry-standard secure password hashing algorithm |
| **python-dotenv** | Loads environment variables from a `.env` file | Lets us keep secrets (API keys, database URLs) out of the code and in a separate file that is never committed to Git | Simple, widely used, works everywhere |
| **httpx** | An async HTTP client for Python | Lets the backend make outbound HTTP requests (to Notion API, etc.) asynchronously | Async-native, which pairs perfectly with FastAPI's async architecture |
| **pytest + pytest-asyncio** | Python testing frameworks | Lets us write and run automated tests for every function before connecting it to the API | pytest is the Python standard; pytest-asyncio adds async test support needed for our async FastAPI functions |

### Frontend — Web

| Technology | What it is | Problem it solves | Why we chose it |
|---|---|---|---|
| **React 18** | A JavaScript library for building user interfaces | Lets us build complex, interactive UIs from simple reusable components | The industry standard for web UIs, massive ecosystem |
| **TypeScript** | JavaScript with declared data types | Catches mistakes at edit time instead of runtime, makes large codebases much safer to work in | Strongly recommended for any React project of meaningful size |
| **Vite** | A modern build tool and dev server for frontend projects | Bundles and serves the React app; replaces the older Create React App | Extremely fast hot-reload, minimal config, modern standard |
| **TailwindCSS** | A utility-first CSS framework | Lets us style components directly in JSX using class names, without writing separate CSS files | Pairs perfectly with the Duolingo-style design approach; fast to prototype with |
| **React Router v6** | A navigation library for React | Handles switching between pages (routes) in the single-page app | The standard routing solution for React |
| **Axios** | An HTTP client for the browser | Makes API calls from the frontend to the backend | Simple API, handles JSON automatically, easy to add auth headers globally |
| **Zustand** | A minimal state management library for React | Stores global app state (current user, active module, quiz state) without the complexity of Redux | Tiny, simple, no boilerplate — perfect for a solo dev |

### Frontend — Mobile

| Technology | What it is | Problem it solves | Why we chose it |
|---|---|---|---|
| **React Native** | A framework for building native mobile apps using React | Lets us write one codebase that runs on Android (and iOS if needed later) | Shares component knowledge with the web frontend |
| **Expo** | A toolchain and platform that sits on top of React Native | Removes the complexity of native build tooling; provides a dev client and EAS Build for APK generation | Essential for solo developers — no Xcode or Android Studio configuration headaches |
| **NativeWind** | TailwindCSS for React Native | Lets us use the same Tailwind class name approach on mobile | Consistent styling approach between web and mobile |

### Infrastructure

| Technology | What it is | Problem it solves | Why we chose it |
|---|---|---|---|
| **Supabase** | A hosted Postgres database + file storage + auth service | Provides the database and file storage without managing servers | Free tier is generous, has a great dashboard, Storage is built in |
| **Railway** | A cloud platform for deploying backend services | Hosts the FastAPI backend so it is accessible from the internet | Simple Git-based deployment, good free tier, Python-friendly |
| **Vercel** | A cloud platform for deploying frontend apps | Hosts the React web app so users can visit it in a browser | Deploys React/Vite apps with zero configuration, free tier is excellent |
| **Google Identity Services** | Google's official OAuth platform | Lets users sign in with their Google account | Required for Google OAuth — there is no other way |

---

## Section 4 — Monorepo Folder Structure

```
MasterMindAI/                          ← Root of the entire project
├── CLAUDE.md                          ← This file — Claude Code memory
├── ROADMAP.md                         ← Stage-by-stage build plan
├── README.md                          ← Public project description
├── .gitignore                         ← Files Git should never track
│
├── backend/                           ← Everything for the FastAPI Python backend
│   ├── main.py                        ← FastAPI app entry point; registers all routers
│   ├── requirements.txt               ← All Python package dependencies
│   ├── .env                           ← Secret environment variables (never committed)
│   ├── .env.example                   ← Template showing what variables are needed (committed)
│   ├── alembic.ini                    ← Alembic configuration file
│   │
│   ├── alembic/                       ← Database migration files managed by Alembic
│   │   ├── env.py                     ← Alembic environment setup; connects to the database
│   │   └── versions/                  ← Each migration file lives here (auto-generated)
│   │
│   ├── app/                           ← Main application package
│   │   ├── __init__.py                ← Marks this folder as a Python package
│   │   │
│   │   ├── core/                      ← Core config shared across the whole app
│   │   │   ├── __init__.py
│   │   │   ├── config.py              ← Loads all environment variables using pydantic-settings
│   │   │   ├── database.py            ← SQLAlchemy engine and session factory
│   │   │   └── security.py            ← JWT creation/verification; bcrypt password hashing
│   │   │
│   │   ├── models/                    ← SQLAlchemy ORM models (one file per table group)
│   │   │   ├── __init__.py
│   │   │   ├── user.py                ← User table model
│   │   │   ├── learning.py            ← Topic, Module, Passage, Quiz, Question, Answer models
│   │   │   ├── gamification.py        ← Streak, Achievement, UserAchievement models
│   │   │   └── social.py              ← Friendship, ActivityFeed models
│   │   │
│   │   ├── schemas/                   ← Pydantic v2 schemas for request/response validation
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                ← RegisterRequest, LoginRequest, TokenResponse
│   │   │   ├── learning.py            ← TopicRequest, ModuleResponse, PassageResponse, etc.
│   │   │   ├── quiz.py                ← QuizResponse, QuizSubmission, QuizResult
│   │   │   ├── gamification.py        ← StreakResponse, AchievementResponse
│   │   │   └── social.py              ← FriendRequest, FriendResponse, ActivityResponse
│   │   │
│   │   ├── routers/                   ← FastAPI route handlers (one file per feature area)
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                ← /auth/register, /auth/login, /auth/google
│   │   │   ├── learning.py            ← /learn/start, /learn/quiz, /learn/submit, /learn/remediate
│   │   │   ├── modules.py             ← /modules, /modules/{id}, /modules/{id}/export
│   │   │   ├── gamification.py        ← /streak, /achievements
│   │   │   ├── social.py              ← /friends, /friends/request, /feed
│   │   │   └── notion.py              ← /notion/auth, /notion/export/{module_id}
│   │   │
│   │   ├── services/                  ← Business logic; never put logic directly in routers
│   │   │   ├── __init__.py
│   │   │   ├── ai_service.py          ← All 4 Claude AI functions: ELI5, passages, quiz, remediation
│   │   │   ├── auth_service.py        ← User registration, login, Google OAuth logic
│   │   │   ├── learning_service.py    ← Orchestrates the full learn → quiz → remediate loop
│   │   │   ├── quiz_service.py        ← Scores quizzes, identifies failed concepts
│   │   │   ├── markdown_service.py    ← Generates the Markdown summary file for a completed module
│   │   │   ├── storage_service.py     ← Uploads/downloads files to Supabase Storage
│   │   │   ├── notion_service.py      ← Pushes content to Notion via the Notion API
│   │   │   ├── streak_service.py      ← Calculates and updates daily learning streaks
│   │   │   └── achievement_service.py ← Checks and awards badges/achievements
│   │   │
│   │   └── dependencies.py            ← Shared FastAPI dependencies (e.g. get_current_user)
│   │
│   └── tests/                         ← All pytest test files
│       ├── __init__.py
│       ├── test_ai_service.py         ← Isolated tests for all 4 Claude AI functions
│       ├── test_auth.py               ← Tests for register, login, token verification
│       ├── test_learning.py           ← Tests for the full learning loop
│       └── test_quiz.py               ← Tests for quiz scoring logic
│
├── frontend-web/                      ← Everything for the React web app
│   ├── index.html                     ← HTML entry point for Vite
│   ├── package.json                   ← Node.js dependencies and scripts
│   ├── tsconfig.json                  ← TypeScript configuration
│   ├── vite.config.ts                 ← Vite build configuration
│   ├── tailwind.config.ts             ← TailwindCSS theme configuration
│   ├── postcss.config.js              ← Required by TailwindCSS
│   ├── .env                           ← Frontend environment variables (e.g. API base URL)
│   ├── .env.example                   ← Template for frontend env vars
│   │
│   └── src/
│       ├── main.tsx                   ← React app entry point; mounts the root component
│       ├── App.tsx                    ← Root component with React Router setup
│       │
│       ├── pages/                     ← One component per full page/screen
│       │   ├── Landing.tsx            ← Public landing page for new visitors
│       │   ├── Login.tsx              ← Login form (email or Google)
│       │   ├── Register.tsx           ← Registration form
│       │   ├── Dashboard.tsx          ← Home screen after login — streaks, recent modules
│       │   ├── TopicSelection.tsx     ← Where the user picks a topic and level
│       │   ├── Learning.tsx           ← Shows the ELI5 and passages
│       │   ├── Quiz.tsx               ← Renders the quiz questions
│       │   ├── QuizResults.tsx        ← Shows score, passes/fails per concept
│       │   ├── Remediation.tsx        ← Shows remediation passages for failed concepts
│       │   ├── ModuleComplete.tsx     ← Confetti screen + export buttons (Download / Notion)
│       │   ├── Profile.tsx            ← User profile, streak count, achievements
│       │   ├── Friends.tsx            ← Friend list, search users, activity feed
│       │   ├── KnowledgeMap.tsx       ← Visual graph of completed topics
│       │   └── Settings.tsx           ← Account settings, Notion connection
│       │
│       ├── components/                ← Reusable UI components used across multiple pages
│       │   ├── Navbar.tsx             ← Top navigation bar
│       │   ├── ProgressBar.tsx        ← Shows learning/quiz progress
│       │   ├── QuizCard.tsx           ← Renders a single quiz question
│       │   ├── PassageCard.tsx        ← Renders a single concept passage
│       │   ├── AchievementBadge.tsx   ← Renders a single badge/achievement
│       │   ├── StreakCounter.tsx      ← Displays the current streak flame and count
│       │   └── LoadingSpinner.tsx     ← Generic loading indicator
│       │
│       ├── store/                     ← Zustand global state stores
│       │   ├── authStore.ts           ← Current user, JWT token, login/logout actions
│       │   └── learningStore.ts       ← Active module state, current quiz, results
│       │
│       ├── api/                       ← Axios API call functions (one file per feature)
│       │   ├── axiosClient.ts         ← Axios instance with base URL and auth header
│       │   ├── auth.ts                ← register(), login(), googleLogin()
│       │   ├── learning.ts            ← startModule(), submitQuiz(), getRemediation()
│       │   ├── modules.ts             ← getModules(), getModule(), exportToNotion()
│       │   └── social.ts              ← getFriends(), sendRequest(), getFeed()
│       │
│       └── types/                     ← TypeScript type definitions
│           └── index.ts               ← All shared types: User, Module, Quiz, Question, etc.
│
└── frontend-mobile/                   ← Everything for the React Native Expo Android app
    ├── package.json                   ← Node.js dependencies for the mobile app
    ├── app.json                       ← Expo app configuration (name, slug, icon, etc.)
    ├── babel.config.js                ← Babel configuration required by Expo
    ├── tailwind.config.js             ← NativeWind configuration
    ├── .env                           ← Mobile environment variables
    │
    └── src/
        ├── app/                       ← Expo Router file-based navigation (screens)
        │   ├── index.tsx              ← Root redirect (sends to login or dashboard)
        │   ├── (auth)/                ← Auth screens group
        │   │   ├── login.tsx          ← Mobile login screen
        │   │   └── register.tsx       ← Mobile register screen
        │   └── (app)/                 ← Authenticated screens group
        │       ├── dashboard.tsx      ← Mobile dashboard
        │       ├── topic.tsx          ← Topic selection screen
        │       ├── learning.tsx       ← ELI5 and passages screen
        │       ├── quiz.tsx           ← Quiz screen
        │       ├── results.tsx        ← Quiz results screen
        │       ├── remediation.tsx    ← Remediation screen
        │       ├── complete.tsx       ← Module complete screen
        │       └── profile.tsx        ← Profile and streaks screen
        │
        ├── components/                ← Reusable mobile components
        │   ├── QuizCard.tsx
        │   ├── PassageCard.tsx
        │   └── StreakCounter.tsx
        │
        └── api/                       ← Same API call functions reused for mobile
            └── axiosClient.ts         ← Axios instance with mobile base URL
```

---

## Section 5 — PostgreSQL Database Schema

### Table: `users`
Stores every registered user account.

```sql
users
├── id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── email           VARCHAR(255) UNIQUE NOT NULL
├── hashed_password VARCHAR(255) NULLABLE          -- NULL if user registered via Google OAuth
├── full_name       VARCHAR(255) NOT NULL
├── avatar_url      VARCHAR(500) NULLABLE
├── google_id       VARCHAR(255) UNIQUE NULLABLE   -- Google OAuth subject ID
├── interest_topics TEXT[] NULLABLE                -- 3-5 personal interests entered during onboarding (e.g. ["football", "cooking", "music"]) — used to personalise ELI5 analogies
├── notion_access_token  TEXT NULLABLE             -- Stored after Notion OAuth
├── notion_workspace_id  VARCHAR(255) NULLABLE
├── is_active       BOOLEAN DEFAULT TRUE NOT NULL
├── created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
└── updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
```

### Table: `modules`
Each row is one completed or in-progress learning session on a specific topic.

```sql
modules
├── id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
├── topic           VARCHAR(255) NOT NULL           -- e.g. "Black holes"
├── level           VARCHAR(50) NOT NULL            -- 'kid', 'intermediate', 'expert'
├── eli5_text       TEXT NOT NULL                   -- The ELI5 explanation generated by Claude
├── status          VARCHAR(50) DEFAULT 'in_progress' NOT NULL  -- 'in_progress' | 'completed'
├── markdown_url    VARCHAR(500) NULLABLE           -- Supabase Storage URL of the exported .md file
├── notion_page_id  VARCHAR(255) NULLABLE           -- Notion page ID if exported to Notion
├── completed_at    TIMESTAMPTZ NULLABLE
├── created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
└── updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
```

### Table: `passages`
Each row is one concept passage generated for a module. A module has 2–3 passages.

```sql
passages
├── id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── module_id       UUID NOT NULL REFERENCES modules(id) ON DELETE CASCADE
├── concept_title   VARCHAR(255) NOT NULL           -- e.g. "What is gravity?"
├── content         TEXT NOT NULL                   -- The full passage text
├── order_index     INTEGER NOT NULL                -- 1, 2, or 3 — for display ordering
├── created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
└── updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
```

### Table: `quizzes`
Each row is one quiz attempt for a module. A user may have multiple quiz attempts per module (due to remediation).

```sql
quizzes
├── id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── module_id       UUID NOT NULL REFERENCES modules(id) ON DELETE CASCADE
├── attempt_number  INTEGER NOT NULL DEFAULT 1      -- Increments with each remediation retry
├── score           INTEGER NULLABLE                -- Number of correct answers
├── total_questions INTEGER NULLABLE
├── passed          BOOLEAN NULLABLE                -- True if all questions answered correctly
├── submitted_at    TIMESTAMPTZ NULLABLE
├── created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
└── updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
```

### Table: `questions`
Each row is one question in a specific quiz.

```sql
questions
├── id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── quiz_id         UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE
├── passage_id      UUID NOT NULL REFERENCES passages(id) ON DELETE CASCADE -- which concept this tests
├── question_text   TEXT NOT NULL
├── question_type   VARCHAR(50) NOT NULL            -- 'true_false' | 'multiple_choice'
├── options         JSONB NULLABLE                  -- Array of option strings for MC questions
├── correct_answer  VARCHAR(500) NOT NULL           -- The correct answer string
├── order_index     INTEGER NOT NULL
├── created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
└── updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
```

### Table: `answers`
Each row is the user's answer to one question.

```sql
answers
├── id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── quiz_id         UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE
├── question_id     UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE
├── user_answer     VARCHAR(500) NOT NULL
├── is_correct      BOOLEAN NOT NULL
├── created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
└── updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
```

### Table: `remediations`
Each row is one remediation explanation generated for a failed concept.

```sql
remediations
├── id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── module_id       UUID NOT NULL REFERENCES modules(id) ON DELETE CASCADE
├── passage_id      UUID NOT NULL REFERENCES passages(id) ON DELETE CASCADE -- the concept that failed
├── quiz_id         UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE  -- the quiz attempt that triggered this
├── content         TEXT NOT NULL                   -- New remediation explanation from Claude
├── created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
└── updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
```

### Table: `streaks`
Tracks the daily learning streak for each user.

```sql
streaks
├── id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── user_id         UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE
├── current_streak  INTEGER DEFAULT 0 NOT NULL
├── longest_streak  INTEGER DEFAULT 0 NOT NULL
├── last_activity_date  DATE NULLABLE               -- The last date the user completed a module
├── created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
└── updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
```

### Table: `achievements`
Master list of all possible achievements/badges in the app.

```sql
achievements
├── id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── slug            VARCHAR(100) UNIQUE NOT NULL    -- e.g. 'first_module', 'streak_7'
├── name            VARCHAR(255) NOT NULL           -- e.g. "First Steps"
├── description     TEXT NOT NULL
├── icon_emoji      VARCHAR(10) NOT NULL            -- e.g. "🔥"
└── created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
```

### Table: `user_achievements`
Which users have earned which achievements.

```sql
user_achievements
├── id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
├── achievement_id  UUID NOT NULL REFERENCES achievements(id) ON DELETE CASCADE
├── earned_at       TIMESTAMPTZ DEFAULT NOW() NOT NULL
└── UNIQUE (user_id, achievement_id)
```

### Table: `friendships`
Tracks friend relationships between users. Each accepted friendship is one row.

```sql
friendships
├── id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── requester_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
├── addressee_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
├── status          VARCHAR(50) DEFAULT 'pending' NOT NULL  -- 'pending' | 'accepted' | 'rejected'
├── created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
└── updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
```

### Table: `activity_feed`
Events shown in the friend activity feed (e.g. "Alice completed a module on Photosynthesis").

```sql
activity_feed
├── id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
├── activity_type   VARCHAR(100) NOT NULL           -- 'module_completed' | 'streak_milestone' | 'achievement_earned'
├── metadata        JSONB NOT NULL                  -- Flexible data: {topic, level, achievement_name, streak_count, etc.}
├── created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
└── updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
```

---

## Section 6 — Environment Variables

### backend/.env

```env
# --- DATABASE ---
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DB_NAME
# Where to find it: Supabase dashboard → Project Settings → Database → Connection string (URI mode)
# What it does: Tells SQLAlchemy where to connect to the PostgreSQL database

# --- SUPABASE ---
SUPABASE_URL=https://your-project-ref.supabase.co
# Where to find it: Supabase dashboard → Project Settings → API → Project URL
# What it does: Base URL for Supabase Storage API calls

SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
# Where to find it: Supabase dashboard → Project Settings → API → service_role key (secret)
# What it does: Admin key that allows the backend to read/write Supabase Storage without user auth

# --- JWT AUTH ---
SECRET_KEY=your-long-random-secret-key-here-minimum-32-chars
# Where to find it: Generate it yourself with: python -c "import secrets; print(secrets.token_hex(32))"
# What it does: Secret used to sign and verify JWT tokens — never share this

JWT_ALGORITHM=HS256
# What it does: The algorithm used to sign JWT tokens — HS256 is the standard choice

ACCESS_TOKEN_EXPIRE_MINUTES=60
# What it does: How long a JWT token remains valid before the user must log in again

# --- ANTHROPIC / CLAUDE ---
ANTHROPIC_API_KEY=sk-ant-your-key-here
# Where to find it: https://console.anthropic.com → API Keys
# What it does: Authenticates all calls to the Claude AI API

# --- GOOGLE OAUTH ---
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
# Where to find it: Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client ID
# What it does: Identifies our app to Google when a user clicks "Sign in with Google"

GOOGLE_CLIENT_SECRET=your-google-client-secret
# Where to find it: Same place as GOOGLE_CLIENT_ID
# What it does: Secret that proves to Google our app is who it claims to be

# --- NOTION ---
NOTION_CLIENT_ID=your-notion-oauth-client-id
# Where to find it: https://www.notion.so/my-integrations → your integration → OAuth
# What it does: Identifies our app to Notion during the OAuth flow

NOTION_CLIENT_SECRET=your-notion-oauth-client-secret
# Where to find it: Same place as NOTION_CLIENT_ID
# What it does: Secret for Notion OAuth token exchange

NOTION_REDIRECT_URI=http://localhost:8000/notion/callback
# What it does: The URL Notion redirects back to after the user authorises our app

# --- APP ---
ENVIRONMENT=development
# What it does: Controls behaviour that differs between dev and production (e.g. CORS origins)

FRONTEND_URL=http://localhost:5173
# What it does: Used for CORS — tells FastAPI which origin is allowed to call the API
```

### frontend-web/.env

```env
VITE_API_BASE_URL=http://localhost:8000
# What it does: The base URL all Axios calls use to reach the FastAPI backend

VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
# What it does: Used by Google Identity Services to initiate the Google sign-in popup in the browser
```

---

## Section 7 — Claude AI Prompt Templates

All four functions live in `backend/app/services/ai_service.py`.

### Prompt 1: generate_eli5

```python
async def generate_eli5(topic: str, level: str, user_interests: list[str]) -> str:
    """
    Generate an ELI5 (Explain Like I'm 5) for any topic.
    The analogy is drawn from the user's own personal interests for maximum relatability.
    Always uses simple analogies regardless of the user's chosen level.
    Temperature 0.7 — we want creative, imaginative analogies.
    Max tokens 400 — the ELI5 should be short and punchy.

    user_interests: list of 3-5 interests the user entered during onboarding
                    e.g. ["football", "cooking", "video games"]
    """
    interests_str = ", ".join(user_interests)

    prompt = f"""You are a brilliant teacher who is amazing at explaining complex things simply.

Your task is to explain the topic "{topic}" as if you are talking to a 5-year-old child.

This specific learner is personally interested in: {interests_str}

Rules:
- You MUST build your analogy using one or more of the learner's personal interests listed above — do not use a generic analogy
- Keep it to 3-5 sentences maximum
- Do NOT use jargon or technical terms of any kind
- Start directly with the analogy — do not say "imagine" or "think of it like" as your very first word, be more creative
- Do not mention the difficulty level "{level}" at all
- End with one sentence about why this topic is interesting or useful to know

Return only the ELI5 explanation. No headings, no bullet points, no extra commentary."""

    client = anthropic.AsyncAnthropic()
    message = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=400,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text.strip()
```

### Prompt 2: generate_passages

```python
async def generate_passages(topic: str, level: str, eli5_text: str) -> list[dict]:
    """
    Generate 2-3 core concept passages at the user's chosen level.
    Temperature 0.5 — balanced between accuracy and interesting prose.
    Max tokens 1500 — enough for three detailed passages.
    Returns a list of dicts: [{"concept_title": str, "content": str}]
    """
    level_descriptions = {
        "kid": "a curious 10-12 year old child with no prior knowledge of this subject",
        "intermediate": "a university undergraduate or curious adult who knows the basics",
        "expert": "a graduate-level student or professional in a related field"
    }
    audience = level_descriptions.get(level, level_descriptions["intermediate"])

    prompt = f"""You are an expert educator writing clear, engaging learning content.

Topic: {topic}
Audience: {audience}

Context: The learner has just read this introductory analogy:
"{eli5_text}"

Your task is to write exactly 2 or 3 core concept passages about "{topic}" for this audience.

Rules:
- Each passage must cover one distinct, important concept within the topic
- Each passage must have a clear, specific title (the concept name)
- Each passage should be 100-200 words
- Write at the appropriate level for the audience — not too simple, not too advanced
- Build naturally from the ELI5 analogy above
- Do NOT repeat the ELI5 analogy
- Use active voice and engaging prose

Return your response as valid JSON only, with this exact structure:
[
  {{
    "concept_title": "Title of Concept 1",
    "content": "Full passage text for concept 1..."
  }},
  {{
    "concept_title": "Title of Concept 2",
    "content": "Full passage text for concept 2..."
  }}
]

Return ONLY the JSON array. No explanation, no markdown code blocks, no extra text."""

    client = anthropic.AsyncAnthropic()
    message = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        temperature=0.5,
        messages=[{"role": "user", "content": prompt}]
    )
    import json
    return json.loads(message.content[0].text.strip())
```

### Prompt 3: generate_quiz

```python
async def generate_quiz(topic: str, passages_content: list[dict], level: str) -> list[dict]:
    """
    Generate a quiz of 5-10 questions directly based on the passages.
    Each question is tagged to the concept_title it tests.
    Temperature 0.4 — we want factually accurate questions, not creative ones.
    Max tokens 2000 — enough for up to 10 detailed questions.
    Returns a list of question dicts.
    """
    passages_text = "\n\n".join([
        f"CONCEPT: {p['concept_title']}\n{p['content']}"
        for p in passages_content
    ])

    prompt = f"""You are an expert quiz writer creating assessment questions for a learning app.

Topic: {topic}
Level: {level}

The learner has read the following passages:

{passages_text}

Your task is to write between 5 and 10 quiz questions that test understanding of ONLY the content above.

Rules:
- Each question must be either true/false or multiple choice (your choice per question)
- For multiple choice: provide exactly 4 options (A, B, C, D)
- For true/false: options array should be ["True", "False"]
- The correct_answer must exactly match one of the options strings
- Each question must be tagged with the concept_title it tests (use the exact concept titles from above)
- Do not ask questions about information not covered in the passages
- Questions should test understanding, not just word-matching

Return your response as valid JSON only, with this exact structure:
[
  {{
    "concept_title": "Title of the concept this question tests",
    "question_text": "The question text here?",
    "question_type": "multiple_choice",
    "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
    "correct_answer": "Option A text"
  }},
  {{
    "concept_title": "Title of the concept this question tests",
    "question_text": "True or false: statement here.",
    "question_type": "true_false",
    "options": ["True", "False"],
    "correct_answer": "True"
  }}
]

Return ONLY the JSON array. No explanation, no markdown code blocks, no extra text."""

    client = anthropic.AsyncAnthropic()
    message = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        temperature=0.4,
        messages=[{"role": "user", "content": prompt}]
    )
    import json
    return json.loads(message.content[0].text.strip())
```

### Prompt 4: generate_remediation

```python
async def generate_remediation(
    topic: str,
    failed_concepts: list[str],
    original_passages: list[dict]
) -> list[dict]:
    """
    Generate brand new remediation explanations for concepts the user got wrong.
    Uses completely different analogies from the original passages.
    Temperature 0.7 — high creativity to find fresh analogies.
    Max tokens 1500 — enough for 2-3 remediation passages.
    Returns a list of dicts: [{"concept_title": str, "content": str}]
    """
    original_text = "\n\n".join([
        f"CONCEPT: {p['concept_title']}\nORIGINAL EXPLANATION: {p['content']}"
        for p in original_passages
        if p['concept_title'] in failed_concepts
    ])

    failed_list = "\n".join([f"- {c}" for c in failed_concepts])

    prompt = f"""You are a patient, creative tutor helping a student who did not understand a concept on their first try.

Topic: {topic}

The student struggled with these specific concepts:
{failed_list}

Here are the original explanations they already read (DO NOT repeat these — you must use completely different analogies):
{original_text}

Your task is to re-explain ONLY the failed concepts above using entirely fresh analogies and different wording.

Rules:
- Use a completely different analogy from the original explanation — do not recycle any of the same comparisons
- Be patient, warm, and encouraging in tone
- Each remediation passage should be 100-180 words
- Focus on clarity first — the student found this difficult, so be especially clear
- Do not say "as mentioned before" or reference the original explanation at all

Return your response as valid JSON only, with this exact structure:
[
  {{
    "concept_title": "Exact concept title matching the failed concept",
    "content": "Your new remediation explanation using fresh analogies..."
  }}
]

Return ONLY the JSON array. No explanation, no markdown code blocks, no extra text."""

    client = anthropic.AsyncAnthropic()
    message = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}]
    )
    import json
    return json.loads(message.content[0].text.strip())
```

---

## Section 8 — Full API Endpoint Reference

Base URL (local): `http://localhost:8000`
All protected routes require `Authorization: Bearer <jwt_token>` header.

### Auth Routes (`/auth`)

| Method | Path | Auth | What it does | Request Body | Response |
|---|---|---|---|---|---|
| POST | `/auth/register` | No | Creates a new user account | `{email, password, full_name}` | `{access_token, token_type}` |
| POST | `/auth/login` | No | Logs in with email + password | `{email, password}` | `{access_token, token_type}` |
| POST | `/auth/google` | No | Logs in or registers via Google OAuth | `{id_token}` | `{access_token, token_type}` |
| GET | `/auth/me` | Yes | Returns the current logged-in user's profile | — | `{id, email, full_name, avatar_url, ...}` |

DB tables touched: `users`

---

### Learning Routes (`/learn`)

| Method | Path | Auth | What it does | Request Body | Response |
|---|---|---|---|---|---|
| POST | `/learn/start` | Yes | Starts a new module: generates ELI5 and passages, saves to DB | `{topic, level}` | `{module_id, eli5_text, passages: [...]}` |
| POST | `/learn/quiz/generate` | Yes | Generates a quiz for an existing module | `{module_id}` | `{quiz_id, questions: [...]}` |
| POST | `/learn/quiz/submit` | Yes | Submits quiz answers, scores them, identifies failed concepts | `{quiz_id, answers: [{question_id, user_answer}]}` | `{score, total, passed, failed_concepts: [...]}` |
| POST | `/learn/remediate` | Yes | Generates remediation for failed concepts | `{module_id, quiz_id, failed_concepts: [...]}` | `{remediations: [{concept_title, content}]}` |

DB tables touched: `modules`, `passages`, `quizzes`, `questions`, `answers`, `remediations`, `streaks`, `activity_feed`

---

### Module Routes (`/modules`)

| Method | Path | Auth | What it does | Request Body | Response |
|---|---|---|---|---|---|
| GET | `/modules` | Yes | Lists all modules for the current user | — | `[{id, topic, level, status, completed_at, ...}]` |
| GET | `/modules/{module_id}` | Yes | Returns full detail of one module including passages | — | `{id, topic, eli5_text, passages, quizzes, ...}` |
| POST | `/modules/{module_id}/export/download` | Yes | Generates Markdown file and returns a download URL | — | `{download_url}` |
| POST | `/modules/{module_id}/export/notion` | Yes | Pushes module summary to the user's Notion workspace | — | `{notion_page_url}` |

DB tables touched: `modules`, `passages`, `quizzes`

---

### Gamification Routes (`/gamification`)

| Method | Path | Auth | What it does | Request Body | Response |
|---|---|---|---|---|---|
| GET | `/gamification/streak` | Yes | Returns the user's current and longest streak | — | `{current_streak, longest_streak, last_activity_date}` |
| GET | `/gamification/achievements` | Yes | Returns all achievements the user has earned | — | `[{slug, name, description, icon_emoji, earned_at}]` |

DB tables touched: `streaks`, `user_achievements`, `achievements`

---

### Social Routes (`/social`)

| Method | Path | Auth | What it does | Request Body | Response |
|---|---|---|---|---|---|
| GET | `/social/friends` | Yes | Lists all accepted friends | — | `[{id, full_name, avatar_url, current_streak}]` |
| GET | `/social/friends/requests` | Yes | Lists incoming pending friend requests | — | `[{id, requester: {id, full_name}}]` |
| POST | `/social/friends/request` | Yes | Sends a friend request to a user | `{addressee_id}` | `{message: "Request sent"}` |
| POST | `/social/friends/accept` | Yes | Accepts a pending friend request | `{friendship_id}` | `{message: "Friend added"}` |
| GET | `/social/feed` | Yes | Returns the activity feed for the current user's friends | — | `[{user: {full_name}, activity_type, metadata, created_at}]` |
| GET | `/social/users/search` | Yes | Searches for users by name or email | `?q=search_term` | `[{id, full_name, avatar_url}]` |

DB tables touched: `friendships`, `users`, `activity_feed`, `streaks`

---

### Notion Routes (`/notion`)

| Method | Path | Auth | What it does | Request Body | Response |
|---|---|---|---|---|---|
| GET | `/notion/auth-url` | Yes | Returns the Notion OAuth URL to redirect the user to | — | `{auth_url}` |
| GET | `/notion/callback` | No | Handles Notion OAuth callback, saves token | Query: `?code=...` | Redirect to frontend |
| DELETE | `/notion/disconnect` | Yes | Removes the user's stored Notion credentials | — | `{message: "Disconnected"}` |

DB tables touched: `users`

---

## Section 9 — Build Order

| Stage | Title |
|---|---|
| 1 | Local Environment Setup |
| 2 | Supabase Database Setup |
| 3 | Authentication API |
| 4 | Core AI Service |
| 5 | Learning Module API |
| 6 | Cloud Storage and Markdown Export |
| 7 | Notion Integration |
| 8 | Gamification API |
| 9 | Social Features API |
| 10 | Backend Polish and Railway Deployment |
| 11 | Web Frontend |
| 12 | Android App |

**Why this order?** The backend is built first because the frontend depends on it. Auth is built before any protected features. The AI service is tested in isolation before being wired to routes. The frontend is built last because it simply consumes the already-working API.

---

## Section 10 — Coding Rules

These rules apply to every file in the project without exception.

1. **No logic in routers.** Routers only validate input and call service functions. All business logic lives in `services/`.
2. **All database operations are async.** Use `async def` and `await` for every DB query and Claude API call.
3. **Never commit secrets.** `.env` files are in `.gitignore`. Only `.env.example` (with placeholder values) is committed.
4. **Pydantic for all I/O.** Every API request and response must go through a Pydantic schema. Never return raw SQLAlchemy model objects.
5. **Return consistent JSON shapes.** Successful responses: `{"data": {...}}`. Errors: `{"error": {"code": str, "message": str}}`.
6. **Test AI functions in isolation first.** Before a function is called by a router, it must have a passing pytest test.
7. **One migration per schema change.** Never modify an existing Alembic migration. Always create a new one.
8. **TypeScript strict mode is on.** No `any` types in the frontend. Define all types in `src/types/index.ts`.
9. **All Axios calls go through `axiosClient.ts`.** This is the only file that sets the base URL and auth header. No raw fetch() calls.
10. **Zustand stores must be typed.** Every store in `src/store/` must have a fully typed interface.
11. **No inline styles in React.** All styling uses Tailwind classes only.
12. **Keep prompts in `ai_service.py` only.** Never write prompt strings anywhere else in the codebase.
13. **Use UUIDs for all primary keys.** Never use auto-incrementing integers.

---

## Section 11 — External Accounts and Services

| Service | What you need it for | URL |
|---|---|---|
| **uv** | Python package manager — install before writing any backend code | https://docs.astral.sh/uv/getting-started/installation/ |
| **Anthropic Console** | Get the Claude API key | https://console.anthropic.com |
| **Supabase** | Create the PostgreSQL database and Storage bucket | https://supabase.com |
| **Railway** | Deploy the FastAPI backend | https://railway.app |
| **Vercel** | Deploy the React web frontend | https://vercel.com |
| **Google Cloud Console** | Set up Google OAuth credentials | https://console.cloud.google.com |
| **Notion Developers** | Create the Notion integration for OAuth | https://www.notion.so/my-integrations |
| **GitHub** | Version control and connecting to Railway/Vercel for deployment | https://github.com |

---

## Section 12 — Starting a New Claude Code Session

At the start of every new session, say exactly this:

> "Read CLAUDE.md and confirm you understand the project."

Claude Code will read this file and confirm. You can then say things like:
- "We are on Stage 3. Pick up where we left off on the login endpoint."
- "I got an error in `auth_service.py`. Here is the traceback: ..."
- "Start Stage 4. Begin with `ai_service.py`."

**Before starting any stage**, always tell Claude:
1. Which stage you are on
2. What you completed last session
3. Any errors or blockers you encountered

**Never ask Claude to guess** what was done in a previous session. Always tell it explicitly — this file gives the structure, but you provide the current progress.
