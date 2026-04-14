import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.learning import GraphResponse, PopulateGraphResponse
from app.services import graph_service

router = APIRouter(tags=["graph"])


@router.get("/graph", response_model=GraphResponse)
async def get_knowledge_graph(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GraphResponse:
    return await graph_service.get_graph(current_user.id, db)


@router.post("/graph/populate", response_model=PopulateGraphResponse)
async def populate_graph(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PopulateGraphResponse:
    count = await graph_service.retroactive_populate(current_user.id, db)
    return PopulateGraphResponse(populated=count)


@router.get("/graph/friend/{friend_user_id}", response_model=GraphResponse)
async def get_friend_graph(
    friend_user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GraphResponse:
    try:
        return await graph_service.get_friend_graph(current_user.id, friend_user_id, db)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
