from typing import Annotated

from fastapi import APIRouter, Query

from workbench.dependencies import Database, Workspace
from workbench.logic.activity import activity_page
from workbench.routers.responses import errors
from workbench.schemas.activity import ActivityPage

router = APIRouter(prefix="/api", tags=["Activity"])


@router.get(
    "/activity",
    response_model=ActivityPage,
    operation_id="listActivity",
    summary="Read automatic, individual and bulk analysis activity",
    description=(
        "Includes one item per automatic or individual analysis job, and one per bulk "
        "backfill (without duplicate child-job items). Each job shows only its exact "
        "stored output revision. A new view orders IDs by current scheduling availability "
        "and an ID tie-breaker; this is not a creation timestamp. Membership and order "
        "freeze for ten minutes; status/results can refresh through refresh_cursor. "
        "Signed workspace-scoped cursors page persisted positions with SQL LIMIT. "
        "At most twenty views are retained per workspace, shared with feedback/backfill "
        "views. Each read window contains at most the latest 6000 IDs; has_older reports "
        "older stored activity without blocking new work or deleting history. This flag "
        "stays fixed throughout the view. Omit cursor to include new work. "
        "This endpoint never enqueues work or calls a provider."
    ),
    responses=errors(400, 401, 410),
)
async def activity(
    database: Database,
    workspace_id: Workspace,
    limit: Annotated[
        int, Query(ge=1, le=50, description="Maximum items per page; default ten")
    ] = 10,
    cursor: Annotated[
        str | None,
        Query(description="Opaque next_cursor or refresh_cursor from this activity view"),
    ] = None,
) -> ActivityPage:
    return await activity_page(database, workspace_id, limit, cursor)
