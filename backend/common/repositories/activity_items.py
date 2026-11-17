"""Hydrate one activity page using each job's exact result revision."""

from sqlalchemy import and_
from sqlalchemy.orm import Session

from common.models import AnalysisBatch, AnalysisJob, AnalysisResult, Feedback
from common.repositories.backfills import batch_view
from common.repositories.feedback import job_view, output_view
from common.schemas.activity import ActivityItem, BatchActivity, FeedbackActivity
from common.schemas.backfill_details import BatchItem


def hydrate_activity(
    session: Session, workspace_id: str, event_ids: list[str]
) -> list[ActivityItem]:
    if len(event_ids) > 50:
        raise ValueError("Activity pages are limited to 50 items")
    job_ids = [value.removeprefix("job:") for value in event_ids if value.startswith("job:")]
    indexed: dict[str, ActivityItem] = {}
    if job_ids:
        rows = (
            session.query(AnalysisJob, Feedback, AnalysisResult)
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
            .filter(
                AnalysisJob.workspace_id == workspace_id,
                AnalysisJob.id.in_(job_ids),
                AnalysisJob.origin.in_(["live", "analysis"]),
            )
            .all()
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
        batches = (
            session.query(AnalysisBatch)
            .filter(AnalysisBatch.workspace_id == workspace_id, AnalysisBatch.id.in_(batch_ids))
            .all()
        )
        selected_ids = {record_id for batch in batches for record_id in batch.record_ids}
        jobs = (
            session.query(AnalysisJob)
            .filter(
                AnalysisJob.workspace_id == workspace_id,
                AnalysisJob.record_id.in_(selected_ids),
                AnalysisJob.origin != "analysis",
            )
            .all()
        )
        for batch in batches:
            indexed["batch:" + batch.id] = BatchActivity(id=batch.id, batch=batch_view(batch, jobs))
    return [indexed[value] for value in event_ids if value in indexed]
