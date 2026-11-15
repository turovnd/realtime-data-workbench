import asyncio

import pytest
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.infrastructure.database import session_scope
from workbench.models import ProviderUsage
from workbench.repositories.usage import reserve_live_call
from workbench.settings import Settings


def live_settings() -> Settings:
    return Settings(
        openrouter_calls_enabled=True, openrouter_api_key=SecretStr("test-only-not-a-key")
    )


def completion(content: str, finish_reason: str = "stop") -> dict[str, object]:
    return {"choices": [{"message": {"content": content}, "finish_reason": finish_reason}]}


@pytest.mark.integration
async def test_call_admission_budget_survives_concurrency(database: AsyncEngine) -> None:
    reservations = await asyncio.gather(*(reserve_live_call(database, 2) for _ in range(8)))
    assert sum(reservations) == 2
    assert await reserve_live_call(database, 2) is False


@pytest.mark.integration
async def test_unlimited_admission_preserves_existing_usage_across_concurrency_and_restarts(
    database: AsyncEngine,
) -> None:
    for _ in range(20):
        assert await reserve_live_call(database, 20)
    assert not await reserve_live_call(database, 20)

    admitted = await asyncio.gather(*(reserve_live_call(database, None) for _ in range(8)))
    assert all(admitted)
    async with session_scope(database) as session:
        assert await session.scalar(select(ProviderUsage.calls)) == 28

    await database.dispose()
    assert await reserve_live_call(database, None)
    assert not await reserve_live_call(database, 20)
    assert not await reserve_live_call(database, 29)
    assert await reserve_live_call(database, 30)
    assert not await reserve_live_call(database, 30)
    async with session_scope(database) as session:
        assert await session.scalar(select(ProviderUsage.calls)) == 30


@pytest.mark.integration
async def test_zero_budget_denies_calls_without_creating_or_resetting_usage(
    database: AsyncEngine,
) -> None:
    assert not await reserve_live_call(database, 0)
    async with session_scope(database) as session:
        assert await session.scalar(select(ProviderUsage.calls)) is None
    assert await reserve_live_call(database, None)
    assert not await reserve_live_call(database, 0)
    async with session_scope(database) as session:
        assert await session.scalar(select(ProviderUsage.calls)) == 1
