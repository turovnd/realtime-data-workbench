from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import and_, case, func, insert, or_, select, update
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from workbench.infrastructure.tables import jobs, outputs, records, state
from workbench.logic.errors import ConflictError
from workbench.repositories.coordination import changed, lock_workspace
from workbench.schemas.common import Config
from workbench.schemas.enrichment import Enrichment


@dataclass(frozen=True)
class Claim:
    id: str
    record_id: str
    text: str
    config: Config
    fence: int
    attempts: int
    workspace_id: str
    provider: str


async def enqueue(
    conn: AsyncConnection,
    record_id: str,
    config: Config,
    origin: str,
    batch_id: str | None = None,
    workspace_id: str = "test",
    provider: str = "deterministic-rules/1",
) -> None:
    await conn.execute(
        insert(jobs).values(
            id=str(uuid4()),
            workspace_id=workspace_id,
            record_id=record_id,
            config=config,
            origin=origin,
            provider=provider,
            batch_id=batch_id,
            status="queued",
            attempts=0,
            fence=0,
            available_at=datetime.now(UTC),
            error=None,
        )
    )


async def claim_job(engine: AsyncEngine, lease_seconds: int = 30) -> Claim | None:
    async with engine.begin() as conn:
        await lock_workspace(conn)
        now = datetime.now(UTC)
        exhausted = await conn.execute(
            update(jobs)
            .where(jobs.c.status == "leased", jobs.c.lease_until <= now, jobs.c.attempts >= 3)
            .values(status="failed", error="Lease expired after three attempts", lease_until=None)
        )
        if exhausted.rowcount:
            await conn.execute(update(state).values(cursor=state.c.cursor + 1))
        active = int(
            await conn.scalar(
                select(func.count())
                .select_from(jobs)
                .where(jobs.c.status == "leased", jobs.c.lease_until > now)
            )
            or 0
        )
        if active >= 2:
            return None
        row = (
            (
                await conn.execute(
                    select(jobs, records.c.text)
                    .join(records, records.c.id == jobs.c.record_id)
                    .where(
                        jobs.c.attempts < 3,
                        or_(
                            and_(jobs.c.status == "queued", jobs.c.available_at <= now),
                            and_(jobs.c.status == "leased", jobs.c.lease_until <= now),
                        ),
                    )
                    .order_by(
                        case((jobs.c.origin == "live", 0), else_=1), jobs.c.available_at, jobs.c.id
                    )
                    .with_for_update(skip_locked=True)
                    .limit(1)
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        fence, attempts = int(row["fence"]) + 1, int(row["attempts"]) + 1
        await conn.execute(
            update(jobs)
            .where(jobs.c.id == row["id"])
            .values(
                status="leased",
                fence=fence,
                attempts=attempts,
                lease_until=now + timedelta(seconds=lease_seconds),
                error=None,
            )
        )
        await changed(conn, str(row["workspace_id"]))
        config: Config = "v2" if row["config"] == "v2" else "v1"
        return Claim(
            str(row["id"]),
            str(row["record_id"]),
            str(row["text"]),
            config,
            fence,
            attempts,
            str(row["workspace_id"]),
            str(row["provider"]),
        )


async def finish_job(
    engine: AsyncEngine,
    claim: Claim,
    result: Enrichment | None,
    error: str | None = None,
    retryable: bool = True,
) -> bool:
    async with engine.begin() as conn:
        await lock_workspace(conn)
        now = datetime.now(UTC)
        current = await conn.scalar(
            select(jobs.c.id).where(
                jobs.c.id == claim.id,
                jobs.c.status == "leased",
                jobs.c.fence == claim.fence,
                jobs.c.lease_until > now,
            )
        )
        if not current:
            return False
        if result is not None:
            await conn.execute(
                insert(outputs).values(
                    id=str(uuid4()),
                    workspace_id=claim.workspace_id,
                    record_id=claim.record_id,
                    config=claim.config,
                    payload=result.model_dump(),
                    provider=claim.provider,
                    created_at=now,
                )
            )
        status = (
            "succeeded" if result else ("queued" if retryable and claim.attempts < 3 else "failed")
        )
        await conn.execute(
            update(jobs)
            .where(jobs.c.id == claim.id)
            .values(
                status=status,
                lease_until=None,
                error=error,
                available_at=now + timedelta(seconds=2**claim.attempts),
            )
        )
        await changed(conn, claim.workspace_id)
        return True


async def retry_job(engine: AsyncEngine, job_id: str, workspace_id: str = "test") -> None:
    async with engine.begin() as conn:
        await lock_workspace(conn)
        job = (
            (
                await conn.execute(
                    select(jobs).where(jobs.c.workspace_id == workspace_id, jobs.c.id == job_id)
                )
            )
            .mappings()
            .first()
        )
        if not job or job["status"] not in ("failed", "cancelled") or job["attempts"] >= 3:
            raise ConflictError("Only terminal jobs with remaining attempts can be retried")
        await conn.execute(
            update(jobs)
            .where(jobs.c.workspace_id == workspace_id, jobs.c.id == job_id)
            .values(
                status="queued", available_at=datetime.now(UTC), error=None, fence=jobs.c.fence + 1
            )
        )
        await changed(conn, workspace_id)
