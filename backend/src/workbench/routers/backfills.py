from typing import Annotated

from fastapi import APIRouter, Path

from workbench.dependencies import AppSettings, Database, Workspace
from workbench.logic.backfills import cancel_backfill, start_backfill
from workbench.repositories.jobs import retry_job
from workbench.routers.responses import errors
from workbench.schemas.backfills import BackfillCreated, BackfillInput
from workbench.schemas.common import EmptyRequest, OkResponse

router = APIRouter(prefix="/api", tags=["Backfills and recovery"])


@router.post(
    "/backfills",
    response_model=BackfillCreated,
    operation_id="createBackfill",
    summary="Reprocess a fixed selection with another configuration",
    description=(
        "Freezes up to 100 record IDs belonging to this workspace and enqueues the "
        "missing target versions atomically. Input and previous outputs stay "
        "unchanged. The unique (record, config) operation is idempotent; existing "
        "unfinished work must be retried or cancelled, not duplicated. Progress is "
        "available in /api/status."
    ),
    responses=errors(401, 403, 409, 413),
)
async def backfill(
    request: BackfillInput, database: Database, workspace_id: Workspace, settings: AppSettings
) -> BackfillCreated:
    return BackfillCreated(
        id=await start_backfill(database, request, workspace_id, settings.provider_id)
    )


@router.post(
    "/backfills/{batch_id}/cancel",
    response_model=OkResponse,
    operation_id="cancelBackfill",
    summary="Stop unfinished work in a backfill",
    description=(
        "Cancels queued/claimed jobs and fences in-flight completions. Already "
        "completed versions are preserved. Only a batch in the current workspace "
        "can be cancelled. Send an empty JSON object."
    ),
    responses=errors(401, 403, 409, 413),
)
async def cancel(
    batch_id: Annotated[str, Path(description="Backfill id returned by createBackfill")],
    database: Database,
    workspace_id: Workspace,
    _body: EmptyRequest | None = None,
) -> OkResponse:
    await cancel_backfill(database, batch_id, workspace_id)
    return OkResponse()


@router.post(
    "/jobs/{job_id}/retry",
    response_model=OkResponse,
    operation_id="retryEnrichment",
    summary="Retry an eligible failed or cancelled version",
    description=(
        "Only terminal jobs in this workspace with fewer than three lifetime "
        "attempts can be retried. Retry retains the original provider/configuration "
        "and does not overwrite completed output. Failed provider calls never "
        "silently switch to deterministic mode. Send an empty JSON object."
    ),
    responses=errors(401, 403, 409, 413),
)
async def retry(
    job_id: Annotated[str, Path(description="Job id from a feedback record's processing history")],
    database: Database,
    workspace_id: Workspace,
    _body: EmptyRequest | None = None,
) -> OkResponse:
    await retry_job(database, job_id, workspace_id)
    return OkResponse()
