import asyncio
import logging
from collections.abc import Mapping

from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.deterministic import generate_demo
from workbench.logic.enrichment import Generate, enrich
from workbench.logic.errors import TerminalProviderError
from workbench.repositories.jobs import claim_job, finish_job, retry_delay
from workbench.repositories.usage import reserve_live_call

logger = logging.getLogger("workbench.worker")


async def process_one(
    engine: AsyncEngine,
    *,
    generate: Generate | None = None,
    lease_seconds: int = 30,
    timeout_seconds: float = 10,
    generators: Mapping[str, Generate] | None = None,
    live_budget: int | None = 0,
    job_id: str | None = None,
) -> bool:
    claim = await claim_job(engine, lease_seconds, job_id=job_id)
    if claim is None:
        return False
    try:
        selected = generators.get(claim.provider) if generators is not None else generate
        if selected is None and generators is None and claim.provider == "deterministic-rules/1":
            selected = generate_demo
        if selected is None:
            raise TerminalProviderError("Selected provider is not configured")
        if claim.provider != "deterministic-rules/1" and not await reserve_live_call(
            engine, live_budget, claim.provider.partition("/")[0]
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
        logger.warning("job=%s provider_failure=%s", claim.id, str(exc))
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


async def process_job(
    engine: AsyncEngine,
    job_id: str,
    *,
    lease_seconds: int = 30,
    timeout_seconds: float = 10,
    generators: Mapping[str, Generate] | None = None,
    live_budget: int | None = 0,
) -> int | None:
    """Process exactly one queued ID, then tell its delivery whether to retry."""
    await process_one(
        engine,
        job_id=job_id,
        lease_seconds=lease_seconds,
        timeout_seconds=timeout_seconds,
        generators=generators,
        live_budget=live_budget,
    )
    return await retry_delay(engine, job_id)
