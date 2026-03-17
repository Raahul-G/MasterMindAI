from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.learning import (
    GenerateQuizRequest,
    GenerateQuizResponse,
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
async def start_module(
    data: StartModuleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.level not in ("kid", "intermediate", "expert"):
        raise HTTPException(status_code=400, detail="Level must be kid, intermediate, or expert")
    return await learning_service.start_module(data.topic, data.level, current_user, db)


@router.post("/quiz/generate", response_model=GenerateQuizResponse)
async def generate_quiz(
    data: GenerateQuizRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await learning_service.generate_quiz_for_module(data.module_id, db)


@router.post("/quiz/submit", response_model=SubmitQuizResponse)
async def submit_quiz(
    data: SubmitQuizRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await quiz_service.score_quiz(data.quiz_id, data.answers, db)
    return SubmitQuizResponse(**result)


@router.post("/remediate", response_model=RemediateResponse)
async def remediate(
    data: RemediateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not data.failed_concepts:
        raise HTTPException(status_code=400, detail="No failed concepts provided")
    return await learning_service.remediate(data.module_id, data.quiz_id, data.failed_concepts, db)
