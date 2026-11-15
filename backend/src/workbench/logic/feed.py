"""Authenticated cursor interpretation and stable, bounded feed views."""

from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.database import session_scope
from workbench.infrastructure.pagination import encode_cursor
from workbench.logic.errors import CursorError
from workbench.logic.pagination import create_view, resume_view
from workbench.repositories import views
from workbench.repositories.coordination import lock_workspace
from workbench.repositories.feedback import hydrate
from workbench.schemas.feedback import FeedFilters, FeedPage


async def feed_page(
    engine: AsyncEngine,
    workspace_id: str,
    filters: FeedFilters,
    limit: int = 12,
    cursor: str | None = None,
) -> FeedPage:
    if not 1 <= limit <= 50:
        raise CursorError("Limit must be between 1 and 50")
    filter_key = filters.model_dump_json()
    async with session_scope(engine) as session:
        await lock_workspace(session)
        if cursor is not None:
            continuation = await resume_view(session, cursor, workspace_id, filter_key)
            view, before = continuation.view, continuation.position
            if before > view.watermark + 1:
                raise CursorError("The cursor position is outside this feedback view")
        else:
            ids, watermark = await views.matching_ids(session, workspace_id, filters)
            view = await create_view(session, workspace_id, filter_key, ids, watermark)
            before = watermark + 1
        selected = await views.page_ids(session, workspace_id, view.record_ids, before, limit)
        page = selected[:limit]
        next_cursor = (
            encode_cursor(view.id, page[-1][1], view.secret) if len(selected) > limit else None
        )
        return FeedPage(
            workspace_id=workspace_id,
            records=await hydrate(session, workspace_id, [row[0] for row in page]),
            next_cursor=next_cursor,
            refresh_cursor=encode_cursor(view.id, view.watermark + 1, view.secret),
            watermark=view.watermark,
            revision=await views.revision(session, workspace_id),
            total=len(view.record_ids),
        )
