"""Create and resume authenticated, workspace-scoped pagination views."""

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from workbench.infrastructure.pagination import decode_cursor, verify_cursor
from workbench.logic.errors import CursorError, CursorExpired
from workbench.models import FeedView
from workbench.repositories.views import prune_views

VIEW_LIFETIME = timedelta(minutes=10)


@dataclass(frozen=True)
class ViewCursor:
    view: FeedView
    position: int


async def resume_view(
    session: AsyncSession, token: str, workspace_id: str, scope: str
) -> ViewCursor:
    cursor = decode_cursor(token)
    view = await session.get(FeedView, cursor.view_id)
    if view is None or view.workspace_id != workspace_id or view.filter_key != scope:
        raise CursorError("The cursor does not match this workspace and view")

    verify_cursor(cursor, view.secret)
    if view.expires_at <= datetime.now(UTC):
        raise CursorExpired("This view expired. Refresh to open a current view.")

    return ViewCursor(view=view, position=cursor.position)


async def create_view(
    session: AsyncSession,
    workspace_id: str,
    scope: str,
    record_ids: list[str],
    watermark: int,
) -> FeedView:
    now = datetime.now(UTC)
    await prune_views(session, workspace_id, now)

    view = FeedView(
        id=str(uuid4()),
        workspace_id=workspace_id,
        filter_key=scope,
        record_ids=record_ids,
        watermark=watermark,
        secret=secrets.token_urlsafe(32),
        expires_at=now + VIEW_LIFETIME,
    )
    session.add(view)
    await session.flush()
    return view
