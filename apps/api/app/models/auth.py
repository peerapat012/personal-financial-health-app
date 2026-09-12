from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AuthOwner(TimestampMixin, Base):
    __tablename__ = "auth_owner"
    __table_args__ = (
        CheckConstraint("id = 1", name="auth_owner_singleton_check"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    username: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    __table_args__ = (Index("auth_sessions_expires_at_idx", "expires_at"),)

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
