from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.tables import accounts, auth_sessions, state
from workbench.logic.auth import login, register
from workbench.logic.errors import AuthenticationError
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
    async with database.connect() as conn:
        row = (await conn.execute(select(accounts))).mappings().one()
        assert row["password_hash"].startswith("$argon2id$")
        assert credentials.password not in row["password_hash"]
        assert signed_in.token not in [
            row.token_hash for row in (await conn.execute(select(auth_sessions))).all()
        ]
    with pytest.raises(AuthenticationError):
        await login(
            database, Credentials(email=credentials.email, password="incorrect-password-value")
        )
    await logout(database, signed_in.token)
    assert await identity(database, signed_in.token) is None
    assert await identity(database, registered.token) is not None
    async with database.begin() as conn:
        await lock_workspace(conn)
        await conn.execute(
            update(state)
            .where(state.c.id == registered.workspace_id)
            .values(created_at=datetime.now(UTC) - timedelta(days=2))
        )
        assert await cleanup_expired(conn) == 0
    assert (await login(database, credentials)).workspace_id == registered.workspace_id
