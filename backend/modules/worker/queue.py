"""Private Vercel subscribers: event-driven processing with bounded recovery scans."""

import asyncio
import logging
from datetime import UTC, datetime

import httpx
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncEngine
from vercel.queue import RetryAfter, subscribe

from common.infrastructure.database import create_engine, run_transaction, session_scope
from common.infrastructure.queue import (
    ANALYSIS_TOPIC,
    MAINTENANCE_TOPIC,
    PAGE_SIZE,
    JobDispatcher,
    build_dispatcher,
)
from common.repositories.coordination import lock_workspace
from common.repositories.jobs import expire_exhausted, pending_job_ids
from common.repositories.retention import cleanup_expired
from common.schemas.queue import AnalysisMessage, MaintenanceMessage
from common.settings import Settings
from modules.worker.processing import process_job
from modules.worker.providers import build_generators

logger = logging.getLogger("common.queue")


async def recover_pending(
    engine: AsyncEngine, dispatcher: JobDispatcher, request: MaintenanceMessage
) -> int:
    async with session_scope(engine) as session:
        await session.run_sync(lock_workspace)
        await session.run_sync(cleanup_expired)
        await session.run_sync(expire_exhausted, datetime.now(UTC))

    ids = await run_transaction(
        engine,
        pending_job_ids,
        after=str(request.after) if request.after else None,
        limit=PAGE_SIZE,
        due_only=True,
    )
    await dispatcher.publish_jobs(ids)
    if len(ids) == PAGE_SIZE:
        await dispatcher.continue_recovery(request.execution_id, ids[-1])
    return len(ids)


@subscribe(
    topic=ANALYSIS_TOPIC,
    consumer_group="feedback-analysis-worker",
    retry_after=5,
    max_concurrency=2,
    max_attempts=20,
)
async def process_analysis(payload: dict[str, object]) -> None:
    try:
        request = AnalysisMessage.model_validate(payload)
    except ValidationError:
        logger.warning("invalid_analysis_message")
        return

    settings = Settings()
    engine = create_engine(settings.database_url, pooled=False)
    try:
        async with httpx.AsyncClient() as client:
            delay = await process_job(
                engine,
                str(request.job_id),
                lease_seconds=settings.lease_seconds,
                timeout_seconds=settings.provider_timeout_seconds,
                generators=build_generators(settings, client),
                live_budget=settings.live_call_budget,
            )
        if delay is not None:
            raise RetryAfter(delay)
    finally:
        await engine.dispose()


@subscribe(
    topic=MAINTENANCE_TOPIC,
    consumer_group="feedback-maintenance-worker",
    retry_after=30,
    max_concurrency=1,
    max_attempts=5,
)
async def reconcile(payload: dict[str, object]) -> None:
    try:
        request = MaintenanceMessage.model_validate(payload)
    except ValidationError:
        logger.warning("invalid_maintenance_message")
        return

    settings = Settings()
    engine = create_engine(settings.database_url, pooled=False)
    try:
        async with asyncio.timeout(45):
            count = await recover_pending(engine, build_dispatcher(engine, settings), request)
        logger.info("queue_recovery_published count=%s", count)
    except Exception as exc:
        logger.warning("queue_recovery_failed type=%s", type(exc).__name__)
        raise RetryAfter(30) from None
    finally:
        await engine.dispose()
