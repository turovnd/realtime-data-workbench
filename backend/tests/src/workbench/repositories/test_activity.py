from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.tables import jobs, outputs, provider_usage, state
from workbench.logic.activity import activity_page
from workbench.logic.activity_cursors import decode_activity_cursor
from workbench.logic.ingestion import ingest
from workbench.schemas.activity import FeedbackActivity
from workbench.schemas.feedback import FeedbackInput

pytestmark = pytest.mark.integration


async def test_activity_read_window_pages_large_terminal_history_without_changing_work(
    database: AsyncEngine,
) -> None:
    await ingest(
        database,
        [FeedbackInput(identity="long-history", text="Export stops early.", channel="Support")],
    )
    scheduled = datetime(2026, 1, 1, tzinfo=UTC)
    async with database.begin() as conn:
        record_id = await conn.scalar(select(jobs.c.record_id))
        assert record_id is not None
        await conn.execute(update(jobs).values(status="cancelled", available_at=scheduled))
        await conn.execute(
            insert(jobs),
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
        await conn.execute(insert(provider_usage).values(id="openrouter", calls=7))
        revision = await conn.scalar(select(state.c.cursor).where(state.c.id == "test"))

    page = await activity_page(database, "test", limit=50)
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
        positions.append(decode_activity_cursor(page.next_cursor)[1])
        page = await activity_page(database, "test", limit=50, cursor=page.next_cursor)

    assert seen_runs == list(range(6002, 2, -1))
    assert len(seen_ids) == len(set(seen_ids)) == 6000
    assert 500 in positions and 550 in positions and positions[-1] == 5950
    assert seen_statuses == {"failed", "cancelled"}
    refreshed = await activity_page(database, "test", limit=50, cursor=first.refresh_cursor)
    assert refreshed.items == first.items and refreshed.has_older
    async with database.connect() as conn:
        assert await conn.scalar(select(func.count()).select_from(jobs)) == 6002
        assert await conn.scalar(select(func.count()).select_from(outputs)) == 0
        assert await conn.scalar(select(provider_usage.c.calls)) == 7
        assert await conn.scalar(select(state.c.cursor).where(state.c.id == "test")) == revision
