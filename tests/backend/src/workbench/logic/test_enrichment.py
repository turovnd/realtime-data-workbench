import json

import pytest

from workbench.infrastructure.deterministic import generate_demo
from workbench.logic.enrichment import enrich
from workbench.logic.synthetic import synthetic_inputs


async def test_demo_is_repeatable_and_quotes_source() -> None:
    value = synthetic_inputs("seed", 1)[0]
    result = await enrich(value.text, "v1", generate=generate_demo)
    assert result == await enrich(value.text, "v1", generate=generate_demo)
    assert result.evidence[0] in value.text
    assert result.topic == "reliability"


@pytest.mark.parametrize(
    "payload",
    [
        {"topic": "other", "intent": "unclear", "summary": "x", "evidence": ["invented"]},
        {"topic": "invented", "intent": "unclear", "summary": "x", "evidence": ["source"]},
        {"topic": "other", "intent": "unclear", "summary": 4, "evidence": ["source"]},
    ],
)
async def test_provider_output_is_untrusted(payload: dict[str, object]) -> None:
    async def generate(_text: str, _config: str) -> str:
        return json.dumps(payload)

    with pytest.raises(ValueError):
        await enrich("source", "v1", generate=generate)


async def test_oversized_provider_response_is_rejected() -> None:
    async def generate(_text: str, _config: str) -> str:
        return " " * 8193

    with pytest.raises(ValueError, match="8192"):
        await enrich("source", "v1", generate=generate)
