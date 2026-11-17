import json
import logging
from datetime import UTC, datetime

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncEngine

from common.infrastructure.database import run_transaction, session_scope
from common.infrastructure.deterministic import generate_demo
from common.logic.backfills import start_backfill
from common.logic.enrichment import enrich
from common.logic.ingestion import ingest
from common.logic.synthetic import synthetic_inputs
from common.models import AnalysisJob, ProviderUsage
from common.repositories.inspection import snapshot
from common.repositories.jobs import claim_job, retry_job
from common.schemas.backfills import BackfillInput
from common.schemas.common import Config
from common.schemas.feedback import FeedbackInput
from common.settings import Settings
from modules.worker.processing import process_one
from modules.worker.providers import build_generators

pytestmark = pytest.mark.integration


async def test_crash_after_provider_response_recovers_from_committed_job(
    database: AsyncEngine,
) -> None:
    await run_transaction(database, ingest, synthetic_inputs("seed", 1))
    lost = await run_transaction(database, claim_job, lease_seconds=-1)
    assert lost
    await enrich(lost.text, lost.config, generate=generate_demo)
    # No completion: this models a process dying after the provider returned.
    assert await process_one(database)
    view = await run_transaction(database, snapshot)
    assert view.records[0].jobs[0].status == "succeeded"
    assert view.records[0].jobs[0].attempts == 2


async def test_invalid_output_is_durable_and_selectively_retryable(database: AsyncEngine) -> None:
    await run_transaction(database, ingest, synthetic_inputs("seed", 1))

    async def invalid(_text: str, _config: str) -> str:
        return "{}"

    await process_one(database, generate=invalid)
    failed = await run_transaction(database, snapshot)
    job = failed.records[0].jobs[0]
    assert job.status == "failed" and job.attempts == 1
    await run_transaction(database, retry_job, job.id)
    await process_one(database)
    assert (await run_transaction(database, snapshot)).records[0].jobs[0].status == "succeeded"


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
    caplog.set_level(logging.INFO, logger="modules.worker")
    source = (
        "В Activity → View details теперь раскрываются сообщения, результаты конкретного запуска, "
        "статусы, модель, время и ошибки. Добавлены переход к отзыву и подгрузка списка."
    )
    await run_transaction(
        database, ingest, [FeedbackInput(identity="russian", text=source, channel="In-app")]
    )

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
        initial = (await run_transaction(database, snapshot)).records[0]
        await run_transaction(
            database, start_backfill, BackfillInput(record_ids=[initial.id], config="v2")
        )
    previous_outputs = (await run_transaction(database, snapshot)).records[0].outputs
    calls = 0

    async def invalid(text: str, current_config: str) -> str:
        nonlocal calls
        calls += 1
        assert text == source and current_config == config
        return json.dumps(invalid_payload, ensure_ascii=False)

    assert await process_one(database, generate=invalid)
    failed = (await run_transaction(database, snapshot)).records[0]
    job = failed.jobs[-1]
    assert job.status == "failed" and job.attempts == 1
    assert job.error is not None and job.error.startswith(reason)
    assert "PRIVATE_PROVIDER_MARKER" not in job.error and source not in job.error
    assert "PRIVATE_FIELD_MARKER" not in job.error and "job=spoofed" not in job.error
    assert failed.outputs == previous_outputs
    assert not await process_one(database, generate=invalid)
    assert calls == 1
    assert (await run_transaction(database, snapshot)).records[0] == failed

    await run_transaction(database, retry_job, job.id)
    assert await process_one(database, generate=valid)
    recovered = (await run_transaction(database, snapshot)).records[0]
    assert recovered.jobs[-1].status == "succeeded" and recovered.jobs[-1].attempts == 2
    assert recovered.outputs[:-1] == previous_outputs
    assert recovered.outputs[-1].config == config
    assert recovered.outputs[-1].evidence == ["результаты конкретного запуска"]
    assert "PRIVATE_PROVIDER_MARKER" not in caplog.text
    assert "PRIVATE_FIELD_MARKER" not in caplog.text
    assert source not in caplog.text


async def test_unconfigured_live_job_fails_without_falling_back_or_spending_budget(
    database: AsyncEngine,
) -> None:
    settings = Settings(
        provider_mode="openrouter", openrouter_calls_enabled=False, openrouter_api_key=None
    )
    await run_transaction(
        database, ingest, synthetic_inputs("seed", 1), provider=settings.provider_id
    )

    def handler(_request: httpx.Request) -> httpx.Response:
        pytest.fail("An unconfigured live provider must not call the network")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        assert await process_one(database, generators=build_generators(settings, client))
    record = (await run_transaction(database, snapshot)).records[0]
    assert record.outputs == []
    assert record.jobs[0].status == "failed" and record.jobs[0].attempts == 1
    assert record.jobs[0].error == "Selected provider is not configured"
    async with session_scope(database) as session:
        assert await session.scalar(select(ProviderUsage.calls)) is None


async def test_provider_retries_are_three_durable_worker_attempts(
    database: AsyncEngine,
) -> None:
    settings = Settings(
        openrouter_calls_enabled=True,
        openrouter_api_key=SecretStr("test-only-not-a-key"),
        provider_mode="openrouter",
    )
    await run_transaction(
        database, ingest, synthetic_inputs("seed", 1), provider=settings.provider_id
    )
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(429, text="PRIVATE_UPSTREAM_MARKER")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        generators = build_generators(settings, client)
        for attempt in range(1, 4):
            assert await process_one(database, generators=generators, live_budget=3)
            record = (await run_transaction(database, snapshot)).records[0]
            assert calls == attempt == record.jobs[0].attempts
            assert record.jobs[0].status == ("queued" if attempt < 3 else "failed")
            assert record.outputs == []
            assert record.jobs[0].error == "RetryableProviderError"
            if attempt < 3:
                async with session_scope(database) as session:
                    await session.execute(
                        update(AnalysisJob)
                        .where(AnalysisJob.id == record.jobs[0].id)
                        .values(available_at=datetime.now(UTC))
                    )
        assert not await process_one(database, generators=generators, live_budget=3)
    async with session_scope(database) as session:
        assert await session.scalar(select(ProviderUsage.calls)) == 3
    assert calls == 3


async def test_default_worker_never_substitutes_demo_output_for_a_live_job(
    database: AsyncEngine,
) -> None:
    await run_transaction(
        database, ingest, synthetic_inputs("live-default", 1), provider="openrouter/test"
    )
    assert await process_one(database, live_budget=3)
    record = (await run_transaction(database, snapshot)).records[0]
    assert record.outputs == []
    assert record.jobs[0].provider == "openrouter/test"
    assert record.jobs[0].status == "failed"
    assert record.jobs[0].error == "Selected provider is not configured"
    async with session_scope(database) as session:
        assert await session.get(ProviderUsage, "openrouter") is None
