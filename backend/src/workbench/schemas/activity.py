from typing import Annotated, Literal

from pydantic import Field

from workbench.schemas.backfill_details import BatchItem
from workbench.schemas.backfills import BatchView
from workbench.schemas.common import StrictModel


class FeedbackActivity(StrictModel):
    kind: Literal["feedback"] = "feedback"
    id: str
    feedback: BatchItem


class BatchActivity(StrictModel):
    kind: Literal["batch"] = "batch"
    id: str
    batch: BatchView


ActivityItem = Annotated[FeedbackActivity | BatchActivity, Field(discriminator="kind")]


class ActivityPage(StrictModel):
    items: list[ActivityItem] = Field(max_length=50)
    next_cursor: str | None
    refresh_cursor: str = Field(description="Rehydrate the first page of this same frozen view")
    total: int = Field(ge=0, le=6000, description="Items in this frozen read window")
    has_older: bool = Field(
        description="Older stored activity exists beyond the latest 6000-item window"
    )
    revision: int
