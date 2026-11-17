import asyncio
import logging
from collections.abc import Mapping

from sqlalchemy.ext.asyncio import AsyncEngine

from common.infrastructure.database import run_transaction
from common.infrastructure.deterministic import generate_demo
from common.logic.enrichment import Generate, enrich
from common.logic.errors import TerminalProviderError
from common.repositories.jobs import claim_job, finish_job, retry_delay
from common.repositories.usage import reserve_live_call

logger = logging.getLogger("modules.worker")


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
    claim = await run_transaction(engine, claim_job, lease_seconds, job_id=job_id)
    if claim is None:
        return False
    try:
        selected = generators.get(claim.provider) if generators is not None else generate
        if selected is None and generators is None and claim.provider == "deterministic-rules/1":
            selected = generate_demo
        if selected is None:
            raise TerminalProviderError("Selected provider is not configured")
        if claim.provider != "deterministic-rules/1" and not await run_transaction(
            engine, reserve_live_call, live_budget, claim.provider.partition("/")[0]
        ):
            await run_transaction(
                engine,
                finish_job,
                claim,
                None,
                "Live provider call budget exhausted",
                retryable=False,
            )
            return True
        async with asyncio.timeout(timeout_seconds):
            result = await enrich(claim.text, claim.config, generate=selected)
        stored = await run_transaction(engine, finish_job, claim, result)
        logger.info("job=%s fence=%s stored=%s", claim.id, claim.fence, stored)
    except (TimeoutError, ConnectionError) as exc:
        await run_transaction(engine, finish_job, claim, None, type(exc).__name__, retryable=True)
    except TerminalProviderError as exc:
        logger.warning("job=%s provider_failure=%s", claim.id, str(exc))
        await run_transaction(engine, finish_job, claim, None, str(exc), retryable=False)
    except ValueError:
        await run_transaction(
            engine,
            finish_job,
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
    return await run_transaction(engine, retry_delay, job_id)
