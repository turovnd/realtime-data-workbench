from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.api import create_app
from workbench.infrastructure.database import session_scope
from workbench.logic.analysis import start_analysis
from workbench.logic.backfills import start_backfill
from workbench.logic.feed import feed_page
from workbench.logic.ingestion import ingest
from workbench.logic.synthetic import synthetic_inputs
from workbench.models import AnalysisJob, AnalysisResult, FeedView, ProviderUsage, Workspace
from workbench.repositories.activity import activity_ids
from workbench.repositories.sessions import create_session, issue_session
from workbench.schemas.analysis import AnalysisInput
from workbench.schemas.backfills import BackfillInput
from workbench.schemas.feedback import FeedFilters
from workbench.workers.processing import process_one

pytestmark = pytest.mark.integration


async def headers(database: AsyncEngine) -> dict[str, str]:
    async with session_scope(database) as conn:
        token = await issue_session(conn, "test", None)
    return {"Authorization": f"Bearer {token}"}


async def durable_counts(database: AsyncEngine) -> tuple[int, int, int, int]:
    async with database.connect() as conn:
        return (
            int(await conn.scalar(select(func.count()).select_from(AnalysisJob)) or 0),
            int(await conn.scalar(select(func.count()).select_from(AnalysisResult)) or 0),
            int(await conn.scalar(select(func.sum(ProviderUsage.calls))) or 0),
            int(await conn.scalar(select(Workspace.cursor).where(Workspace.id == "test")) or 0),
        )


async def test_activity_includes_automatic_individual_and_bulk_exact_results(
    database: AsyncEngine,
) -> None:
    await ingest(database, synthetic_inputs("seed", 2))
    async with AsyncClient(
        transport=ASGITransport(app=create_app(database)),
        base_url="http://test",
        headers=await headers(database),
    ) as client:
        first = (await client.get("/api/activity")).json()
        assert first["total"] == 2 and first["next_cursor"] is None
        assert first["has_older"] is False
        assert all(item["kind"] == "feedback" for item in first["items"])
        assert all(item["feedback"]["job"]["status"] == "queued" for item in first["items"])
        assert all(item["feedback"]["output"] is None for item in first["items"])
        while await process_one(database):
            pass
        completed = (
            await client.get("/api/activity", params={"cursor": first["refresh_cursor"]})
        ).json()
        assert [item["id"] for item in completed["items"]] == [
            item["id"] for item in first["items"]
        ]
        assert all(item["feedback"]["job"]["status"] == "succeeded" for item in completed["items"])
        assert all(item["feedback"]["output"]["run"] == 1 for item in completed["items"])
        record_ids = [item["feedback"]["record_id"] for item in first["items"]]
        batch_id = await start_backfill(database, BackfillInput(record_ids=record_ids))
        bulk = (await client.get("/api/activity")).json()
        assert bulk["total"] == 3
        batch = next(item for item in bulk["items"] if item["kind"] == "batch")
        assert batch["id"] == batch_id and batch["batch"]["selected"] == 2
        assert batch["batch"]["completed"] == 0
        while await process_one(database):
            pass
        # Availability is a scheduling field; make earlier scheduling values explicitly old.
        async with database.begin() as conn:
            await conn.execute(
                update(AnalysisJob).values(available_at=datetime.now(UTC) - timedelta(days=1))
            )
        older = min(first["items"], key=lambda item: item["feedback"]["sequence"])
        record, _ = await start_analysis(
            database,
            "test",
            older["feedback"]["record_id"],
            AnalysisInput(identity="manual"),
            "deterministic-rules/1",
        )
        recent = (await client.get("/api/activity")).json()
        assert recent["items"][0]["id"] == record.jobs[-1].id
        assert recent["items"][0]["feedback"]["output"] is None
        assert await process_one(database)
        before_read = await durable_counts(database)
        result = (await client.get("/api/activity")).json()
        assert result["total"] == 4
        assert (
            next(item for item in result["items"] if item["kind"] == "batch")["batch"]["completed"]
            == 2
        )
        for item in result["items"]:
            if item["kind"] == "feedback":
                feedback = item["feedback"]
                assert feedback["job"]["origin"] in ("live", "analysis")
                assert feedback["output"]["run"] == feedback["job"]["run"]
                assert all(quote in feedback["text"] for quote in feedback["output"]["evidence"])
        assert await durable_counts(database) == before_read
        assert before_read[:3] == (5, 5, 0)


async def test_activity_freezes_order_and_membership_through_completion_and_new_arrivals(
    database: AsyncEngine,
) -> None:
    await ingest(database, synthetic_inputs("initial", 12))
    async with session_scope(database) as conn:
        expected = [event.removeprefix("job:") for event in (await activity_ids(conn, "test"))[0]]
    async with AsyncClient(
        transport=ASGITransport(app=create_app(database)),
        base_url="http://test",
        headers=await headers(database),
    ) as client:
        first = (await client.get("/api/activity", params={"limit": 5})).json()
        while await process_one(database):
            pass
        await ingest(database, synthetic_inputs("new", 1))
        second = (
            await client.get("/api/activity", params={"limit": 5, "cursor": first["next_cursor"]})
        ).json()
        third = (
            await client.get("/api/activity", params={"limit": 5, "cursor": second["next_cursor"]})
        ).json()
        ids = [item["id"] for page in (first, second, third) for item in page["items"]]
        assert ids == expected and len(set(ids)) == 12
        assert third["next_cursor"] is None and third["total"] == 12
        repeated = (
            await client.get("/api/activity", params={"limit": 5, "cursor": first["next_cursor"]})
        ).json()
        assert repeated["items"] == second["items"]
        refreshed = (
            await client.get(
                "/api/activity", params={"limit": 5, "cursor": first["refresh_cursor"]}
            )
        ).json()
        assert [item["id"] for item in refreshed["items"]] == expected[:5]
        fresh = (await client.get("/api/activity")).json()
        assert fresh["total"] == 13 and len(fresh["items"]) == 10


async def test_activity_scopes_cursors_expires_bounds_and_handles_empty_workspace(
    database: AsyncEngine,
) -> None:
    owner = await headers(database)
    foreign_token = await create_session(database)
    foreign = {"Authorization": f"Bearer {foreign_token}"}
    await ingest(database, synthetic_inputs("seed", 2))
    async with AsyncClient(
        transport=ASGITransport(app=create_app(database)), base_url="http://test"
    ) as client:
        assert (await client.get("/api/activity")).status_code == 401
        empty = (await client.get("/api/activity", headers=foreign)).json()
        assert empty["items"] == [] and empty["total"] == 0 and empty["next_cursor"] is None
        first = (await client.get("/api/activity", headers=owner, params={"limit": 1})).json()
        cursor = first["next_cursor"]
        assert cursor
        assert (
            await client.get("/api/activity", headers=foreign, params={"cursor": cursor})
        ).status_code == 400
        for bad in ("invalid", "a.é", "x" * 301, cursor[:-1] + ("a" if cursor[-1] != "a" else "b")):
            assert (
                await client.get("/api/activity", headers=owner, params={"cursor": bad})
            ).status_code == 400
        feed = await feed_page(database, "test", FeedFilters())
        assert (
            await client.get("/api/activity", headers=owner, params={"cursor": feed.refresh_cursor})
        ).status_code == 400
        assert (
            await client.get(
                "/api/feedback", headers=owner, params={"cursor": first["refresh_cursor"]}
            )
        ).status_code == 400
        for limit in (0, 51, "bad"):
            assert (
                await client.get("/api/activity", headers=owner, params={"limit": limit})
            ).status_code == 422
        async with database.begin() as conn:
            await conn.execute(
                update(FeedView).values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
            )
        assert (
            await client.get("/api/activity", headers=owner, params={"cursor": cursor})
        ).status_code == 410
        before = await durable_counts(database)
        for _ in range(25):
            assert (await client.get("/api/activity", headers=owner)).status_code == 200
        assert await durable_counts(database) == before
        async with database.connect() as conn:
            assert await conn.scalar(select(func.count()).select_from(FeedView)) == 20
