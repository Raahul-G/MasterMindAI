"""
Notion router — public OAuth flow.

  GET  /notion/auth-url   → returns the Notion OAuth URL (user clicks → redirected to Notion)
  GET  /notion/callback   → exchanges code, creates MasterMind root page, saves to user
  GET  /notion/status     → returns connection status + workspace name
  DELETE /notion/disconnect → clears all notion fields from user
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services import notion_service

router = APIRouter(prefix="/notion", tags=["notion"])


@router.get("/auth-url")
async def get_auth_url(current_user: User = Depends(get_current_user)):
    """Returns the Notion OAuth URL. Frontend redirects the user there."""
    if not settings.NOTION_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Notion integration is not configured.")
    url = notion_service.get_auth_url(str(current_user.id))
    return {"url": url}


@router.get("/callback")
async def notion_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Notion redirects here after the user authorises the integration.
    Exchanges the code, creates the MasterMind root page, saves everything to the user.
    Redirects back to the frontend profile page.
    """
    frontend_profile = f"{settings.FRONTEND_URL}/profile"

    if error or not code or not state:
        return RedirectResponse(url=f"{frontend_profile}?notion=error")

    # Look up user via state (user_id)
    result = await db.execute(select(User).where(User.id == state))
    user = result.scalar_one_or_none()
    if not user:
        return RedirectResponse(url=f"{frontend_profile}?notion=error")

    try:
        token_data = await notion_service.exchange_code_for_token(code)
        mastermind_page_id = await notion_service.create_mastermind_root_page(
            token_data["access_token"]
        )
    except Exception:
        return RedirectResponse(url=f"{frontend_profile}?notion=error")

    user.notion_access_token = token_data["access_token"]
    user.notion_workspace_id = token_data["workspace_id"]
    user.notion_workspace_name = token_data["workspace_name"]
    user.notion_mastermind_page_id = mastermind_page_id
    await db.commit()

    return RedirectResponse(url=f"{frontend_profile}?notion=connected")


@router.get("/status")
async def notion_status(current_user: User = Depends(get_current_user)):
    """Returns whether Notion is connected and the workspace name."""
    return {
        "connected": current_user.notion_access_token is not None,
        "workspace_name": current_user.notion_workspace_name,
    }


@router.delete("/disconnect")
async def disconnect_notion(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.notion_access_token = None
    current_user.notion_workspace_id = None
    current_user.notion_workspace_name = None
    current_user.notion_mastermind_page_id = None
    await db.commit()
    return {"message": "Notion disconnected"}
