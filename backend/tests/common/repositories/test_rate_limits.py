import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from common.infrastructure.database import run_transaction
from common.logic.errors import RateLimitError
from common.repositories.rate_limits import limit_auth

pytestmark = pytest.mark.integration


async def test_auth_rate_limit_is_persisted(database: AsyncEngine) -> None:
    for _ in range(3):
        await run_transaction(database, limit_auth, "email:blocked@example.test", 3)
    with pytest.raises(RateLimitError):
        await run_transaction(database, limit_auth, "email:blocked@example.test", 3)
    await run_transaction(database, limit_auth, "email:other@example.test", 3)
