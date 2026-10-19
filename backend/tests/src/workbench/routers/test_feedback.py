import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.api import create_app

pytestmark = pytest.mark.integration


async def test_api_contract_and_origin_guard(database: AsyncEngine) -> None:
    app = create_app(database)
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        assert (await client.get("/health")).status_code == 200
        assert (await client.get("/api/feedback")).status_code == 401
        token = (await client.post("/api/auth/demo", json={})).json()["token"]
        client.headers["Authorization"] = f"Bearer {token}"
        denied = await client.post(
            "/api/simulations",
            json={"request_id": "x", "count": 1},
            headers={"Origin": "https://untrusted.test"},
        )
        assert denied.status_code == 403
        created = await client.post("/api/simulations", json={"request_id": "api", "count": 2})
        assert created.json() == {"inserted": 2}
        assert (
            await client.post("/api/simulations", json={"request_id": "api", "count": 2})
        ).json() == {"inserted": 0}
        view = await client.get("/api/feedback")
        assert len(view.json()["records"]) == 12
        assert view.headers["cache-control"] == "no-store"


async def test_sessions_cannot_read_retry_or_backfill_another_workspace(
    database: AsyncEngine,
) -> None:
    app = create_app(database)
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        first = (await client.post("/api/auth/demo", json={})).json()["token"]
        second = (await client.post("/api/auth/demo", json={})).json()["token"]
        owner = {"Authorization": f"Bearer {first}"}
        visitor = {"Authorization": f"Bearer {second}"}
        await client.post(
            "/api/simulations", json={"request_id": "isolation", "count": 1}, headers=owner
        )
        a = (await client.get("/api/feedback", headers=owner)).json()
        b = (await client.get("/api/feedback", headers=visitor)).json()
        assert a["workspace_id"] != b["workspace_id"]
        assert len(a["records"]) == 12 and len(b["records"]) == 12
        assert {row["id"] for row in a["records"]}.isdisjoint(row["id"] for row in b["records"])
        row = a["records"][0]
        assert (
            await client.post(
                "/api/backfills", json={"record_ids": [row["id"]], "config": "v2"}, headers=visitor
            )
        ).status_code == 409
        assert (
            await client.post(f"/api/jobs/{row['jobs'][0]['id']}/retry", json={}, headers=visitor)
        ).status_code == 409
