import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.database import migrate
from workbench.logic.analysis import start_analysis
from workbench.logic.backfills import start_backfill
from workbench.logic.ingestion import ingest
from workbench.logic.synthetic import synthetic_inputs
from workbench.repositories.inspection import snapshot
from workbench.schemas.analysis import AnalysisInput
from workbench.schemas.backfills import BackfillInput
from workbench.workers.processing import process_one

pytestmark = pytest.mark.integration


async def test_legacy_v1_v2_history_survives_idempotent_run_migration(
    database: AsyncEngine,
) -> None:
    await ingest(database, synthetic_inputs("legacy", 1))
    assert await process_one(database)
    record = (await snapshot(database)).records[0]
    await start_backfill(database, BackfillInput(record_ids=[record.id]))
    assert await process_one(database)
    before = (await snapshot(database)).records[0]
    async with database.begin() as conn:
        await conn.execute(text("ALTER TABLE jobs DROP COLUMN run CASCADE"))
        await conn.execute(text("ALTER TABLE jobs DROP COLUMN request_identity CASCADE"))
        await conn.execute(text("DROP INDEX uq_job_legacy_config"))
        await conn.execute(
            text("ALTER TABLE jobs ADD CONSTRAINT uq_job_version UNIQUE(record_id,config)")
        )
        await conn.execute(text("ALTER TABLE enrichments DROP COLUMN run CASCADE"))
        await conn.execute(
            text(
                "ALTER TABLE enrichments ADD CONSTRAINT uq_output_version UNIQUE(record_id,config)"
            )
        )
    await migrate(database)
    await migrate(database)
    assert (await snapshot(database)).records[0] == before
    pending, inserted = await start_analysis(
        database, "test", record.id, AnalysisInput(identity="post-migration"), "openrouter/test"
    )
    assert inserted and pending.jobs[-1].run == 3
    assert pending.outputs == before.outputs
    assert await process_one(database, live_budget=1)
    assert len((await snapshot(database)).records[0].outputs) == 3
    with pytest.raises(DBAPIError, match="immutable record"):
        async with database.begin() as conn:
            await conn.execute(text("UPDATE enrichments SET payload='{}'::json"))
    with pytest.raises(DBAPIError, match="immutable record"):
        async with database.begin() as conn:
            await conn.execute(text("UPDATE feedback SET text='changed'"))
