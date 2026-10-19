import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.api import create_app
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
