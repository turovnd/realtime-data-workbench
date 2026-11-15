"""One bounded OpenRouter request; durable retries belong to the worker."""

import logging
from time import monotonic

import httpx
from pydantic import SecretStr, ValidationError

from workbench.logic.errors import RetryableProviderError, TerminalProviderError
from workbench.schemas.providers import Completion, GenerationRequest, GenerationResult

logger = logging.getLogger(__name__)

CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_RESPONSE_BYTES = 64 * 1024


class OpenRouterClient:
    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        api_key: SecretStr,
        model: str,
        timeout_seconds: float,
        max_tokens: int,
    ) -> None:
        self._client = client
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._max_tokens = max_tokens

    async def complete(self, request: GenerationRequest) -> GenerationResult:
        payload = {
            "model": self._model,
            "provider": {"require_parameters": True, "data_collection": "deny"},
            "temperature": 0,
            "max_tokens": self._max_tokens,
            "messages": [
                {"role": "system", "content": request.instructions},
                {"role": "user", "content": request.source},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": request.schema_name,
                    "strict": True,
                    "schema": request.output_schema,
                },
            },
        }
        started = monotonic()
        try:
            body = await self._request(payload)
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

    async def _request(self, payload: dict[str, object]) -> bytes:
        try:
            async with self._client.stream(
                "POST",
                CHAT_COMPLETIONS_URL,
                json=payload,
                headers={"Authorization": f"Bearer {self._api_key.get_secret_value()}"},
                timeout=self._timeout_seconds,
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
