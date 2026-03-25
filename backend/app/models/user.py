import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    interest_topics: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    notion_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    notion_workspace_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notion_workspace_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notion_mastermind_page_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    @property
    def notion_connected(self) -> bool:
        """Derived field — read by Pydantic UserResponse via from_attributes=True."""
        return self.notion_access_token is not None
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
