from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol

from pydantic import ValidationError

from common.logic.errors import TerminalProviderError
from common.logic.prompts import feedback_request
from common.schemas.common import Config
from common.schemas.enrichment import MAX_GENERATED_TEXT_LENGTH, Enrichment
from common.schemas.feedback import MAX_FEEDBACK_LENGTH
from common.schemas.providers import GenerationRequest, GenerationResult

Generate = Callable[[str, Config], Awaitable[str]]


class ModelClient(Protocol):
    async def complete(self, request: GenerationRequest) -> GenerationResult: ...


@dataclass(frozen=True)
class FeedbackGenerator:
    client: ModelClient

    async def __call__(self, text: str, config: Config) -> str:
        if not text.strip() or len(text) > MAX_FEEDBACK_LENGTH:
            raise TerminalProviderError(
                f"Source feedback must contain 1–{MAX_FEEDBACK_LENGTH} characters"
            )
        result = await self.client.complete(feedback_request(text, config))
        return result.content


def _schema_failure(error: ValidationError) -> TerminalProviderError:
    fields = {"topic", "intent", "summary", "evidence"}
    kinds = {
        "json_invalid",
        "model_type",
        "missing",
        "extra_forbidden",
        "literal_error",
        "string_type",
        "string_too_short",
        "string_too_long",
        "list_type",
        "too_short",
        "too_long",
    }
    details = set()

    for issue in error.errors(include_input=False, include_context=False, include_url=False):
        location = issue["loc"][0] if issue["loc"] else "output"
        field = location if location in fields else "output"
        kind = issue["type"] if issue["type"] in kinds else "invalid"
        details.add(f"{field}: {kind}")

    return TerminalProviderError(
        f"Provider output schema validation failed ({'; '.join(sorted(details))})"
    )


async def enrich(text: str, config: Config, *, generate: Generate) -> Enrichment:
    raw = await generate(text, config)

    if len(raw) > MAX_GENERATED_TEXT_LENGTH:
        raise TerminalProviderError(
            f"Provider output exceeds {MAX_GENERATED_TEXT_LENGTH} characters"
        )

    try:
        result = Enrichment.model_validate_json(raw)
    except ValidationError as exc:
        raise _schema_failure(exc) from None

    if any(not quote.strip() or quote not in text for quote in result.evidence):
        raise TerminalProviderError(
            "Provider evidence validation failed: quotes must match the original message exactly"
        )

    return result
