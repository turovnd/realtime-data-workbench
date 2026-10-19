"""Hydrate only one activity page, preserving each job's exact result revision."""

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncConnection

from workbench.infrastructure.tables import jobs, outputs, records
from workbench.repositories.backfills import get_backfill
from workbench.schemas.activity import ActivityItem, BatchActivity, FeedbackActivity
from workbench.schemas.backfill_details import BatchItem
from workbench.schemas.enrichment import OutputView
from workbench.schemas.feedback import JobView


async def hydrate_activity(
    conn: AsyncConnection, workspace_id: str, event_ids: list[str]
) -> list[ActivityItem]:
    if len(event_ids) > 50:
        raise ValueError("Activity pages are limited to 50 items")
    job_ids = [value.removeprefix("job:") for value in event_ids if value.startswith("job:")]
    rows = (
        (
            await conn.execute(
                select(
                    jobs,
                    records.c.sequence,
                    records.c.text,
                    records.c.channel,
                    outputs.c.payload.label("output_payload"),
                    outputs.c.provider.label("output_provider"),
                    outputs.c.created_at.label("output_created_at"),
                )
                .join(
                    records,
                    and_(records.c.id == jobs.c.record_id, records.c.workspace_id == workspace_id),
                )
                .outerjoin(
                    outputs,
                    and_(
                        outputs.c.record_id == jobs.c.record_id,
                        outputs.c.run == jobs.c.run,
                        outputs.c.workspace_id == workspace_id,
                    ),
                )
                .where(
                    jobs.c.workspace_id == workspace_id,
                    jobs.c.id.in_(job_ids),
                    jobs.c.origin.in_(["live", "analysis"]),
                )
            )
        )
        .mappings()
        .all()
    )
    indexed: dict[str, ActivityItem] = {}
    for row in rows:
        job = JobView.model_validate(
            {
                key: row[key]
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
        output = (
            OutputView.model_validate(
                {
                    **row["output_payload"],
                    "config": job.config,
                    "run": job.run,
                    "provider": row["output_provider"],
                    "created_at": row["output_created_at"].isoformat(),
                }
            )
            if row["output_payload"] is not None
            else None
        )
        indexed["job:" + job.id] = FeedbackActivity(
            id=job.id,
            feedback=BatchItem(
                record_id=str(row["record_id"]),
                sequence=int(row["sequence"]),
                text=str(row["text"]),
                channel=str(row["channel"]),
                job=job,
                output=output,
            ),
        )
    for value in event_ids:
        if value.startswith("batch:"):
            batch = await get_backfill(conn, workspace_id, value.removeprefix("batch:"))
            if batch is not None:
                indexed[value] = BatchActivity(id=batch.view.id, batch=batch.view)
    return [indexed[value] for value in event_ids if value in indexed]
