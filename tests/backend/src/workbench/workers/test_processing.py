import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.deterministic import generate_demo
from workbench.logic.enrichment import enrich
from workbench.logic.ingestion import ingest
from workbench.logic.synthetic import synthetic_inputs
from workbench.repositories.inspection import snapshot
from workbench.repositories.jobs import claim_job, retry_job
from workbench.workers.processing import process_one

pytestmark = pytest.mark.integration


async def test_crash_after_provider_response_recovers_from_committed_job(
    database: AsyncEngine,
) -> None:
    await ingest(database, synthetic_inputs("seed", 1))
    lost = await claim_job(database, lease_seconds=-1)
    assert lost
    await enrich(lost.text, lost.config, generate=generate_demo)
    # No completion: this models a process dying after the provider returned.
    assert await process_one(database)
    view = await snapshot(database)
    assert view.records[0].jobs[0].status == "succeeded"
    assert view.records[0].jobs[0].attempts == 2


async def test_invalid_output_is_durable_and_selectively_retryable(database: AsyncEngine) -> None:
    await ingest(database, synthetic_inputs("seed", 1))

    async def invalid(_text: str, _config: str) -> str:
        return "{}"

    await process_one(database, generate=invalid)
    failed = await snapshot(database)
    job = failed.records[0].jobs[0]
    assert job.status == "failed" and job.attempts == 1
    await retry_job(database, job.id)
    await process_one(database)
    assert (await snapshot(database)).records[0].jobs[0].status == "succeeded"
