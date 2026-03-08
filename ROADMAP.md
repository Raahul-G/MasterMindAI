# ROADMAP.md — MasterMind Build Plan

> This is your stage-by-stage recipe for building the entire MasterMind app.
> Work through stages in order. Do not skip ahead.
> Check off every box before moving to the next stage.

---

## Stage 1 — Local Environment Setup

**Goal:** Get your computer fully configured so you can write and run code.

**Why this comes first:** You cannot write a single line of code without a working environment. If your tools are not set up correctly, nothing else will work. This stage also prevents the most common beginner mistake: accidentally mixing up Python versions or packages between projects.

**What is a virtual environment?**
Imagine your computer is a kitchen shared by many chefs. Each chef (each Python project) needs specific ingredients (packages) in specific versions. A virtual environment is a private locked drawer in that kitchen — it holds only the ingredients for YOUR project. When you activate it, your project only sees its own packages, not anything installed globally on your computer. This prevents conflicts between projects and makes your setup reproducible on any machine.

**What is uv?**
`uv` is a modern tool written in Rust that replaces two older Python tools — `python -m venv` (for creating virtual environments) and `pip` (for installing packages). It does both jobs and is 10 to 100 times faster than the original tools. The commands are nearly identical to what you may have seen before — `uv venv` instead of `python -m venv .venv`, and `uv pip install` instead of `pip install`. You activate the virtual environment the same way as before.

**Difficulty:** Easy

---

### Sub-tasks

- [ ] Install Python 3.12 or later from https://python.org/downloads — verify the install
- [ ] Install uv from https://docs.astral.sh/uv/getting-started/installation/ — this replaces pip and venv with one fast tool
- [ ] Install Node.js 20 LTS from https://nodejs.org — this is needed for the React frontends
- [ ] Install VS Code from https://code.visualstudio.com
- [ ] Install these VS Code extensions: Python, Pylance, ESLint, Prettier, Tailwind CSS IntelliSense, GitLens
- [ ] Install Git from https://git-scm.com if not already installed
- [ ] Create a GitHub account at https://github.com if you do not have one
- [ ] Create the monorepo folder structure
- [ ] Create and activate the Python virtual environment using uv
- [ ] Install all Python backend dependencies using uv
- [ ] Create the backend `.env` file from the `.env.example` template
- [ ] Verify the environment is working by running a test Python script

---

### Terminal Commands

```bash
# Install uv on Mac/Linux — uv is a modern Python package manager written in Rust
# It replaces both "python -m venv" and "pip" with one blazing fast tool
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart your terminal after installing uv, then verify it installed correctly
uv --version

# Verify Python is installed and is version 3.12+
python3 --version

# Verify Node.js is installed and is version 20+
node --version

# Verify npm is installed
npm --version

# Go into the project root (adjust path to match where YOUR project lives)
cd "/Users/raahul/Workspace/Friday Vision/Projects/MasterMindAI"

# Create the backend folder — this is where all Python code will live
mkdir backend

# Go into the backend folder
cd backend

# Create a Python virtual environment inside a folder called .venv
# uv does this much faster than the built-in python -m venv
# The --python flag pins the exact Python version so the project is reproducible
uv venv --python 3.12

# Activate the virtual environment (Mac/Linux)
# After this command your terminal prompt will start with (.venv)
# This means the virtual environment is ON — all installs go here
source .venv/bin/activate

# Install all backend Python dependencies in one command
# uv pip install works exactly like pip install but is 10-100x faster
# fastapi: the web framework
# uvicorn: the server that runs FastAPI
# sqlalchemy: talks to the database using Python
# alembic: manages database schema changes over time
# asyncpg: async driver for PostgreSQL
# pydantic-settings: loads environment variables into typed config objects
# anthropic: official SDK to call Claude AI
# python-jose[cryptography]: creates and verifies JWT tokens
# passlib[bcrypt]: hashes passwords securely
# python-dotenv: loads .env files
# httpx: makes async HTTP requests to external APIs like Notion
# pytest pytest-asyncio: testing frameworks
uv pip install fastapi uvicorn[standard] sqlalchemy[asyncio] alembic asyncpg pydantic-settings anthropic "python-jose[cryptography]" "passlib[bcrypt]" python-dotenv httpx pytest pytest-asyncio

# Save the exact versions of everything you just installed to a file
# This file is committed to Git so anyone can recreate the same environment exactly
uv pip freeze > requirements.txt

# Go back to the project root
cd ..

# Create the frontend web app using Vite with React and TypeScript
# This single command creates the entire React project structure
npm create vite@latest frontend-web -- --template react-ts

# Go into the frontend web folder
cd frontend-web

# Install the React project's Node dependencies
npm install

# Install TailwindCSS and its required tools
npm install -D tailwindcss postcss autoprefixer

# Set up TailwindCSS config files automatically
npx tailwindcss init -p

# Install React Router for navigation between pages
npm install react-router-dom

# Install Axios for making HTTP calls to the backend API
npm install axios

# Install Zustand for global state management
npm install zustand

# Go back to the project root
cd ..

# Create the mobile app folder (Expo setup comes in Stage 12)
mkdir frontend-mobile

# Create the .env.example file for the backend — this goes in Git
# The real .env file (with real secrets) never goes in Git
cat > backend/.env.example << 'EOF'
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DB_NAME
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
SECRET_KEY=your-long-random-secret-key-here-minimum-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ANTHROPIC_API_KEY=sk-ant-your-key-here
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
NOTION_CLIENT_ID=your-notion-oauth-client-id
NOTION_CLIENT_SECRET=your-notion-oauth-client-secret
NOTION_REDIRECT_URI=http://localhost:8000/notion/callback
ENVIRONMENT=development
FRONTEND_URL=http://localhost:5173
EOF

# Copy the example to create your real .env file
# You will fill in the real values as you create each service account
cp backend/.env.example backend/.env

# Generate a secure SECRET_KEY value — copy the output into your .env file
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**What you will see when this stage is done:**
- Your terminal prompt shows `(.venv)` when inside the backend folder
- Running `uv pip list` shows all the packages installed
- Running `npm run dev` inside `frontend-web/` starts a local server and opens a React app in your browser at http://localhost:5173

**Common beginner mistakes to avoid:**
- Forgetting to run `source .venv/bin/activate` before running `uv pip install` — packages will install globally instead of in your project
- Forgetting to restart the terminal after installing uv — the `uv` command will not be found until the shell reloads
- Using `python` instead of `python3` on Mac (they may point to different versions)
- Committing the `.env` file to Git — it contains your real secrets and must stay local

---

## Stage 2 — Supabase Database Setup

**Goal:** Set up the cloud PostgreSQL database and create all database tables by running the first Alembic migration.

**Why this comes before Stage 3:** The auth system (Stage 3) needs the `users` table to exist before it can save or look up users. The database must be ready first.

**What is a database migration? (Using an analogy)**
Imagine your database schema is a shared Google Doc that many people depend on. A migration is like a tracked change in that document — it records exactly what changed (e.g. "Added a new column called `avatar_url`"), who made the change, and in what order. Alembic keeps a history of every change you have ever made to the database structure. If something goes wrong, you can roll back. If you deploy to a new server, you can replay all the changes in order to get the same database structure. Never edit the database by hand — always use migrations.

**Difficulty:** Medium

---

### Sub-tasks

- [ ] Create a free Supabase account at https://supabase.com
- [ ] Create a new Supabase project (choose a region close to you)
- [ ] Copy the database connection string and paste it into `backend/.env` as `DATABASE_URL`
- [ ] Copy the Supabase project URL and service role key into `backend/.env`
- [ ] Create the full SQLAlchemy model files inside `backend/app/models/`
- [ ] Set up Alembic inside the backend folder
- [ ] Configure Alembic to read from your `.env` file
- [ ] Generate the first migration (auto-detects all your models)
- [ ] Run the migration to create all tables in Supabase
- [ ] Verify all tables exist in the Supabase table editor

---

### Terminal Commands

```bash
# Make sure you are in the backend folder with the virtual environment active
cd backend
source .venv/bin/activate

# Create the full app folder structure
mkdir -p app/core app/models app/schemas app/routers app/services
touch app/__init__.py app/core/__init__.py app/models/__init__.py
touch app/schemas/__init__.py app/routers/__init__.py app/services/__init__.py
touch app/dependencies.py

# Initialise Alembic — this creates the alembic/ folder and alembic.ini config file
# Think of this as setting up the "change tracking" system for your database
alembic init alembic

# After creating all your SQLAlchemy model files (app/models/),
# generate the first migration automatically
# Alembic reads your models and figures out what SQL commands are needed
# The -m flag adds a human-readable label to the migration file
alembic revision --autogenerate -m "initial_schema"

# Run the migration — this actually executes the SQL and creates the tables in Supabase
# "head" means "apply all migrations up to the latest one"
alembic upgrade head

# Verify by listing all tables (requires psql to be installed, or just use the Supabase dashboard)
# In the Supabase dashboard: Table Editor → you should see all your tables listed
```

**What you will see when this stage is done:**
- The Supabase Table Editor shows all your tables: users, modules, passages, quizzes, questions, answers, remediations, streaks, achievements, user_achievements, friendships, activity_feed
- Running `alembic history` shows your first migration in the list

**Common beginner mistakes to avoid:**
- Using the `User` (Session mode) connection string from Supabase instead of the `Direct connection` string — use the Direct connection URI and add `+asyncpg` to make it `postgresql+asyncpg://...`
- Forgetting to import all your model files in `alembic/env.py` so Alembic can detect them — if a model is not imported, Alembic will not create that table
- Editing a migration file after it has already been run — always generate a new migration instead

---

## Stage 3 — Authentication API

**Goal:** Build and test the complete auth system: register, login, and Google OAuth.

**Why this comes before Stage 4:** Every other API endpoint is protected — users must be logged in to use them. The auth system is the foundation that all other features sit on.

**Why we never store plain passwords (using an analogy):**
Storing a password in plain text is like writing your house key code on a sticky note on your front door. If anyone ever sees your database (through a hack, a breach, or a mistake), they have everyone's passwords instantly. Instead, we use bcrypt to hash passwords. Hashing is like putting the key code through a meat grinder — the output (the hash) looks like random garbage, but it always produces the SAME garbage for the SAME input. When a user logs in, we grind their password again and compare the two piles of garbage. If they match, the password is correct. The actual password is never stored anywhere.

**How JWT tokens work (using an analogy):**
A JWT token is like a theme park wristband. When you pay at the gate (log in), the cashier gives you a wristband (the JWT token) that proves you paid. At every ride (every protected API endpoint), you just show your wristband — no one calls the gate to verify. The wristband has an encoded message that proves who you are and when it expires. Our `SECRET_KEY` is the ink that makes the wristband tamper-proof — if anyone tries to forge it, the ink colour is wrong.

**Difficulty:** Medium

---

### Sub-tasks

- [ ] Create `app/core/config.py` — loads all environment variables using pydantic-settings
- [ ] Create `app/core/database.py` — sets up the async SQLAlchemy engine and session
- [ ] Create `app/core/security.py` — bcrypt hashing and JWT create/verify functions
- [ ] Create `app/models/user.py` — the User SQLAlchemy model
- [ ] Create `app/schemas/auth.py` — Pydantic schemas for register, login, token
- [ ] Create `app/services/auth_service.py` — register, login, Google OAuth business logic
- [ ] Create `app/routers/auth.py` — the three auth route handlers
- [ ] Create `app/dependencies.py` — the `get_current_user` FastAPI dependency
- [ ] Create `main.py` — the FastAPI app entry point, register the auth router
- [ ] Test all three auth endpoints using FastAPI Swagger UI at http://localhost:8000/docs

---

### Terminal Commands

```bash
# Make sure the virtual environment is active (created with uv in Stage 1)
source .venv/bin/activate

# Start the FastAPI development server
# uvicorn is the server that runs FastAPI
# --reload means the server restarts automatically whenever you save a file
# main:app means "find the variable called 'app' inside main.py"
uvicorn main:app --reload --port 8000

# Open your browser and go to: http://localhost:8000/docs
# You will see the Swagger UI — a visual interface to test all your API endpoints
# Click on any endpoint, click "Try it out", fill in the form, click "Execute"

# To run all tests (open a second terminal with the venv active)
pytest tests/ -v
# -v means verbose — shows each test name and whether it passed or failed
```

**What you will see when this stage is done:**
- Swagger UI at http://localhost:8000/docs shows `/auth/register`, `/auth/login`, `/auth/google`, `/auth/me`
- You can register a new user and receive a JWT token in the response
- You can log in with that user's credentials and receive a new token
- The `users` table in Supabase shows the new user row with a hashed password (not the plain text one)
- `GET /auth/me` with the token in the Authorization header returns the user's profile

**Common beginner mistakes to avoid:**
- Forgetting to add `async` to database session functions — SQLAlchemy 2.0 with asyncpg requires async throughout
- Returning the SQLAlchemy model object directly from the router — always convert it to a Pydantic schema first
- Hardcoding the SECRET_KEY in the code instead of reading it from the environment variable

---

## Stage 4 — Core AI Service

**Goal:** Write and test all 4 Claude AI functions completely in isolation before connecting them to any routes.

**Why this comes before Stage 5:** If the AI functions have bugs or produce unexpected output, you want to discover that in a test file, not buried inside a complex API route. Testing in isolation means each function has one job and you can verify it works on its own. This is called unit testing.

**Why test in isolation first:**
Imagine building a car. You would not bolt the engine directly into the car body and then try to drive it to see if the engine works. You test the engine on a bench first — no wheels, no body, just the engine. If it does not work, you fix it there. This is exactly what we do with `ai_service.py`: test each function on a bench before bolting it into the API.

**Difficulty:** Medium

---

### Sub-tasks

- [ ] Create `app/services/ai_service.py` with all 4 Claude functions: `generate_eli5`, `generate_passages`, `generate_quiz`, `generate_remediation`
- [ ] Add the Anthropic API key to your `.env` file (get it from https://console.anthropic.com)
- [ ] Create `tests/test_ai_service.py` with pytest tests for each function
- [ ] Run the tests and verify all 4 functions return valid, correctly structured output
- [ ] Inspect the raw output — check JSON parsing works correctly for passages, quiz, remediation

---

### Terminal Commands

```bash
# Make sure the virtual environment is active (created with uv in Stage 1)
source .venv/bin/activate

# Run only the AI service tests (these will make real Claude API calls and cost a small amount)
# The -s flag shows print() output from inside tests — useful for seeing raw Claude responses
pytest tests/test_ai_service.py -v -s

# Run a quick one-off test directly in Python (useful for rapid iteration)
python3 -c "
import asyncio
from app.services.ai_service import generate_eli5
result = asyncio.run(generate_eli5('Photosynthesis', 'intermediate'))
print(result)
"
```

**What you will see when this stage is done:**
- All 4 pytest tests pass (green)
- Each test prints the actual Claude output so you can read it and verify it makes sense
- The quiz output is valid JSON that you can parse without errors
- The remediation output uses noticeably different analogies from the passage output

**Common beginner mistakes to avoid:**
- Calling `client.messages.create()` without `await` — these are async functions
- Forgetting to parse the JSON response with `json.loads()` for passages, quiz, and remediation
- Not checking that `correct_answer` in the quiz output exactly matches one of the `options` strings — the quiz scoring logic depends on this

---

## Stage 5 — Learning Module API

**Goal:** Wire the AI service into FastAPI routes to build the complete learn → quiz → remediate loop, saving everything to the database.

**Why this comes after Stage 4:** The AI functions are verified working. Now we connect them to the database and expose them as API endpoints.

**Difficulty:** Hard

---

### Sub-tasks

- [ ] Create `app/models/learning.py` — Module, Passage, Quiz, Question, Answer, Remediation models
- [ ] Run a new Alembic migration for the learning models
- [ ] Create `app/schemas/learning.py` and `app/schemas/quiz.py` — all request/response schemas
- [ ] Create `app/services/learning_service.py` — orchestrates the full flow, saves AI output to DB
- [ ] Create `app/services/quiz_service.py` — scores quiz answers, identifies failed concepts
- [ ] Create `app/routers/learning.py` — the 4 learning route handlers
- [ ] Register the learning router in `main.py`
- [ ] Test the complete end-to-end flow in Swagger UI (start → generate quiz → submit → remediate)
- [ ] Verify all data is saved correctly in Supabase tables

---

### Terminal Commands

```bash
source .venv/bin/activate

# After creating the new learning models, generate a new migration
# Never edit the first migration — always create a new one
alembic revision --autogenerate -m "add_learning_tables"

# Apply the new migration
alembic upgrade head

# Restart the server and test the full flow in Swagger UI
uvicorn main:app --reload --port 8000
# Visit http://localhost:8000/docs
# Sequence to test: POST /learn/start → POST /learn/quiz/generate → POST /learn/quiz/submit → POST /learn/remediate
```

**What you will see when this stage is done:**
- You can start a learning module and receive an ELI5 + passages in the response
- You can generate a quiz for that module and see 5-10 questions
- You can submit answers and receive a score with a list of failed concepts
- If you fail some questions, you can get remediation explanations
- The Supabase tables (modules, passages, quizzes, questions, answers, remediations) contain real data rows

**Common beginner mistakes to avoid:**
- Not committing the module to `completed` status when all quiz questions are passed — make sure the status update is in the quiz service
- Forgetting to update the streak when a module is completed — call `streak_service` from `learning_service` after completion
- Returning database model objects directly from service functions instead of converting to Pydantic schemas

---

## Stage 6 — Cloud Storage and Markdown Export

**Goal:** Generate a Markdown summary file for completed modules and make it downloadable.

**Why this comes after Stage 5:** You need completed modules with real data in the database before you can generate summaries for them.

**Difficulty:** Medium

---

### Sub-tasks

- [ ] Create a Storage bucket in Supabase called `module-exports` (set to private)
- [ ] Create `app/services/markdown_service.py` — assembles the Markdown summary from a module's DB data
- [ ] Create `app/services/storage_service.py` — uploads files to and generates signed download URLs from Supabase Storage
- [ ] Create `app/routers/modules.py` — the module list, detail, and export endpoints
- [ ] Register the modules router in `main.py`
- [ ] Test downloading a completed module's Markdown file

---

### Terminal Commands

```bash
source .venv/bin/activate

# Install the Supabase Python client for Storage operations
uv pip install supabase

# Save the updated requirements
uv pip freeze > requirements.txt

# Restart the server
uvicorn main:app --reload --port 8000
# Test: POST /modules/{module_id}/export/download
# You should receive a signed URL in the response
# Open the URL in your browser — you should see or download the Markdown file
```

**What you will see when this stage is done:**
- Calling the download export endpoint returns a URL
- Opening that URL downloads a `.md` file containing the ELI5, passages, quiz questions, correct answers, and any remediation explanations used
- The Supabase Storage dashboard shows the uploaded file in the `module-exports` bucket

**Common beginner mistakes to avoid:**
- Making the Storage bucket public instead of private — use signed URLs for security
- Forgetting to handle the case where a module is not yet completed — return a 400 error if `status != 'completed'`

---

## Stage 7 — Notion Integration

**Goal:** Let users connect their Notion workspace and export completed module summaries as Notion pages.

**Why this comes after Stage 6:** The Markdown export (Stage 6) uses the same content that gets pushed to Notion. Understanding the Markdown structure first makes the Notion service easier to write.

**Difficulty:** Hard

---

### Sub-tasks

- [ ] Create a Notion integration at https://www.notion.so/my-integrations
- [ ] Enable OAuth (Public Integration) in the Notion integration settings
- [ ] Copy `NOTION_CLIENT_ID` and `NOTION_CLIENT_SECRET` into your `.env` file
- [ ] Create `app/services/notion_service.py` — handles OAuth token exchange and page creation via Notion API
- [ ] Create `app/routers/notion.py` — OAuth URL, callback, disconnect, and export endpoints
- [ ] Register the Notion router in `main.py`
- [ ] Test the complete OAuth flow: connect Notion → export a module → verify the page appears in Notion

---

### Terminal Commands

```bash
source .venv/bin/activate

# Restart the server
uvicorn main:app --reload --port 8000

# To test the Notion OAuth flow:
# 1. Call GET /notion/auth-url — copy the returned URL
# 2. Open that URL in your browser — you will be asked to select a Notion workspace
# 3. After authorising, Notion redirects to your /notion/callback endpoint
# 4. The callback saves the access token to the users table
# 5. Call POST /modules/{module_id}/export/notion to push a module to Notion
```

**What you will see when this stage is done:**
- Your `users` table has `notion_access_token` and `notion_workspace_id` populated after OAuth
- Calling the Notion export endpoint creates a real Notion page in your workspace
- The Notion page contains the ELI5, passages, quiz results, and any remediation used

**Common beginner mistakes to avoid:**
- Using `requests` (synchronous) instead of `httpx` (async) for Notion API calls — the backend is async throughout
- Not storing the Notion token per-user in the database — each user connects their own Notion workspace

---

## Stage 8 — Gamification API

**Goal:** Add streak tracking and achievements to reward users for their learning progress.

**Why this comes after Stage 7:** Gamification depends on modules being completed (Stage 5) and is a standalone feature layer on top of the core learning system.

**Difficulty:** Medium

---

### Sub-tasks

- [ ] Create `app/models/gamification.py` — Streak, Achievement, UserAchievement models
- [ ] Run a new Alembic migration
- [ ] Seed the `achievements` table with the initial set of badges (e.g. first module, 7-day streak, 10 modules)
- [ ] Create `app/services/streak_service.py` — calculates and updates the daily streak
- [ ] Create `app/services/achievement_service.py` — checks conditions and awards badges
- [ ] Create `app/routers/gamification.py` — streak and achievements endpoints
- [ ] Wire streak and achievement checks into `learning_service.py` so they trigger on module completion
- [ ] Register the gamification router in `main.py`
- [ ] Test streaks and achievements in Swagger UI

---

### Terminal Commands

```bash
# Make sure the virtual environment is active (created with uv in Stage 1)
source .venv/bin/activate

alembic revision --autogenerate -m "add_gamification_tables"
alembic upgrade head

# After creating the achievement seeder script:
python3 scripts/seed_achievements.py

uvicorn main:app --reload --port 8000
# Test: complete a module, then call GET /gamification/streak and GET /gamification/achievements
```

**What you will see when this stage is done:**
- Completing a module updates the streak counter in the `streaks` table
- Earning an achievement for the first time returns it from `GET /gamification/achievements`
- The `user_achievements` table has a row for each badge earned

**Common beginner mistakes to avoid:**
- Using Python's `datetime.now()` for streak calculations instead of `datetime.utcnow()` — always use UTC in the database
- Awarding an achievement more than once — check for an existing row in `user_achievements` before inserting

---

## Stage 9 — Social Features API

**Goal:** Add friend requests, an activity feed, and user search.

**Why this comes after Stage 8:** Social features display gamification data (streaks) in the feed. The gamification layer must exist first.

**Difficulty:** Medium

---

### Sub-tasks

- [ ] Create `app/models/social.py` — Friendship and ActivityFeed models
- [ ] Run a new Alembic migration
- [ ] Create `app/services/social_service.py` — friend request logic, feed queries
- [ ] Create `app/routers/social.py` — all 6 social endpoints
- [ ] Wire activity feed inserts into `learning_service.py` and `achievement_service.py` so events are recorded
- [ ] Register the social router in `main.py`
- [ ] Test the full friend request → accept → view feed flow in Swagger UI

---

### Terminal Commands

```bash
# Make sure the virtual environment is active (created with uv in Stage 1)
source .venv/bin/activate

alembic revision --autogenerate -m "add_social_tables"
alembic upgrade head

uvicorn main:app --reload --port 8000
# Test with two user accounts:
# 1. Register User A and User B
# 2. As User A: POST /social/friends/request with User B's id
# 3. As User B: POST /social/friends/accept
# 4. As User A: Complete a module
# 5. As User B: GET /social/feed — should see User A's activity
```

**What you will see when this stage is done:**
- Two users can become friends through the request/accept flow
- The activity feed returns events from friends (module completions, streaks, achievements)
- User search returns matching users by name

**Common beginner mistakes to avoid:**
- Allowing a user to send a friend request to themselves — add a check in the service
- Not filtering the activity feed to show only friends' activities — add a JOIN on the friendships table

---

## Stage 10 — Backend Polish and Railway Deployment

**Goal:** Clean up the backend, write integration tests, and deploy to Railway so the API is live on the internet.

**Why this comes before Stage 11:** The web frontend needs a live backend URL to connect to. You cannot build a frontend pointing at `localhost` — it only works on your computer.

**What does deployment mean? (Using an analogy):**
Right now your FastAPI server runs on `localhost:8000` — it only exists on your laptop. The moment you close your terminal, it stops. Deployment is like moving from cooking in your home kitchen to opening a restaurant. The food (your code) is the same. But now it runs on a server somewhere in the world, 24/7, accessible to anyone with the URL. Railway provides the "restaurant building" — you push your code, and Railway handles everything else.

**Difficulty:** Hard

---

### Sub-tasks

- [ ] Standardise all API responses to use `{"data": {...}}` for success and `{"error": {...}}` for errors
- [ ] Add proper HTTP exception handling for 401, 403, 404, 422, and 500 errors
- [ ] Write integration tests that test multiple endpoints together
- [ ] Create a `Procfile` in the backend folder (Railway uses this to know how to start your app)
- [ ] Create a Railway account at https://railway.app
- [ ] Create a new Railway project and connect your GitHub repository
- [ ] Add all environment variables to Railway's environment settings (Settings → Variables)
- [ ] Deploy and verify the app is running at your Railway URL
- [ ] Test all endpoints using the live Railway URL

---

### Terminal Commands

```bash
source .venv/bin/activate

# Run the full test suite before deploying
pytest tests/ -v

# Create the Procfile (tells Railway how to start the server)
# web: is the process type — Railway looks for this
echo 'web: uvicorn main:app --host 0.0.0.0 --port $PORT' > Procfile

# Commit everything to Git
git add .
git commit -m "feat: complete backend with all features"
git push origin main
# After pushing, Railway automatically detects the push and deploys the new version

# To check Railway logs (requires Railway CLI)
# Install Railway CLI: npm install -g @railway/cli
# Login: railway login
# View logs: railway logs
```

**What you will see when this stage is done:**
- Railway dashboard shows your app as "Active" with a green status
- You have a public URL like `https://mastermind-backend.up.railway.app`
- Visiting `https://your-railway-url.up.railway.app/docs` shows the Swagger UI
- All Swagger UI tests work using the live URL (not localhost)

**Common beginner mistakes to avoid:**
- Hardcoding `localhost` anywhere in the backend code — always use environment variables
- Forgetting to add `FRONTEND_URL` to Railway's environment variables — CORS will block the frontend
- Not setting the `--host 0.0.0.0` flag in the Procfile — Railway requires the app to listen on all interfaces

---

## Stage 11 — Web Frontend

**Goal:** Build the complete React web app with all pages and connect it to the live backend.

**Why this comes after Stage 10:** The frontend makes API calls to the backend. The backend must be deployed and working before the frontend can be built against it.

**Difficulty:** Hard

---

### Sub-tasks

- [ ] Configure `tailwind.config.ts` with the content paths and custom theme colours
- [ ] Create `src/types/index.ts` with all TypeScript types (User, Module, Passage, Quiz, Question, etc.)
- [ ] Create `src/api/axiosClient.ts` — Axios instance with base URL from env and auth header interceptor
- [ ] Create `src/api/auth.ts`, `src/api/learning.ts`, `src/api/modules.ts`, `src/api/social.ts`
- [ ] Create `src/store/authStore.ts` — Zustand store for user and token
- [ ] Create `src/store/learningStore.ts` — Zustand store for active module state
- [ ] Create `App.tsx` with React Router and protected route logic
- [ ] Build all 14 pages (see folder structure in CLAUDE.md Section 4)
- [ ] Build all reusable components (Navbar, ProgressBar, QuizCard, etc.)
- [ ] Implement Google OAuth using Google Identity Services in the Login page
- [ ] Deploy to Vercel: connect GitHub repo, set `VITE_API_BASE_URL` to your Railway URL

---

### Terminal Commands

```bash
# Make sure you are in the frontend-web folder
cd frontend-web

# Start the local dev server — hot reloads on every file save
npm run dev
# Visit http://localhost:5173

# Build for production (run this before deploying to test the build)
npm run build
# If this fails, fix all TypeScript errors before deploying

# Deploy to Vercel (requires Vercel CLI)
npm install -g vercel
vercel
# Follow the prompts — Vercel will detect Vite automatically
# Set the environment variable VITE_API_BASE_URL to your Railway URL in the Vercel dashboard
```

**What you will see when this stage is done:**
- A real, styled web app accessible at your Vercel URL
- Users can register, log in with email or Google, and start a learning session
- The full learn → quiz → remediate loop works in the browser
- Completed modules show the export buttons (Download and Notion)
- The dashboard shows streak count and recent modules

**Common beginner mistakes to avoid:**
- Using `process.env` instead of `import.meta.env` to read environment variables in Vite — Vite uses `import.meta.env.VITE_*`
- Not wrapping protected pages with a route guard that redirects to login if no token is present
- Forgetting to add the Vercel domain to the `FRONTEND_URL` environment variable in Railway — CORS will block requests

---

## Stage 12 — Android App

**Goal:** Build the complete Android app using React Native with Expo and generate an APK.

**Why this comes last:** The mobile app is essentially a second client for the same backend. All the hard work (backend, auth, AI, gamification, social) is already done. The mobile app just consumes the existing API.

**Difficulty:** Hard

---

### Sub-tasks

- [ ] Install Expo CLI and set up the mobile project
- [ ] Set up Android emulator via Android Studio, OR use Expo Go on a real Android phone for development
- [ ] Configure NativeWind for Tailwind-style mobile styling
- [ ] Set up Expo Router for file-based navigation
- [ ] Create the `.env` file for the mobile app with the backend URL
- [ ] Build all mobile screens (matching the pages built in Stage 11)
- [ ] Create shared API functions (reuse the same Axios client approach as the web)
- [ ] Implement push notifications for streak reminders using Expo Notifications
- [ ] Create an Expo account at https://expo.dev
- [ ] Build the production APK using Expo EAS Build
- [ ] Test the APK on a real Android device

---

### Terminal Commands

```bash
# Go back to the project root
cd ..

# Install Expo CLI globally
npm install -g expo-cli eas-cli

# Initialise the Expo project inside the frontend-mobile folder
npx create-expo-app frontend-mobile --template

# Go into the mobile folder
cd frontend-mobile

# Install NativeWind and its dependencies
npm install nativewind
npm install --save-dev tailwindcss

# Install Expo Router for navigation
npx expo install expo-router react-native-safe-area-context react-native-screens

# Install Expo Notifications for push notifications
npx expo install expo-notifications expo-device

# Start the Expo development server
npx expo start
# Scan the QR code with Expo Go on your Android phone, OR press 'a' to open in Android emulator

# Build a production APK using Expo EAS
# First, log in to your Expo account
eas login

# Configure EAS Build for your project (creates eas.json)
eas build:configure

# Build the APK for Android (this runs in the cloud on Expo's servers)
# 'preview' profile builds an APK (installable file) rather than an AAB (for Play Store)
eas build --platform android --profile preview

# When the build completes, you will receive a download URL for the APK
# Install it on your Android device to test
```

**What you will see when this stage is done:**
- A working Android app on your phone or emulator
- All core screens function: login, dashboard, topic selection, learning, quiz, remediation, module complete
- Push notifications work — if a user has not completed a module by a certain time, they receive a streak reminder
- You have a downloadable APK file that can be installed on any Android device

**Common beginner mistakes to avoid:**
- Using `localhost` as the API base URL in the mobile app — the phone is a different device and cannot reach your laptop's localhost. Use your deployed Railway URL.
- Not handling the different screen sizes and safe areas on Android — always use `SafeAreaView` from `react-native-safe-area-context`
- Forgetting to add the Expo push notification token to the backend so it can send notifications

---

## Summary: Stage Completion Checklist

| Stage | Title | Done? |
|---|---|---|
| 1 | Local Environment Setup | [ ] |
| 2 | Supabase Database Setup | [ ] |
| 3 | Authentication API | [ ] |
| 4 | Core AI Service | [ ] |
| 5 | Learning Module API | [ ] |
| 6 | Cloud Storage and Markdown Export | [ ] |
| 7 | Notion Integration | [ ] |
| 8 | Gamification API | [ ] |
| 9 | Social Features API | [ ] |
| 10 | Backend Polish and Railway Deployment | [ ] |
| 11 | Web Frontend | [ ] |
| 12 | Android App | [ ] |
