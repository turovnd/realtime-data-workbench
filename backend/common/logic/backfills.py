"""Freeze one selection, retain prior versions, and fence cancellation atomically."""

from uuid import uuid4

from sqlalchemy.orm import Session

from common.logic.errors import ConflictError
from common.repositories import backfills
from common.repositories.coordination import changed, lock_workspace
from common.repositories.jobs import enqueue
from common.schemas.backfills import BackfillInput


def start_backfill(
    session: Session,
    request: BackfillInput,
    workspace_id: str = "test",
    provider: str = "deterministic-rules/1",
) -> str:
    lock_workspace(session)
    ids = list(dict.fromkeys(request.record_ids))
    found = backfills.selected_records(session, workspace_id, ids)
    if len(found) != len(ids):
        raise ConflictError("Some selected records no longer exist")
    existing = backfills.existing_jobs(session, ids, request.config)
    if any(job.status != "succeeded" for job in existing):
        raise ConflictError("Selected version already has work; retry or cancel its existing batch")
    completed = {job.record_id for job in existing}
    if len(completed) == len(ids):
        raise ConflictError("This version is already complete for every selected record")
    batch_id = str(uuid4())
    backfills.insert_backfill(
        session,
        workspace_id,
        batch_id,
        ids,
        request.config,
        max(row.sequence for row in found),
    )
    for record_id in ids:
        if record_id not in completed:
            enqueue(
                session, record_id, request.config, "backfill", batch_id, workspace_id, provider
            )
    changed(session, workspace_id)
    return batch_id


def cancel_backfill(session: Session, batch_id: str, workspace_id: str = "test") -> None:
    lock_workspace(session)
    if not backfills.contains_backfill(session, workspace_id, batch_id):
        raise ConflictError("Batch does not exist")
    backfills.cancel_unfinished(session, workspace_id, batch_id)
    changed(session, workspace_id)
