import asyncio

import pytest
from sqlalchemy import update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine

from common.infrastructure.database import run_transaction
from common.logic.errors import ConflictError
from common.logic.ingestion import ingest
from common.logic.synthetic import synthetic_inputs
from common.models import Feedback
from common.repositories.inspection import snapshot
from common.schemas.feedback import FeedbackInput

pytestmark = pytest.mark.integration


async def test_atomic_idempotent_ingestion_and_conflict(database: AsyncEngine) -> None:
    inputs = synthetic_inputs("same", 2)
    results = await asyncio.gather(
        run_transaction(database, ingest, inputs), run_transaction(database, ingest, inputs)
    )
    assert sorted(results) == [0, 2]
    bad = FeedbackInput(identity=inputs[0].identity, text="different", channel="Support")
    with pytest.raises(ConflictError):
        await run_transaction(database, ingest, [bad])
    view = await run_transaction(database, snapshot)
    assert len(view.records) == 2
    assert sum(len(row.jobs) for row in view.records) == 2
    async with database.begin() as conn:
        with pytest.raises(DBAPIError, match="immutable record"):
            await conn.execute(update(Feedback).values(text="cannot rewrite history"))
