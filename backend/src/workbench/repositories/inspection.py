from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.tables import batches, jobs, records, state
from workbench.repositories.coordination import lock_workspace
from workbench.repositories.feedback import hydrate
from workbench.schemas.backfills import BatchView
from workbench.schemas.feedback import Snapshot


async def snapshot(engine: AsyncEngine, workspace_id: str = "test") -> Snapshot:
    async with engine.begin() as conn:
        await lock_workspace(conn)
        cursor = int(
            await conn.scalar(
                select(state.c.cursor).where(state.c.id == workspace_id).with_for_update(read=True)
            )
            or 0
        )
        record_ids = list(
            (
                await conn.execute(
                    select(records.c.id)
                    .where(records.c.workspace_id == workspace_id)
                    .order_by(records.c.sequence.desc())
                )
            ).scalars()
        )
        views = await hydrate(conn, workspace_id, record_ids)
        job_rows = (
            (
                await conn.execute(
                    select(jobs).where(
                        jobs.c.workspace_id == workspace_id, jobs.c.origin != "analysis"
                    )
                )
            )
            .mappings()
            .all()
        )
        batch_rows = (
            (await conn.execute(select(batches).where(batches.c.workspace_id == workspace_id)))
            .mappings()
            .all()
        )
        batch_views = []
        for batch in batch_rows:
            relevant = [
                job
                for job in job_rows
                if job["record_id"] in batch["record_ids"]
                and job["config"] == batch["config"]
                and job["origin"] != "analysis"
            ]
            batch_views.append(
                BatchView(
                    id=str(batch["id"]),
                    config=batch["config"],
                    selected=len(batch["record_ids"]),
                    completed=sum(job["status"] == "succeeded" for job in relevant),
                    failed=sum(job["status"] == "failed" for job in relevant),
                    cancelled=bool(batch["cancelled"]),
                    watermark=int(batch["watermark"]),
                )
            )
        return Snapshot(
            workspace_id=workspace_id, cursor=cursor, records=views, batches=batch_views
        )
