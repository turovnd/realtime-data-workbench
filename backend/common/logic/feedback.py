"""Workspace-scoped detail reads and idempotent user-authored feedback submission."""

from sqlalchemy.orm import Session

from common.logic.errors import NotFoundError
from common.logic.ingestion import ingest
from common.repositories.coordination import lock_workspace
from common.repositories.feedback import hydrate
from common.repositories.ingestion import find_input
from common.schemas.feedback import FeedbackInput, RecordView


def get_feedback(session: Session, workspace_id: str, record_id: str) -> RecordView:
    lock_workspace(session)
    rows = hydrate(session, workspace_id, [record_id])
    if not rows:
        raise NotFoundError("Feedback was not found")
    return rows[0]


def create_feedback(
    session: Session, workspace_id: str, value: FeedbackInput, provider: str
) -> tuple[RecordView, bool]:
    inserted = ingest(session, [value], workspace_id, provider)
    lock_workspace(session)
    raw = find_input(session, workspace_id, value.identity)
    if raw is None:
        raise NotFoundError("Feedback was not found")
    rows = hydrate(session, workspace_id, [raw.id])
    return rows[0], inserted > 0
