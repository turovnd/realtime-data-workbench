"""Durable analysis admission, leases and fenced completion."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import and_, case, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from workbench.infrastructure.database import session_scope
from workbench.logic.errors import ConflictError
from workbench.models import AnalysisJob, AnalysisResult, Feedback, Workspace
from workbench.repositories.coordination import changed, lock_workspace
from workbench.schemas.common import Config
from workbench.schemas.enrichment import Enrichment

MAX_ATTEMPTS = 3
MAX_ACTIVE_JOBS = 2


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
    run: int


async def find_analysis_request(session: AsyncSession, record_id: str, identity: str) -> bool:
    return bool(
        await session.scalar(
            select(AnalysisJob.id).where(
                AnalysisJob.record_id == record_id, AnalysisJob.request_identity == identity
            )
        )
    )


async def enqueue(
    session: AsyncSession,
    record_id: str,
    config: Config,
    origin: str,
    batch_id: str | None = None,
    workspace_id: str = "test",
    provider: str = "deterministic-rules/1",
    request_identity: str | None = None,
) -> None:
    latest = await session.scalar(
        select(func.max(AnalysisJob.run)).where(AnalysisJob.record_id == record_id)
    )
    active = await session.scalar(
        select(AnalysisJob.id)
        .where(AnalysisJob.record_id == record_id, AnalysisJob.status.in_(["queued", "leased"]))
        .limit(1)
    )
    if active:
        raise ConflictError("Analysis is already in progress for this feedback")
    session.add(
        AnalysisJob(
            id=str(uuid4()),
            workspace_id=workspace_id,
            record_id=record_id,
            config=config,
            run=(latest or 0) + 1,
            request_identity=request_identity,
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
    async with session_scope(engine) as session:
        await lock_workspace(session)
        now = datetime.now(UTC)
        exhausted_workspaces = set(
            await session.scalars(
                update(AnalysisJob)
                .where(
                    AnalysisJob.status == "leased",
                    AnalysisJob.lease_until <= now,
                    AnalysisJob.attempts >= MAX_ATTEMPTS,
                )
                .values(
                    status="failed", error="Lease expired after three attempts", lease_until=None
                )
                .returning(AnalysisJob.workspace_id)
            )
        )
        if exhausted_workspaces:
            await session.execute(
                update(Workspace)
                .where(Workspace.id.in_(exhausted_workspaces))
                .values(cursor=Workspace.cursor + 1)
            )
        active = await session.scalar(
            select(func.count())
            .select_from(AnalysisJob)
            .where(AnalysisJob.status == "leased", AnalysisJob.lease_until > now)
        )
        if (active or 0) >= MAX_ACTIVE_JOBS:
            return None
        candidate = (
            await session.execute(
                select(AnalysisJob, Feedback.text)
                .join(Feedback, Feedback.id == AnalysisJob.record_id)
                .where(
                    AnalysisJob.attempts < MAX_ATTEMPTS,
                    or_(
                        and_(AnalysisJob.status == "queued", AnalysisJob.available_at <= now),
                        and_(AnalysisJob.status == "leased", AnalysisJob.lease_until <= now),
                    ),
                )
                .order_by(
                    case((AnalysisJob.origin.in_(["live", "analysis"]), 0), else_=1),
                    AnalysisJob.available_at,
                    AnalysisJob.id,
                )
                .with_for_update(skip_locked=True, of=AnalysisJob)
                .limit(1)
            )
        ).first()
        if candidate is None:
            return None
        job, source = candidate
        job.status = "leased"
        job.fence += 1
        job.attempts += 1
        job.lease_until = now + timedelta(seconds=lease_seconds)
        job.error = None
        await changed(session, job.workspace_id)
        return Claim(
            id=job.id,
            record_id=job.record_id,
            text=source,
            config=job.config,
            fence=job.fence,
            attempts=job.attempts,
            workspace_id=job.workspace_id,
            provider=job.provider,
            run=job.run,
        )


async def finish_job(
    engine: AsyncEngine,
    claim: Claim,
    result: Enrichment | None,
    error: str | None = None,
    retryable: bool = True,
) -> bool:
    async with session_scope(engine) as session:
        await lock_workspace(session)
        now = datetime.now(UTC)
        job = await session.scalar(
            select(AnalysisJob)
            .where(
                AnalysisJob.id == claim.id,
                AnalysisJob.status == "leased",
                AnalysisJob.fence == claim.fence,
                AnalysisJob.lease_until > now,
            )
            .with_for_update()
        )
        if job is None:
            return False
        if result is not None:
            session.add(
                AnalysisResult(
                    id=str(uuid4()),
                    workspace_id=claim.workspace_id,
                    record_id=claim.record_id,
                    config=claim.config,
                    run=claim.run,
                    payload=result.model_dump(),
                    provider=claim.provider,
                    created_at=now,
                )
            )
            job.status = "succeeded"
        else:
            job.status = "queued" if retryable and claim.attempts < MAX_ATTEMPTS else "failed"
        job.lease_until = None
        job.error = error
        job.available_at = now + timedelta(seconds=2**claim.attempts)
        await changed(session, claim.workspace_id)
        return True


async def retry_job(engine: AsyncEngine, job_id: str, workspace_id: str = "test") -> None:
    async with session_scope(engine) as session:
        await lock_workspace(session)
        job = await session.scalar(
            select(AnalysisJob).where(
                AnalysisJob.workspace_id == workspace_id, AnalysisJob.id == job_id
            )
        )
        if job is None or job.status not in ("failed", "cancelled") or job.attempts >= MAX_ATTEMPTS:
            raise ConflictError("Only terminal jobs with remaining attempts can be retried")
        latest = await session.scalar(
            select(func.max(AnalysisJob.run)).where(AnalysisJob.record_id == job.record_id)
        )
        if job.run != latest:
            raise ConflictError("Only the latest analysis can be retried")
        active = await session.scalar(
            select(AnalysisJob.id)
            .where(
                AnalysisJob.record_id == job.record_id,
                AnalysisJob.status.in_(["queued", "leased"]),
            )
            .limit(1)
        )
        if active:
            raise ConflictError("Analysis is already in progress for this feedback")
        job.status = "queued"
        job.available_at = datetime.now(UTC)
        job.error = None
        job.fence += 1
        await changed(session, workspace_id)
