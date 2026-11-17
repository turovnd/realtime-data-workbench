"""Feedback persistence within the caller's ingestion transaction."""

from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from common.models import Feedback
from common.schemas.feedback import FeedbackInput


def record_counts(session: Session, workspace_id: str) -> tuple[int, int]:
    own = (
        session.query(func.count())
        .select_from(Feedback)
        .filter(Feedback.workspace_id == workspace_id)
        .scalar()
    )
    total = session.query(func.count()).select_from(Feedback).scalar()
    return own or 0, total or 0


def find_input(session: Session, workspace_id: str, identity: str) -> Feedback | None:
    return (
        session.query(Feedback)
        .filter(Feedback.workspace_id == workspace_id, Feedback.identity == identity)
        .one_or_none()
    )


def insert_input(
    session: Session, workspace_id: str, record_id: str, sequence: int, value: FeedbackInput
) -> None:
    session.add(
        Feedback(
            id=record_id,
            workspace_id=workspace_id,
            identity=value.identity,
            sequence=sequence,
            text=value.text,
            channel=value.channel,
            ingested_at=datetime.now(UTC),
        )
    )
    session.flush()
