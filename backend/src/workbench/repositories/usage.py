"""Persist admission for each paid attempt before contacting the provider."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.database import session_scope
from workbench.models import ProviderUsage
from workbench.repositories.coordination import lock_workspace


async def reserve_live_call(
    engine: AsyncEngine, budget: int | None, provider: str = "openrouter"
) -> bool:
    """Count attempts across providers; switching never resets the lifetime ceiling.

    Existing OpenRouter reservations remain in their row. The serialized sum includes
    all provider rows, then increments only the provider admitting this attempt.
    """
    async with session_scope(engine) as session:
        await lock_workspace(session)
        used = int(await session.scalar(select(func.sum(ProviderUsage.calls))) or 0)
        if budget is not None and used >= budget:
            return False
        usage = await session.get(ProviderUsage, provider)
        if usage is None:
            session.add(ProviderUsage(id=provider, calls=1))
        else:
            usage.calls += 1
        return True
