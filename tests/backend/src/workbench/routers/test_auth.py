import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.api import create_app

pytestmark = pytest.mark.integration


async def test_auth_routes_guard_lists_and_mutations(database: AsyncEngine) -> None:
    app = create_app(database)
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        assert (await client.get("/api/feedback")).status_code == 401
        assert (
            await client.post("/api/simulations", json={"request_id": "denied", "count": 1})
        ).status_code == 401
        result = await client.post(
            "/api/auth/register",
            json={"email": "reader@example.test", "password": "correct-password-example"},
        )
        assert result.status_code == 200
        token = result.json()["token"]
        client.headers["Authorization"] = f"Bearer {token}"
        assert (await client.get("/api/auth/me")).json()["kind"] == "account"
        assert (await client.get("/api/feedback?limit=51")).status_code == 422
        for malformed in ("", "x" * 301, "abc.é"):
            assert (
                await client.get("/api/feedback", params={"cursor": malformed})
            ).status_code == 400
        assert (await client.post("/api/auth/logout", json={})).status_code == 200
        assert (await client.get("/api/feedback")).status_code == 401
