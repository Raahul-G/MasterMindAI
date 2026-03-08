from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest
from app.core.security import hash_password, verify_password, create_access_token
import httpx


async def register_user(data: RegisterRequest, db: AsyncSession) -> str:
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
    return create_access_token(user.id)


async def login_user(data: LoginRequest, db: AsyncSession) -> str:
    """Logs in a user. Raises ValueError if credentials are wrong."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise ValueError("Invalid credentials")
    if not verify_password(data.password, user.hashed_password):
        raise ValueError("Invalid credentials")

    return create_access_token(user.id)


async def google_login(id_token: str, db: AsyncSession) -> str:
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

    # Check if user exists by Google ID or email
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
    return create_access_token(user.id)


async def save_interests(user_id: str, interests: list[str], db: AsyncSession) -> None:
    """Saves the user's personal interest topics after onboarding."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.interest_topics = interests
        await db.commit()
