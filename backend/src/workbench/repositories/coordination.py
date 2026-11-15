"""Serialize bounded demo operations and advance affected workspace revisions."""

from sqlalchemy import text, update
from sqlalchemy.ext.asyncio import AsyncSession

from workbench.models import Workspace


async def lock_workspace(session: AsyncSession) -> None:
    # This is intentionally a process-independent global admission lock: capacity
    # and provider budgets are shared across workspaces in this bounded demo.
    await session.execute(text("SELECT pg_advisory_xact_lock(72100692)"))


async def changed(session: AsyncSession, workspace_id: str = "test") -> None:
    await session.execute(
        update(Workspace).where(Workspace.id == workspace_id).values(cursor=Workspace.cursor + 1)
    )
