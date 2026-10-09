import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import delete, func, insert, select
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from workbench.infrastructure.tables import accounts, auth_sessions, state
from workbench.logic.errors import ConflictError
from workbench.repositories.coordination import lock_workspace
from workbench.repositories.retention import cleanup_expired
from workbench.repositories.security import digest
from workbench.schemas.auth import Identity


async def issue_session(conn: AsyncConnection, workspace_id: str, account_id: str | None) -> str:
    token = secrets.token_urlsafe(32)
    await conn.execute(delete(auth_sessions).where(auth_sessions.c.expires_at <= datetime.now(UTC)))
    count = int(
        await conn.scalar(
            select(func.count())
            .select_from(auth_sessions)
            .where(auth_sessions.c.workspace_id == workspace_id)
        )
        or 0
    )
    if count >= 10:
        raise ConflictError(
            "This account has ten active sessions. Sign out of an existing session first."
        )
    await conn.execute(
        insert(auth_sessions).values(
            token_hash=digest(token),
            workspace_id=workspace_id,
            account_id=account_id,
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
    )
    return token


async def create_session(engine: AsyncEngine) -> str:
    """Create an independent temporary demo, never an implicit account login."""
    async with engine.begin() as conn:
        await lock_workspace(conn)
        await cleanup_expired(conn)
        count = int(await conn.scalar(select(func.count()).select_from(state)) or 0)
        if count >= 1000:
            raise ConflictError(
                "Demo capacity reached. Try again after temporary workspaces expire."
            )
        workspace_id = str(uuid4())
        await conn.execute(
            insert(state).values(id=workspace_id, cursor=0, created_at=datetime.now(UTC))
        )
        return await issue_session(conn, workspace_id, None)


async def identity(engine: AsyncEngine, token: str) -> Identity | None:
    if not 32 <= len(token) <= 64:
        return None
    async with engine.connect() as conn:
        row = (
            (
                await conn.execute(
                    select(
                        auth_sessions.c.workspace_id, auth_sessions.c.account_id, accounts.c.email
                    )
                    .outerjoin(accounts, accounts.c.id == auth_sessions.c.account_id)
                    .where(
                        auth_sessions.c.token_hash == digest(token),
                        auth_sessions.c.expires_at > datetime.now(UTC),
                    )
                )
            )
            .mappings()
            .first()
        )
        return (
            Identity(
                workspace_id=str(row["workspace_id"]),
                email=row["email"],
                kind="account" if row["account_id"] else "demo",
            )
            if row
            else None
        )


async def resolve_session(engine: AsyncEngine, token: str) -> str | None:
    result = await identity(engine, token)
    return result.workspace_id if result else None


async def logout(engine: AsyncEngine, token: str) -> None:
    async with engine.begin() as conn:
        await conn.execute(delete(auth_sessions).where(auth_sessions.c.token_hash == digest(token)))
