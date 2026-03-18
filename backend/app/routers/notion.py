"""
Notion router — internal integration token flow.

Migration note: To switch to public OAuth later, replace POST /notion/connect
with GET /notion/auth-url and GET /notion/callback. The disconnect endpoint
and all export logic stay unchanged.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/notion", tags=["notion"])


class ConnectNotionRequest(BaseModel):
    token: str  # The secret_... internal integration token from notion.so/my-integrations


@router.post("/connect")
async def connect_notion(
    data: ConnectNotionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Saves a Notion internal integration token to the user's profile.
    Get your token from: https://www.notion.so/my-integrations
    """
    if not (data.token.startswith("secret_") or data.token.startswith("ntn_")):
        raise HTTPException(
            status_code=400,
            detail="Invalid token. Notion tokens start with 'secret_' or 'ntn_'.",
        )
    current_user.notion_access_token = data.token
    await db.commit()
    return {"message": "Notion connected"}


@router.get("/status")
async def notion_status(current_user: User = Depends(get_current_user)):
    """Returns whether Notion is connected for the current user."""
    return {"connected": current_user.notion_access_token is not None}


@router.delete("/disconnect")
async def disconnect_notion(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.notion_access_token = None
    current_user.notion_workspace_id = None
    await db.commit()
    return {"message": "Notion disconnected"}
