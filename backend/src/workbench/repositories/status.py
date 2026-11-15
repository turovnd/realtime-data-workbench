"""Current feedback counts and recent batch progress for one workspace."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.database import session_scope
from workbench.models import AnalysisBatch, AnalysisJob, Feedback, Workspace
from workbench.repositories.backfills import batch_view
from workbench.repositories.coordination import lock_workspace
from workbench.schemas.feedback import FeedStatus


async def feed_status(engine: AsyncEngine, workspace_id: str, provider: str) -> FeedStatus:
    async with session_scope(engine) as session:
        await lock_workspace(session)
        revision = await session.scalar(
            select(Workspace.cursor).where(Workspace.id == workspace_id)
        )
        latest_job = (
            select(AnalysisJob.status)
            .where(AnalysisJob.record_id == Feedback.id)
            .order_by(AnalysisJob.run.desc())
            .limit(1)
            .scalar_subquery()
        )
        counts = (
            await session.execute(
                select(
                    func.count().label("received"),
                    func.max(Feedback.sequence).label("latest_sequence"),
                    func.count().filter(latest_job == "succeeded").label("enriched"),
                    func.count().filter(latest_job == "failed").label("failed"),
                )
                .select_from(Feedback)
                .where(Feedback.workspace_id == workspace_id)
            )
        ).one()
        batches = list(
            await session.scalars(
                select(AnalysisBatch)
                .where(AnalysisBatch.workspace_id == workspace_id)
                .order_by(AnalysisBatch.watermark.desc())
                .limit(10)
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
