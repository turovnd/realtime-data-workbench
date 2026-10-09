"""Authenticated cursor interpretation and stable, bounded feed views."""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.logic.cursors import decode_cursor, encode_cursor
from workbench.logic.errors import CursorError, CursorExpired
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
    async with engine.begin() as conn:
        await lock_workspace(conn)
        now = datetime.now(UTC)
        if cursor is not None:
            view_id, before, payload, signature = decode_cursor(cursor)
            view = await views.get_view(conn, view_id)
            if not view or view.workspace_id != workspace_id:
                raise CursorError("The cursor does not match this workspace and filter")
            if view.expires_at <= now:
                raise CursorExpired("This view expired. Refresh to open a current view.")
            expected = hmac.new(view.secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected) or view.filter_key != filter_key:
                raise CursorError("The cursor does not match this workspace and filter")
        else:
            await views.prune_views(conn, workspace_id, now)
            ids, watermark = await views.matching_ids(conn, workspace_id, filters)
            before = watermark + 1
            view = views.StoredView(
                id=str(uuid4()),
                workspace_id=workspace_id,
                filter_key=filter_key,
                record_ids=ids,
                watermark=watermark,
                secret=secrets.token_urlsafe(32),
                expires_at=now + timedelta(minutes=10),
            )
            await views.store_view(conn, view)
        selected = await views.page_ids(conn, workspace_id, view.record_ids, before, limit)
        page = selected[:limit]
        next_cursor = (
            encode_cursor(view.id, page[-1][1], view.secret) if len(selected) > limit else None
        )
        return FeedPage(
            workspace_id=workspace_id,
            records=await hydrate(conn, workspace_id, [row[0] for row in page]),
            next_cursor=next_cursor,
            refresh_cursor=encode_cursor(view.id, view.watermark + 1, view.secret),
            watermark=view.watermark,
            revision=await views.revision(conn, workspace_id),
            total=len(view.record_ids),
        )
