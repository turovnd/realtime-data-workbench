from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.database import session_scope
from workbench.logic.errors import RateLimitError
from workbench.models import AuthBucket
from workbench.repositories.coordination import lock_workspace
from workbench.repositories.security import digest


async def limit_auth(engine: AsyncEngine, key: str, limit: int = 20) -> None:
    async with session_scope(engine) as session:
        await lock_workspace(session)

        now = datetime.now(UTC)
        await session.execute(delete(AuthBucket).where(AuthBucket.expires_at <= now))
        name = digest(key)
        bucket = await session.get(AuthBucket, name)

        if bucket is not None:
            if bucket.attempts >= limit:
                raise RateLimitError("Too many authentication attempts. Try again in 15 minutes.")

            bucket.attempts += 1
            return

        count = await session.scalar(select(func.count()).select_from(AuthBucket))
        if count is not None and count >= 2000:
            raise RateLimitError("Authentication is temporarily busy. Try again later.")

        session.add(AuthBucket(key=name, attempts=1, expires_at=now + timedelta(minutes=15)))
