from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from common.models.base import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspace_state.id"), nullable=False, unique=True
    )
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    token_hash: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspace_state.id"), nullable=False)
    account_id: Mapped[str | None] = mapped_column(ForeignKey("accounts.id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AuthBucket(Base):
    __tablename__ = "auth_buckets"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
