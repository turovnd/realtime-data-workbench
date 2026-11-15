import json

import httpx
import pytest
from pydantic import SecretStr

from workbench.logic.enrichment import enrich
from workbench.logic.errors import RetryableProviderError, TerminalProviderError
from workbench.schemas.common import Config
from workbench.settings import Settings
from workbench.workers.providers import build_generators, openrouter_generator


def live_settings() -> Settings:
    return Settings(
        openrouter_calls_enabled=True, openrouter_api_key=SecretStr("test-only-not-a-key")
    )


def completion(content: str, finish_reason: str = "stop") -> dict[str, object]:
    return {"choices": [{"message": {"content": content}, "finish_reason": finish_reason}]}


async def test_openrouter_sends_strict_schema_and_validates_evidence() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["provider"] == {"require_parameters": True, "data_collection": "deny"}
        assert body["response_format"]["json_schema"]["schema"]["additionalProperties"] is False
        assert body["model"] == "openai/gpt-4.1-mini" and body["max_tokens"] == 800
        assert body["messages"][0]["role"] == "system"
        result = {
            "topic": "other",
            "intent": "unclear",
            "summary": "Unclear source",
            "evidence": ["source"],
        }
        return httpx.Response(200, json=completion(json.dumps(result)))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await enrich(
            "source", "v1", generate=openrouter_generator(live_settings(), client)
        )
        assert result.evidence == ["source"]


@pytest.mark.parametrize(
    "status,exception",
    [
        (429, RetryableProviderError),
        (503, RetryableProviderError),
        (401, TerminalProviderError),
        (402, TerminalProviderError),
        (400, TerminalProviderError),
    ],
)
async def test_provider_failure_never_falls_back(status: int, exception: type[Exception]) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, text="sensitive upstream response must not be forwarded")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(exception) as error:
            await openrouter_generator(live_settings(), client)("source", "v1")
        assert "sensitive" not in str(error.value)


async def test_live_mode_requires_explicit_enablement() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        pytest.fail("Disabled provider must never call the network")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(TerminalProviderError):
            await openrouter_generator(Settings(), client)("source", "v1")


@pytest.mark.parametrize(
    "body", [completion("{}", "length"), completion("x" * 8193), {"bad": "schema"}]
)
async def test_provider_incomplete_and_invalid_outputs_are_rejected(
    body: dict[str, object],
) -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=body))
    ) as client:
        with pytest.raises(ValueError):
            await openrouter_generator(live_settings(), client)("source", "v1")


RUSSIAN_SOURCE = (
    "В Activity → View details теперь раскрываются сообщения, результаты конкретного запуска, "
    "статусы, модель, время и ошибки. Добавлены переход к отзыву и подгрузка списка."
)


@pytest.mark.parametrize("config", ["v1", "v2"])
@pytest.mark.parametrize("escaped_response", [False, True])
async def test_russian_feedback_and_normal_json_escapes_round_trip_unchanged(
    config: Config, escaped_response: bool
) -> None:
    result_payload = {
        "topic": "other",
        "intent": "unclear",
        "summary": "В Activity доступны результаты конкретного запуска и переход к отзыву.",
        "evidence": ["результаты конкретного запуска", "переход к отзыву и подгрузка списка"],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        source_message = body["messages"][1]["content"]
        assert json.loads(source_message) == {"source_feedback": RUSSIAN_SOURCE}
        # The model must see the actual source, not a second layer of Unicode escape text.
        assert RUSSIAN_SOURCE in source_message
        return httpx.Response(
            200, json=completion(json.dumps(result_payload, ensure_ascii=escaped_response))
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await enrich(
            RUSSIAN_SOURCE, config, generate=openrouter_generator(live_settings(), client)
        )
    assert result.summary == result_payload["summary"]
    assert result.evidence == result_payload["evidence"]


@pytest.mark.parametrize("config", ["v1", "v2"])
@pytest.mark.parametrize(
    "quote",
    [
        "теперь раскрываются".encode("unicode_escape").decode("ascii"),
        "results from the specific run",
        "В Activity -> View details",
    ],
    ids=["double-escaped-cyrillic", "translated-quote", "changed-punctuation"],
)
async def test_changed_russian_quotes_are_not_repaired_or_accepted(
    config: Config, quote: str
) -> None:
    result_payload = {
        "topic": "other",
        "intent": "unclear",
        "summary": "Описание возможностей Activity.",
        "evidence": [quote],
    }
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json=completion(json.dumps(result_payload)))
        )
    ) as client:
        with pytest.raises(
            TerminalProviderError, match="^Provider evidence validation failed"
        ) as error:
            await enrich(
                RUSSIAN_SOURCE, config, generate=openrouter_generator(live_settings(), client)
            )
    assert quote not in str(error.value)
    assert RUSSIAN_SOURCE not in str(error.value)


@pytest.mark.parametrize(
    "body",
    [
        b"PRIVATE_UPSTREAM_MARKER is not JSON",
        b'{"choices":[{"message":{"content":{"private":"PRIVATE_UPSTREAM_MARKER"}},"finish_reason":"stop"}]}',
    ],
)
async def test_invalid_provider_envelope_has_a_safe_terminal_reason(body: bytes) -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=body))
    ) as client:
        with pytest.raises(
            TerminalProviderError, match="^Provider response envelope validation failed"
        ) as error:
            await openrouter_generator(live_settings(), client)(RUSSIAN_SOURCE, "v2")
    assert "PRIVATE_UPSTREAM_MARKER" not in str(error.value)
    assert RUSSIAN_SOURCE not in str(error.value)


@pytest.mark.parametrize("enabled,configured", [(False, False), (False, True), (True, False)])
async def test_unavailable_live_provider_is_not_registered(enabled: bool, configured: bool) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        pytest.fail("Unavailable live provider must never call the network")

    settings = Settings(
        provider_mode="openrouter",
        openrouter_calls_enabled=enabled,
        openrouter_api_key=SecretStr("test-only-not-a-key") if configured else None,
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        generators = build_generators(settings, client)
        assert set(generators) == {"deterministic-rules/1"}
        assert generators.get(settings.provider_id) is None
        with pytest.raises(TerminalProviderError, match="disabled or not configured"):
            openrouter_generator(settings, client)


async def test_worker_composition_preserves_explicit_model_timeout_and_token_limit() -> None:
    settings = Settings(
        openrouter_calls_enabled=True,
        openrouter_api_key=SecretStr("test-only-not-a-key"),
        openrouter_model="configured/model",
        openrouter_max_tokens=456,
        provider_timeout_seconds=4.5,
    )

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["model"] == "configured/model"
        assert body["max_tokens"] == 456
        assert request.extensions["timeout"] == {
            "connect": 4.5,
            "read": 4.5,
            "write": 4.5,
            "pool": 4.5,
        }
        assert request.headers["Authorization"] == "Bearer test-only-not-a-key"
        return httpx.Response(200, json=completion("{}"))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        generators = build_generators(settings, client)
        assert set(generators) == {"deterministic-rules/1", "openrouter/configured/model"}
        assert await generators["openrouter/configured/model"]("source", "v2") == "{}"
