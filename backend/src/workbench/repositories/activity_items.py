"""Hydrate one activity page using each job's exact result revision."""

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from workbench.models import AnalysisBatch, AnalysisJob, AnalysisResult, Feedback
from workbench.repositories.backfills import batch_view
from workbench.repositories.feedback import job_view, output_view
from workbench.schemas.activity import ActivityItem, BatchActivity, FeedbackActivity
from workbench.schemas.backfill_details import BatchItem


async def hydrate_activity(
    session: AsyncSession, workspace_id: str, event_ids: list[str]
) -> list[ActivityItem]:
    if len(event_ids) > 50:
        raise ValueError("Activity pages are limited to 50 items")
    job_ids = [value.removeprefix("job:") for value in event_ids if value.startswith("job:")]
    indexed: dict[str, ActivityItem] = {}
    if job_ids:
        rows = await session.execute(
            select(AnalysisJob, Feedback, AnalysisResult)
            .join(
                Feedback,
                and_(Feedback.id == AnalysisJob.record_id, Feedback.workspace_id == workspace_id),
            )
            .outerjoin(
                AnalysisResult,
                and_(
                    AnalysisResult.record_id == AnalysisJob.record_id,
                    AnalysisResult.run == AnalysisJob.run,
                    AnalysisResult.workspace_id == workspace_id,
                ),
            )
            .where(
                AnalysisJob.workspace_id == workspace_id,
                AnalysisJob.id.in_(job_ids),
                AnalysisJob.origin.in_(["live", "analysis"]),
            )
        )
        for job, feedback, output in rows:
            indexed["job:" + job.id] = FeedbackActivity(
                id=job.id,
                feedback=BatchItem(
                    record_id=feedback.id,
                    sequence=feedback.sequence,
                    text=feedback.text,
                    channel=feedback.channel,
                    job=job_view(job),
                    output=output_view(output) if output is not None else None,
                ),
            )
    batch_ids = [value.removeprefix("batch:") for value in event_ids if value.startswith("batch:")]
    if batch_ids:
        batches = list(
            await session.scalars(
                select(AnalysisBatch).where(
                    AnalysisBatch.workspace_id == workspace_id,
                    AnalysisBatch.id.in_(batch_ids),
                )
            )
        )
        selected_ids = {record_id for batch in batches for record_id in batch.record_ids}
        jobs = list(
            await session.scalars(
                select(AnalysisJob).where(
                    AnalysisJob.workspace_id == workspace_id,
                    AnalysisJob.record_id.in_(selected_ids),
                    AnalysisJob.origin != "analysis",
                )
            )
        )
        for batch in batches:
            indexed["batch:" + batch.id] = BatchActivity(id=batch.id, batch=batch_view(batch, jobs))
    return [indexed[value] for value in event_ids if value in indexed]
