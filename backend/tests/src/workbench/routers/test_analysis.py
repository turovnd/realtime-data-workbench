import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.api import create_app
from workbench.infrastructure.deterministic import generate_demo
from workbench.logic.backfills import start_backfill
from workbench.logic.ingestion import ingest
from workbench.logic.synthetic import synthetic_inputs
from workbench.repositories.feedback import hydrate
from workbench.schemas.backfills import BackfillInput
from workbench.schemas.common import Config
from workbench.schemas.enrichment import Enrichment
from workbench.settings import Settings
from workbench.workers.processing import process_one

pytestmark = pytest.mark.integration


async def test_real_analysis_repeats_without_overwriting_history_or_batch_progress(
    database: AsyncEngine,
) -> None:
    settings = Settings(provider_mode="openrouter", openrouter_calls_enabled=True)
    app = create_app(database, settings)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        person = (
            await client.post(
                "/api/auth/register",
                json={
                    "email": "analysis@example.test",
                    "password": "long-test-password",
                },
            )
        ).json()
        owner = {"Authorization": f"Bearer {person['token']}"}
        await ingest(database, synthetic_inputs("seed", 1), person["workspace_id"])
        assert await process_one(database)
        row = (await client.get("/api/feedback", headers=owner)).json()["records"][0]
        await start_backfill(
            database, BackfillInput(record_ids=[row["id"]]), person["workspace_id"]
        )
        assert await process_one(database)
        path = f"/api/feedback/{row['id']}/analysis"
        before = (await client.get(f"/api/feedback/{row['id']}", headers=owner)).json()
        assert [output["run"] for output in before["outputs"]] == [1, 2]
        assert (await client.post(path, json={"identity": "one"})).status_code == 401
        first, replay = await asyncio.gather(
            *[client.post(path, json={"identity": "one"}, headers=owner) for _ in range(2)]
        )
        assert sorted([first.status_code, replay.status_code]) == [200, 202]
        pending = first.json()
        assert pending["outputs"] == before["outputs"]
        assert len(pending["jobs"]) == 3
        assert pending["jobs"][-1]["run"] == 3
        assert pending["jobs"][-1]["origin"] == "analysis"
        assert pending["jobs"][-1]["provider"] == settings.provider_id
        assert first.json()["jobs"][-1]["id"] == replay.json()["jobs"][-1]["id"]
        assert (
            await client.post(path, json={"identity": "different"}, headers=owner)
        ).status_code == 409
        for invalid in (
            {"identity": " "},
            {"identity": "bad\x00key"},
            {"identity": "a", "workspace_id": "foreign"},
        ):
            assert (await client.post(path, json=invalid, headers=owner)).status_code == 422
        stranger = (
            await client.post(
                "/api/auth/register",
                json={
                    "email": "stranger@example.test",
                    "password": "long-test-password",
                },
            )
        ).json()
        assert (
            await client.post(
                path,
                json={"identity": "one"},
                headers={"Authorization": f"Bearer {stranger['token']}"},
            )
        ).status_code == 404
        assert (
            await client.post(
                "/api/feedback/missing/analysis", json={"identity": "one"}, headers=owner
            )
        ).status_code == 404

        calls: list[str] = []

        async def provider(text: str, config: Config) -> str:
            calls.append(text)
            assert config == "v2"
            return Enrichment(
                topic="billing",
                intent="issue",
                summary=f"AI result {len(calls)}",
                evidence=[text[:100]],
            ).model_dump_json()

        generators = {settings.provider_id: provider, "deterministic-rules/1": generate_demo}
        assert await process_one(database, generators=generators, live_budget=2)
        completed = (await client.get(f"/api/feedback/{row['id']}", headers=owner)).json()
        assert completed["outputs"][:2] == before["outputs"]
        assert completed["outputs"][-1]["run"] == 3
        assert completed["outputs"][-1]["provider"] == settings.provider_id
        assert completed["text"] == before["text"] and len(calls) == 1
        assert (await client.get("/api/feedback?topic=billing", headers=owner)).json()["total"] == 1
        assert (await client.post(path, json={"identity": "two"}, headers=owner)).status_code == 202
        assert await process_one(database, generators=generators, live_budget=2)
        repeated = (await client.get(f"/api/feedback/{row['id']}", headers=owner)).json()
        assert [output["run"] for output in repeated["outputs"]] == [1, 2, 3, 4]
        assert repeated["outputs"][-1]["summary"] == "AI result 2"
        assert repeated["outputs"][:3] == completed["outputs"]
        assert (
            await client.post(path, json={"identity": "three"}, headers=owner)
        ).status_code == 202
        assert await process_one(database, generators=generators, live_budget=2)
        failed = (await client.get(f"/api/feedback/{row['id']}", headers=owner)).json()
        assert failed["jobs"][-1]["run"] == 5 and failed["jobs"][-1]["status"] == "failed"
        assert failed["jobs"][-1]["error"] == "Live provider call budget exhausted"
        assert failed["outputs"] == repeated["outputs"] and len(calls) == 2
        status = (await client.get("/api/status", headers=owner)).json()
        assert status["failed"] == 1 and status["enriched"] == 0
        assert status["batches"][0]["completed"] == 1 and status["batches"][0]["failed"] == 0
        assert (
            await client.get("/api/feedback?status=failed&topic=billing", headers=owner)
        ).json()["total"] == 1
        async with database.connect() as conn:
            persisted = (await hydrate(conn, person["workspace_id"], [row["id"]]))[0]
        assert persisted.outputs[-1].run == 4


@pytest.mark.parametrize("mode,enabled", [("deterministic", True), ("openrouter", False)])
async def test_analysis_refuses_unconfigured_or_disabled_real_provider(
    database: AsyncEngine, mode: str, enabled: bool
) -> None:
    settings = Settings(
        provider_mode="openrouter" if mode == "openrouter" else "deterministic",
        openrouter_calls_enabled=enabled,
    )
    async with AsyncClient(
        transport=ASGITransport(app=create_app(database, settings)), base_url="http://test"
    ) as client:
        session = (await client.post("/api/auth/demo", json={})).json()
        response = await client.post(
            "/api/feedback/any/analysis",
            json={"identity": "one"},
            headers={"Authorization": f"Bearer {session['token']}"},
        )
        assert response.status_code == 503
        assert "not configured" in response.json()["detail"]
