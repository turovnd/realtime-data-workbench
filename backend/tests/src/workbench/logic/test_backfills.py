import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.deterministic import generate_demo
from workbench.logic.backfills import cancel_backfill, start_backfill
from workbench.logic.enrichment import enrich
from workbench.logic.ingestion import ingest
from workbench.logic.synthetic import synthetic_inputs
from workbench.repositories.inspection import snapshot
from workbench.repositories.jobs import claim_job, finish_job
from workbench.schemas.backfills import BackfillInput
from workbench.workers.processing import process_one

pytestmark = pytest.mark.integration


async def test_backfill_freezes_selection_and_keeps_old_output(database: AsyncEngine) -> None:
    await ingest(database, synthetic_inputs("first", 2))
    while await process_one(database):
        pass
    before = await snapshot(database)
    batch_id = await start_backfill(
        database, BackfillInput(record_ids=[row.id for row in before.records], config="v2")
    )
    await ingest(database, synthetic_inputs("later", 1))
    while await process_one(database):
        pass
    after = await snapshot(database)
    assert after.batches[0].id == batch_id
    assert after.batches[0].completed == 2
    assert after.batches[0].watermark == 2
    assert len(after.records[0].outputs) == 1
    assert all(
        [output.config for output in row.outputs] == ["v1", "v2"] for row in after.records[1:]
    )


async def test_cancellation_fences_inflight_and_preserves_completed(database: AsyncEngine) -> None:
    await ingest(database, synthetic_inputs("first", 1))
    await process_one(database)
    before = await snapshot(database)
    batch_id = await start_backfill(
        database, BackfillInput(record_ids=[before.records[0].id], config="v2")
    )
    claim = await claim_job(database)
    assert claim
    await cancel_backfill(database, batch_id)
    result = await enrich(claim.text, claim.config, generate=generate_demo)
    assert not await finish_job(database, claim, result)
    after = await snapshot(database)
    assert after.batches[0].cancelled
    assert len(after.records[0].outputs) == 1
