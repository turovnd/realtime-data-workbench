from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, insert, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.tables import accounts, state
from workbench.logic.errors import ConflictError
from workbench.repositories.coordination import lock_workspace
from workbench.repositories.sessions import issue_session
from workbench.schemas.auth import SessionResult


async def create_account(engine: AsyncEngine, email: str, password_hash: str) -> SessionResult:
    async with engine.begin() as conn:
        await lock_workspace(conn)
        if await conn.scalar(select(accounts.c.id).where(accounts.c.email == email)):
            raise ConflictError("Unable to register with those details. Try signing in.")
        count = int(await conn.scalar(select(func.count()).select_from(state)) or 0)
        if count >= 1000:
            raise ConflictError("Account capacity reached")
        workspace_id, account_id = str(uuid4()), str(uuid4())
        await conn.execute(
            insert(state).values(id=workspace_id, cursor=0, created_at=datetime.now(UTC))
        )
        await conn.execute(
            insert(accounts).values(
                id=account_id,
                workspace_id=workspace_id,
                email=email,
                password_hash=password_hash,
            )
        )
        token = await issue_session(conn, workspace_id, account_id)
        return SessionResult(workspace_id=workspace_id, email=email, kind="account", token=token)


async def find_account(engine: AsyncEngine, email: str) -> RowMapping | None:
    async with engine.connect() as conn:
        return (
            (await conn.execute(select(accounts).where(accounts.c.email == email)))
            .mappings()
            .first()
        )


async def account_session(engine: AsyncEngine, account: RowMapping) -> SessionResult:
    async with engine.begin() as conn:
        await lock_workspace(conn)
        token = await issue_session(conn, str(account["workspace_id"]), str(account["id"]))
        return SessionResult(
            workspace_id=str(account["workspace_id"]),
            email=str(account["email"]),
            kind="account",
            token=token,
        )
