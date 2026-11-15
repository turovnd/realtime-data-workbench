from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.database import session_scope
from workbench.logic.errors import ConflictError
from workbench.models import Account, Workspace
from workbench.repositories.coordination import lock_workspace
from workbench.repositories.sessions import issue_session
from workbench.schemas.auth import SessionResult


async def create_account(engine: AsyncEngine, email: str, password_hash: str) -> SessionResult:
    async with session_scope(engine) as session:
        await lock_workspace(session)

        existing = await session.scalar(select(Account.id).where(Account.email == email))
        if existing is not None:
            raise ConflictError("Unable to register with those details. Try signing in.")

        count = await session.scalar(select(func.count()).select_from(Workspace))
        if count is not None and count >= 1000:
            raise ConflictError("Account capacity reached")

        workspace = Workspace(id=str(uuid4()), cursor=0, created_at=datetime.now(UTC))
        session.add(workspace)
        await session.flush()

        account = Account(
            id=str(uuid4()),
            workspace_id=workspace.id,
            email=email,
            password_hash=password_hash,
        )
        session.add(account)
        await session.flush()

        token = await issue_session(session, workspace.id, account.id)

        return SessionResult(
            workspace_id=workspace.id,
            email=account.email,
            kind="account",
            token=token,
        )


async def find_account(engine: AsyncEngine, email: str) -> Account | None:
    async with session_scope(engine) as session:
        return await session.scalar(select(Account).where(Account.email == email))


async def account_session(engine: AsyncEngine, account: Account) -> SessionResult:
    async with session_scope(engine) as session:
        await lock_workspace(session)
        token = await issue_session(session, account.workspace_id, account.id)

        return SessionResult(
            workspace_id=account.workspace_id,
            email=account.email,
            kind="account",
            token=token,
        )
