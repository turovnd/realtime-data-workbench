"""Freeze one selection, retain prior versions, and fence cancellation atomically."""

from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.database import session_scope
from workbench.logic.errors import ConflictError
from workbench.repositories import backfills
from workbench.repositories.coordination import changed, lock_workspace
from workbench.repositories.jobs import enqueue
from workbench.schemas.backfills import BackfillInput


async def start_backfill(
    engine: AsyncEngine,
    request: BackfillInput,
    workspace_id: str = "test",
    provider: str = "deterministic-rules/1",
) -> str:
    async with session_scope(engine) as session:
        await lock_workspace(session)
        ids = list(dict.fromkeys(request.record_ids))
        found = await backfills.selected_records(session, workspace_id, ids)
        if len(found) != len(ids):
            raise ConflictError("Some selected records no longer exist")
        existing = await backfills.existing_jobs(session, ids, request.config)
        if any(job.status != "succeeded" for job in existing):
            raise ConflictError(
                "Selected version already has work; retry or cancel its existing batch"
            )
        completed = {job.record_id for job in existing}
        if len(completed) == len(ids):
            raise ConflictError("This version is already complete for every selected record")
        batch_id = str(uuid4())
        await backfills.insert_backfill(
            session,
            workspace_id,
            batch_id,
            ids,
            request.config,
            max(row.sequence for row in found),
        )
        for record_id in ids:
            if record_id not in completed:
                await enqueue(
                    session, record_id, request.config, "backfill", batch_id, workspace_id, provider
                )
        await changed(session, workspace_id)
        return batch_id


async def cancel_backfill(engine: AsyncEngine, batch_id: str, workspace_id: str = "test") -> None:
    async with session_scope(engine) as session:
        await lock_workspace(session)
        if not await backfills.contains_backfill(session, workspace_id, batch_id):
            raise ConflictError("Batch does not exist")
        await backfills.cancel_unfinished(session, workspace_id, batch_id)
        await changed(session, workspace_id)
