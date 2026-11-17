"""Validate idempotent input and commit each bounded run with its durable work."""

from uuid import uuid4

from sqlalchemy.orm import Session

from common.logic.errors import ConflictError
from common.repositories.coordination import changed, lock_workspace
from common.repositories.ingestion import find_input, insert_input, record_counts
from common.repositories.jobs import enqueue
from common.schemas.feedback import FeedbackInput


def ingest(
    session: Session,
    inputs: list[FeedbackInput],
    workspace_id: str = "test",
    provider: str = "deterministic-rules/1",
) -> int:
    lock_workspace(session)
    size, global_size = record_counts(session, workspace_id)
    inserted = 0
    for value in inputs:
        previous = find_input(session, workspace_id, value.identity)
        if previous:
            if previous.text != value.text or previous.channel != value.channel:
                raise ConflictError("An input identity cannot be reused with different content")
            continue
        if global_size + inserted >= 5000:
            raise ConflictError(
                "Global demo record capacity reached; try after expired sessions are cleaned up"
            )
        if size + inserted >= 500:
            raise ConflictError("This bounded demo workspace is full (500 records)")
        record_id = str(uuid4())
        inserted += 1
        insert_input(session, workspace_id, record_id, size + inserted, value)
        enqueue(session, record_id, "v1", "live", workspace_id=workspace_id, provider=provider)
    if inserted:
        changed(session, workspace_id)
    return inserted
