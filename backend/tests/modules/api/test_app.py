import hashlib
import json
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine

from common.infrastructure.database import create_engine
from common.settings import Settings
from modules.api.app import create_app


async def test_public_openapi_documents_contracts_and_workspace_security() -> None:
    engine = create_engine(Settings().database_url)
    app = create_app(engine)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        paths = schema["paths"]
        assert len(paths) == 16
        assert schema["components"]["securitySchemes"]["WorkspaceBearer"]["scheme"] == "bearer"
        public = {"/health", "/api/auth/demo", "/api/auth/register", "/api/auth/login"}
        for path, methods in paths.items():
            for operation in methods.values():
                assert operation["summary"] and operation["description"] and operation["tags"]
                assert operation["operationId"]
                assert operation["responses"]["200"]["content"]["application/json"]["schema"]
                if path in public:
                    assert "security" not in operation
                else:
                    assert operation["security"] == [{"WorkspaceBearer": []}]
                    assert "401" in operation["responses"]
        feed = paths["/api/feedback"]["get"]
        parameters = {item["name"]: item for item in feed["parameters"]}
        assert parameters["limit"]["schema"]["maximum"] == 50
        assert "cursor" in parameters and "description" in parameters["cursor"]
        assert {"400", "410", "422"}.issubset(feed["responses"])
        activity = paths["/api/activity"]["get"]
        assert activity["operationId"] == "listActivity"
        assert {"400", "401", "410", "422"}.issubset(activity["responses"])
        activity_items = schema["components"]["schemas"]["ActivityPage"]["properties"]["items"]
        assert activity_items["items"]["discriminator"]["propertyName"] == "kind"
        batch = paths["/api/backfills/{batch_id}"]["get"]
        assert {"400", "401", "404", "410", "422"}.issubset(batch["responses"])
        batch_parameters = {item["name"]: item for item in batch["parameters"]}
        assert batch_parameters["limit"]["schema"]["default"] == 10
        assert batch_parameters["limit"]["schema"]["maximum"] == 50
        assert "cursor" in batch_parameters
        detail = paths["/api/feedback/{record_id}"]["get"]
        assert "404" in detail["responses"]
        create = paths["/api/feedback"]["post"]
        assert {"200", "201", "409", "422"}.issubset(create["responses"])
        assert create["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith(
            "/FeedbackInput"
        )
        feedback_input = schema["components"]["schemas"]["FeedbackInput"]
        assert feedback_input["additionalProperties"] is False
        assert feedback_input["properties"]["text"]["maxLength"] == 4000
        credentials = schema["components"]["schemas"]["Credentials"]["properties"]
        assert credentials["password"]["writeOnly"] is True
        assert "Settings" not in schema["components"]["schemas"]
        assert "openrouter_api_key" not in response.text
        assert all("worker" not in path for path in paths)
        docs = await client.get("/docs")
        assert docs.status_code == 200
        assert "/docs-assets/swagger-ui-bundle.js" in docs.text
        assert "cdn.jsdelivr" not in docs.text and "unpkg.com" not in docs.text
        assert '"persistAuthorization": false' in docs.text
        assert '"validatorUrl": null' in docs.text
        for asset in ("swagger-ui-bundle.js", "swagger-ui.css", "favicon-32x32.png"):
            result = await client.get(f"/docs-assets/{asset}")
            assert result.status_code == 200 and len(result.content) > 100
    await engine.dispose()


def test_swagger_vendor_files_match_pinned_manifest() -> None:
    import modules.api.app

    assets = Path(modules.api.app.__file__).parent / "static/swagger"
    manifest = json.loads((assets / "manifest.json").read_text())
    assert manifest["version"] == "5.33.1"
    assert manifest["package"] == "swagger-ui-dist"
    for name, expected in manifest["sha256"].items():
        assert hashlib.sha256((assets / name).read_bytes()).hexdigest() == expected


@pytest.mark.integration
async def test_swagger_same_origin_auth_flow_remains_workspace_scoped(
    database: AsyncEngine,
) -> None:
    app = create_app(database, Settings(allowed_origins=[]))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://api.test") as client:
        denied = await client.post(
            "/api/auth/demo", json={}, headers={"Origin": "https://evil.test"}
        )
        assert denied.status_code == 403
        session = await client.post(
            "/api/auth/demo", json={}, headers={"Origin": "https://api.test"}
        )
        assert session.status_code == 200
        client.headers["Authorization"] = f"Bearer {session.json()['token']}"
        page = await client.get("/api/feedback?limit=12")
        assert page.status_code == 200
        assert page.json()["workspace_id"] == session.json()["workspace_id"]
        assert len(page.json()["records"]) == 12
        assert (await client.post("/api/auth/logout", json={})).status_code == 200
        assert (await client.get("/api/feedback")).status_code == 401
