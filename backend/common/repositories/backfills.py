"""Frozen batch selections and their original processing results."""

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import and_
from sqlalchemy.orm import Session

from common.models import AnalysisBatch, AnalysisJob, AnalysisResult, Feedback
from common.repositories.feedback import job_view, output_view
from common.schemas.backfill_details import BatchItem
from common.schemas.backfills import BatchView
from common.schemas.common import Config


def selected_records(session: Session, workspace_id: str, ids: list[str]) -> list[Feedback]:
    return (
        session.query(Feedback)
        .filter(Feedback.workspace_id == workspace_id, Feedback.id.in_(ids))
        .all()
    )


def existing_jobs(session: Session, ids: list[str], config: Config) -> list[AnalysisJob]:
    return (
        session.query(AnalysisJob)
        .filter(
            AnalysisJob.record_id.in_(ids),
            AnalysisJob.config == config,
            AnalysisJob.origin != "analysis",
        )
        .all()
    )


def insert_backfill(
    session: Session,
    workspace_id: str,
    batch_id: str,
    ids: list[str],
    config: Config,
    watermark: int,
) -> None:
    session.add(
        AnalysisBatch(
            id=batch_id,
            workspace_id=workspace_id,
            config=config,
            record_ids=ids,
            watermark=watermark,
            cancelled=False,
        )
    )


def contains_backfill(session: Session, workspace_id: str, batch_id: str) -> bool:
    return bool(
        session.query(AnalysisBatch.id)
        .filter(AnalysisBatch.workspace_id == workspace_id, AnalysisBatch.id == batch_id)
        .scalar()
    )


def cancel_unfinished(session: Session, workspace_id: str, batch_id: str) -> None:
    # Fencing every unfinished child in the same transaction prevents late results
    # from a worker which already started an external call.
    session.query(AnalysisBatch).filter(
        AnalysisBatch.workspace_id == workspace_id, AnalysisBatch.id == batch_id
    ).update({AnalysisBatch.cancelled: True})
    session.query(AnalysisJob).filter(
        AnalysisJob.workspace_id == workspace_id,
        AnalysisJob.batch_id == batch_id,
        AnalysisJob.status.in_(["queued", "leased"]),
    ).update(
        {
            AnalysisJob.status: "cancelled",
            AnalysisJob.fence: AnalysisJob.fence + 1,
            AnalysisJob.lease_until: None,
        }
    )


@dataclass(frozen=True)
class StoredBatch:
    view: BatchView
    record_ids: list[str]


def batch_view(batch: AnalysisBatch, jobs: Sequence[AnalysisJob]) -> BatchView:
    selected = set(batch.record_ids)
    progress = [
        job.status
        for job in jobs
        if job.workspace_id == batch.workspace_id
        and job.record_id in selected
        and job.config == batch.config
        and job.origin != "analysis"
    ]
    return BatchView(
        id=batch.id,
        config=batch.config,
        selected=len(batch.record_ids),
        completed=progress.count("succeeded"),
        failed=progress.count("failed"),
        cancelled=batch.cancelled,
        watermark=batch.watermark,
    )


def get_backfill(session: Session, workspace_id: str, batch_id: str) -> StoredBatch | None:
    batch = (
        session.query(AnalysisBatch)
        .filter(AnalysisBatch.workspace_id == workspace_id, AnalysisBatch.id == batch_id)
        .one_or_none()
    )
    if batch is None:
        return None
    jobs = (
        session.query(AnalysisJob)
        .filter(
            AnalysisJob.workspace_id == workspace_id,
            AnalysisJob.record_id.in_(batch.record_ids),
            AnalysisJob.config == batch.config,
            AnalysisJob.origin != "analysis",
        )
        .all()
    )
    return StoredBatch(view=batch_view(batch, jobs), record_ids=batch.record_ids)


def batch_items(
    session: Session, workspace_id: str, ids: list[str], config: Config
) -> list[BatchItem]:
    """Read exact historical batch results without a recent-history window."""
    if len(ids) > 50:
        raise ValueError("Batch detail pages are limited to 50 records")
    rows = (
        session.query(Feedback, AnalysisJob, AnalysisResult)
        .outerjoin(
            AnalysisJob,
            and_(
                AnalysisJob.record_id == Feedback.id,
                AnalysisJob.workspace_id == workspace_id,
                AnalysisJob.config == config,
                AnalysisJob.origin != "analysis",
            ),
        )
        .outerjoin(
            AnalysisResult,
            and_(
                AnalysisResult.record_id == Feedback.id,
                AnalysisResult.workspace_id == workspace_id,
                AnalysisResult.run == AnalysisJob.run,
                AnalysisResult.config == AnalysisJob.config,
            ),
        )
        .filter(Feedback.workspace_id == workspace_id, Feedback.id.in_(ids))
        .order_by(Feedback.sequence.desc())
        .all()
    )
    return [
        BatchItem(
            record_id=feedback.id,
            sequence=feedback.sequence,
            text=feedback.text,
            channel=feedback.channel,
            job=job_view(job) if job is not None else None,
            output=output_view(output) if output is not None else None,
        )
        for feedback, job, output in rows
    ]
