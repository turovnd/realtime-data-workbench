"""HTTP application factory. Domain operations and the worker live in separate modules."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.responses import HTMLResponse

from workbench.dependencies import get_database, get_dispatcher, get_settings
from workbench.infrastructure.database import create_engine
from workbench.infrastructure.http import install_http
from workbench.infrastructure.queue import JobDispatcher, build_dispatcher
from workbench.routers import activity, analysis, auth, backfills, feedback, health
from workbench.settings import Settings


def create_app(
    engine: AsyncEngine | None = None,
    settings: Settings | None = None,
    dispatcher: JobDispatcher | None = None,
) -> FastAPI:
    config = settings or Settings()
    database = engine or create_engine(config.database_url)
    jobs = dispatcher or build_dispatcher(database, config)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        yield
        if engine is None:
            await database.dispose()

    app = FastAPI(
        title="Feedback Desk API",
        version="0.3.0",
        description=(
            "Independent customer-feedback workspace API. First register, sign in or "
            "open a demo; use its returned token in Authorize (WorkspaceBearer). "
            "Protected reads and writes are scoped to that workspace. Immutable input "
            "and versioned results are processed by a separate durable worker. No "
            "worker/provider credentials are exposed by this API."
        ),
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
        openapi_tags=[
            {
                "name": "Authentication",
                "description": (
                    "Independent accounts and isolated temporary demos; revocable opaque sessions."
                ),
            },
            {
                "name": "Feedback",
                "description": (
                    "User-authored or synthetic inputs, bounded cursor pages, results and progress."
                ),
            },
            {
                "name": "Backfills and recovery",
                "description": "Fixed selections, version history, cancellation and bounded retry.",
            },
            {
                "name": "Activity",
                "description": "Unified automatic, individual and bulk processing history.",
            },
            {"name": "Health", "description": "Public API/database readiness only."},
        ],
    )
    app.dependency_overrides[get_database] = lambda: database
    app.dependency_overrides[get_settings] = lambda: config
    app.dependency_overrides[get_dispatcher] = lambda: jobs
    install_http(app, config)
    for router in (
        auth.router,
        feedback.router,
        analysis.router,
        activity.router,
        backfills.router,
        health.router,
    ):
        app.include_router(router)
    app.mount(
        "/docs-assets",
        StaticFiles(directory=Path(__file__).parent / "static/swagger"),
        name="swagger-assets",
    )

    @app.get("/docs", include_in_schema=False)
    async def swagger() -> HTMLResponse:
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="Feedback Desk API · Swagger UI",
            swagger_js_url="/docs-assets/swagger-ui-bundle.js",
            swagger_css_url="/docs-assets/swagger-ui.css",
            swagger_favicon_url="/docs-assets/favicon-32x32.png",
            swagger_ui_parameters={
                "persistAuthorization": False,
                "validatorUrl": None,
                "defaultModelsExpandDepth": 0,
                "displayRequestDuration": True,
            },
        )

    return app


app = create_app()
