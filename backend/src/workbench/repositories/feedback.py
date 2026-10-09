from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection

from workbench.infrastructure.tables import jobs, outputs, records
from workbench.schemas.enrichment import OutputView
from workbench.schemas.feedback import JobView, RecordView


async def hydrate(conn: AsyncConnection, workspace_id: str, ids: list[str]) -> list[RecordView]:
    raw = (
        (
            await conn.execute(
                select(records)
                .where(records.c.workspace_id == workspace_id, records.c.id.in_(ids))
                .order_by(records.c.sequence.desc())
            )
        )
        .mappings()
        .all()
    )
    job_rows = (
        (
            await conn.execute(
                select(jobs)
                .where(jobs.c.workspace_id == workspace_id, jobs.c.record_id.in_(ids))
                .order_by(jobs.c.config)
            )
        )
        .mappings()
        .all()
    )
    output_rows = (
        (
            await conn.execute(
                select(outputs)
                .where(outputs.c.workspace_id == workspace_id, outputs.c.record_id.in_(ids))
                .order_by(outputs.c.config)
            )
        )
        .mappings()
        .all()
    )
    return [
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
        for row in raw
    ]
