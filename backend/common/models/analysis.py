from datetime import datetime
from typing import Literal

from pydantic import JsonValue
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from common.models.base import Base
from common.schemas.common import Config, Status


class AnalysisBatch(Base):
    __tablename__ = "backfills"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspace_state.id"), nullable=False)
    config: Mapped[Config] = mapped_column(String, nullable=False)
    record_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    watermark: Mapped[int] = mapped_column(Integer, nullable=False)
    cancelled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class AnalysisJob(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("record_id", "run", name="uq_job_run"),
        UniqueConstraint("record_id", "request_identity", name="uq_job_request_identity"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspace_state.id"), nullable=False)
    record_id: Mapped[str] = mapped_column(ForeignKey("feedback.id"), nullable=False)
    config: Mapped[Config] = mapped_column(String, nullable=False)
    run: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    request_identity: Mapped[str | None] = mapped_column(String)
    origin: Mapped[Literal["live", "backfill", "analysis"]] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False, default="deterministic-rules/1")
    batch_id: Mapped[str | None] = mapped_column(ForeignKey("backfills.id"))
    status: Mapped[Status] = mapped_column(String, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    error: Mapped[str | None] = mapped_column(Text)


Index(
    "uq_job_legacy_config",
    AnalysisJob.record_id,
    AnalysisJob.config,
    unique=True,
    postgresql_where=AnalysisJob.origin != "analysis",
)


class AnalysisResult(Base):
    __tablename__ = "enrichments"
    __table_args__ = (UniqueConstraint("record_id", "run", name="uq_output_run"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspace_state.id"), nullable=False)
    record_id: Mapped[str] = mapped_column(ForeignKey("feedback.id"), nullable=False)
    config: Mapped[Config] = mapped_column(String, nullable=False)
    run: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    payload: Mapped[dict[str, JsonValue]] = mapped_column(JSON, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
