from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from common.infrastructure.database import run_transaction, session_scope
from common.logic.ingestion import ingest
from common.logic.synthetic import synthetic_inputs
from common.models import Workspace
from common.repositories.coordination import lock_workspace
from common.repositories.inspection import snapshot
from common.repositories.retention import cleanup_expired
from common.repositories.sessions import create_session, resolve_session
from modules.worker.processing import process_one

pytestmark = pytest.mark.integration


async def test_expired_session_cleanup_preserves_active_workspace(database: AsyncEngine) -> None:
    expired_token = await run_transaction(database, create_session)
    active_token = await run_transaction(database, create_session)
    expired = await run_transaction(database, resolve_session, expired_token)
    active = await run_transaction(database, resolve_session, active_token)
    assert expired and active

    await run_transaction(database, ingest, synthetic_inputs("same-identity", 1), expired)
    await run_transaction(database, ingest, synthetic_inputs("same-identity", 1), active)
    await process_one(database)

    async with session_scope(database) as session:
        await session.run_sync(lock_workspace)
        workspace = await session.get(Workspace, expired)
        assert workspace is not None
        workspace.created_at = datetime.now(UTC) - timedelta(hours=25)
        await session.flush()

        assert await session.run_sync(cleanup_expired) == 1

    assert await run_transaction(database, resolve_session, expired_token) is None
    assert len((await run_transaction(database, snapshot, active)).records) == 1
    assert (await run_transaction(database, snapshot, expired)).records == []
