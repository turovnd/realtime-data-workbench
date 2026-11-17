"""Durable analysis admission, leases and fenced completion."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import ceil
from uuid import uuid4

from sqlalchemy import and_, case, func, or_, true, update
from sqlalchemy.orm import Session

from common.logic.errors import ConflictError
from common.models import AnalysisJob, AnalysisResult, Feedback, Workspace
from common.repositories.coordination import changed, lock_workspace
from common.schemas.common import Config
from common.schemas.enrichment import Enrichment

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


def find_analysis_request(session: Session, record_id: str, identity: str) -> bool:
    return bool(
        session.query(AnalysisJob.id)
        .filter(AnalysisJob.record_id == record_id, AnalysisJob.request_identity == identity)
        .scalar()
    )


def enqueue(
    session: Session,
    record_id: str,
    config: Config,
    origin: str,
    batch_id: str | None = None,
    workspace_id: str = "test",
    provider: str = "deterministic-rules/1",
    request_identity: str | None = None,
) -> None:
    latest = (
        session.query(func.max(AnalysisJob.run)).filter(AnalysisJob.record_id == record_id).scalar()
    )
    active = (
        session.query(AnalysisJob.id)
        .filter(AnalysisJob.record_id == record_id, AnalysisJob.status.in_(["queued", "leased"]))
        .limit(1)
        .scalar()
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


def expire_exhausted(session: Session, now: datetime) -> None:
    workspaces = set(
        session.scalars(
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
        session.query(Workspace).filter(Workspace.id.in_(workspaces)).update(
            {Workspace.cursor: Workspace.cursor + 1}
        )


def claim_job(
    session: Session, lease_seconds: int = 30, *, job_id: str | None = None
) -> Claim | None:
    lock_workspace(session)
    now = datetime.now(UTC)
    expire_exhausted(session, now)
    active = (
        session.query(func.count())
        .select_from(AnalysisJob)
        .filter(AnalysisJob.status == "leased", AnalysisJob.lease_until > now)
        .scalar()
    )
    if (active or 0) >= MAX_ACTIVE_JOBS:
        return None
    candidate = (
        session.query(AnalysisJob, Feedback.text)
        .join(Feedback, Feedback.id == AnalysisJob.record_id)
        .filter(
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
        .first()
    )
    if candidate is None:
        return None
    job, source = candidate
    job.status = "leased"
    job.fence += 1
    job.attempts += 1
    job.lease_until = now + timedelta(seconds=lease_seconds)
    job.error = None
    changed(session, job.workspace_id)
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


def retry_delay(session: Session, job_id: str) -> int | None:
    """Queue acknowledgement follows durable state, not delivery count."""
    job = session.get(AnalysisJob, job_id)
    if job is None or job.status not in {"queued", "leased"}:
        return None
    due_at = job.lease_until if job.status == "leased" else job.available_at
    seconds = (due_at - datetime.now(UTC)).total_seconds() if due_at else 0
    return min(60, max(5, ceil(seconds)))


def pending_job_ids(
    session: Session,
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
    query = session.query(AnalysisJob.id).filter(AnalysisJob.status.in_(["queued", "leased"]))
    if workspace_id is not None:
        query = query.filter(AnalysisJob.workspace_id == workspace_id)
    if record_ids is not None:
        query = query.filter(AnalysisJob.record_id.in_(record_ids))
    if identities is not None:
        query = query.join(Feedback, Feedback.id == AnalysisJob.record_id).filter(
            Feedback.identity.in_(identities)
        )
    if batch_id is not None:
        query = query.filter(AnalysisJob.batch_id == batch_id)
    if job_ids is not None:
        query = query.filter(AnalysisJob.id.in_(job_ids))
    if after is not None:
        query = query.filter(AnalysisJob.id > after)
    if due_only:
        query = query.filter(
            or_(
                and_(AnalysisJob.status == "queued", AnalysisJob.available_at <= now),
                and_(AnalysisJob.status == "leased", AnalysisJob.lease_until <= now),
            )
        )
    return [row[0] for row in query.order_by(AnalysisJob.id).limit(min(limit, 100)).all()]


def finish_job(
    session: Session,
    claim: Claim,
    result: Enrichment | None,
    error: str | None = None,
    retryable: bool = True,
) -> bool:
    lock_workspace(session)
    now = datetime.now(UTC)
    job = (
        session.query(AnalysisJob)
        .filter(
            AnalysisJob.id == claim.id,
            AnalysisJob.status == "leased",
            AnalysisJob.fence == claim.fence,
            AnalysisJob.lease_until > now,
        )
        .with_for_update()
        .one_or_none()
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
    changed(session, claim.workspace_id)
    return True


def retry_job(session: Session, job_id: str, workspace_id: str = "test") -> None:
    lock_workspace(session)
    job = (
        session.query(AnalysisJob)
        .filter(AnalysisJob.workspace_id == workspace_id, AnalysisJob.id == job_id)
        .one_or_none()
    )
    if job is None or job.status not in ("failed", "cancelled") or job.attempts >= MAX_ATTEMPTS:
        raise ConflictError("Only terminal jobs with remaining attempts can be retried")
    latest = (
        session.query(func.max(AnalysisJob.run))
        .filter(AnalysisJob.record_id == job.record_id)
        .scalar()
    )
    if job.run != latest:
        raise ConflictError("Only the latest analysis can be retried")
    active = (
        session.query(AnalysisJob.id)
        .filter(
            AnalysisJob.record_id == job.record_id, AnalysisJob.status.in_(["queued", "leased"])
        )
        .limit(1)
        .scalar()
    )
    if active:
        raise ConflictError("Analysis is already in progress for this feedback")
    job.status = "queued"
    job.available_at = datetime.now(UTC)
    job.error = None
    job.fence += 1
    changed(session, workspace_id)
