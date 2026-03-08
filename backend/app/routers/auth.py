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
