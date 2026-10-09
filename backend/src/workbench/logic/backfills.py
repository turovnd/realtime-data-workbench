"""Freeze one selection, retain prior versions, and fence cancellation atomically."""

from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncEngine

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
    async with engine.begin() as conn:
        await lock_workspace(conn)
        ids = list(dict.fromkeys(request.record_ids))
        found = await backfills.selected_records(conn, workspace_id, ids)
        if len(found) != len(ids):
            raise ConflictError("Some selected records no longer exist")
        existing = await backfills.existing_jobs(conn, ids, request.config)
        if any(job["status"] != "succeeded" for job in existing):
            raise ConflictError(
                "Selected version already has work; retry or cancel its existing batch"
            )
        completed = {str(job["record_id"]) for job in existing}
        if len(completed) == len(ids):
            raise ConflictError("This version is already complete for every selected record")
        batch_id = str(uuid4())
        await backfills.insert_backfill(
            conn,
            workspace_id,
            batch_id,
            ids,
            request.config,
            max(int(row["sequence"]) for row in found),
        )
        for record_id in ids:
            if record_id not in completed:
                await enqueue(
                    conn, record_id, request.config, "backfill", batch_id, workspace_id, provider
                )
        await changed(conn, workspace_id)
        return batch_id


async def cancel_backfill(engine: AsyncEngine, batch_id: str, workspace_id: str = "test") -> None:
    async with engine.begin() as conn:
        await lock_workspace(conn)
        if not await backfills.contains_backfill(conn, workspace_id, batch_id):
            raise ConflictError("Batch does not exist")
        await backfills.cancel_unfinished(conn, workspace_id, batch_id)
        await changed(conn, workspace_id)
