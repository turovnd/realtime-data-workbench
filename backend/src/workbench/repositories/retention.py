from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncConnection

from workbench.infrastructure.tables import (
    accounts,
    auth_sessions,
    batches,
    feed_views,
    jobs,
    outputs,
    records,
    state,
)


async def cleanup_expired(conn: AsyncConnection) -> int:
    now = datetime.now(UTC)
    await conn.execute(delete(feed_views).where(feed_views.c.expires_at <= now))
    await conn.execute(delete(auth_sessions).where(auth_sessions.c.expires_at <= now))
    expired = list(
        (
            await conn.execute(
                select(state.c.id)
                .where(
                    state.c.created_at < now - timedelta(hours=24),
                    ~state.c.id.in_(select(accounts.c.workspace_id)),
                )
                .limit(20)
            )
        ).scalars()
    )
    if not expired:
        return 0
    await conn.execute(text("SET LOCAL workbench.maintenance = 'on'"))
    for table in (auth_sessions, feed_views, outputs, jobs, batches, records):
        await conn.execute(delete(table).where(table.c.workspace_id.in_(expired)))
    await conn.execute(delete(state).where(state.c.id.in_(expired)))
    await conn.execute(text("SET LOCAL workbench.maintenance = 'off'"))
    return len(expired)
