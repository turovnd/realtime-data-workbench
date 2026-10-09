import asyncio
import logging
from collections.abc import Mapping

from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.deterministic import generate_demo
from workbench.logic.enrichment import Generate, enrich
from workbench.logic.errors import TerminalProviderError
from workbench.repositories.jobs import claim_job, finish_job
from workbench.repositories.usage import reserve_live_call

logger = logging.getLogger("workbench.worker")


async def process_one(
    engine: AsyncEngine,
    *,
    generate: Generate = generate_demo,
    lease_seconds: int = 30,
    timeout_seconds: float = 10,
    generators: Mapping[str, Generate] | None = None,
    live_budget: int = 0,
) -> bool:
    claim = await claim_job(engine, lease_seconds)
    if claim is None:
        return False
    try:
        selected = generate if generators is None else generators.get(claim.provider)
        if selected is None:
            raise TerminalProviderError("Selected provider is not configured")
        if claim.provider.startswith("openrouter/") and not await reserve_live_call(
            engine, live_budget
        ):
            await finish_job(
                engine, claim, None, "Live provider call budget exhausted", retryable=False
            )
            return True
        async with asyncio.timeout(timeout_seconds):
            result = await enrich(claim.text, claim.config, generate=selected)
        stored = await finish_job(engine, claim, result)
        logger.info("job=%s fence=%s stored=%s", claim.id, claim.fence, stored)
    except (TimeoutError, ConnectionError) as exc:
        await finish_job(engine, claim, None, type(exc).__name__, retryable=True)
    except TerminalProviderError as exc:
        await finish_job(engine, claim, None, str(exc), retryable=False)
    except ValueError:
        await finish_job(
            engine,
            claim,
            None,
            "Provider output failed schema or evidence validation",
            retryable=False,
        )
    return True
