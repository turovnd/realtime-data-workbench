"""Current feedback counts and recent batch progress for one workspace."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from common.models import AnalysisBatch, AnalysisJob, Feedback, Workspace
from common.repositories.backfills import batch_view
from common.repositories.coordination import lock_workspace
from common.schemas.feedback import FeedStatus


def feed_status(session: Session, workspace_id: str, provider: str) -> FeedStatus:
    lock_workspace(session)
    revision = session.query(Workspace.cursor).filter(Workspace.id == workspace_id).scalar()
    latest_job = (
        session.query(AnalysisJob.status)
        .filter(AnalysisJob.record_id == Feedback.id)
        .order_by(AnalysisJob.run.desc())
        .limit(1)
        .scalar_subquery()
    )
    counts = (
        session.query(
            func.count().label("received"),
            func.max(Feedback.sequence).label("latest_sequence"),
            func.count().filter(latest_job == "succeeded").label("enriched"),
            func.count().filter(latest_job == "failed").label("failed"),
        )
        .select_from(Feedback)
        .filter(Feedback.workspace_id == workspace_id)
        .one()
    )
    batches = (
        session.query(AnalysisBatch)
        .filter(AnalysisBatch.workspace_id == workspace_id)
        .order_by(AnalysisBatch.watermark.desc())
        .limit(10)
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
    return FeedStatus(
        workspace_id=workspace_id,
        revision=revision or 0,
        latest_sequence=counts.latest_sequence or 0,
        received=counts.received,
        enriched=counts.enriched,
        failed=counts.failed,
        batches=[batch_view(batch, jobs) for batch in batches],
        provider=provider,
    )
