from typing import Annotated, Literal

from pydantic import Field

from common.schemas.common import Config, StrictModel, Topic

MAX_GENERATED_TEXT_LENGTH = 8192
MAX_SUMMARY_LENGTH = 240
MAX_EVIDENCE_LENGTH = 200
MIN_EVIDENCE_ITEMS = 1
MAX_EVIDENCE_ITEMS = 3


class Enrichment(StrictModel):
    topic: Topic
    intent: Literal["issue", "request", "praise", "unclear"]
    summary: str = Field(min_length=1, max_length=MAX_SUMMARY_LENGTH)
    evidence: list[Annotated[str, Field(min_length=1, max_length=MAX_EVIDENCE_LENGTH)]] = Field(
        min_length=MIN_EVIDENCE_ITEMS, max_length=MAX_EVIDENCE_ITEMS
    )


class OutputView(Enrichment):
    config: Config
    run: int = Field(ge=1, description="The completed job revision; previous outputs are retained")
    provider: str
    created_at: str
