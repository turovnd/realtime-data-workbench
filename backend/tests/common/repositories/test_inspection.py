import asyncio

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from common.infrastructure.database import run_transaction, session_scope
from common.logic.ingestion import ingest
from common.logic.synthetic import synthetic_inputs
from common.models import Workspace
from common.repositories.inspection import snapshot

pytestmark = pytest.mark.integration


async def test_snapshot_waits_for_mutation_counter_commit(database: AsyncEngine) -> None:
    await run_transaction(database, ingest, synthetic_inputs("first", 1))

    async with session_scope(database) as session:
        workspace = (await session.scalars(select(Workspace).with_for_update())).one()
        workspace.cursor += 1
        await session.flush()
        pending = asyncio.create_task(run_transaction(database, snapshot))

    view = await pending
    assert view.cursor == 2
    assert len(view.records) == 1
