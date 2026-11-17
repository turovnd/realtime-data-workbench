import ssl
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Concatenate

from sqlalchemy import text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool


def connection_options(value: str) -> tuple[URL, dict[str, object]]:
    """Adapt PostgreSQL URLs with an explicit verified-TLS policy for Neon."""
    try:
        url = make_url(value)
        if url.drivername not in {"postgres", "postgresql", "postgresql+asyncpg"}:
            raise ValueError("Only PostgreSQL connections using asyncpg are supported")
        # Validate the port here so a malformed URL cannot leak credentials in driver errors.
        url = url.set(drivername="postgresql+asyncpg", port=url.port)
    except (ArgumentError, ValueError):
        raise ValueError("Invalid PostgreSQL connection URL") from None

    mode = url.query.get("sslmode")
    verified_modes = {"require", "verify-ca", "verify-full"}
    binding = url.query.get("channel_binding")
    if binding is not None:
        if (
            binding != "require"
            or not isinstance(mode, str)
            or mode not in verified_modes
            or not (url.host or "").lower().endswith(".neon.tech")
            or {"host", "hostaddr"}.intersection(url.query)
        ):
            raise ValueError("Unsupported database channel_binding or TLS configuration")
        # Neon documents verified TLS as the alternative for clients without channel
        # binding. Apply that policy only to its known URL form, never arbitrary hosts.
        url = url.difference_update_query(["channel_binding"])

    options: dict[str, object] = {"timeout": 10}
    if mode is not None:
        if "ssl" in url.query or not isinstance(mode, str):
            raise ValueError("Specify a single database sslmode without a conflicting ssl option")
        if mode in verified_modes:
            # asyncpg's string 'require' disables verification. A context verifies both
            # the trust chain and hostname, including for Neon-generated require URLs.
            options["ssl"] = ssl.create_default_context()
        elif mode == "disable":
            options["ssl"] = False
        else:
            raise ValueError("Database sslmode must be require, verify-ca, verify-full or disable")
        url = url.difference_update_query(["sslmode"])
    return url, options


def create_engine(url: str, *, pooled: bool = True) -> AsyncEngine:
    address, options = connection_options(url)
    if not pooled:
        return create_async_engine(address, connect_args=options, poolclass=NullPool)
    return create_async_engine(
        address,
        connect_args=options,
        pool_size=3,
        max_overflow=1,
        pool_timeout=10,
        pool_pre_ping=True,
    )


async def check_database(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


@asynccontextmanager
async def session_scope(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with AsyncSession(engine, expire_on_commit=False) as session, session.begin():
        yield session


async def run_transaction[Result, **Params](
    engine: AsyncEngine,
    operation: Callable[Concatenate[Session, Params], Result],
    *args: Params.args,
    **kwargs: Params.kwargs,
) -> Result:
    """Run one ORM operation atomically while database I/O yields to asyncio."""
    async with session_scope(engine) as session:
        return await session.run_sync(operation, *args, **kwargs)
