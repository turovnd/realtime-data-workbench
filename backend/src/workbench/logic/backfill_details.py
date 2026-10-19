"""Read a frozen batch selection and its original processing results."""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.logic.cursors import decode_cursor, encode_cursor
from workbench.logic.errors import CursorError, CursorExpired, NotFoundError
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
    async with engine.begin() as conn:
        await lock_workspace(conn)
        batch = await backfills.get_backfill(conn, workspace_id, batch_id)
        if batch is None:
            raise NotFoundError("Batch does not exist")
        now = datetime.now(UTC)
        if cursor is not None:
            view_id, before, payload, signature = decode_cursor(cursor)
            view = await views.get_view(conn, view_id)
            if not view or view.workspace_id != workspace_id or view.filter_key != scope:
                raise CursorError("The cursor does not match this workspace and batch")
            expected = hmac.new(view.secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected):
                raise CursorError("The cursor does not match this workspace and batch")
            if view.expires_at <= now:
                raise CursorExpired("This view expired. Refresh to reopen this batch.")
        else:
            await views.prune_views(conn, workspace_id, now)
            before = batch.view.watermark + 1
            view = views.StoredView(
                id=str(uuid4()),
                workspace_id=workspace_id,
                filter_key=scope,
                record_ids=batch.record_ids,
                watermark=batch.view.watermark,
                secret=secrets.token_urlsafe(32),
                expires_at=now + timedelta(minutes=10),
            )
            await views.store_view(conn, view)
        selected = await views.page_ids(conn, workspace_id, view.record_ids, before, limit)
        page = selected[:limit]
        items = await backfills.batch_items(
            conn, workspace_id, [row[0] for row in page], batch.view.config
        )
        return BatchPage(
            batch=batch.view,
            items=items,
            next_cursor=(
                encode_cursor(view.id, page[-1][1], view.secret) if len(selected) > limit else None
            ),
        )
