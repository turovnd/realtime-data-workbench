from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.database import session_scope
from workbench.logic.ingestion import ingest
from workbench.logic.synthetic import synthetic_inputs
from workbench.models import Workspace
from workbench.repositories.coordination import lock_workspace
from workbench.repositories.inspection import snapshot
from workbench.repositories.retention import cleanup_expired
from workbench.repositories.sessions import create_session, resolve_session
from workbench.workers.processing import process_one

pytestmark = pytest.mark.integration


async def test_expired_session_cleanup_preserves_active_workspace(database: AsyncEngine) -> None:
    expired_token = await create_session(database)
    active_token = await create_session(database)
    expired = await resolve_session(database, expired_token)
    active = await resolve_session(database, active_token)
    assert expired and active

    await ingest(database, synthetic_inputs("same-identity", 1), expired)
    await ingest(database, synthetic_inputs("same-identity", 1), active)
    await process_one(database)

    async with session_scope(database) as session:
        await lock_workspace(session)
        workspace = await session.get(Workspace, expired)
        assert workspace is not None
        workspace.created_at = datetime.now(UTC) - timedelta(hours=25)
        await session.flush()

        assert await cleanup_expired(session) == 1

    assert await resolve_session(database, expired_token) is None
    assert len((await snapshot(database, active)).records) == 1
    assert (await snapshot(database, expired)).records == []
