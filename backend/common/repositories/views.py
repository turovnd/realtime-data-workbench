"""Bounded frozen-view storage and SQL keyset paging."""

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from common.models import AnalysisJob, AnalysisResult, Feedback, FeedView, Workspace
from common.schemas.feedback import FeedFilters


def prune_views(session: Session, workspace_id: str, now: datetime) -> None:
    session.query(FeedView).filter(FeedView.expires_at <= now).delete()
    count = int(
        session.query(func.count())
        .select_from(FeedView)
        .filter(FeedView.workspace_id == workspace_id)
        .scalar()
        or 0
    )
    if count >= 20:
        oldest = (
            session.query(FeedView.id)
            .filter(FeedView.workspace_id == workspace_id)
            .order_by(FeedView.expires_at)
            .limit(1)
            .scalar_subquery()
        )
        session.query(FeedView).filter(FeedView.id == oldest).delete()


def matching_ids(
    session: Session, workspace_id: str, filters: FeedFilters
) -> tuple[list[str], int]:
    latest_job = (
        session.query(AnalysisJob.status)
        .filter(AnalysisJob.record_id == Feedback.id)
        .order_by(AnalysisJob.run.desc())
        .limit(1)
        .scalar_subquery()
    )
    latest_topic = (
        session.query(AnalysisResult.payload["topic"].as_string())
        .filter(AnalysisResult.record_id == Feedback.id)
        .order_by(AnalysisResult.run.desc())
        .limit(1)
        .scalar_subquery()
    )
    query = session.query(Feedback.id).filter(Feedback.workspace_id == workspace_id)
    if filters.q:
        query = query.filter(func.lower(Feedback.text).contains(filters.q.lower(), autoescape=True))
    if filters.status != "all":
        query = query.filter(latest_job == filters.status)
    if filters.topic != "all":
        query = query.filter(latest_topic == filters.topic)
    ids = [row[0] for row in query.order_by(Feedback.sequence.desc()).all()]
    watermark = int(
        session.query(func.max(Feedback.sequence))
        .filter(Feedback.workspace_id == workspace_id)
        .scalar()
        or 0
    )
    return ids, watermark


def page_ids(
    session: Session, workspace_id: str, ids: list[str], before: int, limit: int
) -> list[tuple[str, int]]:
    rows = (
        session.query(Feedback.id, Feedback.sequence)
        .filter(
            Feedback.workspace_id == workspace_id, Feedback.id.in_(ids), Feedback.sequence < before
        )
        .order_by(Feedback.sequence.desc())
        .limit(limit + 1)
        .all()
    )
    return [(str(row.id), int(row.sequence)) for row in rows]


def revision(session: Session, workspace_id: str) -> int:
    return int(session.query(Workspace.cursor).filter(Workspace.id == workspace_id).scalar() or 0)
