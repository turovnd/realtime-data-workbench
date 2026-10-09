from pydantic import Field

from workbench.schemas.common import Config, StrictModel


class BackfillInput(StrictModel):
    record_ids: list[str] = Field(min_length=1, max_length=100)
    config: Config = "v2"


class BatchView(StrictModel):
    id: str
    config: Config
    selected: int
    completed: int
    failed: int
    cancelled: bool
    watermark: int


class BackfillCreated(StrictModel):
    id: str = Field(description="Identifier of the persisted fixed-selection backfill")
