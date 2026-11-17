"""Durable analysis admission, leases and fenced completion."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import ceil
from uuid import uuid4

from sqlalchemy import and_, case, func, or_, select, true, update
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


async def expire_exhausted(session: AsyncSession, now: datetime) -> None:
    workspaces = set(
        await session.scalars(
            update(AnalysisJob)
            .where(
                AnalysisJob.status == "leased",
                AnalysisJob.lease_until <= now,
                AnalysisJob.attempts >= MAX_ATTEMPTS,
            )
            .values(status="failed", error="Lease expired after three attempts", lease_until=None)
            .returning(AnalysisJob.workspace_id)
        )
    )
    if workspaces:
        await session.execute(
            update(Workspace)
            .where(Workspace.id.in_(workspaces))
            .values(cursor=Workspace.cursor + 1)
        )


async def claim_job(
    engine: AsyncEngine, lease_seconds: int = 30, *, job_id: str | None = None
) -> Claim | None:
    async with session_scope(engine) as session:
        await lock_workspace(session)
        now = datetime.now(UTC)
        await expire_exhausted(session, now)
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
                    AnalysisJob.id == job_id if job_id is not None else true(),
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


async def retry_delay(engine: AsyncEngine, job_id: str) -> int | None:
    """Queue acknowledgement follows durable state, not delivery count."""
    async with session_scope(engine) as session:
        job = await session.get(AnalysisJob, job_id)
        if job is None or job.status not in {"queued", "leased"}:
            return None
        due_at = job.lease_until if job.status == "leased" else job.available_at
        seconds = (due_at - datetime.now(UTC)).total_seconds() if due_at else 0
        return min(60, max(5, ceil(seconds)))


async def pending_job_ids(
    engine: AsyncEngine,
    *,
    workspace_id: str | None = None,
    record_ids: list[str] | None = None,
    identities: list[str] | None = None,
    batch_id: str | None = None,
    job_ids: list[str] | None = None,
    after: str | None = None,
    limit: int = 100,
    due_only: bool = False,
) -> list[str]:
    """Read a bounded page of committed work; publishing never owns its lifecycle."""
    now = datetime.now(UTC)
    query = select(AnalysisJob.id).where(AnalysisJob.status.in_(["queued", "leased"]))
    if workspace_id is not None:
        query = query.where(AnalysisJob.workspace_id == workspace_id)
    if record_ids is not None:
        query = query.where(AnalysisJob.record_id.in_(record_ids))
    if identities is not None:
        query = query.join(Feedback, Feedback.id == AnalysisJob.record_id).where(
            Feedback.identity.in_(identities)
        )
    if batch_id is not None:
        query = query.where(AnalysisJob.batch_id == batch_id)
    if job_ids is not None:
        query = query.where(AnalysisJob.id.in_(job_ids))
    if after is not None:
        query = query.where(AnalysisJob.id > after)
    if due_only:
        query = query.where(
            or_(
                and_(AnalysisJob.status == "queued", AnalysisJob.available_at <= now),
                and_(AnalysisJob.status == "leased", AnalysisJob.lease_until <= now),
            )
        )
    async with session_scope(engine) as session:
        return list(await session.scalars(query.order_by(AnalysisJob.id).limit(min(limit, 100))))


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
