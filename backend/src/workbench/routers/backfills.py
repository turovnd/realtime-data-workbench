from typing import Annotated

from fastapi import APIRouter, Path, Query

from workbench.dependencies import AppSettings, Database, Dispatcher, Workspace
from workbench.logic.backfill_details import backfill_page
from workbench.logic.backfills import cancel_backfill, start_backfill
from workbench.repositories.jobs import retry_job
from workbench.routers.responses import errors
from workbench.schemas.backfill_details import BatchPage
from workbench.schemas.backfills import BackfillCreated, BackfillInput
from workbench.schemas.common import EmptyRequest, OkResponse

router = APIRouter(prefix="/api", tags=["Backfills and recovery"])


@router.get(
    "/backfills/{batch_id}",
    response_model=BatchPage,
    operation_id="getBackfill",
    summary="Read the feedback and original results of one backfill",
    description=(
        "Pages the persisted fixed selection in descending source sequence with SQL "
        "keyset pagination. Membership never expands with new arrivals. Each item shows "
        "its original non-analysis target-configuration job and only that job's output; "
        "later individual analyses are excluded. A selection may reuse an already "
        "completed target version. Progress and job states may refresh. Missing and "
        "foreign-workspace batches both return 404. Signed cursors are bound to this "
        "workspace and batch for ten minutes, sharing the twenty-view workspace limit "
        "with feedback views. Reading does not enqueue work or call a provider."
    ),
    responses=errors(400, 401, 404, 410),
)
async def detail(
    batch_id: Annotated[str, Path(description="Persisted fixed-selection backfill identifier")],
    database: Database,
    workspace_id: Workspace,
    limit: Annotated[
        int, Query(ge=1, le=50, description="Maximum items per page; default ten")
    ] = 10,
    cursor: Annotated[
        str | None,
        Query(
            description="Opaque next_cursor for this workspace/batch; omit to read its first page"
        ),
    ] = None,
) -> BatchPage:
    return await backfill_page(database, workspace_id, batch_id, limit, cursor)


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
    request: BackfillInput,
    database: Database,
    workspace_id: Workspace,
    settings: AppSettings,
    dispatcher: Dispatcher,
) -> BackfillCreated:
    batch_id = await start_backfill(database, request, workspace_id, settings.provider_id)
    await dispatcher.notify(workspace_id, batch_id=batch_id)
    return BackfillCreated(id=batch_id)


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
    dispatcher: Dispatcher,
    _body: EmptyRequest | None = None,
) -> OkResponse:
    await retry_job(database, job_id, workspace_id)
    await dispatcher.notify(workspace_id, job_ids=[job_id])
    return OkResponse()
