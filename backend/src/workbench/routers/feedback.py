from typing import Annotated, Literal

from fastapi import APIRouter, Query

from workbench.dependencies import AppSettings, Database, Workspace
from workbench.logic.feed import feed_page
from workbench.logic.ingestion import ingest
from workbench.logic.synthetic import synthetic_inputs
from workbench.repositories.status import feed_status
from workbench.routers.responses import errors
from workbench.schemas.feedback import (
    FeedFilters,
    FeedPage,
    FeedStatus,
    SimulationCreated,
    SimulationInput,
)

router = APIRouter(prefix="/api", tags=["Feedback"])


@router.get(
    "/feedback",
    response_model=FeedPage,
    operation_id="listFeedback",
    summary="Read one stable page of feedback",
    description=(
        "The first request freezes matching IDs for ten minutes (at most twenty "
        "views per workspace). Subsequent requests use a signed opaque cursor and "
        "descending sequence keyset with SQL LIMIT. Only one page is hydrated. "
        "Processing results may refresh, but membership stays fixed to prevent "
        "skips/duplicates. New arrivals and changed matches appear after starting "
        "without a cursor. Never construct or reuse a cursor with another workspace "
        "or filter."
    ),
    responses=errors(400, 401, 410),
)
async def feedback(
    database: Database,
    workspace_id: Workspace,
    q: Annotated[
        str,
        Query(
            max_length=100,
            description="Case-insensitive source-text substring; retained with the cursor",
        ),
    ] = "",
    status: Annotated[
        Literal["all", "queued", "leased", "succeeded", "failed", "cancelled"],
        Query(description="Latest configuration's job status at view creation"),
    ] = "all",
    topic: Annotated[
        Literal["all", "reliability", "usability", "billing", "performance", "other"],
        Query(description="Latest stored output topic at view creation"),
    ] = "all",
    limit: Annotated[
        int, Query(ge=1, le=50, description="Page size; default UI page is twelve")
    ] = 12,
    cursor: Annotated[
        str | None,
        Query(
            description=(
                "Opaque next_cursor or refresh_cursor from the same workspace/filter view; "
                "absent opens a current view. Invalid values return 400; retained expired "
                "views return 410."
            )
        ),
    ] = None,
) -> FeedPage:
    return await feed_page(
        database, workspace_id, FeedFilters(q=q, status=status, topic=topic), limit, cursor
    )


@router.get(
    "/status",
    response_model=FeedStatus,
    operation_id="getFeedbackStatus",
    summary="Read counts, processing progress and new-arrival marker",
    description=(
        "Returns workspace totals and at most ten backfills. latest_sequence can "
        "signal arrivals newer than the current feed watermark. The UI polls every "
        "three seconds; this endpoint does not stream events."
    ),
    responses=errors(401),
)
async def status(database: Database, workspace_id: Workspace, settings: AppSettings) -> FeedStatus:
    return await feed_status(database, workspace_id, settings.provider_id)


@router.post(
    "/simulations",
    response_model=SimulationCreated,
    operation_id="createSimulation",
    summary="Enqueue a finite batch of synthetic feedback",
    description=(
        "Commits one to twelve immutable inputs and durable v1 jobs atomically. "
        "Repeating request_id is idempotent; conflicting content is rejected. "
        "Bounds: 500 records per workspace and 5,000 globally. A separate worker "
        "processes jobs; the HTTP request does not wait for enrichment."
    ),
    responses=errors(401, 403, 409, 413),
)
async def simulate(
    request: SimulationInput, database: Database, workspace_id: Workspace, settings: AppSettings
) -> SimulationCreated:
    inserted = await ingest(
        database,
        synthetic_inputs(request.request_id, request.count),
        workspace_id,
        settings.provider_id,
    )
    return SimulationCreated(inserted=inserted)
