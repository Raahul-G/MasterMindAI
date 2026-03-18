# Milestone 1 — The Foundation

> **Covers:** Stage 1 (Environment) + Stage 2 (Database) + Stage 3 (Auth API)
> **Status:** Not started

---

## What this milestone is

Before you write a single learning feature, you need three things to exist and work together:

1. Your **computer** is configured to run Python code
2. A **real cloud database** exists with all your tables
3. A **working API** that can register and log in users

Nothing else in the app can be built without these. Every future stage assumes this milestone is complete.

## What you will be able to do when this milestone is done

- Open a browser and visit `http://localhost:8000/docs`
- Register a brand new user via the Swagger UI
- Log in with that user's email and password and receive a JWT token
- Use that token to call `GET /auth/me` and see the user's profile returned
- Sign in with a Google account and receive a token
- Open the Supabase dashboard and see a real row in the `users` table
- The stored password in the database is a hash — unreadable garbage, not the real password

---

## The chunks

Each chunk is one focused block of work. Complete and test each one before moving to the next.

---

### Chunk 1 — Install all tools and verify they work

**What you learn:** What each tool is for and why it is needed before you can write any code.

- [ ] Install Python 3.12+ from https://python.org/downloads
- [ ] Run `python3 --version` in the terminal — confirm it shows `3.12.x` or higher
- [ ] Confirm uv is installed — run `uv --version`
- [ ] Install Node.js 20 LTS from https://nodejs.org
- [ ] Run `node --version` — confirm it shows `v20.x.x`
- [ ] Install VS Code from https://code.visualstudio.com
- [ ] Install these VS Code extensions (search in the Extensions panel):
  - [ ] Python
  - [ ] Pylance
  - [ ] ESLint
  - [ ] Prettier
  - [ ] Tailwind CSS IntelliSense
  - [ ] GitLens
- [ ] Install Git from https://git-scm.com if not already installed — run `git --version` to verify
- [ ] Create a GitHub account at https://github.com if you do not have one

**Outcome:** Every tool runs without errors. Your terminal can run `python3`, `uv`, `node`, `npm`, and `git`.

---

### Chunk 2 — Create the project skeleton and virtual environment

**What you learn:** What a monorepo is, what a virtual environment does, and why the folder structure matters before writing any code.

- [ ] In your terminal, navigate to the project root:
  ```bash
  cd "/Users/raahul/Workspace/Friday Vision/Projects/MasterMindAI"
  ```
- [ ] Create the `backend` folder:
  ```bash
  mkdir backend
  ```
- [ ] Go into the backend folder and create the virtual environment:
  ```bash
  cd backend
  uv venv --python 3.12
  ```
- [ ] Activate the virtual environment:
  ```bash
  source .venv/bin/activate
  ```
- [ ] Confirm the prompt now starts with `(.venv)`
- [ ] Install all Python dependencies in one command:
  ```bash
  uv pip install fastapi uvicorn[standard] sqlalchemy[asyncio] alembic asyncpg pydantic-settings anthropic "python-jose[cryptography]" "passlib[bcrypt]" python-dotenv httpx pytest pytest-asyncio
  ```
- [ ] Save installed versions to file:
  ```bash
  uv pip freeze > requirements.txt
  ```
- [ ] Create the full folder structure inside `backend/app/`:
  ```bash
  mkdir -p app/core app/models app/schemas app/routers app/services tests
  touch app/__init__.py app/core/__init__.py app/models/__init__.py
  touch app/schemas/__init__.py app/routers/__init__.py app/services/__init__.py
  touch app/dependencies.py tests/__init__.py
  ```
- [ ] Create the `.env.example` file (see Section 6 of CLAUDE.md for contents)
- [ ] Copy it to create your real `.env` file:
  ```bash
  cp .env.example .env
  ```
- [ ] Generate a SECRET_KEY and paste it into `.env`:
  ```bash
  python3 -c "import secrets; print(secrets.token_hex(32))"
  ```

**Outcome:** The `backend/` folder exists with the correct structure, the virtual environment is active, and all packages are installed. Running `uv pip list` shows all packages.

---

### Chunk 3 — Create a Supabase project and connect the database

**What you learn:** What a hosted database is, how to get a connection string, and what DATABASE_URL means.

- [ ] Create a free account at https://supabase.com
- [ ] Click "New project" — choose a name, set a strong database password, pick a region close to you
- [ ] Wait for the project to finish setting up (~2 minutes)
- [ ] Go to: Project Settings → Database → Connection string → URI mode
- [ ] Copy the URI and paste it into `backend/.env` as `DATABASE_URL`
  - Change `postgresql://` to `postgresql+asyncpg://` at the start
  - Replace `[YOUR-PASSWORD]` with the password you set when creating the project
- [ ] Go to: Project Settings → API
  - [ ] Copy "Project URL" → paste into `.env` as `SUPABASE_URL`
  - [ ] Copy "service_role" key (the secret one) → paste into `.env` as `SUPABASE_SERVICE_ROLE_KEY`

**Outcome:** Your `.env` file has a real working `DATABASE_URL`. The app can now reach your Supabase database.

---

### Chunk 4 — Write the core config and database connection files

**What you learn:** How environment variables are loaded into Python, how FastAPI connects to PostgreSQL, and what SQLAlchemy sessions are.

- [ ] Create `app/core/config.py`:
  ```python
  from pydantic_settings import BaseSettings

  class Settings(BaseSettings):
      DATABASE_URL: str
      SUPABASE_URL: str
      SUPABASE_SERVICE_ROLE_KEY: str
      SECRET_KEY: str
      JWT_ALGORITHM: str = "HS256"
      ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
      ANTHROPIC_API_KEY: str
      GOOGLE_CLIENT_ID: str
      GOOGLE_CLIENT_SECRET: str
      NOTION_CLIENT_ID: str = ""
      NOTION_CLIENT_SECRET: str = ""
      NOTION_REDIRECT_URI: str = ""
      ENVIRONMENT: str = "development"
      FRONTEND_URL: str = "http://localhost:5173"

      class Config:
          env_file = ".env"

  settings = Settings()
  ```
- [ ] Create `app/core/database.py`:
  ```python
  from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
  from sqlalchemy.orm import DeclarativeBase
  from app.core.config import settings

  engine = create_async_engine(settings.DATABASE_URL, echo=True)
  AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

  class Base(DeclarativeBase):
      pass

  async def get_db() -> AsyncSession:
      async with AsyncSessionLocal() as session:
          yield session
  ```

**Outcome:** The app can import `settings` from anywhere and read environment variables. The database engine is set up and ready to execute queries.

---

### Chunk 5 — Write the User model and run the first migration

**What you learn:** What a SQLAlchemy model is (a Python class that maps to a database table), what Alembic does, and why migrations are safer than editing tables by hand.

- [ ] Create `app/models/user.py`:
  ```python
  import uuid
  from sqlalchemy import String, Boolean, Text, ARRAY
  from sqlalchemy.orm import Mapped, mapped_column
  from sqlalchemy.dialects.postgresql import UUID
  from datetime import datetime, timezone
  from app.core.database import Base

  class User(Base):
      __tablename__ = "users"

      id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
      hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
      full_name: Mapped[str] = mapped_column(String(255), nullable=False)
      avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
      google_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
      interest_topics: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
      notion_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
      notion_workspace_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
      is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
      created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), nullable=False)
      updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
  ```
- [ ] Add the User import to `app/models/__init__.py`:
  ```python
  from app.models.user import User
  ```
- [ ] Initialise Alembic:
  ```bash
  alembic init alembic
  ```
- [ ] Open `alembic/env.py` and make two changes:
  - At the top, import your settings and models:
    ```python
    from app.core.config import settings
    from app.core.database import Base
    from app.models import User  # noqa: F401 — must import so Alembic can detect the model
    ```
  - Set the database URL:
    ```python
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    ```
  - Set the metadata:
    ```python
    target_metadata = Base.metadata
    ```
- [ ] Generate the first migration:
  ```bash
  alembic revision --autogenerate -m "create_users_table"
  ```
- [ ] Apply the migration:
  ```bash
  alembic upgrade head
  ```
- [ ] Open Supabase dashboard → Table Editor → verify the `users` table exists with all columns

**Outcome:** The `users` table exists in your real Supabase cloud database. You can see it in the Supabase Table Editor.

---

### Chunk 6 — Write password hashing and JWT token logic

**What you learn:** Why we never store plain passwords (bcrypt hashing), and how JWT tokens work as a secure "wristband" that proves who a user is.

- [ ] Create `app/core/security.py`:
  ```python
  from datetime import datetime, timedelta, timezone
  from typing import Any
  from jose import JWTError, jwt
  from passlib.context import CryptContext
  from app.core.config import settings

  pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

  def hash_password(password: str) -> str:
      """Converts a plain password into a bcrypt hash. The original is never stored."""
      return pwd_context.hash(password)

  def verify_password(plain_password: str, hashed_password: str) -> bool:
      """Checks a plain password against the stored hash. Returns True if they match."""
      return pwd_context.verify(plain_password, hashed_password)

  def create_access_token(subject: str | Any) -> str:
      """Creates a signed JWT token containing the user's ID. Expires after the configured time."""
      expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
      payload = {"sub": str(subject), "exp": expire}
      return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

  def decode_access_token(token: str) -> str | None:
      """Decodes and verifies a JWT token. Returns the user ID (sub) or None if invalid."""
      try:
          payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
          return payload.get("sub")
      except JWTError:
          return None
  ```

**Outcome:** You can call `hash_password("mypassword")` and get back a long string of garbage. Calling `verify_password("mypassword", that_hash)` returns `True`. This is the security heart of the auth system.

---

### Chunk 7 — Write Pydantic schemas for auth

**What you learn:** What Pydantic schemas are (data validators), why they are separate from the database models, and how they protect the API from bad input.

- [ ] Create `app/schemas/auth.py`:
  ```python
  from pydantic import BaseModel, EmailStr
  import uuid

  class RegisterRequest(BaseModel):
      email: EmailStr
      password: str
      full_name: str

  class LoginRequest(BaseModel):
      email: EmailStr
      password: str

  class GoogleLoginRequest(BaseModel):
      id_token: str  # The token Google sends back to the frontend after sign-in

  class TokenResponse(BaseModel):
      access_token: str
      token_type: str = "bearer"

  class UserResponse(BaseModel):
      id: uuid.UUID
      email: str
      full_name: str
      avatar_url: str | None
      interest_topics: list[str] | None
      is_active: bool

      model_config = {"from_attributes": True}
  ```
- [ ] Install email validation support (required by `EmailStr`):
  ```bash
  uv pip install "pydantic[email]"
  uv pip freeze > requirements.txt
  ```

**Outcome:** FastAPI will automatically validate that every register request has a valid email, a password, and a name. If anything is missing or wrong, FastAPI returns a clear error before your code even runs.

---

### Chunk 8 — Write the auth service (business logic)

**What you learn:** Why all logic lives in services (not routers), and how the register → hash → save and login → verify → issue token flows actually work.

- [ ] Create `app/services/auth_service.py`:
  ```python
  from sqlalchemy.ext.asyncio import AsyncSession
  from sqlalchemy import select
  from app.models.user import User
  from app.schemas.auth import RegisterRequest, LoginRequest
  from app.core.security import hash_password, verify_password, create_access_token
  import httpx

  async def register_user(data: RegisterRequest, db: AsyncSession) -> str:
      """Creates a new user. Raises ValueError if the email is already registered."""
      result = await db.execute(select(User).where(User.email == data.email))
      if result.scalar_one_or_none():
          raise ValueError("Email already registered")

      user = User(
          email=data.email,
          hashed_password=hash_password(data.password),
          full_name=data.full_name,
      )
      db.add(user)
      await db.commit()
      await db.refresh(user)
      return create_access_token(user.id)

  async def login_user(data: LoginRequest, db: AsyncSession) -> str:
      """Logs in a user. Raises ValueError if credentials are wrong."""
      result = await db.execute(select(User).where(User.email == data.email))
      user = result.scalar_one_or_none()

      if not user or not user.hashed_password:
          raise ValueError("Invalid credentials")
      if not verify_password(data.password, user.hashed_password):
          raise ValueError("Invalid credentials")

      return create_access_token(user.id)

  async def google_login(id_token: str, db: AsyncSession) -> str:
      """Verifies a Google ID token, then logs in or registers the user."""
      async with httpx.AsyncClient() as client:
          response = await client.get(
              f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
          )
      if response.status_code != 200:
          raise ValueError("Invalid Google token")

      google_data = response.json()
      google_id = google_data["sub"]
      email = google_data["email"]
      full_name = google_data.get("name", email)
      avatar_url = google_data.get("picture")

      # Check if user exists by Google ID or email
      result = await db.execute(select(User).where(User.google_id == google_id))
      user = result.scalar_one_or_none()

      if not user:
          result = await db.execute(select(User).where(User.email == email))
          user = result.scalar_one_or_none()

      if not user:
          user = User(email=email, full_name=full_name, google_id=google_id, avatar_url=avatar_url)
          db.add(user)
      else:
          user.google_id = google_id
          if avatar_url:
              user.avatar_url = avatar_url

      await db.commit()
      await db.refresh(user)
      return create_access_token(user.id)

  async def save_interests(user_id: str, interests: list[str], db: AsyncSession) -> None:
      """Saves the user's personal interest topics after onboarding."""
      result = await db.execute(select(User).where(User.id == user_id))
      user = result.scalar_one_or_none()
      if user:
          user.interest_topics = interests
          await db.commit()
  ```

**Outcome:** The register and login logic is fully written and testable in isolation before it is connected to any route.

---

### Chunk 9 — Write the `get_current_user` dependency and auth routes

**What you learn:** What a FastAPI dependency is (a reusable function that runs before a route handler), how to protect routes so only logged-in users can call them, and how to expose your logic to the internet via HTTP routes.

- [ ] Create `app/dependencies.py`:
  ```python
  from fastapi import Depends, HTTPException, status
  from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
  from sqlalchemy.ext.asyncio import AsyncSession
  from sqlalchemy import select
  from app.core.database import get_db
  from app.core.security import decode_access_token
  from app.models.user import User

  bearer_scheme = HTTPBearer()

  async def get_current_user(
      credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
      db: AsyncSession = Depends(get_db),
  ) -> User:
      """
      Extracts the JWT token from the Authorization header, verifies it,
      and returns the User object. Used as a dependency on all protected routes.
      """
      token = credentials.credentials
      user_id = decode_access_token(token)
      if not user_id:
          raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

      result = await db.execute(select(User).where(User.id == user_id))
      user = result.scalar_one_or_none()
      if not user or not user.is_active:
          raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

      return user
  ```
- [ ] Create `app/routers/auth.py`:
  ```python
  from fastapi import APIRouter, Depends, HTTPException, status
  from sqlalchemy.ext.asyncio import AsyncSession
  from app.core.database import get_db
  from app.schemas.auth import RegisterRequest, LoginRequest, GoogleLoginRequest, TokenResponse, UserResponse
  from app.services import auth_service
  from app.dependencies import get_current_user
  from app.models.user import User

  router = APIRouter(prefix="/auth", tags=["auth"])

  @router.post("/register", response_model=TokenResponse)
  async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
      try:
          token = await auth_service.register_user(data, db)
          return TokenResponse(access_token=token)
      except ValueError as e:
          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

  @router.post("/login", response_model=TokenResponse)
  async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
      try:
          token = await auth_service.login_user(data, db)
          return TokenResponse(access_token=token)
      except ValueError as e:
          raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

  @router.post("/google", response_model=TokenResponse)
  async def google_login(data: GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
      try:
          token = await auth_service.google_login(data.id_token, db)
          return TokenResponse(access_token=token)
      except ValueError as e:
          raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

  @router.get("/me", response_model=UserResponse)
  async def get_me(current_user: User = Depends(get_current_user)):
      return current_user

  @router.post("/interests")
  async def save_interests(
      interests: list[str],
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ):
      if len(interests) < 3 or len(interests) > 5:
          raise HTTPException(status_code=400, detail="Provide between 3 and 5 interests")
      await auth_service.save_interests(str(current_user.id), interests, db)
      return {"message": "Interests saved"}
  ```

**Outcome:** Four auth endpoints exist as Python code. They are not yet running — that happens in the next chunk.

---

### Chunk 10 — Create `main.py` and run the server

**What you learn:** What the FastAPI app entry point is, what CORS is and why it is needed, and how to start the development server.

- [ ] Create `backend/main.py`:
  ```python
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  from app.core.config import settings
  from app.routers import auth

  app = FastAPI(title="MasterMind API", version="0.1.0")

  app.add_middleware(
      CORSMiddleware,
      allow_origins=[settings.FRONTEND_URL],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )

  app.include_router(auth.router)

  @app.get("/health")
  async def health():
      return {"status": "ok"}
  ```
- [ ] Start the server:
  ```bash
  uvicorn main:app --reload --port 8000
  ```
- [ ] Open http://localhost:8000/docs in your browser
- [ ] Confirm you see the Swagger UI with the auth endpoints listed

**Outcome:** The server is running. The Swagger UI is visible in the browser.

---

### Chunk 11 — Test all auth endpoints end to end

**What you learn:** How to use Swagger UI to test an API, how to read a JWT token response, and how to use a token to call a protected route.

- [ ] In Swagger UI, test `POST /auth/register`:
  - [ ] Fill in a real email, password, and full name
  - [ ] Click Execute — confirm you receive `{"access_token": "...", "token_type": "bearer"}`
- [ ] Open Supabase Table Editor → `users` table:
  - [ ] Confirm the new user row is there
  - [ ] Confirm `hashed_password` is a long string of garbage (starts with `$2b$`) — NOT your real password
- [ ] In Swagger UI, test `POST /auth/login`:
  - [ ] Use the same email and password
  - [ ] Confirm you receive a token
- [ ] In Swagger UI, click the "Authorize" button (padlock icon at the top):
  - [ ] Paste your token into the value field (no "Bearer " prefix needed in Swagger)
  - [ ] Click Authorize
- [ ] Test `GET /auth/me`:
  - [ ] Confirm you receive the user's profile data back
- [ ] Test `POST /auth/interests`:
  - [ ] Send `["football", "cooking", "music"]`
  - [ ] Confirm `{"message": "Interests saved"}` is returned
  - [ ] Check the Supabase users table — confirm `interest_topics` is now populated

**Outcome:** Every auth endpoint works correctly end to end. Real data is being saved to the real Supabase cloud database.

---

### Chunk 12 — Write tests for the auth service

**What you learn:** What automated tests are, why you write them, and what "testing in isolation" means.

- [ ] Create `tests/test_auth.py`:
  ```python
  from app.core.security import hash_password, verify_password, create_access_token, decode_access_token

  def test_password_hash_is_not_plain_text():
      hashed = hash_password("mysecretpassword")
      assert hashed != "mysecretpassword"

  def test_correct_password_verifies():
      hashed = hash_password("mysecretpassword")
      assert verify_password("mysecretpassword", hashed) is True

  def test_wrong_password_fails():
      hashed = hash_password("mysecretpassword")
      assert verify_password("wrongpassword", hashed) is False

  def test_jwt_token_round_trip():
      token = create_access_token("user-123")
      decoded_id = decode_access_token(token)
      assert decoded_id == "user-123"

  def test_tampered_token_returns_none():
      token = create_access_token("user-123")
      bad_token = token + "tampered"
      assert decode_access_token(bad_token) is None
  ```
- [ ] Run the tests:
  ```bash
  pytest tests/test_auth.py -v
  ```
- [ ] Confirm all 5 tests pass (green)

**Outcome:** You have automated proof that the security functions work correctly. If you ever accidentally break them during future development, the tests will catch it immediately.

---

## Milestone 1 complete checklist (summary)

- [ ] Chunk 1 — All tools installed and verified
- [ ] Chunk 2 — Project skeleton and virtual environment
- [ ] Chunk 3 — Supabase project created and connected
- [ ] Chunk 4 — Config and database connection files
- [ ] Chunk 5 — User model and first migration run
- [ ] Chunk 6 — Password hashing and JWT logic
- [ ] Chunk 7 — Pydantic schemas for auth
- [ ] Chunk 8 — Auth service (business logic)
- [ ] Chunk 9 — Dependencies and auth routes
- [ ] Chunk 10 — `main.py` and server running
- [ ] Chunk 11 — All endpoints tested in Swagger UI
- [ ] Chunk 12 — Automated tests passing

---

## Before starting Milestone 2

Do not start Milestone 2 until every box above is checked AND:

- The Supabase `users` table has at least one real row in it
- `pytest tests/test_auth.py -v` shows 5 passing tests
- `GET /auth/me` with a valid token returns the user profile

Tell Claude: "Milestone 1 is complete. Starting Milestone 2."
