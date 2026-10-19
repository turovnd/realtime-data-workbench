import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.deterministic import generate_demo
from workbench.infrastructure.tables import jobs
from workbench.logic.enrichment import enrich
from workbench.logic.errors import ConflictError
from workbench.logic.ingestion import ingest
from workbench.logic.synthetic import synthetic_inputs
from workbench.repositories.inspection import snapshot
from workbench.repositories.jobs import claim_job, finish_job, retry_job

pytestmark = pytest.mark.integration


async def test_concurrent_claims_are_unique_and_globally_bounded(database: AsyncEngine) -> None:
    await ingest(database, synthetic_inputs("seed", 4))
    claims = await asyncio.gather(*(claim_job(database) for _ in range(6)))
    ids = [claim.id for claim in claims if claim]
    assert len(ids) == 2
    assert len(set(ids)) == 2


async def test_expired_lease_fences_stale_provider_result(database: AsyncEngine) -> None:
    await ingest(database, synthetic_inputs("seed", 1))
    first = await claim_job(database)
    assert first
    result = await enrich(first.text, first.config, generate=generate_demo)
    async with database.begin() as conn:
        await conn.execute(
            update(jobs)
            .where(jobs.c.id == first.id)
            .values(lease_until=datetime.now(UTC) - timedelta(seconds=1))
        )
    second = await claim_job(database)
    assert second and second.id == first.id and second.fence == first.fence + 1
    assert await finish_job(database, first, result) is False
    assert await finish_job(database, second, result) is True
    assert await finish_job(database, second, result) is False
    view = await snapshot(database)
    assert len(view.records[0].outputs) == 1
    assert view.records[0].jobs[0].attempts == 2


async def test_retry_budget_survives_restarts_and_manual_retry(database: AsyncEngine) -> None:
    await ingest(database, synthetic_inputs("seed", 1))
    for _ in range(3):
        claim = await claim_job(database, lease_seconds=-1)
        assert claim
    assert await claim_job(database) is None
    view = await snapshot(database)
    assert view.records[0].jobs[0].status == "failed"
    with pytest.raises(ConflictError):
        await retry_job(database, view.records[0].jobs[0].id)
