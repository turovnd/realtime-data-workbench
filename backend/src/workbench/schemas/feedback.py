from typing import Literal

from pydantic import Field, field_validator

from workbench.schemas.backfills import BatchView
from workbench.schemas.common import Config, Status, StrictModel
from workbench.schemas.enrichment import OutputView


class FeedbackInput(StrictModel):
    identity: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=4000)
    channel: Literal["Support", "In-app", "Community"]

    @field_validator("text", "identity")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value must not be blank")
        if "\x00" in value:
            raise ValueError("Value must not contain a null character")
        return value


class SimulationInput(StrictModel):
    request_id: str = Field(pattern=r"^[a-zA-Z0-9-]{1,64}$")
    count: int = Field(default=12, ge=1, le=12)


class JobView(StrictModel):
    id: str
    config: Config
    run: int = Field(ge=1, description="Monotonic analysis revision within this feedback")
    provider: str
    status: Status
    attempts: int
    error: str | None
    origin: Literal["live", "backfill", "analysis"]


class RecordView(StrictModel):
    id: str
    sequence: int
    text: str
    channel: str
    ingested_at: str
    jobs: list[JobView] = Field(
        max_length=10, description="The latest ten jobs, ordered by increasing run"
    )
    outputs: list[OutputView] = Field(
        max_length=10, description="The latest ten successful outputs, ordered by increasing run"
    )


class Snapshot(StrictModel):
    workspace_id: str
    cursor: int
    records: list[RecordView]
    batches: list[BatchView]
    mode: Literal["server", "browser-demo"] = "server"


class FeedFilters(StrictModel):
    q: str = Field(default="", max_length=100)
    status: Literal["all", "queued", "leased", "succeeded", "failed", "cancelled"] = "all"
    topic: Literal["all", "reliability", "usability", "billing", "performance", "other"] = "all"


class FeedPage(StrictModel):
    workspace_id: str
    records: list[RecordView]
    next_cursor: str | None = Field(
        description="Opaque continuation token, or null when this frozen view is exhausted"
    )
    refresh_cursor: str = Field(
        description="Refresh the first page of this same frozen view without changing membership"
    )
    watermark: int = Field(description="Highest source sequence when this view opened")
    revision: int
    total: int = Field(description="Number of records matching the frozen view")


class FeedStatus(StrictModel):
    workspace_id: str
    revision: int
    latest_sequence: int
    received: int
    enriched: int
    failed: int
    batches: list[BatchView]
    provider: str


class SimulationCreated(StrictModel):
    inserted: int = Field(ge=0, le=12, description="Number of newly inserted immutable records")
