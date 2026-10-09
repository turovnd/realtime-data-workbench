from collections.abc import Awaitable, Callable

from workbench.schemas.common import Config
from workbench.schemas.enrichment import Enrichment

Generate = Callable[[str, Config], Awaitable[str]]


async def enrich(text: str, config: Config, *, generate: Generate) -> Enrichment:
    raw = await generate(text, config)
    if len(raw) > 8192:
        raise ValueError("Provider output exceeds 8192 characters")
    result = Enrichment.model_validate_json(raw)
    if any(not quote.strip() or quote not in text for quote in result.evidence):
        raise ValueError("Evidence must quote the immutable source exactly")
    return result
