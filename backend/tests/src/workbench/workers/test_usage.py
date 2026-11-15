import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.database import session_scope
from workbench.infrastructure.deterministic import generate_demo
from workbench.logic.ingestion import ingest
from workbench.models import ProviderUsage
from workbench.repositories.inspection import snapshot
from workbench.schemas.common import Config
from workbench.schemas.feedback import FeedbackInput
from workbench.workers.processing import process_one

pytestmark = pytest.mark.integration


async def test_worker_can_complete_more_than_twenty_calls_without_losing_usage(
    database: AsyncEngine,
) -> None:
    records = [
        FeedbackInput(
            identity=f"unlimited-{index}", text=f"Export {index} stops early.", channel="Support"
        )
        for index in range(25)
    ]
    await ingest(database, records, provider="openrouter/test")
    calls = 0

    async def mocked_provider(text: str, config: Config) -> str:
        nonlocal calls
        calls += 1
        return await generate_demo(text, config)

    for _ in records:
        assert await process_one(
            database, generators={"openrouter/test": mocked_provider}, live_budget=None
        )
    assert not await process_one(database, live_budget=None)
    assert calls == 25
    stored = (await snapshot(database)).records
    assert len(stored) == 25
    assert all(
        record.jobs[0].status == "succeeded" and len(record.outputs) == 1 for record in stored
    )
    async with session_scope(database) as session:
        assert await session.scalar(select(ProviderUsage.calls)) == 25


@pytest.mark.parametrize("budget", [0, 2])
async def test_worker_keeps_zero_and_finite_budgets_effective(
    database: AsyncEngine, budget: int
) -> None:
    await ingest(
        database,
        [
            FeedbackInput(
                identity=f"finite-{index}", text=f"Export {index} stops early.", channel="Support"
            )
            for index in range(3)
        ],
        provider="openrouter/test",
    )
    calls = 0

    async def mocked_provider(text: str, config: Config) -> str:
        nonlocal calls
        calls += 1
        return await generate_demo(text, config)

    for _ in range(3):
        assert await process_one(
            database, generators={"openrouter/test": mocked_provider}, live_budget=budget
        )
    assert calls == budget
    stored = (await snapshot(database)).records
    assert sum(len(record.outputs) for record in stored) == budget
    rejected = [record for record in stored if record.jobs[0].status == "failed"]
    assert len(rejected) == 3 - budget
    assert all(record.jobs[0].error == "Live provider call budget exhausted" for record in rejected)
    async with session_scope(database) as session:
        assert await session.scalar(select(ProviderUsage.calls)) == (budget or None)
