"""Best-effort post-commit delivery; PostgreSQL remains the pending-work ledger."""

import asyncio
import logging
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncEngine
from vercel.queue import QueueClient

from common.infrastructure.database import run_transaction
from common.repositories.jobs import pending_job_ids
from common.settings import Settings

ANALYSIS_TOPIC = "feedback-analysis"
MAINTENANCE_TOPIC = "feedback-maintenance"
PAGE_SIZE = 100
logger = logging.getLogger("common.queue")


class Publisher(Protocol):
    async def send(
        self, topic: str, payload: dict[str, str], *, retention: int = 86400
    ) -> str | None: ...


class JobDispatcher:
    def __init__(
        self,
        engine: AsyncEngine,
        publisher: Publisher | None = None,
        *,
        timeout_seconds: float = 3,
    ) -> None:
        self.engine = engine
        self.publisher = publisher
        self.timeout_seconds = timeout_seconds

    async def notify(
        self,
        workspace_id: str,
        *,
        record_ids: list[str] | None = None,
        identities: list[str] | None = None,
        batch_id: str | None = None,
        job_ids: list[str] | None = None,
    ) -> None:
        """The caller has already committed; a handoff failure cannot undo acceptance."""
        if self.publisher is None:
            return
        try:
            async with asyncio.timeout(self.timeout_seconds):
                ids = await run_transaction(
                    self.engine,
                    pending_job_ids,
                    workspace_id=workspace_id,
                    record_ids=record_ids,
                    identities=identities,
                    batch_id=batch_id,
                    job_ids=job_ids,
                )
                await self.publish_jobs(ids)
        except Exception as exc:
            # SDK exceptions can contain headers/credentials. Log only the exception type.
            logger.warning("queue_handoff_failed type=%s", type(exc).__name__)

    async def publish_jobs(self, job_ids: list[str]) -> None:
        if self.publisher is None:
            raise RuntimeError("Queue publisher is not configured")
        publisher = self.publisher
        semaphore = asyncio.Semaphore(10)

        async def publish(job_id: str) -> None:
            async with semaphore:
                await publisher.send(ANALYSIS_TOPIC, {"job_id": job_id}, retention=86400)

        async with asyncio.TaskGroup() as tasks:
            for job_id in job_ids:
                tasks.create_task(publish(job_id))

    async def continue_recovery(self, execution_id: str, after: str) -> None:
        if self.publisher is None:
            raise RuntimeError("Queue publisher is not configured")
        await self.publisher.send(
            MAINTENANCE_TOPIC, {"executionId": execution_id, "after": after}, retention=86400
        )


def build_dispatcher(engine: AsyncEngine, settings: Settings) -> JobDispatcher:
    publisher = (
        QueueClient(region=settings.queue_region, timeout=3) if settings.queue_enabled else None
    )
    return JobDispatcher(engine, publisher)
