import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.learning import Answer, Module, Passage, Question, Quiz
from app.models.user import User
from app.schemas.learning import (
    ExportDownloadResponse,
    ExportNotionResponse,
    ModuleDetail,
    ModuleListItem,
    ModuleReviewResponse,
    PassageResponse,
    ReviewQuestionResponse,
)
from app.services import markdown_service, storage_service

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


@router.get("/{module_id}/review", response_model=ModuleReviewResponse)
async def get_module_review(
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

    # Most recent quiz (passed or latest attempt)
    quiz_result = await db.execute(
        select(Quiz)
        .where(Quiz.module_id == module_id)
        .order_by(Quiz.attempt_number.desc())
    )
    quiz = quiz_result.scalars().first()

    questions_with_answers: list[ReviewQuestionResponse] = []
    if quiz:
        question_result = await db.execute(
            select(Question).where(Question.quiz_id == quiz.id).order_by(Question.order_index)
        )
        questions = question_result.scalars().all()

        answer_result = await db.execute(
            select(Answer).where(Answer.quiz_id == quiz.id)
        )
        answers = answer_result.scalars().all()
        answer_map = {a.question_id: a for a in answers}

        passage_id_to_title = {p.id: p.concept_title for p in passages}

        for q in questions:
            ans = answer_map.get(q.id)
            questions_with_answers.append(ReviewQuestionResponse(
                question_text=q.question_text,
                concept_title=passage_id_to_title.get(q.passage_id, ""),
                options=q.options or [],
                correct_answer=q.correct_answer,
                user_answer=ans.user_answer if ans else None,
                is_correct=ans.is_correct if ans else None,
            ))

    return ModuleReviewResponse(
        id=module.id,
        topic=module.topic,
        level=module.level,
        eli5_text=module.eli5_text,
        status=module.status,
        completed_at=module.completed_at,
        passages=[PassageResponse.model_validate(p) for p in passages],
        quiz_score=quiz.score if quiz else None,
        quiz_total=quiz.total_questions if quiz else None,
        quiz_attempts=quiz.attempt_number if quiz else None,
        questions=questions_with_answers,
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

    from app.services import notion_service  # imported here to avoid circular on missing creds

    markdown = await markdown_service.generate_module_markdown(module_id, db)
    try:
        page_url = await notion_service.create_page(
            access_token=current_user.notion_access_token,
            topic=module.topic,
            markdown_content=markdown,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Notion API error: {str(e)}")

    module.notion_page_id = page_url.split("/")[-1]
    await db.commit()

    return ExportNotionResponse(notion_page_url=page_url)
