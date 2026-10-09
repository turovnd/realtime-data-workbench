from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.tables import batches, jobs, records, state
from workbench.repositories.coordination import lock_workspace
from workbench.schemas.backfills import BatchView
from workbench.schemas.feedback import FeedStatus


async def feed_status(engine: AsyncEngine, workspace_id: str, provider: str) -> FeedStatus:
    async with engine.begin() as conn:
        await lock_workspace(conn)
        revision = int(
            await conn.scalar(select(state.c.cursor).where(state.c.id == workspace_id)) or 0
        )
        latest_job = (
            select(jobs.c.status)
            .where(jobs.c.record_id == records.c.id)
            .order_by(jobs.c.config.desc())
            .limit(1)
            .scalar_subquery()
        )
        counts = (
            await conn.execute(
                select(
                    func.count(),
                    func.max(records.c.sequence),
                    func.count().filter(latest_job == "succeeded"),
                    func.count().filter(latest_job == "failed"),
                )
                .select_from(records)
                .where(records.c.workspace_id == workspace_id)
            )
        ).one()
        batch_rows = (
            (
                await conn.execute(
                    select(batches)
                    .where(batches.c.workspace_id == workspace_id)
                    .order_by(batches.c.watermark.desc())
                    .limit(10)
                )
            )
            .mappings()
            .all()
        )
        batch_views = []
        for batch in batch_rows:
            progress = (
                (
                    await conn.execute(
                        select(jobs.c.status).where(
                            jobs.c.workspace_id == workspace_id,
                            jobs.c.record_id.in_(batch["record_ids"]),
                            jobs.c.config == batch["config"],
                        )
                    )
                )
                .scalars()
                .all()
            )
            batch_views.append(
                BatchView(
                    id=str(batch["id"]),
                    config=batch["config"],
                    selected=len(batch["record_ids"]),
                    completed=progress.count("succeeded"),
                    failed=progress.count("failed"),
                    cancelled=bool(batch["cancelled"]),
                    watermark=int(batch["watermark"]),
                )
            )
        return FeedStatus(
            workspace_id=workspace_id,
            revision=revision,
            latest_sequence=int(counts[1] or 0),
            received=int(counts[0]),
            enriched=int(counts[2]),
            failed=int(counts[3]),
            batches=batch_views,
            provider=provider,
        )
