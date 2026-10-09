from typing import Annotated, Literal

from pydantic import Field

from workbench.schemas.common import Config, StrictModel, Topic


class Enrichment(StrictModel):
    topic: Topic
    intent: Literal["issue", "request", "praise", "unclear"]
    summary: str = Field(min_length=1, max_length=240)
    evidence: list[Annotated[str, Field(min_length=1, max_length=200)]] = Field(
        min_length=1, max_length=3
    )


class OutputView(Enrichment):
    config: Config
    provider: str
    created_at: str
