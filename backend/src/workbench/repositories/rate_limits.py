from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.tables import auth_buckets
from workbench.logic.errors import RateLimitError
from workbench.repositories.coordination import lock_workspace
from workbench.repositories.security import digest


async def limit_auth(engine: AsyncEngine, key: str, limit: int = 20) -> None:
    async with engine.begin() as conn:
        await lock_workspace(conn)
        now = datetime.now(UTC)
        await conn.execute(delete(auth_buckets).where(auth_buckets.c.expires_at <= now))
        name = digest(key)
        row = (
            (await conn.execute(select(auth_buckets).where(auth_buckets.c.key == name)))
            .mappings()
            .first()
        )
        if row and int(row["attempts"]) >= limit:
            raise RateLimitError("Too many authentication attempts. Try again in 15 minutes.")
        if row:
            await conn.execute(
                update(auth_buckets)
                .where(auth_buckets.c.key == name)
                .values(attempts=auth_buckets.c.attempts + 1)
            )
        else:
            count = int(await conn.scalar(select(func.count()).select_from(auth_buckets)) or 0)
            if count >= 2000:
                raise RateLimitError("Authentication is temporarily busy. Try again later.")
            await conn.execute(
                insert(auth_buckets).values(
                    key=name, attempts=1, expires_at=now + timedelta(minutes=15)
                )
            )
