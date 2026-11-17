import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine

from common.infrastructure.database import run_transaction, session_scope
from common.logic.analysis import start_analysis
from common.logic.backfill_details import backfill_page
from common.logic.backfills import start_backfill
from common.logic.errors import NotFoundError
from common.logic.ingestion import ingest
from common.logic.synthetic import synthetic_inputs
from common.models import AnalysisJob, AnalysisResult, Feedback
from common.repositories.backfills import batch_items
from common.repositories.feedback import hydrate
from common.repositories.sessions import create_session, resolve_session
from common.schemas.analysis import AnalysisInput
from common.schemas.backfills import BackfillInput
from modules.worker.processing import process_one

pytestmark = pytest.mark.integration


async def test_activity_keeps_exact_original_result_beyond_recent_history_window(
    database: AsyncEngine,
) -> None:
    await run_transaction(database, ingest, synthetic_inputs("history", 1))
    assert await process_one(database)
    async with session_scope(database) as session:
        record_id = await session.scalar(select(Feedback.id).where(Feedback.workspace_id == "test"))
    assert record_id
    batch_id = await run_transaction(
        database, start_backfill, BackfillInput(record_ids=[record_id])
    )
    assert await process_one(database)
    before = await run_transaction(database, backfill_page, "test", batch_id)
    assert before.items[0].job is not None and before.items[0].job.run == 2
    assert before.items[0].output is not None and before.items[0].output.run == 2

    for index in range(12):
        await run_transaction(
            database,
            start_analysis,
            "test",
            record_id,
            AnalysisInput(identity=f"repeat-{index}"),
            "deterministic-rules/1",
        )
        assert await process_one(database)

    async with session_scope(database) as session:
        recent = (await session.run_sync(hydrate, "test", [record_id]))[0]
        assert len(recent.jobs) == len(recent.outputs) == 10
        assert all(job.run > 2 for job in recent.jobs)
        assert all(output.run > 2 for output in recent.outputs)
        assert (
            await session.scalar(
                select(func.count())
                .select_from(AnalysisJob)
                .where(AnalysisJob.record_id == record_id)
            )
            == 14
        )
        assert (
            await session.scalar(
                select(func.count())
                .select_from(AnalysisResult)
                .where(AnalysisResult.record_id == record_id)
            )
            == 14
        )
    assert await run_transaction(database, backfill_page, "test", batch_id) == before

    token = await run_transaction(database, create_session)
    foreign = await run_transaction(database, resolve_session, token)
    assert foreign
    await run_transaction(database, ingest, synthetic_inputs("foreign", 1), foreign)
    assert await process_one(database)
    async with session_scope(database) as session:
        foreign_id = await session.scalar(
            select(Feedback.id).where(Feedback.workspace_id == foreign)
        )
        assert foreign_id
        assert await session.run_sync(batch_items, foreign, [record_id], "v2") == []
        assert (
            await session.run_sync(batch_items, "test", [record_id, foreign_id], "v2")
            == before.items
        )
        missing_version = await session.run_sync(batch_items, foreign, [foreign_id], "v2")
        assert len(missing_version) == 1
        assert missing_version[0].job is None and missing_version[0].output is None
        with pytest.raises(ValueError, match="50"):
            await session.run_sync(batch_items, "test", [record_id] * 51, "v2")
    with pytest.raises(NotFoundError):
        await run_transaction(database, backfill_page, foreign, batch_id)
