from sqlalchemy import Table, func, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncConnection

from workbench.infrastructure.tables import jobs, outputs, records
from workbench.schemas.enrichment import OutputView
from workbench.schemas.feedback import JobView, RecordView


async def _recent_history(
    conn: AsyncConnection, table: Table, workspace_id: str, ids: list[str]
) -> list[RowMapping]:
    ranked = (
        select(
            table,
            func.row_number()
            .over(partition_by=table.c.record_id, order_by=table.c.run.desc())
            .label("position"),
        )
        .where(table.c.workspace_id == workspace_id, table.c.record_id.in_(ids))
        .subquery()
    )
    return list(
        (
            await conn.execute(select(ranked).where(ranked.c.position <= 10).order_by(ranked.c.run))
        ).mappings()
    )


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
    job_rows = await _recent_history(conn, jobs, workspace_id, ids)
    output_rows = await _recent_history(conn, outputs, workspace_id, ids)
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
                        for key in (
                            "id",
                            "config",
                            "run",
                            "provider",
                            "status",
                            "attempts",
                            "error",
                            "origin",
                        )
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
                        "run": output["run"],
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
