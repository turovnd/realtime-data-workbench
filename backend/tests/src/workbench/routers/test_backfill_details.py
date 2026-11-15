from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.api import create_app
from workbench.infrastructure.database import session_scope
from workbench.logic.analysis import start_analysis
from workbench.logic.backfills import cancel_backfill, start_backfill
from workbench.logic.feed import feed_page
from workbench.logic.ingestion import ingest
from workbench.logic.synthetic import synthetic_inputs
from workbench.models import AnalysisJob, FeedView, ProviderUsage
from workbench.repositories.inspection import snapshot
from workbench.repositories.sessions import create_session, issue_session, resolve_session
from workbench.schemas.analysis import AnalysisInput
from workbench.schemas.backfills import BackfillInput
from workbench.schemas.feedback import FeedFilters
from workbench.workers.processing import process_one

pytestmark = pytest.mark.integration


async def owner_headers(database: AsyncEngine) -> dict[str, str]:
    async with session_scope(database) as conn:
        token = await issue_session(conn, "test", None)
    return {"Authorization": f"Bearer {token}"}


async def test_batch_pages_keep_selection_and_original_results_after_later_analysis(
    database: AsyncEngine,
) -> None:
    await ingest(database, synthetic_inputs("first", 12))
    await ingest(database, synthetic_inputs("second", 9))
    while await process_one(database):
        pass
    original = (await snapshot(database)).records
    batch_id = await start_backfill(
        database, BackfillInput(record_ids=[row.id for row in reversed(original)])
    )
    headers = await owner_headers(database)
    path = f"/api/backfills/{batch_id}"
    async with AsyncClient(
        transport=ASGITransport(app=create_app(database)), base_url="http://test", headers=headers
    ) as client:
        head = await client.get(path)
        assert head.status_code == 200
        first = head.json()
        assert len(first["items"]) == 10 and first["batch"]["selected"] == 21
        assert first["batch"]["completed"] == 0
        assert all(item["job"]["status"] == "queued" for item in first["items"])
        assert all(item["output"] is None for item in first["items"])
        await ingest(database, synthetic_inputs("new-arrival", 1))
        while await process_one(database):
            pass
        second = (await client.get(path, params={"cursor": first["next_cursor"]})).json()
        third = (await client.get(path, params={"cursor": second["next_cursor"]})).json()
        all_items = first["items"] + second["items"] + third["items"]
        assert [item["sequence"] for item in all_items] == list(range(21, 0, -1))
        assert len({item["record_id"] for item in all_items}) == 21
        assert third["next_cursor"] is None and third["batch"]["completed"] == 21
        previous = (await client.get(path, params={"limit": 50})).json()
        record_id = original[0].id
        await start_analysis(
            database, "test", record_id, AnalysisInput(identity="later"), "deterministic-rules/1"
        )
        assert await process_one(database)
        after = (await client.get(path, params={"limit": 50})).json()
        assert after == previous
        full_record = (await client.get(f"/api/feedback/{record_id}")).json()
        assert full_record["outputs"][-1]["run"] == 3
        assert after["items"][0]["job"]["run"] == 2
        assert after["items"][0]["output"]["run"] == 2
        assert after["items"][0]["text"] == original[0].text
        assert after["items"][0]["channel"] == original[0].channel
        newest = (await snapshot(database)).records[0]
        reused_batch = await start_backfill(
            database, BackfillInput(record_ids=[record_id, newest.id])
        )
        reused = (await client.get(f"/api/backfills/{reused_batch}")).json()
        old = next(item for item in reused["items"] if item["record_id"] == record_id)
        assert old["job"] == after["items"][0]["job"]
        assert old["output"] == after["items"][0]["output"]
        assert reused["batch"]["selected"] == 2 and reused["batch"]["completed"] == 1
        async with database.connect() as conn:
            assert await conn.scalar(select(func.count()).select_from(AnalysisJob)) == 45
            assert await conn.scalar(select(func.count()).select_from(ProviderUsage)) == 0


async def test_batch_cursor_is_authenticated_bounded_and_scope_bound(database: AsyncEngine) -> None:
    await ingest(database, synthetic_inputs("seed", 4))
    while await process_one(database):
        pass
    rows = (await snapshot(database)).records
    first_batch = await start_backfill(database, BackfillInput(record_ids=[r.id for r in rows[:2]]))
    other_batch = await start_backfill(database, BackfillInput(record_ids=[r.id for r in rows[2:]]))
    foreign_token = await create_session(database)
    foreign = await resolve_session(database, foreign_token)
    assert foreign
    await ingest(database, synthetic_inputs("foreign", 2), foreign)
    while await process_one(database):
        pass
    foreign_rows = (await snapshot(database, foreign)).records
    foreign_batch = await start_backfill(
        database, BackfillInput(record_ids=[row.id for row in foreign_rows]), foreign
    )
    headers = await owner_headers(database)
    path = f"/api/backfills/{first_batch}"
    async with AsyncClient(
        transport=ASGITransport(app=create_app(database)), base_url="http://test"
    ) as client:
        assert (await client.get(path)).status_code == 401
        assert (await client.get("/api/backfills/missing", headers=headers)).status_code == 404
        assert (
            await client.get(f"/api/backfills/{foreign_batch}", headers=headers)
        ).status_code == 404
        foreign_headers = {"Authorization": f"Bearer {foreign_token}"}
        assert (await client.get(path, headers=foreign_headers)).status_code == 404
        page = (await client.get(path, headers=headers, params={"limit": 1})).json()
        cursor = page["next_cursor"]
        assert cursor
        for bad in ("invalid", cursor[:-1] + ("a" if cursor[-1] != "a" else "b"), "a.é"):
            assert (
                await client.get(path, headers=headers, params={"cursor": bad})
            ).status_code == 400
        assert (
            await client.get(
                f"/api/backfills/{other_batch}", headers=headers, params={"cursor": cursor}
            )
        ).status_code == 400
        assert (
            await client.get(
                f"/api/backfills/{foreign_batch}",
                headers=foreign_headers,
                params={"cursor": cursor},
            )
        ).status_code == 400
        feed_cursor = (await feed_page(database, "test", FeedFilters())).refresh_cursor
        assert (
            await client.get(path, headers=headers, params={"cursor": feed_cursor})
        ).status_code == 400
        assert (
            await client.get("/api/feedback", headers=headers, params={"cursor": cursor})
        ).status_code == 400
        for limit in (0, 51, "bad"):
            assert (
                await client.get(path, headers=headers, params={"limit": limit})
            ).status_code == 422
        async with database.begin() as conn:
            await conn.execute(
                update(FeedView).values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
            )
        assert (
            await client.get(path, headers=headers, params={"cursor": cursor})
        ).status_code == 410
        for _ in range(25):
            assert (await client.get(path, headers=headers)).status_code == 200
        async with database.connect() as conn:
            assert await conn.scalar(select(func.count()).select_from(FeedView)) == 20


async def test_batch_failed_and_cancelled_jobs_never_show_previous_version_outputs(
    database: AsyncEngine,
) -> None:
    await ingest(database, synthetic_inputs("seed", 2))
    while await process_one(database):
        pass
    rows = (await snapshot(database)).records
    batch_id = await start_backfill(database, BackfillInput(record_ids=[row.id for row in rows]))

    async def invalid_provider(text: str, config: str) -> str:
        return "invalid JSON"

    assert await process_one(database, generate=invalid_provider)
    await cancel_backfill(database, batch_id)
    async with AsyncClient(
        transport=ASGITransport(app=create_app(database)),
        base_url="http://test",
        headers=await owner_headers(database),
    ) as client:
        result = (await client.get(f"/api/backfills/{batch_id}")).json()
        assert result["batch"]["cancelled"] is True
        assert result["batch"]["failed"] == 1 and result["batch"]["completed"] == 0
        assert {item["job"]["status"] for item in result["items"]} == {"failed", "cancelled"}
        assert all(item["job"]["run"] == 2 and item["output"] is None for item in result["items"])
        assert all(len(record.outputs) == 1 for record in (await snapshot(database)).records)
