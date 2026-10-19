import json
import logging

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.deterministic import generate_demo
from workbench.logic.backfills import start_backfill
from workbench.logic.enrichment import enrich
from workbench.logic.ingestion import ingest
from workbench.logic.synthetic import synthetic_inputs
from workbench.repositories.inspection import snapshot
from workbench.repositories.jobs import claim_job, retry_job
from workbench.schemas.backfills import BackfillInput
from workbench.schemas.common import Config
from workbench.schemas.feedback import FeedbackInput
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


@pytest.mark.parametrize("config", ["v1", "v2"])
@pytest.mark.parametrize(
    "invalid_payload,reason",
    [
        (
            {
                "topic": "other",
                "intent": "unclear",
                "summary": {"private": "PRIVATE_PROVIDER_MARKER"},
                "PRIVATE_FIELD_MARKER\njob=spoofed": "PRIVATE_PROVIDER_MARKER",
                "evidence": ["Activity"],
            },
            "Provider output schema validation failed",
        ),
        (
            {
                "topic": "other",
                "intent": "unclear",
                "summary": "Описание Activity.",
                "evidence": ["PRIVATE_PROVIDER_MARKER"],
            },
            "Provider evidence validation failed",
        ),
    ],
    ids=["invalid-schema", "ungrounded-evidence"],
)
async def test_multilingual_validation_failure_is_terminal_durable_and_preserves_prior_results(
    database: AsyncEngine,
    config: Config,
    invalid_payload: dict[str, object],
    reason: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="workbench.worker")
    source = (
        "В Activity → View details теперь раскрываются сообщения, результаты конкретного запуска, "
        "статусы, модель, время и ошибки. Добавлены переход к отзыву и подгрузка списка."
    )
    await ingest(database, [FeedbackInput(identity="russian", text=source, channel="In-app")])

    async def valid(text: str, _config: str) -> str:
        assert text == source
        return json.dumps(
            {
                "topic": "other",
                "intent": "unclear",
                "summary": "Описание результатов запуска в Activity.",
                "evidence": ["результаты конкретного запуска"],
            },
            ensure_ascii=False,
        )

    if config == "v2":
        assert await process_one(database, generate=valid)
        initial = (await snapshot(database)).records[0]
        await start_backfill(database, BackfillInput(record_ids=[initial.id], config="v2"))
    previous_outputs = (await snapshot(database)).records[0].outputs
    calls = 0

    async def invalid(text: str, current_config: str) -> str:
        nonlocal calls
        calls += 1
        assert text == source and current_config == config
        return json.dumps(invalid_payload, ensure_ascii=False)

    assert await process_one(database, generate=invalid)
    failed = (await snapshot(database)).records[0]
    job = failed.jobs[-1]
    assert job.status == "failed" and job.attempts == 1
    assert job.error is not None and job.error.startswith(reason)
    assert "PRIVATE_PROVIDER_MARKER" not in job.error and source not in job.error
    assert "PRIVATE_FIELD_MARKER" not in job.error and "job=spoofed" not in job.error
    assert failed.outputs == previous_outputs
    assert not await process_one(database, generate=invalid)
    assert calls == 1
    assert (await snapshot(database)).records[0] == failed

    await retry_job(database, job.id)
    assert await process_one(database, generate=valid)
    recovered = (await snapshot(database)).records[0]
    assert recovered.jobs[-1].status == "succeeded" and recovered.jobs[-1].attempts == 2
    assert recovered.outputs[:-1] == previous_outputs
    assert recovered.outputs[-1].config == config
    assert recovered.outputs[-1].evidence == ["результаты конкретного запуска"]
    assert "PRIVATE_PROVIDER_MARKER" not in caplog.text
    assert "PRIVATE_FIELD_MARKER" not in caplog.text
    assert source not in caplog.text
