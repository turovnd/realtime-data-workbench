import asyncio

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.database import session_scope
from workbench.logic.ingestion import ingest
from workbench.logic.synthetic import synthetic_inputs
from workbench.models import Workspace
from workbench.repositories.inspection import snapshot

pytestmark = pytest.mark.integration


async def test_snapshot_waits_for_mutation_counter_commit(database: AsyncEngine) -> None:
    await ingest(database, synthetic_inputs("first", 1))

    async with session_scope(database) as session:
        workspace = (await session.scalars(select(Workspace).with_for_update())).one()
        workspace.cursor += 1
        await session.flush()
        pending = asyncio.create_task(snapshot(database))

    view = await pending
    assert view.cursor == 2
    assert len(view.records) == 1
