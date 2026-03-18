# Milestone 3 — Export, Storage, and Notion Integration

> **Covers:** Stage 6 (Cloud Storage + Markdown Export) + Stage 7 (Notion Integration)
> **Status:** Not started

---

## What this milestone is

Milestone 2 gave you a working learn → quiz → remediate loop. Milestone 3 gives you the ability to capture the result of that loop — a clean Markdown summary of everything that happened — and let the user keep it forever.

There are three parts:

1. **Markdown Service** — one function that assembles a complete module (ELI5 + passages + quiz Q&A + remediations) into a single Markdown document.
2. **Storage Service** — uploads that Markdown file to Supabase Storage and returns a public download URL the user can click to save the file.
3. **Notion Integration** — an OAuth flow that connects a user's Notion account, then creates a formatted Notion page from the same content.

There are also two new sets of API endpoints: `/modules` (browse past modules, trigger exports) and `/notion` (OAuth + disconnect).

## What you will be able to do when this milestone is done

- Call `GET /modules` and see a list of all your learning modules
- Call `GET /modules/{id}` and see the full detail of any module including its passages
- Call `POST /modules/{id}/export/download` and receive a URL that downloads a `.md` file with the full module summary
- Open that URL and see a properly formatted Markdown document with ELI5, passages, quiz Q&A, and any remediations
- Connect your Notion account via OAuth and call `POST /modules/{id}/export/notion` to push the same content as a Notion page
- Call `DELETE /notion/disconnect` to remove the Notion connection

---

## The chunks

Each chunk is one focused block of work. Complete and test each one before moving to the next.

---

### Chunk 1 — Create the Supabase Storage bucket

**What you learn:** What Supabase Storage is, how it is separate from the database, and how public buckets work.

- [ ] Go to your Supabase project dashboard
- [ ] In the left sidebar click **Storage**
- [ ] Click **New bucket**
- [ ] Name it exactly: `modules`
- [ ] Toggle **Public bucket** ON (this lets download URLs work without authentication)
- [ ] Click **Save**
- [ ] Confirm the `modules` bucket appears in the bucket list

**Outcome:** A public Supabase Storage bucket called `modules` exists. Files uploaded there will be accessible via a public URL.

---

### Chunk 2 — Write `markdown_service.py`

**What you learn:** How to query multiple related tables and assemble their content into a formatted document.

- [ ] Create `backend/app/services/markdown_service.py`:
  ```python
  import uuid
  from sqlalchemy.ext.asyncio import AsyncSession
  from sqlalchemy import select
  from app.models.learning import Module, Passage, Quiz, Question, Answer, Remediation


  async def generate_module_markdown(module_id: uuid.UUID, db: AsyncSession) -> str:
      """
      Compiles a completed module into a Markdown summary string.
      Structure: title → ELI5 → Passages → Quiz Q&A → Remediations
      """
      module_result = await db.execute(select(Module).where(Module.id == module_id))
      module = module_result.scalar_one()

      passage_result = await db.execute(
          select(Passage).where(Passage.module_id == module_id).order_by(Passage.order_index)
      )
      passages = passage_result.scalars().all()

      # Fetch the most recent passed quiz
      quiz_result = await db.execute(
          select(Quiz)
          .where(Quiz.module_id == module_id, Quiz.passed == True)
          .order_by(Quiz.attempt_number.desc())
      )
      quiz = quiz_result.scalars().first()

      lines = []

      # Title block
      lines.append(f"# {module.topic}")
      lines.append(f"\n**Level:** {module.level.capitalize()}")
      if module.completed_at:
          lines.append(f"**Completed:** {module.completed_at.strftime('%Y-%m-%d')}")
      lines.append("\n---\n")

      # ELI5
      lines.append("## The Simple Version")
      lines.append(f"\n{module.eli5_text}\n")
      lines.append("\n---\n")

      # Passages
      lines.append("## Core Concepts")
      for passage in passages:
          lines.append(f"\n### {passage.concept_title}")
          lines.append(f"\n{passage.content}\n")
      lines.append("\n---\n")

      # Quiz Q&A
      if quiz:
          lines.append("## Quiz Results")
          lines.append(f"\n**Score:** {quiz.score}/{quiz.total_questions} — "
                       f"{'Passed' if quiz.passed else 'Failed'}")
          lines.append(f"**Attempts needed:** {quiz.attempt_number}\n")

          question_result = await db.execute(
              select(Question).where(Question.quiz_id == quiz.id).order_by(Question.order_index)
          )
          questions = question_result.scalars().all()

          answer_result = await db.execute(
              select(Answer).where(Answer.quiz_id == quiz.id)
          )
          answers = answer_result.scalars().all()
          answer_map = {a.question_id: a for a in answers}

          for i, q in enumerate(questions, 1):
              answer = answer_map.get(q.id)
              marker = "✓" if (answer and answer.is_correct) else "✗"
              lines.append(f"\n**Q{i}: {q.question_text}**")
              lines.append(f"Correct answer: {q.correct_answer}")
              if answer:
                  lines.append(f"Your answer: {answer.user_answer} {marker}")

          lines.append("\n---\n")

      # Remediations
      remediation_result = await db.execute(
          select(Remediation).where(Remediation.module_id == module_id)
      )
      remediations = remediation_result.scalars().all()

      if remediations:
          lines.append("## Extra Help")
          passage_map = {p.id: p for p in passages}
          seen_passage_ids: set = set()

          for r in remediations:
              if r.passage_id not in seen_passage_ids:
                  seen_passage_ids.add(r.passage_id)
                  passage = passage_map.get(r.passage_id)
                  title = passage.concept_title if passage else "Concept"
                  lines.append(f"\n### {title} (revisited)")
              lines.append(f"\n{r.content}\n")

      return "\n".join(lines)
  ```

**Outcome:** `generate_module_markdown()` exists and will produce a complete Markdown document for any module ID.

---

### Chunk 3 — Write `storage_service.py`

**What you learn:** How to call the Supabase Storage REST API directly using httpx, and how public bucket URLs are constructed.

- [ ] Create `backend/app/services/storage_service.py`:
  ```python
  import uuid
  import httpx
  from app.core.config import settings


  async def upload_markdown(content: str, module_id: uuid.UUID) -> str:
      """
      Uploads a Markdown string to the Supabase 'modules' storage bucket.
      Uses upsert so re-exporting the same module overwrites the existing file.
      Returns the public download URL.
      """
      bucket = "modules"
      path = f"{module_id}.md"
      upload_url = f"{settings.SUPABASE_URL}/storage/v1/object/{bucket}/{path}"

      async with httpx.AsyncClient() as client:
          response = await client.post(
              upload_url,
              content=content.encode("utf-8"),
              headers={
                  "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                  "Content-Type": "text/markdown",
                  "x-upsert": "true",
              },
          )
          response.raise_for_status()

      public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}"
      return public_url
  ```

**Outcome:** `upload_markdown()` uploads a string to Supabase Storage and returns a URL you can open in a browser to download the file.

---

### Chunk 4 — Add module completion to `quiz_service.py`

**What you learn:** Why a service function that detects completion should update the parent record — keeping all state transitions in the service layer.

- [ ] Open `backend/app/services/quiz_service.py`
- [ ] Add the `Module` import to the imports at the top:
  ```python
  from app.models.learning import Quiz, Question, Answer, Passage, Module
  ```
- [ ] Inside `score_quiz()`, find the line `await db.commit()` that comes after setting `quiz.passed`. Add these lines **before** that commit:
  ```python
      # If the quiz is fully passed, mark the module as completed
      if passed:
          module_result = await db.execute(
              select(Module).where(Module.id == quiz.module_id)
          )
          module = module_result.scalar_one_or_none()
          if module and module.status != "completed":
              module.status = "completed"
              module.completed_at = datetime.now(timezone.utc)
  ```
- [ ] Make sure `Module` and `datetime` + `timezone` are all imported at the top of the file (they should already be there from Milestone 2 except `Module`)

**Outcome:** When a quiz is submitted and `passed=True`, the parent module's `status` field is automatically updated to `"completed"` and `completed_at` is set. You can verify this in Supabase after submitting a perfect quiz.

---

### Chunk 5 — Add module and export schemas to `learning.py`

**What you learn:** How to extend an existing schema file with new response types without breaking existing routes.

- [ ] Open `backend/app/schemas/learning.py`
- [ ] At the bottom of the file, add these new schemas:
  ```python
  class ModuleDetail(BaseModel):
      id: uuid.UUID
      topic: str
      level: str
      eli5_text: str
      status: str
      markdown_url: str | None
      notion_page_id: str | None
      completed_at: datetime | None
      created_at: datetime
      passages: list[PassageResponse]

      model_config = {"from_attributes": True}


  class ExportDownloadResponse(BaseModel):
      download_url: str


  class ExportNotionResponse(BaseModel):
      notion_page_url: str
  ```

**Outcome:** The three new schemas exist and can be imported by the modules router.

---

### Chunk 6 — Write the `modules` router

**What you learn:** How to build a router that combines DB queries, service calls, and a file upload into clean endpoint handlers.

- [ ] Create `backend/app/routers/modules.py`:
  ```python
  import uuid
  from fastapi import APIRouter, Depends, HTTPException
  from sqlalchemy.ext.asyncio import AsyncSession
  from sqlalchemy import select
  from app.core.database import get_db
  from app.dependencies import get_current_user
  from app.models.user import User
  from app.models.learning import Module, Passage
  from app.schemas.learning import (
      ModuleListItem,
      ModuleDetail,
      PassageResponse,
      ExportDownloadResponse,
      ExportNotionResponse,
  )
  from app.services import markdown_service, storage_service, notion_service

  router = APIRouter(prefix="/modules", tags=["modules"])


  @router.get("", response_model=list[ModuleListItem])
  async def list_modules(
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ):
      result = await db.execute(
          select(Module)
          .where(Module.user_id == current_user.id)
          .order_by(Module.created_at.desc())
      )
      return result.scalars().all()


  @router.get("/{module_id}", response_model=ModuleDetail)
  async def get_module(
      module_id: uuid.UUID,
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ):
      module_result = await db.execute(
          select(Module).where(Module.id == module_id, Module.user_id == current_user.id)
      )
      module = module_result.scalar_one_or_none()
      if not module:
          raise HTTPException(status_code=404, detail="Module not found")

      passage_result = await db.execute(
          select(Passage).where(Passage.module_id == module_id).order_by(Passage.order_index)
      )
      passages = passage_result.scalars().all()

      return ModuleDetail(
          id=module.id,
          topic=module.topic,
          level=module.level,
          eli5_text=module.eli5_text,
          status=module.status,
          markdown_url=module.markdown_url,
          notion_page_id=module.notion_page_id,
          completed_at=module.completed_at,
          created_at=module.created_at,
          passages=[PassageResponse.model_validate(p) for p in passages],
      )


  @router.post("/{module_id}/export/download", response_model=ExportDownloadResponse)
  async def export_download(
      module_id: uuid.UUID,
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ):
      module_result = await db.execute(
          select(Module).where(Module.id == module_id, Module.user_id == current_user.id)
      )
      module = module_result.scalar_one_or_none()
      if not module:
          raise HTTPException(status_code=404, detail="Module not found")

      markdown = await markdown_service.generate_module_markdown(module_id, db)
      download_url = await storage_service.upload_markdown(markdown, module_id)

      module.markdown_url = download_url
      await db.commit()

      return ExportDownloadResponse(download_url=download_url)


  @router.post("/{module_id}/export/notion", response_model=ExportNotionResponse)
  async def export_notion(
      module_id: uuid.UUID,
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ):
      if not current_user.notion_access_token:
          raise HTTPException(
              status_code=400,
              detail="Notion is not connected. Call GET /notion/auth-url first.",
          )

      module_result = await db.execute(
          select(Module).where(Module.id == module_id, Module.user_id == current_user.id)
      )
      module = module_result.scalar_one_or_none()
      if not module:
          raise HTTPException(status_code=404, detail="Module not found")

      markdown = await markdown_service.generate_module_markdown(module_id, db)
      page_url = await notion_service.create_page(
          access_token=current_user.notion_access_token,
          topic=module.topic,
          markdown_content=markdown,
      )

      module.notion_page_id = page_url.split("/")[-1]
      await db.commit()

      return ExportNotionResponse(notion_page_url=page_url)
  ```

**Outcome:** All four module endpoints exist as Python code. They are not yet registered with the app.

---

### Chunk 7 — Register the modules router and test download export

**What you learn:** How adding a router to `main.py` immediately exposes all its endpoints, and how to verify a file upload to Supabase Storage.

- [ ] Open `backend/main.py` and update it:
  ```python
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  from app.core.config import settings
  from app.routers import auth, learning, modules

  app = FastAPI(title="MasterMind API", version="0.1.0")

  app.add_middleware(
      CORSMiddleware,
      allow_origins=[settings.FRONTEND_URL],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )

  app.include_router(auth.router)
  app.include_router(learning.router)
  app.include_router(modules.router)

  @app.get("/health")
  async def health():
      return {"status": "ok"}
  ```
- [ ] Restart the server and visit http://localhost:8000/docs
- [ ] Confirm the `/modules` endpoints appear in the Swagger UI
- [ ] **Test the download export:**
  - [ ] If you don't have a completed module, go back to Swagger and run the full learn → quiz flow, submitting all correct answers so the module is marked `completed`
  - [ ] Call `GET /modules` — confirm the module appears with `"status": "completed"`
  - [ ] Copy the `module_id`
  - [ ] Call `POST /modules/{module_id}/export/download`
  - [ ] Confirm you receive a `download_url` in the response
  - [ ] Open the URL in your browser — confirm it downloads a `.md` file
  - [ ] Open the `.md` file — verify it contains the ELI5, passages, quiz results, and (if applicable) remediations
  - [ ] Open Supabase → Storage → `modules` bucket — confirm the `.md` file is listed there

**Outcome:** The download export works end to end. A real Markdown file is stored in Supabase and accessible via public URL.

---

### Chunk 8 — Set up Notion developer credentials

**What you learn:** What a Notion integration is, how OAuth differs from direct API keys, and what a redirect URI is.

- [ ] Go to https://www.notion.so/my-integrations
- [ ] Click **New integration**
- [ ] Fill in:
  - Name: `MasterMind`
  - Type: **Public** (not internal — you need OAuth for other users)
  - Redirect URIs: `http://localhost:8000/notion/callback`
- [ ] Click **Submit**
- [ ] On the integration page, go to the **OAuth Domain & URIs** tab
- [ ] Copy the **OAuth client ID** — paste it into `backend/.env` as `NOTION_CLIENT_ID`
- [ ] Copy the **OAuth client secret** — paste it into `backend/.env` as `NOTION_CLIENT_SECRET`
- [ ] Set in `backend/.env`:
  ```
  NOTION_REDIRECT_URI=http://localhost:8000/notion/callback
  ```
- [ ] Restart the server so the new env vars are loaded

**Outcome:** Your `.env` has valid Notion OAuth credentials. Notion will accept auth requests from your local server.

---

### Chunk 9 — Write `notion_service.py`

**What you learn:** How to implement OAuth token exchange with httpx, and how to convert Markdown headings into Notion API block objects.

- [ ] Create `backend/app/services/notion_service.py`:
  ```python
  import base64
  import httpx
  from app.core.config import settings

  NOTION_API_VERSION = "2022-06-28"


  def get_auth_url(user_id: str) -> str:
      """
      Returns the Notion OAuth URL that the user visits to grant access.
      user_id is passed as the state parameter so the callback can identify the user.
      """
      return (
          f"https://api.notion.com/v1/oauth/authorize"
          f"?client_id={settings.NOTION_CLIENT_ID}"
          f"&response_type=code"
          f"&owner=user"
          f"&redirect_uri={settings.NOTION_REDIRECT_URI}"
          f"&state={user_id}"
      )


  async def exchange_code_for_token(code: str) -> dict:
      """
      Exchanges the OAuth authorization code for an access token.
      Returns the full token response dict from Notion.
      """
      credentials = f"{settings.NOTION_CLIENT_ID}:{settings.NOTION_CLIENT_SECRET}"
      encoded = base64.b64encode(credentials.encode()).decode()

      async with httpx.AsyncClient() as client:
          response = await client.post(
              "https://api.notion.com/v1/oauth/token",
              json={
                  "grant_type": "authorization_code",
                  "code": code,
                  "redirect_uri": settings.NOTION_REDIRECT_URI,
              },
              headers={
                  "Authorization": f"Basic {encoded}",
                  "Content-Type": "application/json",
                  "Notion-Version": NOTION_API_VERSION,
              },
          )
          response.raise_for_status()
          return response.json()


  async def create_page(access_token: str, topic: str, markdown_content: str) -> str:
      """
      Creates a new Notion page in the user's workspace with the module content.
      Returns the URL of the created page.
      """
      blocks = _markdown_to_notion_blocks(markdown_content)

      async with httpx.AsyncClient() as client:
          response = await client.post(
              "https://api.notion.com/v1/pages",
              json={
                  "parent": {"type": "workspace", "workspace": True},
                  "properties": {
                      "title": {
                          "title": [{"type": "text", "text": {"content": topic}}]
                      }
                  },
                  "children": blocks[:100],  # Notion API allows max 100 blocks per request
              },
              headers={
                  "Authorization": f"Bearer {access_token}",
                  "Content-Type": "application/json",
                  "Notion-Version": NOTION_API_VERSION,
              },
          )
          response.raise_for_status()
          return response.json()["url"]


  def _markdown_to_notion_blocks(markdown: str) -> list[dict]:
      """
      Converts a Markdown string into a list of Notion block objects.
      Handles: ## headings, ### headings, --- dividers, and paragraphs.
      """
      blocks = []
      for line in markdown.split("\n"):
          line = line.strip()
          if not line:
              continue
          if line.startswith("## "):
              blocks.append({
                  "object": "block",
                  "type": "heading_2",
                  "heading_2": {
                      "rich_text": [{"type": "text", "text": {"content": line[3:]}}]
                  },
              })
          elif line.startswith("### "):
              blocks.append({
                  "object": "block",
                  "type": "heading_3",
                  "heading_3": {
                      "rich_text": [{"type": "text", "text": {"content": line[4:]}}]
                  },
              })
          elif line == "---":
              blocks.append({"object": "block", "type": "divider", "divider": {}})
          else:
              # Strip markdown bold markers — Notion handles its own bold
              content = line.replace("**", "")
              if content:
                  blocks.append({
                      "object": "block",
                      "type": "paragraph",
                      "paragraph": {
                          "rich_text": [{"type": "text", "text": {"content": content}}]
                      },
                  })
      return blocks
  ```

**Outcome:** The three Notion service functions exist: `get_auth_url`, `exchange_code_for_token`, and `create_page`. The `_markdown_to_notion_blocks` helper can be tested in isolation.

---

### Chunk 10 — Write the notion router

**What you learn:** How OAuth callbacks work in a backend, and how to pass user identity through the OAuth state parameter.

- [ ] Create `backend/app/routers/notion.py`:
  ```python
  from fastapi import APIRouter, Depends, HTTPException
  from fastapi.responses import RedirectResponse
  from sqlalchemy.ext.asyncio import AsyncSession
  from sqlalchemy import select
  from app.core.database import get_db
  from app.dependencies import get_current_user
  from app.models.user import User
  from app.services import notion_service
  from app.core.config import settings
  import uuid

  router = APIRouter(prefix="/notion", tags=["notion"])


  @router.get("/auth-url")
  async def get_auth_url(current_user: User = Depends(get_current_user)):
      """
      Returns the Notion OAuth URL the frontend should redirect the user to.
      The user's ID is encoded as the state so the callback can identify them.
      """
      url = notion_service.get_auth_url(str(current_user.id))
      return {"url": url}


  @router.get("/callback")
  async def notion_callback(
      code: str,
      state: str,
      db: AsyncSession = Depends(get_db),
  ):
      """
      Notion OAuth callback. Called by Notion after the user approves access.
      - `code` is the authorization code to exchange for a token
      - `state` is the user_id passed when the auth URL was generated
      No JWT auth here — Notion redirects directly to this URL.
      """
      try:
          user_id = uuid.UUID(state)
      except ValueError:
          raise HTTPException(status_code=400, detail="Invalid state parameter")

      try:
          token_data = await notion_service.exchange_code_for_token(code)
      except Exception as e:
          raise HTTPException(status_code=400, detail=f"Notion OAuth failed: {str(e)}")

      result = await db.execute(select(User).where(User.id == user_id))
      user = result.scalar_one_or_none()
      if not user:
          raise HTTPException(status_code=404, detail="User not found")

      user.notion_access_token = token_data["access_token"]
      user.notion_workspace_id = token_data.get("workspace_id", "")
      await db.commit()

      return RedirectResponse(url=f"{settings.FRONTEND_URL}/settings?notion=connected")


  @router.delete("/disconnect")
  async def disconnect_notion(
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ):
      current_user.notion_access_token = None
      current_user.notion_workspace_id = None
      await db.commit()
      return {"message": "Notion disconnected"}
  ```

**Outcome:** Three Notion endpoints exist: `GET /notion/auth-url`, `GET /notion/callback`, and `DELETE /notion/disconnect`.

---

### Chunk 11 — Register the notion router and test Notion export

**What you learn:** How to test an OAuth flow manually and verify that a Notion page is created from your app.

- [ ] Open `backend/main.py` and add the notion router:
  ```python
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  from app.core.config import settings
  from app.routers import auth, learning, modules, notion

  app = FastAPI(title="MasterMind API", version="0.1.0")

  app.add_middleware(
      CORSMiddleware,
      allow_origins=[settings.FRONTEND_URL],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )

  app.include_router(auth.router)
  app.include_router(learning.router)
  app.include_router(modules.router)
  app.include_router(notion.router)

  @app.get("/health")
  async def health():
      return {"status": "ok"}
  ```
- [ ] Restart the server and visit http://localhost:8000/docs
- [ ] Confirm the `/notion` endpoints appear
- [ ] **Test the Notion OAuth flow:**
  - [ ] Authorize in Swagger with your JWT token
  - [ ] Call `GET /notion/auth-url` — copy the `url` from the response
  - [ ] Open that URL in your browser
  - [ ] Sign in to Notion and click **Allow access**
  - [ ] You should be redirected to `http://localhost:5173/settings?notion=connected`
    - (The frontend is not built yet, so you will see a "site cannot be reached" error — that is expected. Check that the URL in your browser shows `notion=connected`.)
  - [ ] Check Supabase → `users` table — confirm `notion_access_token` is now populated for your user
- [ ] **Test the Notion page export:**
  - [ ] In Swagger, call `POST /modules/{module_id}/export/notion` with a completed module ID
  - [ ] Confirm you receive a `notion_page_url` in the response
  - [ ] Open that URL — confirm a Notion page was created with the module content
  - [ ] Verify the page has headings for "The Simple Version", "Core Concepts", "Quiz Results"
- [ ] **Test disconnect:**
  - [ ] Call `DELETE /notion/disconnect`
  - [ ] Confirm `{"message": "Notion disconnected"}` is returned
  - [ ] Check Supabase — confirm `notion_access_token` is null again

**Outcome:** The full Notion integration works. Users can connect Notion, export a module as a Notion page, and disconnect.

---

### Chunk 12 — Write tests for export functions

**What you learn:** How to test pure helper functions in isolation without a real database or network call.

- [ ] Create `backend/tests/test_export.py`:
  ```python
  from app.services.notion_service import get_auth_url, _markdown_to_notion_blocks
  from app.core.config import settings


  def test_auth_url_contains_notion_domain():
      url = get_auth_url("test-user-id")
      assert "api.notion.com" in url


  def test_auth_url_contains_client_id():
      url = get_auth_url("test-user-id")
      assert settings.NOTION_CLIENT_ID in url


  def test_auth_url_contains_state():
      user_id = "abc-123"
      url = get_auth_url(user_id)
      assert f"state={user_id}" in url


  def test_markdown_h2_becomes_heading_2_block():
      blocks = _markdown_to_notion_blocks("## My Section")
      assert len(blocks) == 1
      assert blocks[0]["type"] == "heading_2"
      assert blocks[0]["heading_2"]["rich_text"][0]["text"]["content"] == "My Section"


  def test_markdown_h3_becomes_heading_3_block():
      blocks = _markdown_to_notion_blocks("### Sub Concept")
      assert len(blocks) == 1
      assert blocks[0]["type"] == "heading_3"


  def test_markdown_divider_becomes_divider_block():
      blocks = _markdown_to_notion_blocks("---")
      assert len(blocks) == 1
      assert blocks[0]["type"] == "divider"


  def test_plain_text_becomes_paragraph_block():
      blocks = _markdown_to_notion_blocks("Some plain text here.")
      assert len(blocks) == 1
      assert blocks[0]["type"] == "paragraph"
      assert "plain text" in blocks[0]["paragraph"]["rich_text"][0]["text"]["content"]


  def test_empty_lines_are_skipped():
      blocks = _markdown_to_notion_blocks("Line one\n\n\nLine two")
      assert len(blocks) == 2


  def test_bold_markers_are_stripped():
      blocks = _markdown_to_notion_blocks("**Score:** 9/10")
      content = blocks[0]["paragraph"]["rich_text"][0]["text"]["content"]
      assert "**" not in content
      assert "Score:" in content
  ```
- [ ] Run all tests:
  ```bash
  pytest tests/ -v
  ```
- [ ] Confirm all tests pass — you should now have 13 previous tests + 9 new tests = 22 total

**Outcome:** Automated proof that the auth URL generation and Markdown-to-Notion block conversion work correctly.

---

## Milestone 3 complete checklist (summary)

- [ ] Chunk 1 — Supabase Storage `modules` bucket created as public
- [ ] Chunk 2 — `markdown_service.py` written
- [ ] Chunk 3 — `storage_service.py` written
- [ ] Chunk 4 — Module completion added to `quiz_service.py`
- [ ] Chunk 5 — `ModuleDetail`, `ExportDownloadResponse`, `ExportNotionResponse` added to `learning.py`
- [ ] Chunk 6 — `modules` router written
- [ ] Chunk 7 — Modules router registered; download export tested end to end
- [ ] Chunk 8 — Notion developer credentials in `.env`
- [ ] Chunk 9 — `notion_service.py` written
- [ ] Chunk 10 — Notion router written
- [ ] Chunk 11 — Notion router registered; full OAuth + page export tested
- [ ] Chunk 12 — All 22 tests passing

---

## Before starting Milestone 4

Do not start Milestone 4 until every box above is checked AND:

- Opening a `.md` export URL in your browser downloads a complete, readable Markdown file
- A Notion page created by the app has correct headings and content visible in your Notion workspace
- `pytest tests/ -v` shows all 22 tests passing
- Supabase: `modules` bucket contains at least one `.md` file; `users` table shows `notion_access_token` can be set and cleared

Tell Claude: "Milestone 3 is complete. Starting Milestone 4."
