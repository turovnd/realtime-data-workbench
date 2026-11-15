"""Frozen batch selections and their original processing results."""

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from workbench.models import AnalysisBatch, AnalysisJob, AnalysisResult, Feedback
from workbench.repositories.feedback import job_view, output_view
from workbench.schemas.backfill_details import BatchItem
from workbench.schemas.backfills import BatchView
from workbench.schemas.common import Config


async def selected_records(
    session: AsyncSession, workspace_id: str, ids: list[str]
) -> list[Feedback]:
    return list(
        await session.scalars(
            select(Feedback).where(Feedback.workspace_id == workspace_id, Feedback.id.in_(ids))
        )
    )


async def existing_jobs(session: AsyncSession, ids: list[str], config: Config) -> list[AnalysisJob]:
    return list(
        await session.scalars(
            select(AnalysisJob).where(
                AnalysisJob.record_id.in_(ids),
                AnalysisJob.config == config,
                AnalysisJob.origin != "analysis",
            )
        )
    )


async def insert_backfill(
    session: AsyncSession,
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


async def contains_backfill(session: AsyncSession, workspace_id: str, batch_id: str) -> bool:
    return bool(
        await session.scalar(
            select(AnalysisBatch.id).where(
                AnalysisBatch.workspace_id == workspace_id, AnalysisBatch.id == batch_id
            )
        )
    )


async def cancel_unfinished(session: AsyncSession, workspace_id: str, batch_id: str) -> None:
    # Fencing every unfinished child in the same transaction prevents late results
    # from a worker which already started an external call.
    await session.execute(
        update(AnalysisBatch)
        .where(AnalysisBatch.workspace_id == workspace_id, AnalysisBatch.id == batch_id)
        .values(cancelled=True)
    )
    await session.execute(
        update(AnalysisJob)
        .where(
            AnalysisJob.workspace_id == workspace_id,
            AnalysisJob.batch_id == batch_id,
            AnalysisJob.status.in_(["queued", "leased"]),
        )
        .values(status="cancelled", fence=AnalysisJob.fence + 1, lease_until=None)
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


async def get_backfill(
    session: AsyncSession, workspace_id: str, batch_id: str
) -> StoredBatch | None:
    batch = await session.scalar(
        select(AnalysisBatch).where(
            AnalysisBatch.workspace_id == workspace_id, AnalysisBatch.id == batch_id
        )
    )
    if batch is None:
        return None
    jobs = list(
        await session.scalars(
            select(AnalysisJob).where(
                AnalysisJob.workspace_id == workspace_id,
                AnalysisJob.record_id.in_(batch.record_ids),
                AnalysisJob.config == batch.config,
                AnalysisJob.origin != "analysis",
            )
        )
    )
    return StoredBatch(view=batch_view(batch, jobs), record_ids=batch.record_ids)


async def batch_items(
    session: AsyncSession, workspace_id: str, ids: list[str], config: Config
) -> list[BatchItem]:
    """Read exact historical batch results without a recent-history window."""
    if len(ids) > 50:
        raise ValueError("Batch detail pages are limited to 50 records")
    rows = await session.execute(
        select(Feedback, AnalysisJob, AnalysisResult)
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
        .where(Feedback.workspace_id == workspace_id, Feedback.id.in_(ids))
        .order_by(Feedback.sequence.desc())
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
