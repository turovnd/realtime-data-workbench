from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncEngine

from common.infrastructure.database import run_transaction
from common.infrastructure.pagination import decode_cursor, encode_cursor
from common.logic.errors import CursorError, CursorExpired
from common.logic.feed import feed_page
from common.logic.ingestion import ingest
from common.logic.synthetic import synthetic_inputs
from common.models import FeedView
from common.repositories.sessions import create_session, resolve_session
from common.repositories.status import feed_status
from common.schemas.feedback import FeedFilters
from modules.worker.processing import process_one

pytestmark = pytest.mark.integration


async def test_keyset_pages_freeze_membership_and_exclude_new_arrivals(
    database: AsyncEngine,
) -> None:
    await run_transaction(database, ingest, synthetic_inputs("first", 12))
    head = await run_transaction(database, feed_page, "test", FeedFilters(), limit=5)
    await run_transaction(database, ingest, synthetic_inputs("new", 12))
    assert head.next_cursor is not None
    middle = await run_transaction(
        database, feed_page, "test", FeedFilters(), limit=5, cursor=head.next_cursor
    )
    assert middle.next_cursor is not None
    tail = await run_transaction(
        database, feed_page, "test", FeedFilters(), limit=5, cursor=middle.next_cursor
    )
    sequences = [row.sequence for page in (head, middle, tail) for row in page.records]
    assert sequences == list(range(12, 0, -1))
    assert tail.next_cursor is None
    assert [
        row.sequence
        for row in (await run_transaction(database, feed_page, "test", FeedFilters(), 5)).records
    ] == [24, 23, 22, 21, 20]
    status = await run_transaction(database, feed_status, "test", "deterministic-rules/1")
    assert status.received == 24 and status.latest_sequence == 24


async def test_filter_membership_stays_stable_while_jobs_change(database: AsyncEngine) -> None:
    await run_transaction(database, ingest, synthetic_inputs("first", 12))
    filters = FeedFilters(status="queued")
    first = await run_transaction(database, feed_page, "test", filters, 5)
    while await process_one(database):
        pass
    assert first.next_cursor
    second = await run_transaction(database, feed_page, "test", filters, 5, first.next_cursor)
    assert [row.sequence for row in second.records] == [7, 6, 5, 4, 3]
    refreshed = await run_transaction(database, feed_page, "test", filters, 5, first.refresh_cursor)
    assert all(row.jobs[0].status == "succeeded" for row in refreshed.records)
    assert (await run_transaction(database, feed_page, "test", filters)).total == 0


async def test_cursor_rejects_tampering_workspace_and_filter_changes(database: AsyncEngine) -> None:
    await run_transaction(database, ingest, synthetic_inputs("first", 12))
    first = await run_transaction(database, feed_page, "test", FeedFilters(q="page"), 1)
    cursor = first.refresh_cursor
    token = await run_transaction(database, create_session)
    other = await run_transaction(database, resolve_session, token)
    assert other
    with pytest.raises(CursorError):
        await run_transaction(database, feed_page, other, FeedFilters(q="page"), cursor=cursor)
    with pytest.raises(CursorError):
        await run_transaction(database, feed_page, "test", FeedFilters(q="changed"), cursor=cursor)
    for bad in (
        cursor[:-1] + ("a" if cursor[-1] != "a" else "b"),
        cursor.split(".")[0] + ".é",
        "invalid",
        "A" * 301,
    ):
        with pytest.raises(CursorError):
            await run_transaction(database, feed_page, "test", FeedFilters(q="page"), cursor=bad)


async def test_cursor_expiry_and_active_view_bound(database: AsyncEngine) -> None:
    first = await run_transaction(database, feed_page, "test", FeedFilters())
    async with database.begin() as conn:
        await conn.execute(
            update(FeedView).values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
        )
    with pytest.raises(CursorExpired):
        await run_transaction(
            database, feed_page, "test", FeedFilters(), cursor=first.refresh_cursor
        )
    for index in range(25):
        await run_transaction(database, feed_page, "test", FeedFilters(q=str(index)))
    async with database.connect() as conn:
        assert len((await conn.execute(select(FeedView.id))).all()) == 20


async def test_valid_signature_does_not_allow_positions_outside_saved_membership(
    database: AsyncEngine,
) -> None:
    await run_transaction(database, ingest, synthetic_inputs("bounded-view", 1))
    page = await run_transaction(database, feed_page, "test", FeedFilters())
    cursor = decode_cursor(page.refresh_cursor)
    async with database.connect() as conn:
        secret = await conn.scalar(select(FeedView.secret).where(FeedView.id == cursor.view_id))
    assert isinstance(secret, str)
    outside = encode_cursor(cursor.view_id, page.watermark + 2, secret)
    with pytest.raises(CursorError, match="outside this feedback view"):
        await run_transaction(database, feed_page, "test", FeedFilters(), cursor=outside)
