from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.tables import provider_usage
from workbench.repositories.coordination import lock_workspace


async def reserve_live_call(engine: AsyncEngine, budget: int | None) -> bool:
    """Count every admitted attempt; None removes the ceiling without resetting usage."""
    async with engine.begin() as conn:
        await lock_workspace(conn)
        row = await conn.scalar(
            select(provider_usage.c.calls).where(provider_usage.c.id == "openrouter")
        )
        used = int(row or 0)
        if budget is not None and used >= budget:
            return False
        if row is None:
            await conn.execute(insert(provider_usage).values(id="openrouter", calls=1))
        else:
            await conn.execute(
                update(provider_usage)
                .where(provider_usage.c.id == "openrouter")
                .values(calls=used + 1)
            )
        return True
