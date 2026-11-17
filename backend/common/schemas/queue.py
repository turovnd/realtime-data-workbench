"""Small private queue contracts; customer text stays in PostgreSQL."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AnalysisMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: UUID


class MaintenanceMessage(BaseModel):
    # Schedules adds its own envelope fields alongside executionId.
    execution_id: str = Field(alias="executionId", min_length=1, max_length=200)
    after: UUID | None = None
