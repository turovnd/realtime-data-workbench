import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from common.db import upgrade_database
from common.infrastructure.database import create_engine


@pytest_asyncio.fixture
async def database() -> AsyncIterator[AsyncEngine]:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to a disposable real PostgreSQL database")
    engine = create_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(upgrade_database)
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE auth_sessions, auth_buckets, accounts, feed_views, provider_usage, "
                "enrichments, jobs, backfills, feedback, workspace_state CASCADE"
            )
        )
        await conn.execute(text("INSERT INTO workspace_state(id,cursor) VALUES ('test',0)"))
    try:
        yield engine
    finally:
        await engine.dispose()
