"""Curated examples used by temporary demo workspaces and local simulations."""

from pathlib import Path

from pydantic import TypeAdapter

from common.schemas.demo import DemoFeedback
from common.schemas.feedback import FeedbackInput

SAMPLES = TypeAdapter(list[DemoFeedback]).validate_json(
    (Path(__file__).resolve().parents[1] / "fixtures" / "feedback.json").read_bytes()
)


def synthetic_inputs(request_id: str, count: int, *, offset: int = 0) -> list[FeedbackInput]:
    return [
        FeedbackInput(
            identity=f"{request_id}:{index}",
            text=SAMPLES[(offset + index) % len(SAMPLES)].text,
            channel=SAMPLES[(offset + index) % len(SAMPLES)].channel,
        )
        for index in range(count)
    ]
