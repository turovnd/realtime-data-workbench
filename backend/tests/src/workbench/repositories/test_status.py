import pytest
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.database import session_scope
from workbench.logic.backfills import start_backfill
from workbench.logic.ingestion import ingest
from workbench.logic.synthetic import synthetic_inputs
from workbench.models import Feedback
from workbench.repositories.status import feed_status
from workbench.schemas.backfills import BackfillInput
from workbench.schemas.feedback import FeedStatus
from workbench.workers.processing import process_one

pytestmark = pytest.mark.integration


async def test_status_query_count_does_not_grow_with_recent_batches(
    database: AsyncEngine,
) -> None:
    await ingest(database, synthetic_inputs("status", 10))
    while await process_one(database):
        pass
    async with session_scope(database) as session:
        record_ids = list(await session.scalars(select(Feedback.id).order_by(Feedback.sequence)))

    first_batch = await start_backfill(database, BackfillInput(record_ids=record_ids[:1]))
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
            status = await feed_status(database, "test", "deterministic-rules/1")
        finally:
            event.remove(database.sync_engine, "before_cursor_execute", record_query)
        return status, len(statements)

    one_batch, one_count = await measured_status()
    assert len(one_batch.batches) == 1
    assert one_batch.batches[0].completed == 1

    for record_id in record_ids[1:]:
        await start_backfill(database, BackfillInput(record_ids=[record_id]))
    ten_batches, ten_count = await measured_status()

    assert one_count == ten_count <= 5
    assert len(ten_batches.batches) == 10
    assert all(batch.selected == 1 and batch.failed == 0 for batch in ten_batches.batches)
    assert {batch.id: batch.completed for batch in ten_batches.batches} == {
        batch.id: int(batch.id == first_batch) for batch in ten_batches.batches
    }
