import asyncio

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine

from common.infrastructure.database import run_transaction
from common.infrastructure.deterministic import generate_demo
from common.logic.analysis import start_analysis
from common.logic.errors import ConflictError
from common.logic.ingestion import ingest
from common.logic.synthetic import synthetic_inputs
from common.models import AnalysisJob, AnalysisResult
from common.repositories.inspection import snapshot
from common.repositories.jobs import retry_job
from common.schemas.analysis import AnalysisInput
from modules.worker.processing import process_one

pytestmark = pytest.mark.integration


async def test_unlimited_runs_keep_recent_responses_and_concurrent_clicks_do_not_duplicate_work(
    database: AsyncEngine,
) -> None:
    await run_transaction(database, ingest, synthetic_inputs("seed", 1))
    initial = (await run_transaction(database, snapshot)).records[0]
    with pytest.raises(ConflictError, match="already in progress"):
        await run_transaction(
            database,
            start_analysis,
            "test",
            initial.id,
            AnalysisInput(identity="early"),
            "openrouter/test",
        )
    assert await process_one(database)
    results = await asyncio.gather(
        *[
            run_transaction(
                database,
                start_analysis,
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
        pending, inserted = await run_transaction(
            database,
            start_analysis,
            "test",
            initial.id,
            AnalysisInput(identity=f"run-{run}"),
            "openrouter/test",
        )
        assert inserted and pending.jobs[-1].run == run
        assert await process_one(database, generate=generate_demo, live_budget=None)
    complete = (await run_transaction(database, snapshot)).records[0]
    assert [job.run for job in complete.jobs] == list(range(16, 26))
    assert [output.run for output in complete.outputs] == list(range(16, 26))
    replay, inserted = await run_transaction(
        database,
        start_analysis,
        "test",
        initial.id,
        AnalysisInput(identity="run-3"),
        "openrouter/test",
    )
    assert not inserted and len(replay.jobs) == 10
    async with database.connect() as conn:
        assert await conn.scalar(select(func.count()).select_from(AnalysisJob)) == 25
        assert await conn.scalar(select(func.count()).select_from(AnalysisResult)) == 25
    assert (await run_transaction(database, snapshot)).batches == []

    await run_transaction(database, ingest, synthetic_inputs("another", 1))
    assert await process_one(database)
    records = (await run_transaction(database, snapshot)).records
    assert len(records) == 2
    assert len(records[0].jobs) == len(records[0].outputs) == 1
    assert len(records[1].jobs) == len(records[1].outputs) == 10


async def test_recent_history_retains_last_success_after_many_failed_runs(
    database: AsyncEngine,
) -> None:
    await run_transaction(database, ingest, synthetic_inputs("seed", 1))
    assert await process_one(database)
    initial = (await run_transaction(database, snapshot)).records[0]

    async def invalid(_text: str, _config: str) -> str:
        return "{}"

    for run in range(2, 14):
        await run_transaction(
            database,
            start_analysis,
            "test",
            initial.id,
            AnalysisInput(identity=f"run-{run}"),
            "openrouter/test",
        )
        assert await process_one(database, generate=invalid, live_budget=None)

    complete = (await run_transaction(database, snapshot)).records[0]
    assert [job.run for job in complete.jobs] == list(range(4, 14))
    assert all(job.status == "failed" for job in complete.jobs)
    assert [output.run for output in complete.outputs] == [1]
    async with database.connect() as conn:
        assert await conn.scalar(select(func.count()).select_from(AnalysisJob)) == 13
        assert await conn.scalar(select(func.count()).select_from(AnalysisResult)) == 1


async def test_an_older_failed_run_cannot_be_retried_behind_newer_work(
    database: AsyncEngine,
) -> None:
    await run_transaction(database, ingest, synthetic_inputs("seed", 1))

    async def invalid(_text: str, _config: str) -> str:
        return "{}"

    assert await process_one(database, generate=invalid)
    failed = (await run_transaction(database, snapshot)).records[0]
    await run_transaction(
        database,
        start_analysis,
        "test",
        failed.id,
        AnalysisInput(identity="new"),
        "openrouter/test",
    )
    with pytest.raises(ConflictError, match="latest analysis"):
        await run_transaction(database, retry_job, failed.jobs[0].id)
    assert await process_one(database, generate=generate_demo, live_budget=1)
    record = (await run_transaction(database, snapshot)).records[0]
    assert record.outputs[0].run == 2
    assert record.jobs[0].status == "failed" and record.jobs[1].status == "succeeded"
