"""Direct DeepSeek JSON output; domain validation still belongs to enrichment."""

import json
from dataclasses import dataclass

import httpx
from pydantic import SecretStr

from workbench.infrastructure.chat_completions import request_completion
from workbench.schemas.providers import GenerationRequest, GenerationResult

CHAT_COMPLETIONS_URL = "https://api.deepseek.com/chat/completions"


def system_instructions(request: GenerationRequest) -> str:
    schema = json.dumps(request.output_schema, ensure_ascii=False, separators=(",", ":"))
    return f"{request.instructions}\nReturn a JSON object matching this JSON schema:\n{schema}"


@dataclass(frozen=True)
class DeepSeekClient:
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
                "temperature": 0,
                "max_tokens": self.max_tokens,
                "thinking": {"type": "disabled"},
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system_instructions(request)},
                    {"role": "user", "content": request.source},
                ],
            },
        )
