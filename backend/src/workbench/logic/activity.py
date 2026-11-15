"""Read unified activity without enqueuing jobs or contacting a provider."""

from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.database import session_scope
from workbench.infrastructure.pagination import encode_cursor
from workbench.logic.errors import CursorError
from workbench.logic.pagination import create_view, resume_view
from workbench.repositories import activity, views
from workbench.repositories.activity_items import hydrate_activity
from workbench.repositories.coordination import lock_workspace
from workbench.schemas.activity import ActivityPage


async def activity_page(
    engine: AsyncEngine, workspace_id: str, limit: int = 10, cursor: str | None = None
) -> ActivityPage:
    if not 1 <= limit <= 50:
        raise CursorError("Limit must be between 1 and 50")
    async with session_scope(engine) as session:
        await lock_workspace(session)
        if cursor is not None:
            continuation = await resume_view(session, cursor, workspace_id, "activity")
            view, after = continuation.view, continuation.position
            if after > len(view.record_ids):
                raise CursorError("The activity cursor position is invalid")
        else:
            ids, has_older = await activity.activity_ids(session, workspace_id)
            view = await create_view(session, workspace_id, "activity", ids, int(has_older))
            after = 0
        selected = await activity.page_activity_ids(session, workspace_id, view.id, after, limit)
        page = selected[:limit]
        return ActivityPage(
            items=await hydrate_activity(session, workspace_id, [row[0] for row in page]),
            next_cursor=(
                encode_cursor(view.id, page[-1][1], view.secret) if len(selected) > limit else None
            ),
            refresh_cursor=encode_cursor(view.id, 0, view.secret),
            total=len(view.record_ids),
            has_older=bool(view.watermark),
            revision=await views.revision(session, workspace_id),
        )
