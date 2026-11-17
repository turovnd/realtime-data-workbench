import pytest
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncEngine

from common.infrastructure.database import run_transaction, session_scope
from common.logic.backfills import start_backfill
from common.logic.ingestion import ingest
from common.logic.synthetic import synthetic_inputs
from common.models import Feedback
from common.repositories.status import feed_status
from common.schemas.backfills import BackfillInput
from common.schemas.feedback import FeedStatus
from modules.worker.processing import process_one

pytestmark = pytest.mark.integration


async def test_status_query_count_does_not_grow_with_recent_batches(
    database: AsyncEngine,
) -> None:
    await run_transaction(database, ingest, synthetic_inputs("status", 10))
    while await process_one(database):
        pass
    async with session_scope(database) as session:
        record_ids = list(await session.scalars(select(Feedback.id).order_by(Feedback.sequence)))

    first_batch = await run_transaction(
        database, start_backfill, BackfillInput(record_ids=record_ids[:1])
    )
    assert await process_one(database)

    async def measured_status() -> tuple[FeedStatus, int]:
        statements: list[str] = []

        def record_query(
            _connection: object,
            _cursor: object,
            statement: str,
            _parameters: object,
            _context: object,
            _executemany: bool,
        ) -> None:
            statements.append(statement)

        event.listen(database.sync_engine, "before_cursor_execute", record_query)
        try:
            status = await run_transaction(database, feed_status, "test", "deterministic-rules/1")
        finally:
            event.remove(database.sync_engine, "before_cursor_execute", record_query)
        return status, len(statements)

    one_batch, one_count = await measured_status()
    assert len(one_batch.batches) == 1
    assert one_batch.batches[0].completed == 1

    for record_id in record_ids[1:]:
        await run_transaction(database, start_backfill, BackfillInput(record_ids=[record_id]))
    ten_batches, ten_count = await measured_status()

    assert one_count == ten_count <= 5
    assert len(ten_batches.batches) == 10
    assert all(batch.selected == 1 and batch.failed == 0 for batch in ten_batches.batches)
    assert {batch.id: batch.completed for batch in ten_batches.batches} == {
        batch.id: int(batch.id == first_batch) for batch in ten_batches.batches
    }
