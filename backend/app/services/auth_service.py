import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import httpx

from app.models.user import User
from app.models.auth import RefreshToken
from app.schemas.auth import RegisterRequest, LoginRequest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    generate_refresh_token,
    hash_token,
)
from app.core.config import settings


async def _create_token_pair(user_id: uuid.UUID, db: AsyncSession) -> tuple[str, str]:
    """Issues a new access + refresh token pair. Persists the refresh token hash to DB."""
    access_token = create_access_token(user_id)
    raw_refresh = generate_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(
        user_id=user_id,
        token_hash=hash_token(raw_refresh),
        expires_at=expires_at,
    ))
    await db.commit()
    return access_token, raw_refresh


async def _revoke_all(user_id: uuid.UUID, db: AsyncSession) -> None:
    """Revokes every active refresh token for a user (theft detection / logout)."""
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked == False)  # noqa: E712
        .values(revoked=True)
    )
    await db.commit()


async def register_user(data: RegisterRequest, db: AsyncSession) -> tuple[str, str]:
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
    return await _create_token_pair(user.id, db)


async def login_user(data: LoginRequest, db: AsyncSession) -> tuple[str, str]:
    """Logs in a user. Raises ValueError if credentials are wrong."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise ValueError("Invalid credentials")
    if not verify_password(data.password, user.hashed_password):
        raise ValueError("Invalid credentials")

    return await _create_token_pair(user.id, db)


async def google_login(id_token: str, db: AsyncSession) -> tuple[str, str]:
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
    return await _create_token_pair(user.id, db)


async def rotate_refresh_token(token: str, db: AsyncSession) -> tuple[str, str]:
    """
    Validates the presented refresh token, revokes it, and issues a new pair.
    Raises HTTPException-compatible ValueError on any invalid/expired/revoked token.
    If a revoked token is replayed, all sessions for that user are killed (theft detection).
    """
    token_hash = hash_token(token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    record = result.scalar_one_or_none()

    if record is None:
        raise ValueError("Invalid refresh token")

    if record.revoked:
        await _revoke_all(record.user_id, db)
        raise ValueError("Token reuse detected — all sessions revoked")

    if record.expires_at < datetime.now(timezone.utc):
        raise ValueError("Refresh token expired")

    record.revoked = True
    await db.commit()

    return await _create_token_pair(record.user_id, db)


async def logout_user(user_id: uuid.UUID, db: AsyncSession) -> None:
    """Revokes all refresh tokens for the current user, effectively ending all sessions."""
    await _revoke_all(user_id, db)


async def save_interests(user_id: uuid.UUID, interests: list[str], db: AsyncSession) -> None:
    """Saves the user's personal interest topics after onboarding."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.interest_topics = interests
        await db.commit()
