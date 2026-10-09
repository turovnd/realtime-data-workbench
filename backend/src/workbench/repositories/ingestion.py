"""SQL primitives used inside the ingestion transaction."""

from datetime import UTC, datetime

from sqlalchemy import func, insert, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncConnection

from workbench.infrastructure.tables import records
from workbench.schemas.feedback import FeedbackInput


async def record_counts(conn: AsyncConnection, workspace_id: str) -> tuple[int, int]:
    own = await conn.scalar(
        select(func.count()).select_from(records).where(records.c.workspace_id == workspace_id)
    )
    total = await conn.scalar(select(func.count()).select_from(records))
    return int(own or 0), int(total or 0)


async def find_input(conn: AsyncConnection, workspace_id: str, identity: str) -> RowMapping | None:
    return (
        (
            await conn.execute(
                select(records).where(
                    records.c.workspace_id == workspace_id, records.c.identity == identity
                )
            )
        )
        .mappings()
        .first()
    )


async def insert_input(
    conn: AsyncConnection, workspace_id: str, record_id: str, sequence: int, value: FeedbackInput
) -> None:
    await conn.execute(
        insert(records).values(
            id=record_id,
            workspace_id=workspace_id,
            identity=value.identity,
            sequence=sequence,
            text=value.text,
            channel=value.channel,
            ingested_at=datetime.now(UTC),
        )
    )
