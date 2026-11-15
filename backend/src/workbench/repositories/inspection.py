from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.database import session_scope
from workbench.models import AnalysisBatch, AnalysisJob, Feedback, Workspace
from workbench.repositories.backfills import batch_view
from workbench.repositories.coordination import lock_workspace
from workbench.repositories.feedback import hydrate
from workbench.schemas.feedback import Snapshot


async def snapshot(engine: AsyncEngine, workspace_id: str = "test") -> Snapshot:
    async with session_scope(engine) as session:
        await lock_workspace(session)

        cursor = await session.scalar(
            select(Workspace.cursor).where(Workspace.id == workspace_id).with_for_update(read=True)
        )
        record_ids = list(
            await session.scalars(
                select(Feedback.id)
                .where(Feedback.workspace_id == workspace_id)
                .order_by(Feedback.sequence.desc())
            )
        )
        records = await hydrate(session, workspace_id, record_ids)
        jobs = list(
            await session.scalars(
                select(AnalysisJob).where(
                    AnalysisJob.workspace_id == workspace_id,
                    AnalysisJob.origin != "analysis",
                )
            )
        )
        batches = await session.scalars(
            select(AnalysisBatch).where(AnalysisBatch.workspace_id == workspace_id)
        )

        return Snapshot(
            workspace_id=workspace_id,
            cursor=cursor or 0,
            records=records,
            batches=[batch_view(batch, jobs) for batch in batches],
        )
