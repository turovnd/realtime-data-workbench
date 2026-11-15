"""OpenRouter's strict structured-output contract; no implicit provider fallback."""

from dataclasses import dataclass

import httpx
from pydantic import SecretStr

from workbench.infrastructure.chat_completions import request_completion
from workbench.schemas.providers import GenerationRequest, GenerationResult

CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"


@dataclass(frozen=True)
class OpenRouterClient:
    client: httpx.AsyncClient
    api_key: SecretStr
    model: str
    timeout_seconds: float
    max_tokens: int

    async def complete(self, request: GenerationRequest) -> GenerationResult:
        return await request_completion(
            self.client,
            endpoint=CHAT_COMPLETIONS_URL,
            api_key=self.api_key,
            timeout_seconds=self.timeout_seconds,
            payload={
                "model": self.model,
                "provider": {"require_parameters": True, "data_collection": "deny"},
                "temperature": 0,
                "max_tokens": self.max_tokens,
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
            },
        )
