from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.database import session_scope
from workbench.logic.auth import login, register
from workbench.logic.errors import AuthenticationError
from workbench.models import Account, AuthSession, Workspace
from workbench.repositories.coordination import lock_workspace
from workbench.repositories.retention import cleanup_expired
from workbench.repositories.sessions import identity, logout
from workbench.schemas.auth import Credentials

pytestmark = pytest.mark.integration


async def test_password_login_logout_and_demo_cleanup_are_independent(
    database: AsyncEngine,
) -> None:
    credentials = Credentials(email="Reader@example.test", password="correct-horse-example")
    registered = await register(database, credentials)
    signed_in = await login(database, credentials)

    assert signed_in.workspace_id == registered.workspace_id
    assert signed_in.token != registered.token

    async with session_scope(database) as session:
        account = (await session.scalars(select(Account))).one()
        assert account.password_hash.startswith("$argon2id$")
        assert credentials.password not in account.password_hash
        assert signed_in.token not in await session.scalars(select(AuthSession.token_hash))

    with pytest.raises(AuthenticationError):
        await login(
            database, Credentials(email=credentials.email, password="incorrect-password-value")
        )

    await logout(database, signed_in.token)
    assert await identity(database, signed_in.token) is None
    assert await identity(database, registered.token) is not None

    async with session_scope(database) as session:
        await lock_workspace(session)
        workspace = await session.get(Workspace, registered.workspace_id)
        assert workspace is not None
        workspace.created_at = datetime.now(UTC) - timedelta(days=2)
        await session.flush()

        assert await cleanup_expired(session) == 0

    assert (await login(database, credentials)).workspace_id == registered.workspace_id
