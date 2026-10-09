import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.database import create_engine, migrate


@pytest_asyncio.fixture
async def database() -> AsyncIterator[AsyncEngine]:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to a disposable real PostgreSQL database")
    engine = create_engine(url)
    await migrate(engine)
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE auth_sessions, auth_buckets, accounts, feed_views, provider_usage, "
                "enrichments, jobs, backfills, feedback CASCADE"
            )
        )
        await conn.execute(text("UPDATE workspace_state SET cursor=0 WHERE id='test'"))
    try:
        yield engine
    finally:
        await engine.dispose()
