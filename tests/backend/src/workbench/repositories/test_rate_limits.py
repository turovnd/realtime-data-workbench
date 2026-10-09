import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from workbench.logic.errors import RateLimitError
from workbench.repositories.rate_limits import limit_auth

pytestmark = pytest.mark.integration


async def test_auth_rate_limit_is_persisted(database: AsyncEngine) -> None:
    for _ in range(3):
        await limit_auth(database, "email:blocked@example.test", 3)
    with pytest.raises(RateLimitError):
        await limit_auth(database, "email:blocked@example.test", 3)
    await limit_auth(database, "email:other@example.test", 3)
