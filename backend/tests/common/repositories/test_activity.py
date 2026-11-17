from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import event, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncEngine

from common.infrastructure.database import run_transaction, session_scope
from common.infrastructure.pagination import decode_cursor
from common.logic.activity import activity_page
from common.logic.backfills import start_backfill
from common.logic.ingestion import ingest
from common.logic.synthetic import synthetic_inputs
from common.models import AnalysisJob, AnalysisResult, Feedback, ProviderUsage, Workspace
from common.repositories.activity_items import hydrate_activity
from common.schemas.activity import ActivityItem, BatchActivity, FeedbackActivity
from common.schemas.backfills import BackfillInput
from common.schemas.feedback import FeedbackInput
from modules.worker.processing import process_one

pytestmark = pytest.mark.integration


async def test_activity_read_window_pages_large_terminal_history_without_changing_work(
    database: AsyncEngine,
) -> None:
    await run_transaction(
        database,
        ingest,
        [FeedbackInput(identity="long-history", text="Export stops early.", channel="Support")],
    )
    scheduled = datetime(2026, 1, 1, tzinfo=UTC)
    async with session_scope(database) as session:
        record_id = await session.scalar(select(AnalysisJob.record_id))
        assert record_id is not None
        await session.execute(
            update(AnalysisJob).values(status="cancelled", available_at=scheduled)
        )
        await session.execute(
            insert(AnalysisJob),
            [
                {
                    "id": str(UUID(int=run)),
                    "workspace_id": "test",
                    "record_id": record_id,
                    "config": "v2",
                    "run": run,
                    "origin": "analysis",
                    "provider": "deterministic-rules/1",
                    "status": "failed" if run % 2 else "cancelled",
                    "attempts": 3 if run % 2 else 0,
                    "error": "Test failure" if run % 2 else None,
                    "available_at": scheduled + timedelta(seconds=run),
                }
                for run in range(2, 6003)
            ],
        )
        await session.execute(insert(ProviderUsage).values(id="openrouter", calls=7))
        revision = await session.scalar(select(Workspace.cursor).where(Workspace.id == "test"))

    page = await run_transaction(database, activity_page, "test", limit=50)
    first = page
    seen_ids: list[str] = []
    seen_runs: list[int] = []
    seen_statuses: set[str] = set()
    positions: list[int] = []
    while True:
        assert page.total == 6000 and page.has_older
        assert 1 <= len(page.items) <= 50
        for item in page.items:
            assert isinstance(item, FeedbackActivity)
            assert item.feedback.job is not None
            assert item.feedback.output is None
            seen_ids.append(item.id)
            seen_runs.append(item.feedback.job.run)
            seen_statuses.add(item.feedback.job.status)
        if page.next_cursor is None:
            break
        positions.append(decode_cursor(page.next_cursor).position)
        page = await run_transaction(
            database, activity_page, "test", limit=50, cursor=page.next_cursor
        )

    assert seen_runs == list(range(6002, 2, -1))
    assert len(seen_ids) == len(set(seen_ids)) == 6000
    assert 500 in positions and 550 in positions and positions[-1] == 5950
    assert seen_statuses == {"failed", "cancelled"}
    refreshed = await run_transaction(
        database, activity_page, "test", limit=50, cursor=first.refresh_cursor
    )
    assert refreshed.items == first.items and refreshed.has_older
    async with session_scope(database) as session:
        assert await session.scalar(select(func.count()).select_from(AnalysisJob)) == 6002
        assert await session.scalar(select(func.count()).select_from(AnalysisResult)) == 0
        assert await session.scalar(select(ProviderUsage.calls)) == 7
        assert (
            await session.scalar(select(Workspace.cursor).where(Workspace.id == "test")) == revision
        )


async def test_batch_activity_query_count_is_constant_and_preserves_shared_progress(
    database: AsyncEngine,
) -> None:
    await run_transaction(database, ingest, synthetic_inputs("batch-activity", 10))
    while await process_one(database):
        pass
    async with session_scope(database) as session:
        record_ids = list(await session.scalars(select(Feedback.id).order_by(Feedback.sequence)))

    first_batch = await run_transaction(
        database, start_backfill, BackfillInput(record_ids=record_ids[:1])
    )
    assert await process_one(database)

    async def measured_items(batch_ids: list[str]) -> tuple[list[ActivityItem], int]:
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
            async with session_scope(database) as session:
                items = await session.run_sync(
                    hydrate_activity, "test", ["batch:" + batch_id for batch_id in batch_ids]
                )
        finally:
            event.remove(database.sync_engine, "before_cursor_execute", record_query)
        return items, len(statements)

    one_batch, one_count = await measured_items([first_batch])
    assert len(one_batch) == 1
    assert isinstance(one_batch[0], BatchActivity)
    assert one_batch[0].batch.selected == one_batch[0].batch.completed == 1

    batch_ids = [first_batch]
    for record_id in record_ids[1:]:
        batch_ids.append(
            await run_transaction(
                database, start_backfill, BackfillInput(record_ids=[record_ids[0], record_id])
            )
        )
    batch_ids.reverse()
    ten_batches, ten_count = await measured_items(batch_ids)

    assert one_count == ten_count == 2
    assert [item.id for item in ten_batches] == batch_ids
    for item in ten_batches:
        assert isinstance(item, BatchActivity)
        assert item.batch.selected == (1 if item.id == first_batch else 2)
        assert item.batch.completed == 1
        assert item.batch.failed == 0
