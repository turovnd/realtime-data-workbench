import asyncio
import json
import logging
from collections.abc import AsyncIterator, Callable

import httpx
import pytest
from pydantic import SecretStr

from workbench.infrastructure.deepseek import DeepSeekClient
from workbench.infrastructure.openrouter import OpenRouterClient
from workbench.logic.enrichment import ModelClient
from workbench.logic.errors import RetryableProviderError, TerminalProviderError
from workbench.schemas.providers import GenerationRequest


@pytest.fixture(params=["openrouter", "deepseek"])
def model_client(request: pytest.FixtureRequest) -> Callable[[httpx.AsyncClient], ModelClient]:
    factory = DeepSeekClient if request.param == "deepseek" else OpenRouterClient

    def make(client: httpx.AsyncClient) -> ModelClient:
        return factory(
            client,
            api_key=SecretStr("PRIVATE_API_KEY"),
            model="test/model",
            timeout_seconds=0.1,
            max_tokens=800,
        )

    return make


def generation_request() -> GenerationRequest:
    return GenerationRequest(
        instructions="PRIVATE_SYSTEM_INSTRUCTION",
        source="PRIVATE_SOURCE_TEXT",
        schema_name="test_output",
        output_schema={"type": "object", "additionalProperties": False},
    )


@pytest.mark.parametrize("failure", ["timeout", "connection", "429", "503"])
async def test_retryable_failure_performs_one_request_and_exposes_no_upstream_data(
    failure: str,
    model_client: Callable[[httpx.AsyncClient], ModelClient],
) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if failure == "timeout":
            raise httpx.ReadTimeout("PRIVATE_UPSTREAM_MARKER", request=request)
        if failure == "connection":
            raise httpx.ConnectError("PRIVATE_UPSTREAM_MARKER", request=request)
        return httpx.Response(int(failure), text="PRIVATE_UPSTREAM_MARKER")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(RetryableProviderError) as error:
            await model_client(client).complete(generation_request())
    assert calls == 1
    assert "PRIVATE" not in str(error.value)


class Chunks(httpx.AsyncByteStream):
    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks
        self.read = 0
        self.closed = False

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for chunk in self.chunks:
            self.read += 1
            yield chunk

    async def aclose(self) -> None:
        self.closed = True


async def test_oversized_body_stops_reading_and_closes_the_response(
    model_client: Callable[[httpx.AsyncClient], ModelClient],
) -> None:
    body = Chunks([b"x" * 32768, b"x" * 32769, b"never read"])
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, stream=body))
    ) as client:
        with pytest.raises(TerminalProviderError, match="^Provider response exceeds 64 KiB"):
            await model_client(client).complete(generation_request())
    assert body.read == 2
    assert body.closed


async def test_body_at_exact_limit_is_accepted(
    model_client: Callable[[httpx.AsyncClient], ModelClient],
) -> None:
    envelope = json.dumps(
        {"choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}]}
    ).encode()
    body = envelope + b" " * (65536 - len(envelope))
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=body))
    ) as client:
        assert (await model_client(client).complete(generation_request())).content == "{}"


async def test_optional_usage_is_typed_and_logs_never_include_request_or_response_text(
    caplog: pytest.LogCaptureFixture,
    model_client: Callable[[httpx.AsyncClient], ModelClient],
) -> None:
    caplog.set_level(logging.INFO, logger="workbench.infrastructure.chat_completions")
    envelope = {
        "choices": [{"message": {"content": "PRIVATE_OUTPUT"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 7},
        "model": "PRIVATE_MODEL\nspoofed=true",
        "id": "PRIVATE_RESPONSE_ID",
    }
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=envelope))
    ) as client:
        result = await model_client(client).complete(generation_request())
    assert result.prompt_tokens == 12 and result.completion_tokens == 7
    assert result.content == "PRIVATE_OUTPUT"
    assert "elapsed_ms=" in caplog.text
    assert "prompt_tokens=12 completion_tokens=7" in caplog.text
    assert "PRIVATE" not in caplog.text
    assert "spoofed" not in caplog.text


@pytest.mark.parametrize("tokens", ["12", -1, 10_000_001, True])
async def test_usage_cannot_inject_log_text_or_unbounded_values(
    tokens: object,
    model_client: Callable[[httpx.AsyncClient], ModelClient],
) -> None:
    envelope = {
        "choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": tokens},
    }
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=envelope))
    ) as client:
        with pytest.raises(TerminalProviderError, match="envelope validation failed"):
            await model_client(client).complete(generation_request())


async def test_total_deadline_bounds_a_response_that_keeps_sending_chunks(
    model_client: Callable[[httpx.AsyncClient], ModelClient],
) -> None:
    class SlowBody(httpx.AsyncByteStream):
        closed = False

        async def __aiter__(self) -> AsyncIterator[bytes]:
            while True:
                await asyncio.sleep(0.02)
                yield b" "

        async def aclose(self) -> None:
            self.closed = True

    body = SlowBody()
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, stream=body))
    ) as client:
        with pytest.raises(RetryableProviderError, match="timed out"):
            await model_client(client).complete(generation_request())
    assert body.closed


async def test_redirects_are_not_followed_even_when_the_http_client_allows_them(
    model_client: Callable[[httpx.AsyncClient], ModelClient],
) -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(307, headers={"Location": "https://untrusted.invalid/"})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), follow_redirects=True
    ) as client:
        with pytest.raises(TerminalProviderError, match="rejected the request \(307\)"):
            await model_client(client).complete(generation_request())
    assert calls == 1
