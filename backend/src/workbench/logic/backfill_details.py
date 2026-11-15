"""Read a frozen batch selection and its original processing results."""

from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.database import session_scope
from workbench.infrastructure.pagination import encode_cursor
from workbench.logic.errors import CursorError, NotFoundError
from workbench.logic.pagination import create_view, resume_view
from workbench.repositories import backfills, views
from workbench.repositories.coordination import lock_workspace
from workbench.schemas.backfill_details import BatchPage


async def backfill_page(
    engine: AsyncEngine,
    workspace_id: str,
    batch_id: str,
    limit: int = 10,
    cursor: str | None = None,
) -> BatchPage:
    if not 1 <= limit <= 50:
        raise CursorError("Limit must be between 1 and 50")
    scope = "backfill:" + batch_id
    async with session_scope(engine) as session:
        await lock_workspace(session)
        batch = await backfills.get_backfill(session, workspace_id, batch_id)
        if batch is None:
            raise NotFoundError("Batch does not exist")
        if cursor is not None:
            continuation = await resume_view(session, cursor, workspace_id, scope)
            view, before = continuation.view, continuation.position
            if before > view.watermark + 1:
                raise CursorError("The cursor position is outside this batch view")
        else:
            view = await create_view(
                session, workspace_id, scope, batch.record_ids, batch.view.watermark
            )
            before = batch.view.watermark + 1
        selected = await views.page_ids(session, workspace_id, view.record_ids, before, limit)
        page = selected[:limit]
        items = await backfills.batch_items(
            session, workspace_id, [row[0] for row in page], batch.view.config
        )
        return BatchPage(
            batch=batch.view,
            items=items,
            next_cursor=(
                encode_cursor(view.id, page[-1][1], view.secret) if len(selected) > limit else None
            ),
        )
