"""Bounded frozen-view storage and SQL keyset paging."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import delete, func, insert, select
from sqlalchemy.ext.asyncio import AsyncConnection

from workbench.infrastructure.tables import feed_views, jobs, outputs, records, state
from workbench.schemas.feedback import FeedFilters


@dataclass(frozen=True)
class StoredView:
    id: str
    workspace_id: str
    filter_key: str
    record_ids: list[str]
    watermark: int
    secret: str
    expires_at: datetime


async def get_view(conn: AsyncConnection, view_id: str) -> StoredView | None:
    row = (
        (await conn.execute(select(feed_views).where(feed_views.c.id == view_id)))
        .mappings()
        .first()
    )
    if row is None:
        return None
    return StoredView(
        id=str(row["id"]),
        workspace_id=str(row["workspace_id"]),
        filter_key=str(row["filter_key"]),
        record_ids=list(row["record_ids"]),
        watermark=int(row["watermark"]),
        secret=str(row["secret"]),
        expires_at=row["expires_at"],
    )


async def prune_views(conn: AsyncConnection, workspace_id: str, now: datetime) -> None:
    await conn.execute(delete(feed_views).where(feed_views.c.expires_at <= now))
    count = int(
        await conn.scalar(
            select(func.count())
            .select_from(feed_views)
            .where(feed_views.c.workspace_id == workspace_id)
        )
        or 0
    )
    if count >= 20:
        oldest = (
            select(feed_views.c.id)
            .where(feed_views.c.workspace_id == workspace_id)
            .order_by(feed_views.c.expires_at)
            .limit(1)
            .scalar_subquery()
        )
        await conn.execute(delete(feed_views).where(feed_views.c.id == oldest))


async def matching_ids(
    conn: AsyncConnection, workspace_id: str, filters: FeedFilters
) -> tuple[list[str], int]:
    latest_job = (
        select(jobs.c.status)
        .where(jobs.c.record_id == records.c.id)
        .order_by(jobs.c.config.desc())
        .limit(1)
        .scalar_subquery()
    )
    latest_topic = (
        select(outputs.c.payload["topic"].as_string())
        .where(outputs.c.record_id == records.c.id)
        .order_by(outputs.c.config.desc())
        .limit(1)
        .scalar_subquery()
    )
    query = select(records.c.id).where(records.c.workspace_id == workspace_id)
    if filters.q:
        query = query.where(func.lower(records.c.text).contains(filters.q.lower(), autoescape=True))
    if filters.status != "all":
        query = query.where(latest_job == filters.status)
    if filters.topic != "all":
        query = query.where(latest_topic == filters.topic)
    ids = list((await conn.execute(query.order_by(records.c.sequence.desc()))).scalars())
    watermark = int(
        await conn.scalar(
            select(func.max(records.c.sequence)).where(records.c.workspace_id == workspace_id)
        )
        or 0
    )
    return ids, watermark


async def store_view(conn: AsyncConnection, view: StoredView) -> None:
    await conn.execute(
        insert(feed_views).values(
            id=view.id,
            workspace_id=view.workspace_id,
            filter_key=view.filter_key,
            record_ids=view.record_ids,
            watermark=view.watermark,
            secret=view.secret,
            expires_at=view.expires_at,
        )
    )


async def page_ids(
    conn: AsyncConnection, workspace_id: str, ids: list[str], before: int, limit: int
) -> list[tuple[str, int]]:
    rows = (
        await conn.execute(
            select(records.c.id, records.c.sequence)
            .where(
                records.c.workspace_id == workspace_id,
                records.c.id.in_(ids),
                records.c.sequence < before,
            )
            .order_by(records.c.sequence.desc())
            .limit(limit + 1)
        )
    ).all()
    return [(str(row.id), int(row.sequence)) for row in rows]


async def revision(conn: AsyncConnection, workspace_id: str) -> int:
    return int(await conn.scalar(select(state.c.cursor).where(state.c.id == workspace_id)) or 0)
