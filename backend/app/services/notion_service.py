"""
Notion integration service — public OAuth flow.

Connect flow:
  1. GET /notion/auth-url          → redirect user to Notion OAuth page
  2. GET /notion/callback?code=... → exchange code, create MasterMind root page, save to user
  3. DELETE /notion/disconnect     → clear all notion fields on user

Auto-export:
  After every module completion, quiz_service calls create_module_subpage()
  to create a rich sub-page under the user's MasterMind root page.
"""

import base64
import logging
import uuid
from datetime import timezone
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.learning import Answer, Module, Passage, Question, Quiz, Remediation
from app.models.user import User

logger = logging.getLogger(__name__)

NOTION_API_VERSION = "2022-06-28"
NOTION_TOKEN_URL = "https://api.notion.com/v1/oauth/token"
NOTION_AUTH_URL = "https://api.notion.com/v1/oauth/authorize"


# ---------------------------------------------------------------------------
# OAuth helpers
# ---------------------------------------------------------------------------

def get_auth_url(user_id: str) -> str:
    """Builds the Notion OAuth authorisation URL. State carries the user ID."""
    params = urlencode({
        "client_id": settings.NOTION_CLIENT_ID,
        "response_type": "code",
        "owner": "user",
        "redirect_uri": settings.NOTION_REDIRECT_URI,
        "state": user_id,
    })
    return f"{NOTION_AUTH_URL}?{params}"


async def exchange_code_for_token(code: str) -> dict:
    """
    Exchanges an OAuth authorisation code for an access token.
    Returns {"access_token", "workspace_id", "workspace_name"}.
    """
    credentials = base64.b64encode(
        f"{settings.NOTION_CLIENT_ID}:{settings.NOTION_CLIENT_SECRET}".encode()
    ).decode()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            NOTION_TOKEN_URL,
            json={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.NOTION_REDIRECT_URI,
            },
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()

    data = response.json()
    return {
        "access_token": data["access_token"],
        "workspace_id": data.get("workspace_id", ""),
        "workspace_name": data.get("workspace_name", ""),
    }


# ---------------------------------------------------------------------------
# MasterMind root page
# ---------------------------------------------------------------------------

async def create_mastermind_root_page(access_token: str) -> str:
    """
    Creates the top-level 'MasterMind' page in the user's Notion workspace.
    Uses OAuth workspace parent so no shared page is needed.
    Returns the new page ID.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.notion.com/v1/pages",
            json={
                "parent": {"type": "workspace", "workspace": True},
                "icon": {"type": "emoji", "emoji": "🧠"},
                "properties": {
                    "title": {
                        "title": [{"type": "text", "text": {"content": "MasterMind"}}]
                    }
                },
                "children": [
                    _paragraph(
                        "Your MasterMind learning hub. "
                        "Every topic you master appears here as a sub-page."
                    ),
                ],
            },
            headers=_headers(access_token),
        )
        response.raise_for_status()

    return response.json()["id"]


# ---------------------------------------------------------------------------
# Module sub-page (auto-created on completion)
# ---------------------------------------------------------------------------

async def create_module_subpage(
    access_token: str,
    mastermind_page_id: str,
    module_id: uuid.UUID,
    db: AsyncSession,
) -> str:
    """
    Creates a rich Notion sub-page under the MasterMind root page for a
    completed module. Fetches all data from the DB internally.
    Returns the URL of the created page.
    """
    # --- Fetch module ---
    module_result = await db.execute(select(Module).where(Module.id == module_id))
    module = module_result.scalar_one()

    # --- Fetch passages (ordered) ---
    passage_result = await db.execute(
        select(Passage).where(Passage.module_id == module_id).order_by(Passage.order_index)
    )
    passages = passage_result.scalars().all()

    # --- Fetch most recent passed quiz ---
    quiz_result = await db.execute(
        select(Quiz)
        .where(Quiz.module_id == module_id, Quiz.passed == True)  # noqa: E712
        .order_by(Quiz.attempt_number.desc())
    )
    quiz = quiz_result.scalars().first()

    # --- Fetch questions + answers for that quiz ---
    questions_answers: list[dict] = []
    if quiz:
        q_result = await db.execute(
            select(Question).where(Question.quiz_id == quiz.id).order_by(Question.order_index)
        )
        questions = q_result.scalars().all()

        a_result = await db.execute(select(Answer).where(Answer.quiz_id == quiz.id))
        answer_map = {a.question_id: a for a in a_result.scalars().all()}

        for q in questions:
            ans = answer_map.get(q.id)
            questions_answers.append({
                "question_text": q.question_text,
                "correct_answer": q.correct_answer,
                "user_answer": ans.user_answer if ans else None,
                "is_correct": ans.is_correct if ans else None,
            })

    # --- Fetch remediations ---
    rem_result = await db.execute(
        select(Remediation).where(Remediation.module_id == module_id)
    )
    remediations = rem_result.scalars().all()
    passage_map = {p.id: p.concept_title for p in passages}
    rem_data = [
        {"concept_title": passage_map.get(r.passage_id, "Concept"), "content": r.content}
        for r in remediations
    ]

    # --- Build blocks ---
    blocks = _build_module_blocks(
        eli5_text=module.eli5_text,
        level=module.level,
        created_at=module.created_at.strftime("%Y-%m-%d") if module.created_at else "—",
        completed_at=module.completed_at.strftime("%Y-%m-%d") if module.completed_at else "—",
        passages=[{"concept_title": p.concept_title, "content": p.content} for p in passages],
        quiz_data={"score": quiz.score, "total": quiz.total_questions, "attempt_number": quiz.attempt_number} if quiz else None,
        questions_answers=questions_answers,
        remediations=rem_data,
    )

    # --- Create Notion page ---
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.notion.com/v1/pages",
            json={
                "parent": {"type": "page_id", "page_id": mastermind_page_id},
                "icon": {"type": "emoji", "emoji": "📖"},
                "properties": {
                    "title": {
                        "title": [{"type": "text", "text": {"content": module.topic}}]
                    }
                },
                "children": blocks[:100],  # Notion API: max 100 blocks per request
            },
            headers=_headers(access_token),
        )
        response.raise_for_status()

    return response.json()["url"]


# ---------------------------------------------------------------------------
# Incremental concept sync (auto-called after each quiz pass)
# ---------------------------------------------------------------------------

async def _create_module_page_shell(
    access_token: str,
    mastermind_page_id: str,
    module: Module,
) -> str:
    """
    Creates a module subpage shell (metadata + ELI5 + 'Core Concepts' heading).
    Returns the new Notion page ID (not URL — we need the ID for PATCH appends).
    """
    started = module.created_at.strftime("%Y-%m-%d") if module.created_at else "—"
    children = [
        {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {
                    "content": f"Level: {module.level.capitalize()}   |   Started: {started}"
                }}],
                "icon": {"type": "emoji", "emoji": "📅"},
                "color": "gray_background",
            },
        },
        _divider(),
        _heading2("The Simple Version"),
        _paragraph(module.eli5_text or ""),
        _divider(),
        _heading2("Core Concepts"),
    ]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.notion.com/v1/pages",
            json={
                "parent": {"type": "page_id", "page_id": mastermind_page_id},
                "icon": {"type": "emoji", "emoji": "📖"},
                "properties": {
                    "title": {
                        "title": [{"type": "text", "text": {"content": module.topic}}]
                    }
                },
                "children": children,
            },
            headers=_headers(access_token),
        )
        response.raise_for_status()

    return response.json()["id"]


def _build_concept_blocks(
    passage: Passage,
    quiz: Quiz,
    questions_answers: list[dict],
    remediations: list[dict],
) -> list[dict]:
    """Returns Notion blocks for one completed concept."""
    mastered_date = (
        quiz.submitted_at.astimezone(timezone.utc).strftime("%Y-%m-%d")
        if quiz.submitted_at
        else "—"
    )
    blocks: list[dict] = [
        _divider(),
        _heading3(passage.concept_title),
        {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {
                    "content": (
                        f"Mastered: {mastered_date}   |   "
                        f"Score: {quiz.score}/{quiz.total_questions}   |   "
                        f"Attempt #{quiz.attempt_number}"
                    )
                }}],
                "icon": {"type": "emoji", "emoji": "📊"},
                "color": "green_background",
            },
        },
        _paragraph(passage.content or ""),
    ]

    if questions_answers:
        blocks.append(_heading3("Quiz Results"))
        for i, qa in enumerate(questions_answers, 1):
            marker = "✓" if qa["is_correct"] else "✗"
            blocks.append(_paragraph(f"Q{i}: {qa['question_text']}"))
            blocks.append(_paragraph(f"Correct answer: {qa['correct_answer']}"))
            if qa["user_answer"]:
                blocks.append(_paragraph(f"Your answer: {qa['user_answer']} {marker}"))

    if remediations:
        blocks.append(_heading3("Extra Help"))
        for r in remediations:
            blocks.append(_paragraph(r["content"]))

    return blocks


async def sync_concept_to_notion(
    user_id: uuid.UUID,
    module_id: uuid.UUID,
    passage_id: uuid.UUID,
    quiz_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """
    Appends a completed concept to the module's Notion subpage.
    Creates the subpage shell on first concept. Silently no-ops if the
    user has no Notion token. Never raises — all errors are logged as warnings.
    """
    try:
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user or not user.notion_access_token or not user.notion_mastermind_page_id:
            return

        module_result = await db.execute(select(Module).where(Module.id == module_id))
        module = module_result.scalar_one_or_none()
        if not module:
            return

        passage_result = await db.execute(select(Passage).where(Passage.id == passage_id))
        passage = passage_result.scalar_one_or_none()
        if not passage:
            return

        quiz_result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
        quiz = quiz_result.scalar_one_or_none()
        if not quiz:
            return

        # Create page shell on first concept
        if not module.notion_page_id:
            page_id = await _create_module_page_shell(
                access_token=user.notion_access_token,
                mastermind_page_id=user.notion_mastermind_page_id,
                module=module,
            )
            module.notion_page_id = page_id
            await db.commit()

        # Build Q&A list for this quiz
        q_result = await db.execute(
            select(Question).where(Question.quiz_id == quiz_id).order_by(Question.order_index)
        )
        questions = q_result.scalars().all()

        a_result = await db.execute(select(Answer).where(Answer.quiz_id == quiz_id))
        answer_map = {a.question_id: a for a in a_result.scalars().all()}

        questions_answers = [
            {
                "question_text": q.question_text,
                "correct_answer": q.correct_answer,
                "user_answer": answer_map[q.id].user_answer if q.id in answer_map else None,
                "is_correct": answer_map[q.id].is_correct if q.id in answer_map else None,
            }
            for q in questions
        ]

        # Load remediations for this passage
        rem_result = await db.execute(
            select(Remediation).where(
                Remediation.module_id == module_id,
                Remediation.passage_id == passage_id,
            )
        )
        remediations = [{"content": r.content} for r in rem_result.scalars().all()]

        blocks = _build_concept_blocks(passage, quiz, questions_answers, remediations)

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"https://api.notion.com/v1/blocks/{module.notion_page_id}/children",
                json={"children": blocks},
                headers=_headers(user.notion_access_token),
            )
            response.raise_for_status()

    except Exception as exc:
        logger.warning("sync_concept_to_notion failed for module %s: %s", module_id, exc)


# ---------------------------------------------------------------------------
# Block builders
# ---------------------------------------------------------------------------

def _build_module_blocks(
    eli5_text: str,
    level: str,
    created_at: str,
    completed_at: str,
    passages: list[dict],
    quiz_data: dict | None,
    questions_answers: list[dict],
    remediations: list[dict],
) -> list[dict]:
    blocks: list[dict] = []

    # --- Meta callout ---
    blocks.append({
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [{"type": "text", "text": {
                "content": f"Level: {level.capitalize()}   |   Created: {created_at}   |   Completed: {completed_at}"
            }}],
            "icon": {"type": "emoji", "emoji": "📅"},
            "color": "gray_background",
        },
    })
    blocks.append(_divider())

    # --- ELI5 ---
    blocks.append(_heading2("The Simple Version"))
    blocks.append(_paragraph(eli5_text))
    blocks.append(_divider())

    # --- Core concepts ---
    blocks.append(_heading2("Core Concepts"))
    for p in passages:
        blocks.append(_heading3(p["concept_title"]))
        blocks.append(_paragraph(p["content"]))
    blocks.append(_divider())

    # --- Quiz ---
    if quiz_data:
        blocks.append(_heading2("Quiz Results"))
        score_line = f"Score: {quiz_data['score']}/{quiz_data['total']}   |   Attempt #{quiz_data['attempt_number']}"
        blocks.append(_paragraph(score_line))

        for i, qa in enumerate(questions_answers, 1):
            marker = "✓" if qa["is_correct"] else "✗"
            blocks.append(_paragraph(f"Q{i}: {qa['question_text']}"))
            blocks.append(_paragraph(f"Correct answer: {qa['correct_answer']}"))
            if qa["user_answer"]:
                blocks.append(_paragraph(f"Your answer: {qa['user_answer']} {marker}"))

    # --- Remediations ---
    if remediations:
        blocks.append(_divider())
        blocks.append(_heading2("Extra Help"))
        seen: set[str] = set()
        for r in remediations:
            title = r["concept_title"]
            if title not in seen:
                seen.add(title)
                blocks.append(_heading3(f"{title} (revisited)"))
            blocks.append(_paragraph(r["content"]))

    return blocks


def _headers(access_token: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION,
    }


def _heading2(text: str) -> dict:
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


def _heading3(text: str) -> dict:
    return {
        "object": "block",
        "type": "heading_3",
        "heading_3": {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


def _paragraph(text: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
    }


def _divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}
