from collections.abc import Awaitable, Callable

from pydantic import ValidationError

from workbench.logic.errors import TerminalProviderError
from workbench.schemas.common import Config
from workbench.schemas.enrichment import Enrichment

Generate = Callable[[str, Config], Awaitable[str]]


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

    if len(raw) > 8192:
        raise TerminalProviderError("Provider output exceeds 8192 characters")

    try:
        result = Enrichment.model_validate_json(raw)
    except ValidationError as exc:
        raise _schema_failure(exc) from exc

    if any(not quote.strip() or quote not in text for quote in result.evidence):
        raise TerminalProviderError(
            "Provider evidence validation failed: quotes must match the original message exactly"
        )

    return result
