"""Authenticated cursor interpretation and stable, bounded feed views."""

from sqlalchemy.orm import Session

from common.infrastructure.pagination import encode_cursor
from common.logic.errors import CursorError
from common.logic.pagination import create_view, resume_view
from common.repositories import views
from common.repositories.coordination import lock_workspace
from common.repositories.feedback import hydrate
from common.schemas.feedback import FeedFilters, FeedPage


def feed_page(
    session: Session,
    workspace_id: str,
    filters: FeedFilters,
    limit: int = 12,
    cursor: str | None = None,
) -> FeedPage:
    if not 1 <= limit <= 50:
        raise CursorError("Limit must be between 1 and 50")
    filter_key = filters.model_dump_json()
    lock_workspace(session)
    if cursor is not None:
        continuation = resume_view(session, cursor, workspace_id, filter_key)
        view, before = continuation.view, continuation.position
        if before > view.watermark + 1:
            raise CursorError("The cursor position is outside this feedback view")
    else:
        ids, watermark = views.matching_ids(session, workspace_id, filters)
        view = create_view(session, workspace_id, filter_key, ids, watermark)
        before = watermark + 1
    selected = views.page_ids(session, workspace_id, view.record_ids, before, limit)
    page = selected[:limit]
    next_cursor = (
        encode_cursor(view.id, page[-1][1], view.secret) if len(selected) > limit else None
    )
    return FeedPage(
        workspace_id=workspace_id,
        records=hydrate(session, workspace_id, [row[0] for row in page]),
        next_cursor=next_cursor,
        refresh_cursor=encode_cursor(view.id, view.watermark + 1, view.secret),
        watermark=view.watermark,
        revision=views.revision(session, workspace_id),
        total=len(view.record_ids),
    )
