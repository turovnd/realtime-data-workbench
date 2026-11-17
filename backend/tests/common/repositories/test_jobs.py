import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncEngine

from common.infrastructure.database import run_transaction, session_scope
from common.infrastructure.deterministic import generate_demo
from common.logic.enrichment import enrich
from common.logic.errors import ConflictError
from common.logic.ingestion import ingest
from common.logic.synthetic import synthetic_inputs
from common.models import AnalysisJob
from common.repositories.inspection import snapshot
from common.repositories.jobs import claim_job, finish_job, retry_job

pytestmark = pytest.mark.integration


async def test_concurrent_claims_are_unique_and_globally_bounded(database: AsyncEngine) -> None:
    await run_transaction(database, ingest, synthetic_inputs("seed", 4))
    claims = await asyncio.gather(*(run_transaction(database, claim_job) for _ in range(6)))
    ids = [claim.id for claim in claims if claim]
    assert len(ids) == 2
    assert len(set(ids)) == 2


async def test_expired_lease_fences_stale_provider_result(database: AsyncEngine) -> None:
    await run_transaction(database, ingest, synthetic_inputs("seed", 1))
    first = await run_transaction(database, claim_job)
    assert first
    result = await enrich(first.text, first.config, generate=generate_demo)
    async with session_scope(database) as session:
        await session.execute(
            update(AnalysisJob)
            .where(AnalysisJob.id == first.id)
            .values(lease_until=datetime.now(UTC) - timedelta(seconds=1))
        )
    second = await run_transaction(database, claim_job)
    assert second and second.id == first.id and second.fence == first.fence + 1
    assert await run_transaction(database, finish_job, first, result) is False
    assert await run_transaction(database, finish_job, second, result) is True
    assert await run_transaction(database, finish_job, second, result) is False
    view = await run_transaction(database, snapshot)
    assert len(view.records[0].outputs) == 1
    assert view.records[0].jobs[0].attempts == 2


async def test_retry_budget_survives_restarts_and_manual_retry(database: AsyncEngine) -> None:
    await run_transaction(database, ingest, synthetic_inputs("seed", 1))
    for _ in range(3):
        claim = await run_transaction(database, claim_job, lease_seconds=-1)
        assert claim
    assert await run_transaction(database, claim_job) is None
    view = await run_transaction(database, snapshot)
    assert view.records[0].jobs[0].status == "failed"
    with pytest.raises(ConflictError):
        await run_transaction(database, retry_job, view.records[0].jobs[0].id)
