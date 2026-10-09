import json

import httpx
import pytest
from pydantic import SecretStr

from workbench.infrastructure.providers import openrouter_generator
from workbench.logic.enrichment import enrich
from workbench.logic.errors import RetryableProviderError, TerminalProviderError
from workbench.settings import Settings


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
