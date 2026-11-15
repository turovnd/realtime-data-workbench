"""Bounded activity membership and paging over saved positions."""

from sqlalchemy import and_, func, literal, select, true, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from workbench.models import AnalysisBatch, AnalysisJob, FeedView

MAX_ACTIVITY_ITEMS = 6000


async def activity_ids(session: AsyncSession, workspace_id: str) -> tuple[list[str], bool]:
    individual = select(
        (literal("job:") + AnalysisJob.id).label("event_id"),
        AnalysisJob.available_at.label("ordering_time"),
    ).where(AnalysisJob.workspace_id == workspace_id, AnalysisJob.origin.in_(["live", "analysis"]))
    grouped = (
        select(
            (literal("batch:") + AnalysisBatch.id).label("event_id"),
            func.max(AnalysisJob.available_at).label("ordering_time"),
        )
        .outerjoin(
            AnalysisJob,
            and_(
                AnalysisJob.batch_id == AnalysisBatch.id,
                AnalysisJob.workspace_id == workspace_id,
                AnalysisJob.origin != "analysis",
            ),
        )
        .where(AnalysisBatch.workspace_id == workspace_id)
        .group_by(AnalysisBatch.id)
    )
    candidates = union_all(individual, grouped).subquery()
    ids = list(
        await session.scalars(
            select(candidates.c.event_id)
            .order_by(candidates.c.ordering_time.desc().nulls_last(), candidates.c.event_id.desc())
            .limit(MAX_ACTIVITY_ITEMS + 1)
        )
    )
    return ids[:MAX_ACTIVITY_ITEMS], len(ids) > MAX_ACTIVITY_ITEMS


async def page_activity_ids(
    session: AsyncSession, workspace_id: str, view_id: str, after: int, limit: int
) -> list[tuple[str, int]]:
    entries = (
        func.json_array_elements_text(FeedView.record_ids)
        .table_valued("value", with_ordinality="position")
        .render_derived()
        .lateral()
    )
    rows = await session.execute(
        select(entries.c.value, entries.c.position)
        .select_from(FeedView)
        .join(entries, true())
        .where(
            FeedView.id == view_id,
            FeedView.workspace_id == workspace_id,
            FeedView.filter_key == "activity",
            entries.c.position > after,
        )
        .order_by(entries.c.position)
        .limit(limit + 1)
    )
    return [(row.value, row.position) for row in rows]
