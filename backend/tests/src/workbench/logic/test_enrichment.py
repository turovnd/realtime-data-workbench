import json

import pytest

from workbench.infrastructure.deterministic import generate_demo
from workbench.logic.enrichment import FeedbackGenerator, enrich
from workbench.logic.errors import TerminalProviderError
from workbench.logic.synthetic import synthetic_inputs
from workbench.schemas.providers import GenerationRequest, GenerationResult


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

    with pytest.raises(TerminalProviderError, match="^Provider output exceeds 8192 characters"):
        await enrich("source", "v1", generate=generate)


async def test_cyrillic_limits_count_characters_without_relaxing_the_schema() -> None:
    source = "Ё" * 200
    payload = {
        "topic": "other",
        "intent": "unclear",
        "summary": "Я" * 240,
        "evidence": [source],
    }

    async def generate(_text: str, _config: str) -> str:
        return json.dumps(payload, ensure_ascii=False)

    result = await enrich(source, "v2", generate=generate)
    assert result.summary == payload["summary"]
    assert result.evidence == [source]


@pytest.mark.parametrize(
    "changed_field",
    [
        {"summary": "Я" * 241},
        {"evidence": ["Ё" * 201]},
        {"evidence": []},
        {"evidence": ["Ё"] * 4},
        {"topic": "другое"},
        {"PRIVATE_FIELD_MARKER\njob=spoofed": "PRIVATE_PROVIDER_MARKER"},
    ],
    ids=[
        "long-summary",
        "long-quote",
        "no-quotes",
        "too-many-quotes",
        "translated-enum",
        "extra-field",
    ],
)
async def test_invalid_multilingual_output_remains_bounded_and_errors_are_safe(
    changed_field: dict[str, object],
) -> None:
    source = "Ё" * 201
    payload = {
        "topic": "other",
        "intent": "unclear",
        "summary": "Краткое описание",
        "evidence": ["Ё"],
        **changed_field,
    }

    async def generate(_text: str, _config: str) -> str:
        return json.dumps(payload, ensure_ascii=False)

    with pytest.raises(
        TerminalProviderError, match="^Provider output schema validation failed"
    ) as error:
        await enrich(source, "v2", generate=generate)
    assert "PRIVATE_PROVIDER_MARKER" not in str(error.value)
    assert "PRIVATE_FIELD_MARKER" not in str(error.value)
    assert "job=spoofed" not in str(error.value)
    assert source not in str(error.value)
    assert "Я" * 241 not in str(error.value)


async def test_cyrillic_quote_is_not_normalized_to_a_different_source() -> None:
    source = "Отчёт ещё не готов — подождите."

    async def generate(_text: str, _config: str) -> str:
        return json.dumps(
            {
                "topic": "other",
                "intent": "unclear",
                "summary": "Ожидание отчёта.",
                "evidence": ["Отчет еще не готов"],
            }
        )

    with pytest.raises(TerminalProviderError, match="^Provider evidence validation failed"):
        await enrich(source, "v1", generate=generate)


class RecordingModel:
    def __init__(self, output: str) -> None:
        self.output = output
        self.requests: list[GenerationRequest] = []

    async def complete(self, request: GenerationRequest) -> GenerationResult:
        self.requests.append(request)
        return GenerationResult(content=self.output)


async def test_feedback_generation_can_use_an_independent_typed_model_client() -> None:
    model = RecordingModel(
        '{"topic":"other","intent":"unclear","summary":"Observation","evidence":["source"]}'
    )
    result = await enrich("source", "v2", generate=FeedbackGenerator(model))
    assert result.evidence == ["source"]
    assert len(model.requests) == 1
    assert json.loads(model.requests[0].source) == {"source_feedback": "source"}


@pytest.mark.parametrize("source", ["", " \n", "x" * 4001])
async def test_invalid_source_never_reaches_the_model(source: str) -> None:
    model = RecordingModel("{}")
    with pytest.raises(TerminalProviderError, match="Source feedback must contain"):
        await FeedbackGenerator(model)(source, "v1")
    assert model.requests == []
