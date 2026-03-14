# CLAUDE.md — MasterMind

> Read at session start. Last updated: 2026-02-28
> Session start command: "Read CLAUDE.md and confirm you understand the project."

---

## 1. Project Summary

**MasterMind** — adaptive AI-powered learning app. Teaches any topic step-by-step using Claude AI. Personalised, gamified, remediation loops until mastery.

**Confirmed decisions:**
- Platforms: Web (React) + Android (React Native + Expo)
- Free, no payments. Auth: Email/password + Google OAuth
- Backend: Python (non-negotiable). Model: `claude-sonnet-4-20250514`
- DB: PostgreSQL on Supabase. Second brain: Notion API
- UI style: Duolingo-like — friendly, colourful, clean
- Solo developer. English only. No offline mode.

---

## 2. Full Learning Flow

1. **Topic Selection** — User picks topic + level: `kid` | `intermediate` | `expert`
2. **ELI5** — Claude generates analogy drawn from user's 3–5 onboarding interests (stored on profile). Always simple regardless of level.
3. **Passages** — Claude generates 2–3 concept passages at chosen level.
4. **Quiz** — Claude generates 5–10 true/false or multiple-choice questions tagged to concept.
5. **Scoring** — App scores quiz, identifies failed concepts.
6. **Remediation** — For each failed concept: Claude generates a NEW explanation with different analogies. User retakes quiz for failed concepts only.
7. **Remediation Loop** — Steps 5–6 repeat until all passed. No attempt limit.
8. **Module Complete** — Auto-generates Markdown summary: ELI5 + passages + quiz Q&A + remediations.
9. **Export** — User downloads Markdown or pushes to Notion.

---

## 3. Tech Stack

### Backend
| Tech | Purpose |
|---|---|
| uv | Package manager + venv (replaces pip) |
| FastAPI | API framework, async-native |
| Pydantic v2 | Request/response validation |
| SQLAlchemy 2.0 | ORM |
| Alembic | DB migrations |
| PostgreSQL (Supabase) | Primary database + storage |
| Anthropic Python SDK | Claude API calls |
| python-jose | JWT creation/verification |
| passlib + bcrypt | Password hashing |
| python-dotenv | Env variable loading |
| httpx | Async outbound HTTP (Notion API) |
| pytest + pytest-asyncio | Testing |

### Frontend — Web
| Tech | Purpose |
|---|---|
| React 18 + TypeScript | UI framework |
| Vite | Build tool / dev server |
| TailwindCSS | Styling |
| React Router v6 | Navigation |
| Axios | API calls |
| Zustand | Global state |

### Frontend — Mobile
| Tech | Purpose |
|---|---|
| React Native + Expo | Android app |
| NativeWind | TailwindCSS for mobile |

### Infrastructure
| Tech | Purpose |
|---|---|
| Supabase | Hosted Postgres + Storage |
| Railway | FastAPI deployment |
| Vercel | React web deployment |
| Google Identity Services | Google OAuth |

---

## 4. Folder Structure

```
MasterMindAI/
├── CLAUDE.md / ROADMAP.md / README.md / .gitignore
├── backend/
│   ├── main.py                        # FastAPI entry point
│   ├── requirements.txt / .env / .env.example / alembic.ini
│   ├── alembic/env.py + versions/
│   └── app/
│       ├── core/config.py + database.py + security.py
│       ├── models/user.py + learning.py + gamification.py + social.py
│       ├── schemas/auth.py + learning.py + quiz.py + gamification.py + social.py
│       ├── routers/auth.py + learning.py + modules.py + gamification.py + social.py + notion.py
│       ├── services/
│       │   ├── ai_service.py          # All 4 Claude functions: ELI5, passages, quiz, remediation
│       │   ├── auth_service.py + learning_service.py + quiz_service.py
│       │   ├── markdown_service.py + storage_service.py + notion_service.py
│       │   └── streak_service.py + achievement_service.py
│       └── dependencies.py
│   └── tests/test_ai_service.py + test_auth.py + test_learning.py + test_quiz.py
├── frontend-web/
│   ├── index.html / package.json / tsconfig.json / vite.config.ts / tailwind.config.ts
│   └── src/
│       ├── main.tsx + App.tsx
│       ├── pages/ Landing + Login + Register + Dashboard + TopicSelection + Learning
│       │         + Quiz + QuizResults + Remediation + ModuleComplete + Profile
│       │         + Friends + KnowledgeMap + Settings
│       ├── components/ Navbar + ProgressBar + QuizCard + PassageCard + AchievementBadge
│       │              + StreakCounter + LoadingSpinner
│       ├── store/ authStore.ts + learningStore.ts
│       ├── api/ axiosClient.ts + auth.ts + learning.ts + modules.ts + social.ts
│       └── types/index.ts
└── frontend-mobile/
    └── src/
        ├── app/ index.tsx + (auth)/login + register + (app)/dashboard + topic
        │         + learning + quiz + results + remediation + complete + profile
        ├── components/ QuizCard + PassageCard + StreakCounter
        └── api/axiosClient.ts
```

---

## 5. Database Schema

```sql
users          id(PK) email(UQ) hashed_password full_name avatar_url google_id(UQ)
               interest_topics(TEXT[]) notion_access_token notion_workspace_id
               is_active created_at updated_at

modules        id(PK) user_id(FK) topic level eli5_text status
               markdown_url notion_page_id completed_at created_at updated_at

passages       id(PK) module_id(FK) concept_title content order_index created_at updated_at

quizzes        id(PK) module_id(FK) attempt_number score total_questions passed
               submitted_at created_at updated_at

questions      id(PK) quiz_id(FK) passage_id(FK) question_text question_type
               options(JSONB) correct_answer order_index created_at updated_at

answers        id(PK) quiz_id(FK) question_id(FK) user_answer is_correct created_at updated_at

remediations   id(PK) module_id(FK) passage_id(FK) quiz_id(FK) content created_at updated_at

streaks        id(PK) user_id(FK,UQ) current_streak longest_streak last_activity_date
               created_at updated_at

achievements   id(PK) slug(UQ) name description icon_emoji created_at

user_achievements  id(PK) user_id(FK) achievement_id(FK) earned_at
                   UNIQUE(user_id, achievement_id)

friendships    id(PK) requester_id(FK) addressee_id(FK)
               status('pending'|'accepted'|'rejected') created_at updated_at

activity_feed  id(PK) user_id(FK) activity_type metadata(JSONB) created_at updated_at
```

**Key notes:** All PKs are UUID. `hashed_password` nullable (Google OAuth users). `interest_topics` TEXT[] used for ELI5 personalisation. `options` JSONB for MC questions.

---

## 6. Environment Variables

### backend/.env
```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DB_NAME
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SECRET_KEY=your-32-char-minimum-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ANTHROPIC_API_KEY=sk-ant-your-key
GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret
NOTION_CLIENT_ID=your-notion-client-id
NOTION_CLIENT_SECRET=your-notion-client-secret
NOTION_REDIRECT_URI=http://localhost:8000/notion/callback
ENVIRONMENT=development
FRONTEND_URL=http://localhost:5173
```

### frontend-web/.env
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com
```

---

## 7. AI Prompt Templates (`backend/app/services/ai_service.py`)

### generate_eli5
- temp=0.7, max_tokens=400
- Analogy MUST use one of `user_interests` (list of 3–5 strings)
- 3–5 sentences, no jargon, no "imagine" opener, end with why topic matters
- Return: plain string

### generate_passages
- temp=0.5, max_tokens=1500
- 2–3 passages, each 100–200 words, one distinct concept each
- Build from ELI5, don't repeat it. Audience varies by level:
  - kid → "curious 10–12 year old"
  - intermediate → "university undergraduate or curious adult"
  - expert → "graduate-level student or professional"
- Return: `[{"concept_title": str, "content": str}]` — JSON only, no markdown fences

### generate_quiz
- temp=0.4, max_tokens=2000
- 5–10 questions. Types: `true_false` | `multiple_choice` (4 options)
- Each question tagged to `concept_title`. `correct_answer` must match an option exactly
- Return: `[{"concept_title", "question_text", "question_type", "options", "correct_answer"}]`

### generate_remediation
- temp=0.7, max_tokens=1500
- Only for `failed_concepts`. Must use DIFFERENT analogies from original passages
- Warm, patient tone. 100–180 words each. No reference to original explanation
- Return: `[{"concept_title": str, "content": str}]`

---

## 8. API Endpoints

Base: `http://localhost:8000` | Protected routes: `Authorization: Bearer <jwt>`

### /auth
| Method | Path | Auth | Body | Response |
|---|---|---|---|---|
| POST | /auth/register | No | email, password, full_name | access_token |
| POST | /auth/login | No | email, password | access_token |
| POST | /auth/google | No | id_token | access_token |
| GET | /auth/me | Yes | — | user profile |

### /learn
| Method | Path | Auth | Body | Response |
|---|---|---|---|---|
| POST | /learn/start | Yes | topic, level | module_id, eli5_text, passages |
| POST | /learn/quiz/generate | Yes | module_id | quiz_id, questions |
| POST | /learn/quiz/submit | Yes | quiz_id, answers[] | score, passed, failed_concepts |
| POST | /learn/remediate | Yes | module_id, quiz_id, failed_concepts | remediations[] |

### /modules
| Method | Path | Auth | Response |
|---|---|---|---|
| GET | /modules | Yes | all user modules |
| GET | /modules/{id} | Yes | full module detail |
| POST | /modules/{id}/export/download | Yes | download_url |
| POST | /modules/{id}/export/notion | Yes | notion_page_url |

### /gamification
| GET /gamification/streak | Yes | current_streak, longest_streak, last_activity_date |
| GET /gamification/achievements | Yes | earned achievements list |

### /social
| Method | Path | Auth | Body/Query |
|---|---|---|---|
| GET | /social/friends | Yes | — |
| GET | /social/friends/requests | Yes | — |
| POST | /social/friends/request | Yes | addressee_id |
| POST | /social/friends/accept | Yes | friendship_id |
| GET | /social/feed | Yes | — |
| GET | /social/users/search | Yes | ?q=term |

### /notion
| GET /notion/auth-url | Yes | Returns OAuth URL |
| GET /notion/callback | No | Handles callback, saves token |
| DELETE /notion/disconnect | Yes | Removes Notion credentials |

---

## 9. Build Order

| Stage | Title |
|---|---|
| 1 | Local Environment Setup |
| 2 | Supabase Database Setup |
| 3 | Authentication API |
| 4 | Core AI Service |
| 5 | Learning Module API |
| 6 | Cloud Storage + Markdown Export |
| 7 | Notion Integration |
| 8 | Gamification API |
| 9 | Social Features API |
| 10 | Backend Polish + Railway Deploy |
| 11 | Web Frontend |
| 12 | Android App |

---

## 10. Coding Rules

1. **No logic in routers** — routers call services only
2. **All DB + Claude calls are async** — `async def` + `await` everywhere
3. **Never commit secrets** — `.env` in `.gitignore`, only `.env.example` committed
4. **Pydantic for all I/O** — never return raw SQLAlchemy objects
5. **Consistent JSON shapes** — success: `{"data": {...}}` | error: `{"error": {"code", "message"}}`
6. **Test AI functions first** — passing pytest before wiring to router
7. **One migration per schema change** — never edit existing Alembic migrations
8. **TypeScript strict mode** — no `any`, all types in `src/types/index.ts`
9. **All Axios calls via `axiosClient.ts`** — no raw `fetch()`
10. **Zustand stores must be typed** — full interface per store
11. **No inline styles** — Tailwind only
12. **Prompts in `ai_service.py` only** — no prompt strings elsewhere
13. **UUIDs for all PKs** — no auto-increment integers

---

## 11. External Services

| Service | Purpose | URL |
|---|---|---|
| uv | Python package manager | https://docs.astral.sh/uv |
| Anthropic Console | Claude API key | https://console.anthropic.com |
| Supabase | DB + Storage | https://supabase.com |
| Railway | Backend deploy | https://railway.app |
| Vercel | Frontend deploy | https://vercel.com |
| Google Cloud Console | OAuth credentials | https://console.cloud.google.com |
| Notion Developers | Notion integration | https://www.notion.so/my-integrations |
| GitHub | Version control | https://github.com |

---

## 12. Session Protocol

**Start every session:**
> "Read CLAUDE.md and confirm you understand the project."

**Then provide:**
1. Current stage number
2. What was completed last session
3. Any errors or blockers

**Never ask Claude to guess prior progress — always state it explicitly.**