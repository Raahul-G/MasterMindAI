import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.limiter import limiter
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.learning import (
    GenerateQuizRequest,
    GenerateQuizResponse,
    NextPairRequest,
    NextPairResponse,
    RemediateRequest,
    RemediateResponse,
    StartModuleRequest,
    StartModuleResponse,
    SubmitQuizRequest,
    SubmitQuizResponse,
)
from app.services import learning_service, quiz_service

router = APIRouter(prefix="/learn", tags=["learning"])


@router.post("/start", response_model=StartModuleResponse)
@limiter.limit("5/minute")
async def start_module(
    request: Request,
    data: StartModuleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.level not in ("kid", "intermediate", "expert"):
        raise HTTPException(status_code=400, detail="Level must be kid, intermediate, or expert")
    return await learning_service.start_module(
        data.topic, data.level, current_user, db, prerequisite_concepts=data.prerequisite_concepts or None
    )


@router.post("/quiz/generate", response_model=GenerateQuizResponse)
@limiter.limit("5/minute")
async def generate_quiz(
    request: Request,
    data: GenerateQuizRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await learning_service.generate_quiz_for_passage(data.passage_id, db)


@router.post("/quiz/submit", response_model=SubmitQuizResponse)
@limiter.limit("5/minute")
async def submit_quiz(
    request: Request,
    data: SubmitQuizRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await quiz_service.score_quiz(data.quiz_id, data.answers, db, data.local_date)
    return SubmitQuizResponse(**result)


@router.post("/passage/next", response_model=NextPairResponse)
@limiter.limit("5/minute")
async def next_passage_pair(
    request: Request,
    data: NextPairRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await learning_service.generate_next_pair(data.module_id, data.covered_concepts, db)


@router.get("/resume/{module_id}", response_model=StartModuleResponse)
@limiter.limit("5/minute")
async def resume_module(
    request: Request,
    module_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await learning_service.resume_module(module_id, db)


@router.post("/remediate", response_model=RemediateResponse)
@limiter.limit("5/minute")
async def remediate(
    request: Request,
    data: RemediateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not data.failed_concepts:
        raise HTTPException(status_code=400, detail="No failed concepts provided")
    return await learning_service.remediate(data.module_id, data.quiz_id, data.failed_concepts, db)
