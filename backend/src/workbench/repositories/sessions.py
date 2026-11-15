import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from workbench.infrastructure.database import session_scope
from workbench.logic.errors import ConflictError
from workbench.models import Account, AuthSession, Workspace
from workbench.repositories.coordination import lock_workspace
from workbench.repositories.retention import cleanup_expired
from workbench.repositories.security import digest
from workbench.schemas.auth import Identity


async def issue_session(session: AsyncSession, workspace_id: str, account_id: str | None) -> str:
    now = datetime.now(UTC)
    await session.execute(delete(AuthSession).where(AuthSession.expires_at <= now))
    count = await session.scalar(
        select(func.count())
        .select_from(AuthSession)
        .where(AuthSession.workspace_id == workspace_id)
    )
    if count is not None and count >= 10:
        raise ConflictError(
            "This account has ten active sessions. Sign out of an existing session first."
        )

    token = secrets.token_urlsafe(32)
    session.add(
        AuthSession(
            token_hash=digest(token),
            workspace_id=workspace_id,
            account_id=account_id,
            expires_at=now + timedelta(hours=24),
        )
    )
    await session.flush()

    return token


async def create_session(engine: AsyncEngine) -> str:
    """Create an independent temporary demo, never an implicit account login."""
    async with session_scope(engine) as session:
        await lock_workspace(session)
        await cleanup_expired(session)

        count = await session.scalar(select(func.count()).select_from(Workspace))
        if count is not None and count >= 1000:
            raise ConflictError(
                "Demo capacity reached. Try again after temporary workspaces expire."
            )

        workspace = Workspace(id=str(uuid4()), cursor=0, created_at=datetime.now(UTC))
        session.add(workspace)
        await session.flush()

        return await issue_session(session, workspace.id, None)


async def identity(engine: AsyncEngine, token: str) -> Identity | None:
    if not 32 <= len(token) <= 64:
        return None

    async with session_scope(engine) as session:
        auth_session = await session.scalar(
            select(AuthSession).where(
                AuthSession.token_hash == digest(token),
                AuthSession.expires_at > datetime.now(UTC),
            )
        )
        if auth_session is None:
            return None

        account = (
            await session.get(Account, auth_session.account_id)
            if auth_session.account_id is not None
            else None
        )

        return Identity(
            workspace_id=auth_session.workspace_id,
            email=account.email if account is not None else None,
            kind="account" if auth_session.account_id is not None else "demo",
        )


async def resolve_session(engine: AsyncEngine, token: str) -> str | None:
    result = await identity(engine, token)

    return result.workspace_id if result is not None else None


async def logout(engine: AsyncEngine, token: str) -> None:
    async with session_scope(engine) as session:
        await session.execute(delete(AuthSession).where(AuthSession.token_hash == digest(token)))
