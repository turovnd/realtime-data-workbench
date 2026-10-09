from sqlalchemy import text, update
from sqlalchemy.ext.asyncio import AsyncConnection

from workbench.infrastructure.tables import state


async def lock_workspace(conn: AsyncConnection) -> None:
    await conn.execute(text("SELECT pg_advisory_xact_lock(72100692)"))


async def changed(conn: AsyncConnection, workspace_id: str = "test") -> None:
    await conn.execute(
        update(state).where(state.c.id == workspace_id).values(cursor=state.c.cursor + 1)
    )
