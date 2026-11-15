import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.api import create_app
from workbench.infrastructure.database import session_scope
from workbench.infrastructure.deterministic import generate_demo
from workbench.models import AnalysisJob, ProviderUsage
from workbench.schemas.common import Config
from workbench.settings import Settings
from workbench.workers.processing import process_one

pytestmark = pytest.mark.integration


async def test_user_feedback_is_durable_idempotent_and_workspace_scoped(
    database: AsyncEngine,
) -> None:
    app = create_app(database)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "identity": "manual-input-1",
            "text": "CSV export is too slow.",
            "channel": "Support",
        }
        assert (await client.post("/api/feedback", json=payload)).status_code == 401
        assert (await client.get("/api/feedback/unknown")).status_code == 401
        person = (
            await client.post(
                "/api/auth/register",
                json={"email": "feedback-owner@example.test", "password": "a-long-test-password"},
            )
        ).json()
        owner = {"Authorization": f"Bearer {person['token']}"}
        created = await client.post("/api/feedback", json=payload, headers=owner)
        assert created.status_code == 201
        row = created.json()
        assert row["text"] == payload["text"] and row["channel"] == payload["channel"]
        assert row["outputs"] == [] and len(row["jobs"]) == 1
        assert row["jobs"][0]["status"] == "queued"
        replay = await client.post("/api/feedback", json=payload, headers=owner)
        assert replay.status_code == 200 and replay.json()["id"] == row["id"]
        collision = await client.post(
            "/api/feedback", json={**payload, "text": "Different"}, headers=owner
        )
        assert collision.status_code == 409
        assert await process_one(database)
        detail = await client.get(f"/api/feedback/{row['id']}", headers=owner)
        assert detail.status_code == 200
        assert detail.json()["jobs"][0]["status"] == "succeeded"
        assert detail.json()["outputs"][0]["evidence"][0] in payload["text"]
        assert detail.json()["text"] == payload["text"]
        assert not await process_one(database)
        stranger = (
            await client.post(
                "/api/auth/register",
                json={
                    "email": "feedback-stranger@example.test",
                    "password": "a-long-test-password",
                },
            )
        ).json()
        foreign = {"Authorization": f"Bearer {stranger['token']}"}
        assert (await client.get(f"/api/feedback/{row['id']}", headers=foreign)).status_code == 404
        assert (await client.get("/api/feedback/missing", headers=owner)).status_code == 404
        independent = await client.post("/api/feedback", json=payload, headers=foreign)
        assert independent.status_code == 201 and independent.json()["id"] != row["id"]


async def test_feedback_validation_and_concurrent_retry(database: AsyncEngine) -> None:
    app = create_app(database)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        person = (
            await client.post(
                "/api/auth/register",
                json={"email": "input-validation@example.test", "password": "a-long-test-password"},
            )
        ).json()
        client.headers["Authorization"] = f"Bearer {person['token']}"
        payload = {"identity": "input-1", "text": "Keep the original input.", "channel": "In-app"}
        for invalid in (
            {**payload, "identity": "   "},
            {**payload, "identity": "bad\x00identity"},
            {**payload, "text": "bad\x00text"},
            {**payload, "text": "   "},
            {**payload, "text": "a" * 4001},
            {**payload, "channel": "Unknown"},
            {**payload, "workspace_id": "someone-else"},
        ):
            assert (await client.post("/api/feedback", json=invalid)).status_code == 422
        first, second = await asyncio.gather(
            client.post("/api/feedback", json=payload), client.post("/api/feedback", json=payload)
        )
        assert sorted([first.status_code, second.status_code]) == [200, 201]
        assert first.json()["id"] == second.json()["id"]
        feed = (await client.get("/api/feedback")).json()
        assert feed["total"] == 1 and len(feed["records"][0]["jobs"]) == 1


async def test_live_workspace_keeps_seeded_examples_free_but_analyzes_new_feedback(
    database: AsyncEngine,
) -> None:
    settings = Settings(provider_mode="openrouter", openrouter_calls_enabled=True)
    async with AsyncClient(
        transport=ASGITransport(app=create_app(database, settings)), base_url="http://test"
    ) as client:
        person = (await client.post("/api/auth/demo", json={})).json()
        client.headers["Authorization"] = f"Bearer {person['token']}"
        async with session_scope(database) as session:
            jobs = list(await session.scalars(select(AnalysisJob)))
            assert len(jobs) == 24
            assert {job.provider for job in jobs} == {"deterministic-rules/1"}

        for _ in range(24):
            assert await process_one(database)
        assert not await process_one(database)
        async with session_scope(database) as session:
            assert await session.scalar(select(func.count()).select_from(ProviderUsage)) == 0

        payload = {
            "identity": "reviewer-example",
            "text": "The monthly export fails; weekly downloads still work.",
            "channel": "Support",
        }
        created = await client.post("/api/feedback", json=payload)
        assert created.status_code == 201
        record = created.json()
        assert len(record["jobs"]) == 1
        assert record["jobs"][0]["provider"] == settings.provider_id
        assert record["jobs"][0]["status"] == "queued"
        assert (await client.post("/api/feedback", json=payload)).status_code == 200

        calls: list[str] = []

        async def provider(source: str, config: Config) -> str:
            calls.append(source)
            return await generate_demo(source, config)

        assert await process_one(
            database, generators={settings.provider_id: provider}, live_budget=1
        )
        completed = (await client.get(f"/api/feedback/{record['id']}")).json()
        assert calls == [payload["text"]]
        assert completed["jobs"][0]["status"] == "succeeded"
        assert completed["outputs"][0]["provider"] == settings.provider_id
        assert len(completed["outputs"]) == 1
