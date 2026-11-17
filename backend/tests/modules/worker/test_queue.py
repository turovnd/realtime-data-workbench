import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncEngine
from vercel.queue import RetryAfter

from common.infrastructure.database import run_transaction, session_scope
from common.infrastructure.deterministic import generate_demo
from common.infrastructure.queue import ANALYSIS_TOPIC, MAINTENANCE_TOPIC, JobDispatcher
from common.logic.ingestion import ingest
from common.logic.synthetic import synthetic_inputs
from common.models import AnalysisJob, ProviderUsage, Workspace
from common.repositories.inspection import snapshot
from common.repositories.jobs import claim_job, pending_job_ids
from common.schemas.common import Config
from common.schemas.feedback import FeedbackInput
from common.schemas.queue import MaintenanceMessage
from common.settings import Settings
from modules.worker import queue
from modules.worker.processing import process_job

pytestmark = pytest.mark.integration


class RecordingPublisher:
    def __init__(self) -> None:
        self.messages: list[tuple[str, dict[str, str]]] = []
        self.fail = False

    async def send(
        self, topic: str, payload: dict[str, str], *, retention: int = 86400
    ) -> str | None:
        assert retention == 86400
        if self.fail:
            raise ConnectionError("private provider diagnostic must not be logged")
        self.messages.append((topic, payload))
        return str(uuid4())


async def test_addressed_job_does_not_process_another_record(database: AsyncEngine) -> None:
    await run_transaction(database, ingest, synthetic_inputs("target", 2))
    ids = await run_transaction(database, pending_job_ids)

    assert await process_job(database, ids[1]) is None
    assert await process_job(database, ids[1]) is None
    assert await process_job(database, str(uuid4())) is None

    records = (await run_transaction(database, snapshot)).records
    jobs = {record.jobs[0].id: record for record in records}
    assert jobs[ids[1]].jobs[0].attempts == 1
    assert len(jobs[ids[1]].outputs) == 1
    assert jobs[ids[0]].jobs[0].attempts == 0
    assert jobs[ids[0]].jobs[0].status == "queued"


async def test_duplicate_delivery_during_active_lease_does_not_spend_again(
    database: AsyncEngine,
) -> None:
    await run_transaction(
        database, ingest, synthetic_inputs("duplicates", 1), provider="openrouter/test"
    )
    job_id = (await run_transaction(database, pending_job_ids))[0]
    started, release = asyncio.Event(), asyncio.Event()
    calls = 0

    async def generate(text: str, config: Config) -> str:
        nonlocal calls
        calls += 1
        started.set()
        await release.wait()
        return await generate_demo(text, config)

    running = asyncio.create_task(
        process_job(database, job_id, generators={"openrouter/test": generate}, live_budget=None)
    )
    try:
        await asyncio.wait_for(started.wait(), 2)
        delay = await process_job(
            database, job_id, generators={"openrouter/test": generate}, live_budget=None
        )
        assert delay is not None and 5 <= delay <= 30
        assert calls == 1
    finally:
        release.set()
        await running

    assert await process_job(database, job_id) is None
    record = (await run_transaction(database, snapshot)).records[0]
    assert record.jobs[0].attempts == 1 and len(record.outputs) == 1
    async with session_scope(database) as session:
        assert await session.scalar(select(ProviderUsage.calls)) == 1


async def test_addressed_claims_keep_global_concurrency_and_delivery_does_not_add_attempts(
    database: AsyncEngine,
) -> None:
    await run_transaction(database, ingest, synthetic_inputs("capacity", 3))
    ids = await run_transaction(database, pending_job_ids)
    assert await run_transaction(database, claim_job, job_id=ids[0])
    assert await run_transaction(database, claim_job, job_id=ids[1])

    assert await process_job(database, ids[2]) == 5
    async with session_scope(database) as session:
        job = await session.get(AnalysisJob, ids[2])
        assert job and job.status == "queued" and job.attempts == 0


async def test_not_yet_due_delivery_and_retryable_result_are_rescheduled(
    database: AsyncEngine,
) -> None:
    await run_transaction(
        database, ingest, synthetic_inputs("retry", 1), provider="openrouter/test"
    )
    job_id = (await run_transaction(database, pending_job_ids))[0]
    calls = 0

    async def unavailable(_text: str, _config: Config) -> str:
        nonlocal calls
        calls += 1
        raise ConnectionError("transient")

    for attempt in range(1, 4):
        delay = await process_job(
            database, job_id, generators={"openrouter/test": unavailable}, live_budget=None
        )
        assert calls == attempt
        assert (delay is None) == (attempt == 3)
        if attempt < 3:
            assert (
                await process_job(
                    database, job_id, generators={"openrouter/test": unavailable}, live_budget=None
                )
                is not None
            )
            assert calls == attempt
            async with session_scope(database) as session:
                await session.execute(
                    update(AnalysisJob)
                    .where(AnalysisJob.id == job_id)
                    .values(available_at=datetime.now(UTC))
                )

    record = (await run_transaction(database, snapshot)).records[0]
    assert record.jobs[0].attempts == 3 and record.jobs[0].status == "failed"
    async with session_scope(database) as session:
        assert await session.scalar(select(ProviderUsage.calls)) == 3


async def test_recovery_publishes_expired_lease_but_never_active_lease(
    database: AsyncEngine,
) -> None:
    await run_transaction(database, ingest, synthetic_inputs("crash", 2))
    ids = await run_transaction(database, pending_job_ids)
    expired = await run_transaction(database, claim_job, lease_seconds=-1, job_id=ids[0])
    active = await run_transaction(database, claim_job, job_id=ids[1])
    assert expired and active
    publisher = RecordingPublisher()

    assert (
        await queue.recover_pending(
            database,
            JobDispatcher(database, publisher),
            MaintenanceMessage(executionId="schedule-execution-1"),
        )
        == 1
    )
    assert publisher.messages == [(ANALYSIS_TOPIC, {"job_id": expired.id})]
    assert await process_job(database, expired.id) is None
    record = next(
        row
        for row in (await run_transaction(database, snapshot)).records
        if row.id == expired.record_id
    )
    assert record.jobs[0].attempts == 2 and len(record.outputs) == 1


async def test_recovery_expires_exhausted_lease_and_cleans_old_demo(
    database: AsyncEngine,
) -> None:
    await run_transaction(database, ingest, synthetic_inputs("old", 1))
    job_id = (await run_transaction(database, pending_job_ids))[0]
    for _ in range(3):
        assert await run_transaction(database, claim_job, lease_seconds=-1, job_id=job_id)
    publisher = RecordingPublisher()
    request = MaintenanceMessage(executionId="cleanup-1")
    assert await queue.recover_pending(database, JobDispatcher(database, publisher), request) == 0
    assert (await run_transaction(database, snapshot)).records[0].jobs[0].status == "failed"

    async with session_scope(database) as session:
        await session.execute(
            update(Workspace)
            .where(Workspace.id == "test")
            .values(created_at=datetime.now(UTC) - timedelta(hours=25))
        )
    assert await queue.recover_pending(database, JobDispatcher(database, publisher), request) == 0
    assert (await run_transaction(database, snapshot)).records == []
    assert publisher.messages == []


async def test_recovery_pages_without_dropping_pending_jobs(database: AsyncEngine) -> None:
    await run_transaction(
        database,
        ingest,
        [
            FeedbackInput(identity=f"paged-{index}", text="CSV export fails.", channel="Support")
            for index in range(105)
        ],
    )
    ids = await run_transaction(database, pending_job_ids)
    publisher = RecordingPublisher()
    dispatcher = JobDispatcher(database, publisher)
    assert (
        await queue.recover_pending(
            database, dispatcher, MaintenanceMessage(executionId="paged-execution")
        )
        == 100
    )
    continuation = publisher.messages[-1]
    assert continuation == (
        MAINTENANCE_TOPIC,
        {"executionId": "paged-execution", "after": ids[-1]},
    )
    assert (
        await queue.recover_pending(
            database, dispatcher, MaintenanceMessage.model_validate(continuation[1])
        )
        == 5
    )
    published = [
        payload["job_id"] for topic, payload in publisher.messages if topic == ANALYSIS_TOPIC
    ]
    assert len(published) == len(set(published)) == 105


async def test_native_subscriber_raises_sdk_retry_for_active_lease(
    database: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    await run_transaction(database, ingest, synthetic_inputs("subscriber", 1))
    job_id = (await run_transaction(database, pending_job_ids))[0]
    assert await run_transaction(database, claim_job, job_id=job_id)
    config = Settings(database_url=database.url.render_as_string(hide_password=False))
    monkeypatch.setattr(queue, "Settings", lambda: config)

    with pytest.raises(RetryAfter) as error:
        await queue.process_analysis({"job_id": job_id})
    assert 5 <= error.value.timeout_seconds <= 30


async def test_native_subscriber_does_not_ack_retryable_provider_failure(
    database: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    await run_transaction(
        database, ingest, synthetic_inputs("native-retry", 1), provider="openrouter/test"
    )
    job_id = (await run_transaction(database, pending_job_ids))[0]
    calls = 0

    async def unavailable(_text: str, _config: Config) -> str:
        nonlocal calls
        calls += 1
        raise ConnectionError("transient")

    config = Settings(
        database_url=database.url.render_as_string(hide_password=False), live_call_budget=None
    )
    monkeypatch.setattr(queue, "Settings", lambda: config)
    monkeypatch.setattr(
        queue, "build_generators", lambda _config, _client: {"openrouter/test": unavailable}
    )

    for _ in range(2):
        with pytest.raises(RetryAfter):
            await queue.process_analysis({"job_id": job_id})
    record = (await run_transaction(database, snapshot)).records[0]
    assert calls == record.jobs[0].attempts == 1
    assert record.jobs[0].status == "queued"


async def test_native_recovery_failure_requests_bounded_retry_without_sensitive_logs(
    database: AsyncEngine, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    await run_transaction(database, ingest, synthetic_inputs("repair-retry", 1))
    config = Settings(database_url=database.url.render_as_string(hide_password=False))
    publisher = RecordingPublisher()
    publisher.fail = True
    monkeypatch.setattr(queue, "Settings", lambda: config)
    monkeypatch.setattr(
        queue, "build_dispatcher", lambda engine, _config: JobDispatcher(engine, publisher)
    )

    with pytest.raises(RetryAfter) as error:
        await queue.reconcile({"executionId": "repair-failure"})
    assert error.value.timeout_seconds == 30
    assert "private provider diagnostic" not in caplog.text
    record = (await run_transaction(database, snapshot)).records[0]
    assert record.jobs[0].attempts == 0 and record.jobs[0].status == "queued"


async def test_invalid_queue_messages_ack_without_database_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected() -> Settings:
        pytest.fail("Malformed private messages must not open the database")

    monkeypatch.setattr(queue, "Settings", unexpected)
    await queue.process_analysis({"job_id": "not-a-uuid"})
    await queue.reconcile({"executionId": "x" * 201})
