import asyncio

import pytest
from sqlalchemy import update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.tables import records
from workbench.logic.errors import ConflictError
from workbench.logic.ingestion import ingest
from workbench.logic.synthetic import synthetic_inputs
from workbench.repositories.inspection import snapshot
from workbench.schemas.feedback import FeedbackInput

pytestmark = pytest.mark.integration


async def test_atomic_idempotent_ingestion_and_conflict(database: AsyncEngine) -> None:
    inputs = synthetic_inputs("same", 2)
    results = await asyncio.gather(ingest(database, inputs), ingest(database, inputs))
    assert sorted(results) == [0, 2]
    bad = FeedbackInput(identity=inputs[0].identity, text="different", channel="Support")
    with pytest.raises(ConflictError):
        await ingest(database, [bad])
    view = await snapshot(database)
    assert len(view.records) == 2
    assert sum(len(row.jobs) for row in view.records) == 2
    async with database.begin() as conn:
        with pytest.raises(DBAPIError, match="immutable record"):
            await conn.execute(update(records).values(text="cannot rewrite history"))
