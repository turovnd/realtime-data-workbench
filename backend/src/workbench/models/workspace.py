from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from workbench.models.base import Base


class Workspace(Base):
    __tablename__ = "workspace_state"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    token_hash: Mapped[str | None] = mapped_column(String, unique=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cursor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
