import asyncio

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.deterministic import generate_demo
from workbench.logic.analysis import start_analysis
from workbench.logic.errors import ConflictError
from workbench.logic.ingestion import ingest
from workbench.logic.synthetic import synthetic_inputs
from workbench.models import AnalysisJob, AnalysisResult
from workbench.repositories.inspection import snapshot
from workbench.repositories.jobs import retry_job
from workbench.schemas.analysis import AnalysisInput
from workbench.workers.processing import process_one

pytestmark = pytest.mark.integration


async def test_unlimited_runs_keep_recent_responses_and_concurrent_clicks_do_not_duplicate_work(
    database: AsyncEngine,
) -> None:
    await ingest(database, synthetic_inputs("seed", 1))
    initial = (await snapshot(database)).records[0]
    with pytest.raises(ConflictError, match="already in progress"):
        await start_analysis(
            database, "test", initial.id, AnalysisInput(identity="early"), "openrouter/test"
        )
    assert await process_one(database)
    results = await asyncio.gather(
        *[
            start_analysis(
                database,
                "test",
                initial.id,
                AnalysisInput(identity=f"parallel-{i}"),
                "openrouter/test",
            )
            for i in range(2)
        ],
        return_exceptions=True,
    )
    assert sum(isinstance(result, ConflictError) for result in results) == 1
    assert await process_one(database, generate=generate_demo, live_budget=None)
    for run in range(3, 26):
        pending, inserted = await start_analysis(
            database, "test", initial.id, AnalysisInput(identity=f"run-{run}"), "openrouter/test"
        )
        assert inserted and pending.jobs[-1].run == run
        assert await process_one(database, generate=generate_demo, live_budget=None)
    complete = (await snapshot(database)).records[0]
    assert [job.run for job in complete.jobs] == list(range(16, 26))
    assert [output.run for output in complete.outputs] == list(range(16, 26))
    replay, inserted = await start_analysis(
        database, "test", initial.id, AnalysisInput(identity="run-3"), "openrouter/test"
    )
    assert not inserted and len(replay.jobs) == 10
    async with database.connect() as conn:
        assert await conn.scalar(select(func.count()).select_from(AnalysisJob)) == 25
        assert await conn.scalar(select(func.count()).select_from(AnalysisResult)) == 25
    assert (await snapshot(database)).batches == []

    await ingest(database, synthetic_inputs("another", 1))
    assert await process_one(database)
    records = (await snapshot(database)).records
    assert len(records) == 2
    assert len(records[0].jobs) == len(records[0].outputs) == 1
    assert len(records[1].jobs) == len(records[1].outputs) == 10


async def test_recent_history_retains_last_success_after_many_failed_runs(
    database: AsyncEngine,
) -> None:
    await ingest(database, synthetic_inputs("seed", 1))
    assert await process_one(database)
    initial = (await snapshot(database)).records[0]

    async def invalid(_text: str, _config: str) -> str:
        return "{}"

    for run in range(2, 14):
        await start_analysis(
            database, "test", initial.id, AnalysisInput(identity=f"run-{run}"), "openrouter/test"
        )
        assert await process_one(database, generate=invalid, live_budget=None)

    complete = (await snapshot(database)).records[0]
    assert [job.run for job in complete.jobs] == list(range(4, 14))
    assert all(job.status == "failed" for job in complete.jobs)
    assert [output.run for output in complete.outputs] == [1]
    async with database.connect() as conn:
        assert await conn.scalar(select(func.count()).select_from(AnalysisJob)) == 13
        assert await conn.scalar(select(func.count()).select_from(AnalysisResult)) == 1


async def test_an_older_failed_run_cannot_be_retried_behind_newer_work(
    database: AsyncEngine,
) -> None:
    await ingest(database, synthetic_inputs("seed", 1))

    async def invalid(_text: str, _config: str) -> str:
        return "{}"

    assert await process_one(database, generate=invalid)
    failed = (await snapshot(database)).records[0]
    await start_analysis(
        database, "test", failed.id, AnalysisInput(identity="new"), "openrouter/test"
    )
    with pytest.raises(ConflictError, match="latest analysis"):
        await retry_job(database, failed.jobs[0].id)
    assert await process_one(database, generate=generate_demo, live_budget=1)
    record = (await snapshot(database)).records[0]
    assert record.outputs[0].run == 2
    assert record.jobs[0].status == "failed" and record.jobs[1].status == "succeeded"
