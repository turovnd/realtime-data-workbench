from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.tables import feed_views
from workbench.logic.errors import CursorError, CursorExpired
from workbench.logic.feed import feed_page
from workbench.logic.ingestion import ingest
from workbench.logic.synthetic import synthetic_inputs
from workbench.repositories.sessions import create_session, resolve_session
from workbench.repositories.status import feed_status
from workbench.schemas.feedback import FeedFilters
from workbench.workers.processing import process_one

pytestmark = pytest.mark.integration


async def test_keyset_pages_freeze_membership_and_exclude_new_arrivals(
    database: AsyncEngine,
) -> None:
    await ingest(database, synthetic_inputs("first", 12))
    head = await feed_page(database, "test", FeedFilters(), limit=5)
    await ingest(database, synthetic_inputs("new", 12))
    assert head.next_cursor is not None
    middle = await feed_page(database, "test", FeedFilters(), limit=5, cursor=head.next_cursor)
    assert middle.next_cursor is not None
    tail = await feed_page(database, "test", FeedFilters(), limit=5, cursor=middle.next_cursor)
    sequences = [row.sequence for page in (head, middle, tail) for row in page.records]
    assert sequences == list(range(12, 0, -1))
    assert tail.next_cursor is None
    assert [
        row.sequence for row in (await feed_page(database, "test", FeedFilters(), 5)).records
    ] == [24, 23, 22, 21, 20]
    status = await feed_status(database, "test", "deterministic-rules/1")
    assert status.received == 24 and status.latest_sequence == 24


async def test_filter_membership_stays_stable_while_jobs_change(database: AsyncEngine) -> None:
    await ingest(database, synthetic_inputs("first", 12))
    filters = FeedFilters(status="queued")
    first = await feed_page(database, "test", filters, 5)
    while await process_one(database):
        pass
    assert first.next_cursor
    second = await feed_page(database, "test", filters, 5, first.next_cursor)
    assert [row.sequence for row in second.records] == [7, 6, 5, 4, 3]
    refreshed = await feed_page(database, "test", filters, 5, first.refresh_cursor)
    assert all(row.jobs[0].status == "succeeded" for row in refreshed.records)
    assert (await feed_page(database, "test", filters)).total == 0


async def test_cursor_rejects_tampering_workspace_and_filter_changes(database: AsyncEngine) -> None:
    await ingest(database, synthetic_inputs("first", 12))
    first = await feed_page(database, "test", FeedFilters(q="page"), 1)
    cursor = first.refresh_cursor
    token = await create_session(database)
    other = await resolve_session(database, token)
    assert other
    with pytest.raises(CursorError):
        await feed_page(database, other, FeedFilters(q="page"), cursor=cursor)
    with pytest.raises(CursorError):
        await feed_page(database, "test", FeedFilters(q="changed"), cursor=cursor)
    for bad in (
        cursor[:-1] + ("a" if cursor[-1] != "a" else "b"),
        cursor.split(".")[0] + ".é",
        "invalid",
        "A" * 301,
    ):
        with pytest.raises(CursorError):
            await feed_page(database, "test", FeedFilters(q="page"), cursor=bad)


async def test_cursor_expiry_and_active_view_bound(database: AsyncEngine) -> None:
    first = await feed_page(database, "test", FeedFilters())
    async with database.begin() as conn:
        await conn.execute(
            update(feed_views).values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
        )
    with pytest.raises(CursorExpired):
        await feed_page(database, "test", FeedFilters(), cursor=first.refresh_cursor)
    for index in range(25):
        await feed_page(database, "test", FeedFilters(q=str(index)))
    async with database.connect() as conn:
        assert len((await conn.execute(select(feed_views.c.id))).all()) == 20
