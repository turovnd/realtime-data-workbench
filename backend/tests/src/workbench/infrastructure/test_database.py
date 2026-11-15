import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.database import session_scope
from workbench.models import Workspace

pytestmark = pytest.mark.integration


async def test_orm_session_scopes_commit_and_rollback(database: AsyncEngine) -> None:
    async with session_scope(database) as session:
        workspace = Workspace(id="session-check", cursor=5)
        session.add(workspace)
    assert workspace.cursor == 5

    with pytest.raises(RuntimeError, match="Rollback check"):
        async with session_scope(database) as session:
            stored = await session.get(Workspace, "session-check")
            assert stored is not None
            stored.cursor = 9
            await session.flush()
            raise RuntimeError("Rollback check")

    async with session_scope(database) as session:
        stored = await session.get(Workspace, "session-check")
        assert stored is not None and stored.cursor == 5
