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
@pytest.mark.parametrize("provider", ["openrouter/test", "deepseek/deepseek-flash"])
async def test_worker_keeps_zero_and_finite_budgets_effective(
    database: AsyncEngine, budget: int, provider: str
) -> None:
    await ingest(
        database,
        [
            FeedbackInput(
                identity=f"finite-{index}", text=f"Export {index} stops early.", channel="Support"
            )
            for index in range(3)
        ],
        provider=provider,
    )
    calls = 0

    async def mocked_provider(text: str, config: Config) -> str:
        nonlocal calls
        calls += 1
        return await generate_demo(text, config)

    for _ in range(3):
        assert await process_one(
            database, generators={provider: mocked_provider}, live_budget=budget
        )
    assert calls == budget
    stored = (await snapshot(database)).records
    assert sum(len(record.outputs) for record in stored) == budget
    rejected = [record for record in stored if record.jobs[0].status == "failed"]
    assert len(rejected) == 3 - budget
    assert all(record.jobs[0].error == "Live provider call budget exhausted" for record in rejected)
    async with session_scope(database) as session:
        assert await session.scalar(select(ProviderUsage.calls)) == (budget or None)


async def test_switching_provider_does_not_bypass_existing_budget_or_relabel_history(
    database: AsyncEngine,
) -> None:
    providers = ["openrouter/old-model", "deepseek/deepseek-flash"]
    for index, provider in enumerate(providers):
        await ingest(
            database,
            [
                FeedbackInput(
                    identity=f"switch-{index}", text=f"Export {index} fails.", channel="Support"
                )
            ],
            provider=provider,
        )
    calls: list[str] = []

    async def mocked_provider(text: str, config: Config) -> str:
        calls.append(text)
        return await generate_demo(text, config)

    generators = dict.fromkeys(providers, mocked_provider)
    assert await process_one(database, generators=generators, live_budget=1)
    assert await process_one(database, generators=generators, live_budget=1)
    records = (await snapshot(database)).records
    by_provider = {record.jobs[0].provider: record for record in records}
    assert calls == ["Export 0 fails."]
    assert by_provider[providers[0]].outputs[0].provider == providers[0]
    assert by_provider[providers[1]].outputs == []
    assert by_provider[providers[1]].jobs[0].error == "Live provider call budget exhausted"
    async with session_scope(database) as session:
        old = await session.get(ProviderUsage, "openrouter")
        assert old is not None and old.calls == 1
        assert await session.get(ProviderUsage, "deepseek") is None


async def test_unknown_injected_generator_cannot_bypass_paid_attempt_admission(
    database: AsyncEngine,
) -> None:
    await ingest(
        database,
        [FeedbackInput(identity="unknown", text="Export fails.", channel="Support")],
        provider="another-provider/model",
    )

    async def forbidden_provider(text: str, config: Config) -> str:
        pytest.fail("A non-deterministic provider must reserve its attempt first")

    assert await process_one(
        database, generators={"another-provider/model": forbidden_provider}, live_budget=0
    )
    record = (await snapshot(database)).records[0]
    assert record.outputs == []
    assert record.jobs[0].error == "Live provider call budget exhausted"
