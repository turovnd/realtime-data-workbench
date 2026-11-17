from pydantic import Field

from common.schemas.common import Channel, StrictModel
from common.schemas.enrichment import Enrichment


class DemoFeedback(StrictModel):
    text: str = Field(min_length=1, max_length=4000)
    channel: Channel
    analysis: Enrichment
