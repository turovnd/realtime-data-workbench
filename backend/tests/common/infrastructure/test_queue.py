import asyncio
import logging
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from common.infrastructure.database import create_engine, run_transaction, session_scope
from common.infrastructure.queue import ANALYSIS_TOPIC, JobDispatcher
from common.models import AnalysisJob
from common.repositories.jobs import pending_job_ids
from common.schemas.queue import MaintenanceMessage
from modules.api.app import create_app
from modules.worker.processing import process_job
from modules.worker.queue import recover_pending

pytestmark = pytest.mark.integration


class CheckedPublisher:
    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine
        self.jobs: list[str] = []
        self.fail = False
        self.wait = False

    async def send(
        self, topic: str, payload: dict[str, str], *, retention: int = 86400
    ) -> str | None:
        assert topic == ANALYSIS_TOPIC and retention == 86400
        # A different connection must see the admitted job before publication starts.
        async with session_scope(self.engine) as session:
            job = await session.get(AnalysisJob, payload["job_id"])
            assert job and job.status == "queued"
        if self.fail:
            raise ConnectionError("PRIVATE_CREDENTIAL_MARKER")
        if self.wait:
            await asyncio.Event().wait()
        self.jobs.append(payload["job_id"])
        return str(uuid4())


@pytest.mark.parametrize("failure", ["exception", "timeout"])
async def test_post_commit_failure_keeps_accepted_job_and_recovery_repairs_handoff(
    database: AsyncEngine, failure: str, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING, logger="common.queue")
    publisher = CheckedPublisher(database)
    publisher.fail = failure == "exception"
    publisher.wait = failure == "timeout"
    dispatcher = JobDispatcher(database, publisher, timeout_seconds=0.1)
    app = create_app(database, dispatcher=dispatcher)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        person = (
            await client.post(
                "/api/auth/register",
                json={"email": "queue@example.test", "password": "long-test-password"},
            )
        ).json()
        client.headers["Authorization"] = f"Bearer {person['token']}"
        payload = {"identity": "one", "text": "CSV export fails.", "channel": "Support"}
        created = await client.post("/api/feedback", json=payload)
        assert created.status_code == 201
        job_id = created.json()["jobs"][0]["id"]
        assert await run_transaction(database, pending_job_ids) == [job_id]
        assert created.json()["jobs"][0]["attempts"] == 0
        assert publisher.jobs == []
        assert "queue_handoff_failed" in caplog.text
        assert "PRIVATE_CREDENTIAL_MARKER" not in caplog.text

        publisher.fail = publisher.wait = False
        assert (
            await recover_pending(database, dispatcher, MaintenanceMessage(executionId="repair"))
            == 1
        )
        assert publisher.jobs == [job_id]
        assert await process_job(database, job_id) is None
        assert (await client.get(f"/api/feedback/{created.json()['id']}")).json()["outputs"]


async def test_replayed_submission_redispatches_same_job_and_terminal_replay_does_not(
    database: AsyncEngine,
) -> None:
    publisher = CheckedPublisher(database)
    app = create_app(database, dispatcher=JobDispatcher(database, publisher))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        person = (
            await client.post(
                "/api/auth/register",
                json={"email": "replay@example.test", "password": "long-test-password"},
            )
        ).json()
        client.headers["Authorization"] = f"Bearer {person['token']}"
        payload = {"identity": "one", "text": "CSV export fails.", "channel": "Support"}
        first = await client.post("/api/feedback", json=payload)
        job_id = first.json()["jobs"][0]["id"]
        assert (await client.post("/api/feedback", json=payload)).status_code == 200
        assert publisher.jobs == [job_id, job_id]
        assert await process_job(database, job_id) is None
        assert (await client.post("/api/feedback", json=payload)).status_code == 200
        assert publisher.jobs == [job_id, job_id]


async def test_demo_dispatches_only_committed_deterministic_seed_jobs(
    database: AsyncEngine,
) -> None:
    publisher = CheckedPublisher(database)
    app = create_app(database, dispatcher=JobDispatcher(database, publisher))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/auth/demo", json={})
    assert response.status_code == 200
    assert len(publisher.jobs) == len(set(publisher.jobs)) == 24
    async with session_scope(database) as session:
        jobs = list(await session.scalars(select(AnalysisJob)))
    assert {job.id for job in jobs} == set(publisher.jobs)
    assert {job.provider for job in jobs} == {"deterministic-rules/1"}
    assert {job.workspace_id for job in jobs} == {response.json()["workspace_id"]}


async def test_disabled_dispatcher_does_not_query_database() -> None:
    engine = create_engine("postgresql://unused:unused@127.0.0.1:1/unused")
    try:
        await JobDispatcher(engine).notify("unreachable")
    finally:
        await engine.dispose()
