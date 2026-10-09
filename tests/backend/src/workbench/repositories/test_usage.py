import pytest
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncEngine

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
    import asyncio

    reservations = await asyncio.gather(*(reserve_live_call(database, 2) for _ in range(8)))
    assert sum(reservations) == 2
    assert await reserve_live_call(database, 2) is False
