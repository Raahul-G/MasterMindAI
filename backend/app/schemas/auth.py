from pydantic import BaseModel, EmailStr
import uuid


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    id_token: str  # The token Google sends back to the frontend after sign-in


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    avatar_url: str | None
    interest_topics: list[str] | None
    is_active: bool

    model_config = {"from_attributes": True}
