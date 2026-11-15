"""Bounded HTTP and envelope validation shared by the two completion APIs."""

import asyncio
import logging
from time import monotonic

import httpx
from pydantic import SecretStr, ValidationError

from workbench.logic.errors import RetryableProviderError, TerminalProviderError
from workbench.schemas.providers import Completion, GenerationResult

logger = logging.getLogger(__name__)
MAX_RESPONSE_BYTES = 64 * 1024


async def request_completion(
    client: httpx.AsyncClient,
    *,
    endpoint: str,
    api_key: SecretStr,
    payload: dict[str, object],
    timeout_seconds: float,
) -> GenerationResult:
    started = monotonic()
    try:
        async with asyncio.timeout(timeout_seconds):
            body = await read_response(
                client,
                endpoint=endpoint,
                api_key=api_key,
                payload=payload,
                timeout_seconds=timeout_seconds,
            )
    except TimeoutError:
        raise RetryableProviderError("Provider request timed out") from None
    finally:
        logger.info("event=provider_request elapsed_ms=%d", (monotonic() - started) * 1000)

    try:
        completion = Completion.model_validate_json(body)
    except ValidationError:
        raise TerminalProviderError("Provider response envelope validation failed") from None
    if completion.choices[0].finish_reason != "stop":
        raise TerminalProviderError("Provider response was incomplete or refused")
    usage = completion.usage
    result = GenerationResult(
        content=completion.choices[0].message.content,
        prompt_tokens=usage.prompt_tokens if usage else None,
        completion_tokens=usage.completion_tokens if usage else None,
    )
    logger.info(
        "event=provider_completion prompt_tokens=%s completion_tokens=%s",
        result.prompt_tokens,
        result.completion_tokens,
    )
    return result


async def read_response(
    client: httpx.AsyncClient,
    *,
    endpoint: str,
    api_key: SecretStr,
    payload: dict[str, object],
    timeout_seconds: float,
) -> bytes:
    try:
        async with client.stream(
            "POST",
            endpoint,
            json=payload,
            headers={"Authorization": f"Bearer {api_key.get_secret_value()}"},
            timeout=timeout_seconds,
            follow_redirects=False,
        ) as response:
            if response.status_code == 429 or response.status_code >= 500:
                raise RetryableProviderError(
                    f"Provider temporarily unavailable ({response.status_code})"
                )
            if response.status_code != 200:
                raise TerminalProviderError(
                    f"Provider rejected the request ({response.status_code})"
                )
            body = bytearray()
            async for chunk in response.aiter_bytes():
                if len(body) + len(chunk) > MAX_RESPONSE_BYTES:
                    raise TerminalProviderError("Provider response exceeds 64 KiB")
                body.extend(chunk)
            return bytes(body)
    except httpx.TimeoutException:
        raise RetryableProviderError("Provider request timed out") from None
    except httpx.TransportError:
        raise RetryableProviderError("Provider connection failed") from None
