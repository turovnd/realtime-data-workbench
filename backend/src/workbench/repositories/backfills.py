"""Backfill selection/progress persistence, scoped by the caller's workspace."""

from sqlalchemy import insert, select, update
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncConnection

from workbench.infrastructure.tables import batches, jobs, records
from workbench.schemas.common import Config


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
                select(jobs).where(jobs.c.record_id.in_(ids), jobs.c.config == config)
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
