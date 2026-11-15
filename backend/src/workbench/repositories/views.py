"""Bounded frozen-view storage and SQL keyset paging."""

from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from workbench.models import AnalysisJob, AnalysisResult, Feedback, FeedView, Workspace
from workbench.schemas.feedback import FeedFilters


async def prune_views(session: AsyncSession, workspace_id: str, now: datetime) -> None:
    await session.execute(delete(FeedView).where(FeedView.expires_at <= now))
    count = int(
        await session.scalar(
            select(func.count()).select_from(FeedView).where(FeedView.workspace_id == workspace_id)
        )
        or 0
    )
    if count >= 20:
        oldest = (
            select(FeedView.id)
            .where(FeedView.workspace_id == workspace_id)
            .order_by(FeedView.expires_at)
            .limit(1)
            .scalar_subquery()
        )
        await session.execute(delete(FeedView).where(FeedView.id == oldest))


async def matching_ids(
    session: AsyncSession, workspace_id: str, filters: FeedFilters
) -> tuple[list[str], int]:
    latest_job = (
        select(AnalysisJob.status)
        .where(AnalysisJob.record_id == Feedback.id)
        .order_by(AnalysisJob.run.desc())
        .limit(1)
        .scalar_subquery()
    )
    latest_topic = (
        select(AnalysisResult.payload["topic"].as_string())
        .where(AnalysisResult.record_id == Feedback.id)
        .order_by(AnalysisResult.run.desc())
        .limit(1)
        .scalar_subquery()
    )
    query = select(Feedback.id).where(Feedback.workspace_id == workspace_id)
    if filters.q:
        query = query.where(func.lower(Feedback.text).contains(filters.q.lower(), autoescape=True))
    if filters.status != "all":
        query = query.where(latest_job == filters.status)
    if filters.topic != "all":
        query = query.where(latest_topic == filters.topic)
    ids = list((await session.execute(query.order_by(Feedback.sequence.desc()))).scalars())
    watermark = int(
        await session.scalar(
            select(func.max(Feedback.sequence)).where(Feedback.workspace_id == workspace_id)
        )
        or 0
    )
    return ids, watermark


async def page_ids(
    session: AsyncSession, workspace_id: str, ids: list[str], before: int, limit: int
) -> list[tuple[str, int]]:
    rows = (
        await session.execute(
            select(Feedback.id, Feedback.sequence)
            .where(
                Feedback.workspace_id == workspace_id,
                Feedback.id.in_(ids),
                Feedback.sequence < before,
            )
            .order_by(Feedback.sequence.desc())
            .limit(limit + 1)
        )
    ).all()
    return [(str(row.id), int(row.sequence)) for row in rows]


async def revision(session: AsyncSession, workspace_id: str) -> int:
    return int(
        await session.scalar(select(Workspace.cursor).where(Workspace.id == workspace_id)) or 0
    )
