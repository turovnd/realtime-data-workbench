"""Bounded activity membership and keyset paging over persisted view positions."""

from sqlalchemy import and_, func, literal, select, text, union_all
from sqlalchemy.ext.asyncio import AsyncConnection

from workbench.infrastructure.tables import batches, jobs


async def activity_ids(conn: AsyncConnection, workspace_id: str) -> tuple[list[str], bool]:
    individual = select(
        (literal("job:") + jobs.c.id).label("event_id"),
        jobs.c.available_at.label("ordering_time"),
    ).where(jobs.c.workspace_id == workspace_id, jobs.c.origin.in_(["live", "analysis"]))
    grouped = (
        select(
            (literal("batch:") + batches.c.id).label("event_id"),
            func.max(jobs.c.available_at).label("ordering_time"),
        )
        .select_from(
            batches.outerjoin(
                jobs,
                and_(
                    jobs.c.batch_id == batches.c.id,
                    jobs.c.workspace_id == workspace_id,
                    jobs.c.origin != "analysis",
                ),
            )
        )
        .where(batches.c.workspace_id == workspace_id)
        .group_by(batches.c.id)
    )
    candidates = union_all(individual, grouped).subquery()
    ids = list(
        (
            await conn.execute(
                select(candidates.c.event_id)
                .order_by(
                    candidates.c.ordering_time.desc().nulls_last(), candidates.c.event_id.desc()
                )
                .limit(6001)
            )
        ).scalars()
    )
    return ids[:6000], len(ids) > 6000


async def page_activity_ids(
    conn: AsyncConnection, workspace_id: str, view_id: str, after: int, limit: int
) -> list[tuple[str, int]]:
    rows = (
        await conn.execute(
            text(
                "SELECT entry.value, entry.position FROM feed_views AS view "
                "CROSS JOIN LATERAL json_array_elements_text(view.record_ids) "
                "WITH ORDINALITY AS entry(value, position) "
                "WHERE view.id = :view_id AND view.workspace_id = :workspace_id "
                "AND view.filter_key = 'activity' AND entry.position > :after "
                "ORDER BY entry.position LIMIT :limit"
            ),
            {"view_id": view_id, "workspace_id": workspace_id, "after": after, "limit": limit + 1},
        )
    ).all()
    return [(str(row[0]), int(row[1])) for row in rows]
