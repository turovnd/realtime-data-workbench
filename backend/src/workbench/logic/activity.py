"""Read unified activity without enqueuing jobs or contacting a provider."""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.logic.activity_cursors import decode_activity_cursor
from workbench.logic.cursors import encode_cursor
from workbench.logic.errors import CursorError, CursorExpired
from workbench.repositories import activity, views
from workbench.repositories.activity_items import hydrate_activity
from workbench.repositories.coordination import lock_workspace
from workbench.schemas.activity import ActivityPage


async def activity_page(
    engine: AsyncEngine, workspace_id: str, limit: int = 10, cursor: str | None = None
) -> ActivityPage:
    if not 1 <= limit <= 50:
        raise CursorError("Limit must be between 1 and 50")
    async with engine.begin() as conn:
        await lock_workspace(conn)
        now = datetime.now(UTC)
        if cursor is not None:
            view_id, after, payload, signature = decode_activity_cursor(cursor)
            view = await views.get_view(conn, view_id)
            if not view or view.workspace_id != workspace_id or view.filter_key != "activity":
                raise CursorError("The cursor does not match this workspace and activity view")
            expected = hmac.new(view.secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected):
                raise CursorError("The activity cursor is invalid")
            if view.expires_at <= now:
                raise CursorExpired("This activity view expired. Refresh to open a new view.")
            if after > len(view.record_ids):
                raise CursorError("The activity cursor position is invalid")
        else:
            await views.prune_views(conn, workspace_id, now)
            ids, has_older = await activity.activity_ids(conn, workspace_id)
            after = 0
            view = views.StoredView(
                id=str(uuid4()),
                workspace_id=workspace_id,
                filter_key="activity",
                record_ids=ids,
                watermark=int(has_older),
                secret=secrets.token_urlsafe(32),
                expires_at=now + timedelta(minutes=10),
            )
            await views.store_view(conn, view)
        selected = await activity.page_activity_ids(conn, workspace_id, view.id, after, limit)
        page = selected[:limit]
        return ActivityPage(
            items=await hydrate_activity(conn, workspace_id, [row[0] for row in page]),
            next_cursor=(
                encode_cursor(view.id, page[-1][1], view.secret) if len(selected) > limit else None
            ),
            refresh_cursor=encode_cursor(view.id, 0, view.secret),
            total=len(view.record_ids),
            has_older=bool(view.watermark),
            revision=await views.revision(conn, workspace_id),
        )
