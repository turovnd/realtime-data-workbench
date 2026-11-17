from pydantic import Field

from common.schemas.backfills import BatchView
from common.schemas.common import StrictModel
from common.schemas.enrichment import OutputView
from common.schemas.feedback import JobView


class BatchItem(StrictModel):
    record_id: str
    sequence: int
    text: str
    channel: str
    job: JobView | None = Field(
        description="Original target-configuration job; later individual analyses are excluded"
    )
    output: OutputView | None = Field(
        description="Completed output of that exact job run, or null if none was stored"
    )


class BatchPage(StrictModel):
    batch: BatchView
    items: list[BatchItem] = Field(max_length=50)
    next_cursor: str | None = Field(
        description="Signed continuation for this workspace/batch, or null at the end"
    )
