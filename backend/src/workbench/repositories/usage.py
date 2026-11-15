"""Persist admission for each paid attempt before contacting the provider."""

from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.database import session_scope
from workbench.models import ProviderUsage
from workbench.repositories.coordination import lock_workspace


async def reserve_live_call(engine: AsyncEngine, budget: int | None) -> bool:
    """Count every admitted attempt; None removes the ceiling without resetting usage."""
    async with session_scope(engine) as session:
        await lock_workspace(session)
        usage = await session.get(ProviderUsage, "openrouter")
        used = usage.calls if usage is not None else 0
        if budget is not None and used >= budget:
            return False
        if usage is None:
            session.add(ProviderUsage(id="openrouter", calls=1))
        else:
            usage.calls += 1
        return True
