import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from common.infrastructure.database import run_transaction
from common.infrastructure.deterministic import generate_demo
from common.logic.backfills import cancel_backfill, start_backfill
from common.logic.enrichment import enrich
from common.logic.ingestion import ingest
from common.logic.synthetic import synthetic_inputs
from common.repositories.inspection import snapshot
from common.repositories.jobs import claim_job, finish_job
from common.schemas.backfills import BackfillInput
from modules.worker.processing import process_one

pytestmark = pytest.mark.integration


async def test_backfill_freezes_selection_and_keeps_old_output(database: AsyncEngine) -> None:
    await run_transaction(database, ingest, synthetic_inputs("first", 2))
    while await process_one(database):
        pass
    before = await run_transaction(database, snapshot)
    batch_id = await run_transaction(
        database,
        start_backfill,
        BackfillInput(record_ids=[row.id for row in before.records], config="v2"),
    )
    await run_transaction(database, ingest, synthetic_inputs("later", 1))
    while await process_one(database):
        pass
    after = await run_transaction(database, snapshot)
    assert after.batches[0].id == batch_id
    assert after.batches[0].completed == 2
    assert after.batches[0].watermark == 2
    assert len(after.records[0].outputs) == 1
    assert all(
        [output.config for output in row.outputs] == ["v1", "v2"] for row in after.records[1:]
    )


async def test_cancellation_fences_inflight_and_preserves_completed(database: AsyncEngine) -> None:
    await run_transaction(database, ingest, synthetic_inputs("first", 1))
    await process_one(database)
    before = await run_transaction(database, snapshot)
    batch_id = await run_transaction(
        database, start_backfill, BackfillInput(record_ids=[before.records[0].id], config="v2")
    )
    claim = await run_transaction(database, claim_job)
    assert claim
    await run_transaction(database, cancel_backfill, batch_id)
    result = await enrich(claim.text, claim.config, generate=generate_demo)
    assert not await run_transaction(database, finish_job, claim, result)
    after = await run_transaction(database, snapshot)
    assert after.batches[0].cancelled
    assert len(after.records[0].outputs) == 1
