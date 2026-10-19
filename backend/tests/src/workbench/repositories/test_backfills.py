import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.tables import jobs, outputs, records
from workbench.logic.analysis import start_analysis
from workbench.logic.backfill_details import backfill_page
from workbench.logic.backfills import start_backfill
from workbench.logic.errors import NotFoundError
from workbench.logic.ingestion import ingest
from workbench.logic.synthetic import synthetic_inputs
from workbench.repositories.backfills import batch_items
from workbench.repositories.feedback import hydrate
from workbench.repositories.sessions import create_session, resolve_session
from workbench.schemas.analysis import AnalysisInput
from workbench.schemas.backfills import BackfillInput
from workbench.workers.processing import process_one

pytestmark = pytest.mark.integration


async def test_activity_keeps_exact_original_result_beyond_recent_history_window(
    database: AsyncEngine,
) -> None:
    await ingest(database, synthetic_inputs("history", 1))
    assert await process_one(database)
    async with database.connect() as conn:
        record_id = await conn.scalar(select(records.c.id).where(records.c.workspace_id == "test"))
    assert record_id
    batch_id = await start_backfill(database, BackfillInput(record_ids=[record_id]))
    assert await process_one(database)
    before = await backfill_page(database, "test", batch_id)
    assert before.items[0].job is not None and before.items[0].job.run == 2
    assert before.items[0].output is not None and before.items[0].output.run == 2

    for index in range(12):
        await start_analysis(
            database,
            "test",
            record_id,
            AnalysisInput(identity=f"repeat-{index}"),
            "deterministic-rules/1",
        )
        assert await process_one(database)

    async with database.connect() as conn:
        recent = (await hydrate(conn, "test", [record_id]))[0]
        assert len(recent.jobs) == len(recent.outputs) == 10
        assert all(job.run > 2 for job in recent.jobs)
        assert all(output.run > 2 for output in recent.outputs)
        assert (
            await conn.scalar(
                select(func.count()).select_from(jobs).where(jobs.c.record_id == record_id)
            )
            == 14
        )
        assert (
            await conn.scalar(
                select(func.count()).select_from(outputs).where(outputs.c.record_id == record_id)
            )
            == 14
        )
    assert await backfill_page(database, "test", batch_id) == before

    token = await create_session(database)
    foreign = await resolve_session(database, token)
    assert foreign
    await ingest(database, synthetic_inputs("foreign", 1), foreign)
    assert await process_one(database)
    async with database.connect() as conn:
        foreign_id = await conn.scalar(
            select(records.c.id).where(records.c.workspace_id == foreign)
        )
        assert foreign_id
        assert await batch_items(conn, foreign, [record_id], "v2") == []
        assert await batch_items(conn, "test", [record_id, foreign_id], "v2") == before.items
        missing_version = await batch_items(conn, foreign, [foreign_id], "v2")
        assert len(missing_version) == 1
        assert missing_version[0].job is None and missing_version[0].output is None
        with pytest.raises(ValueError, match="50"):
            await batch_items(conn, "test", [record_id] * 51, "v2")
    with pytest.raises(NotFoundError):
        await backfill_page(database, foreign, batch_id)
