import asyncio

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.logic.ingestion import ingest
from workbench.logic.synthetic import synthetic_inputs
from workbench.repositories.inspection import snapshot

pytestmark = pytest.mark.integration


async def test_snapshot_waits_for_mutation_counter_commit(database: AsyncEngine) -> None:
    await ingest(database, synthetic_inputs("first", 1))
    async with database.begin() as conn:
        # Holding the workspace lock prevents snapshots from mixing cursor/data commits.
        from workbench.infrastructure.tables import state

        await conn.execute(select(state).with_for_update())
        await conn.execute(update(state).values(cursor=state.c.cursor + 1))
        pending = asyncio.create_task(snapshot(database))
    view = await pending
    assert view.cursor == 2
    assert len(view.records) == 1
