from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from workbench.models.base import Base


class FeedView(Base):
    __tablename__ = "feed_views"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspace_state.id"), nullable=False)
    filter_key: Mapped[str] = mapped_column(String, nullable=False)
    record_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    watermark: Mapped[int] = mapped_column(Integer, nullable=False)
    secret: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
