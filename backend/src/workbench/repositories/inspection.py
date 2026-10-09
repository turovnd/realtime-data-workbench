from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.tables import batches, jobs, outputs, records, state
from workbench.repositories.coordination import lock_workspace
from workbench.schemas.backfills import BatchView
from workbench.schemas.enrichment import OutputView
from workbench.schemas.feedback import JobView, RecordView, Snapshot


async def snapshot(engine: AsyncEngine, workspace_id: str = "test") -> Snapshot:
    async with engine.begin() as conn:
        await lock_workspace(conn)
        cursor = int(
            await conn.scalar(
                select(state.c.cursor).where(state.c.id == workspace_id).with_for_update(read=True)
            )
            or 0
        )
        raw_rows = (
            (
                await conn.execute(
                    select(records)
                    .where(records.c.workspace_id == workspace_id)
                    .order_by(records.c.sequence.desc())
                )
            )
            .mappings()
            .all()
        )
        job_rows = (
            (
                await conn.execute(
                    select(jobs).where(jobs.c.workspace_id == workspace_id).order_by(jobs.c.config)
                )
            )
            .mappings()
            .all()
        )
        output_rows = (
            (
                await conn.execute(
                    select(outputs)
                    .where(outputs.c.workspace_id == workspace_id)
                    .order_by(outputs.c.config)
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
        views = [
            RecordView(
                id=str(row["id"]),
                sequence=int(row["sequence"]),
                text=str(row["text"]),
                channel=str(row["channel"]),
                ingested_at=row["ingested_at"].isoformat(),
                jobs=[
                    JobView.model_validate(
                        {
                            key: job[key]
                            for key in ("id", "config", "status", "attempts", "error", "origin")
                        }
                    )
                    for job in job_rows
                    if job["record_id"] == row["id"]
                ],
                outputs=[
                    OutputView.model_validate(
                        {
                            **output["payload"],
                            "config": output["config"],
                            "provider": output["provider"],
                            "created_at": output["created_at"].isoformat(),
                        }
                    )
                    for output in output_rows
                    if output["record_id"] == row["id"]
                ],
            )
            for row in raw_rows
        ]
        batch_views = []
        for batch in batch_rows:
            relevant = [
                job
                for job in job_rows
                if job["record_id"] in batch["record_ids"] and job["config"] == batch["config"]
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
