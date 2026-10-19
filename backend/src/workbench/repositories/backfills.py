"""Backfill selection/progress persistence, scoped by the caller's workspace."""

from dataclasses import dataclass

from sqlalchemy import and_, insert, select, update
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncConnection

from workbench.infrastructure.tables import batches, jobs, outputs, records
from workbench.schemas.backfill_details import BatchItem
from workbench.schemas.backfills import BatchView
from workbench.schemas.common import Config
from workbench.schemas.enrichment import OutputView
from workbench.schemas.feedback import JobView


async def selected_records(
    conn: AsyncConnection, workspace_id: str, ids: list[str]
) -> list[RowMapping]:
    return list(
        (
            await conn.execute(
                select(records.c.id, records.c.sequence).where(
                    records.c.workspace_id == workspace_id, records.c.id.in_(ids)
                )
            )
        ).mappings()
    )


async def existing_jobs(conn: AsyncConnection, ids: list[str], config: Config) -> list[RowMapping]:
    return list(
        (
            await conn.execute(
                select(jobs).where(
                    jobs.c.record_id.in_(ids), jobs.c.config == config, jobs.c.origin != "analysis"
                )
            )
        ).mappings()
    )


async def insert_backfill(
    conn: AsyncConnection,
    workspace_id: str,
    batch_id: str,
    ids: list[str],
    config: Config,
    watermark: int,
) -> None:
    await conn.execute(
        insert(batches).values(
            id=batch_id,
            workspace_id=workspace_id,
            config=config,
            record_ids=ids,
            watermark=watermark,
            cancelled=False,
        )
    )


async def contains_backfill(conn: AsyncConnection, workspace_id: str, batch_id: str) -> bool:
    return bool(
        await conn.scalar(
            select(batches.c.id).where(
                batches.c.workspace_id == workspace_id, batches.c.id == batch_id
            )
        )
    )


async def cancel_unfinished(conn: AsyncConnection, workspace_id: str, batch_id: str) -> None:
    await conn.execute(
        update(batches)
        .where(batches.c.workspace_id == workspace_id, batches.c.id == batch_id)
        .values(cancelled=True)
    )
    await conn.execute(
        update(jobs)
        .where(jobs.c.batch_id == batch_id, jobs.c.status.in_(["queued", "leased"]))
        .values(status="cancelled", fence=jobs.c.fence + 1, lease_until=None)
    )


@dataclass(frozen=True)
class StoredBatch:
    view: BatchView
    record_ids: list[str]


async def get_backfill(
    conn: AsyncConnection, workspace_id: str, batch_id: str
) -> StoredBatch | None:
    row = (
        (
            await conn.execute(
                select(batches).where(
                    batches.c.workspace_id == workspace_id, batches.c.id == batch_id
                )
            )
        )
        .mappings()
        .first()
    )
    if row is None:
        return None
    ids = list(row["record_ids"])
    progress = list(
        (
            await conn.execute(
                select(jobs.c.status).where(
                    jobs.c.workspace_id == workspace_id,
                    jobs.c.record_id.in_(ids),
                    jobs.c.config == row["config"],
                    jobs.c.origin != "analysis",
                )
            )
        ).scalars()
    )
    return StoredBatch(
        view=BatchView(
            id=str(row["id"]),
            config=row["config"],
            selected=len(ids),
            completed=progress.count("succeeded"),
            failed=progress.count("failed"),
            cancelled=bool(row["cancelled"]),
            watermark=int(row["watermark"]),
        ),
        record_ids=ids,
    )


async def batch_items(
    conn: AsyncConnection, workspace_id: str, ids: list[str], config: Config
) -> list[BatchItem]:
    """Read exact historical batch results without consulting the recent-history window."""
    if len(ids) > 50:
        raise ValueError("Batch detail pages are limited to 50 records")
    job_fields = ("id", "config", "run", "provider", "status", "attempts", "error", "origin")
    rows = (
        (
            await conn.execute(
                select(
                    records.c.id,
                    records.c.sequence,
                    records.c.text,
                    records.c.channel,
                    *(jobs.c[field].label("job_" + field) for field in job_fields),
                    outputs.c.payload.label("output_payload"),
                    outputs.c.config.label("output_config"),
                    outputs.c.run.label("output_run"),
                    outputs.c.provider.label("output_provider"),
                    outputs.c.created_at.label("output_created_at"),
                )
                .select_from(
                    records.outerjoin(
                        jobs,
                        and_(
                            jobs.c.record_id == records.c.id,
                            jobs.c.workspace_id == workspace_id,
                            jobs.c.config == config,
                            jobs.c.origin != "analysis",
                        ),
                    ).outerjoin(
                        outputs,
                        and_(
                            outputs.c.record_id == records.c.id,
                            outputs.c.workspace_id == workspace_id,
                            outputs.c.run == jobs.c.run,
                            outputs.c.config == jobs.c.config,
                        ),
                    )
                )
                .where(records.c.workspace_id == workspace_id, records.c.id.in_(ids))
                .order_by(records.c.sequence.desc())
            )
        )
        .mappings()
        .all()
    )
    return [
        BatchItem(
            record_id=str(row["id"]),
            sequence=int(row["sequence"]),
            text=str(row["text"]),
            channel=str(row["channel"]),
            job=(
                JobView.model_validate({field: row["job_" + field] for field in job_fields})
                if row["job_id"] is not None
                else None
            ),
            output=(
                OutputView.model_validate(
                    {
                        **row["output_payload"],
                        "config": row["output_config"],
                        "run": row["output_run"],
                        "provider": row["output_provider"],
                        "created_at": row["output_created_at"].isoformat(),
                    }
                )
                if row["output_payload"] is not None
                else None
            ),
        )
        for row in rows
    ]
