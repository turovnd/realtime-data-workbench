import asyncio
import ssl
from datetime import UTC, datetime

import pytest
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from common.infrastructure.database import (
    connection_options,
    create_engine,
    run_transaction,
    session_scope,
)
from common.models import Workspace


@pytest.mark.integration
async def test_orm_session_scopes_commit_and_rollback(database: AsyncEngine) -> None:
    async with session_scope(database) as session:
        workspace = Workspace(id="session-check", cursor=5)
        session.add(workspace)
    assert workspace.cursor == 5

    with pytest.raises(RuntimeError, match="Rollback check"):
        async with session_scope(database) as session:
            stored = await session.get(Workspace, "session-check")
            assert stored is not None
            stored.cursor = 9
            await session.flush()
            raise RuntimeError("Rollback check")

    async with session_scope(database) as session:
        stored = await session.get(Workspace, "session-check")
        assert stored is not None and stored.cursor == 5


@pytest.mark.parametrize("scheme", ["postgres", "postgresql", "postgresql+asyncpg"])
@pytest.mark.parametrize("mode", ["require", "verify-ca", "verify-full"])
def test_managed_postgres_urls_preserve_credentials_and_verify_tls(scheme: str, mode: str) -> None:
    url, options = connection_options(
        f"{scheme}://test:p%40ss%2Fword%3F@ep-test-pooler.eu-central-1.aws.neon.tech/feedback"
        f"?sslmode={mode}&prepared_statement_cache_size=20"
    )
    assert url.drivername == "postgresql+asyncpg"
    assert url.password == "p@ss/word?"
    assert url.host == "ep-test-pooler.eu-central-1.aws.neon.tech"
    assert url.database == "feedback"
    assert url.query == {"prepared_statement_cache_size": "20"}
    context = options["ssl"]
    assert isinstance(context, ssl.SSLContext)
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True
    assert options["timeout"] == 10


def test_local_postgres_can_explicitly_disable_tls() -> None:
    url, options = connection_options("postgresql://test:local@127.0.0.1/test?sslmode=disable")
    assert "sslmode" not in url.query
    assert options["ssl"] is False


@pytest.mark.parametrize(
    "query",
    [
        "sslmode=require&channel_binding=require",
        "sslmode=require&ssl=disable",
        "sslmode=require&sslmode=disable",
        "sslmode=prefer",
        "sslmode=unexpected",
    ],
)
def test_unsupported_or_ambiguous_tls_requirements_fail_without_disclosing_url(query: str) -> None:
    with pytest.raises(ValueError) as failure:
        connection_options(f"postgresql://test:PRIVATE_PASSWORD@host/test?{query}")
    assert "PRIVATE_PASSWORD" not in str(failure.value)
    assert "postgresql://" not in str(failure.value)


@pytest.mark.parametrize(
    "value",
    ["not a URL PRIVATE_PASSWORD", "mysql://test:PRIVATE_PASSWORD@host/test"],
)
def test_invalid_database_urls_have_safe_errors(value: str) -> None:
    with pytest.raises(ValueError, match="Invalid PostgreSQL connection URL") as failure:
        connection_options(value)
    assert "PRIVATE_PASSWORD" not in str(failure.value)


async def test_migration_engine_does_not_retain_idle_connections() -> None:
    engine = create_engine("postgresql://test:local@127.0.0.1/test", pooled=False)
    try:
        assert isinstance(engine.pool, NullPool)
    finally:
        await engine.dispose()


@pytest.mark.parametrize("endpoint", ["ep-test", "ep-test-pooler"])
@pytest.mark.parametrize("mode", ["require", "verify-ca", "verify-full"])
def test_neon_channel_binding_is_replaced_with_verified_tls(endpoint: str, mode: str) -> None:
    url, options = connection_options(
        f"postgresql://test:p%40ss@{endpoint}.us-east-1.aws.neon.tech/feedback"
        f"?sslmode={mode}&channel_binding=require"
    )
    assert url.password == "p@ss"
    assert url.host == f"{endpoint}.us-east-1.aws.neon.tech"
    assert url.query == {}
    context = options["ssl"]
    assert isinstance(context, ssl.SSLContext)
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True


@pytest.mark.parametrize(
    "host,query",
    [
        ("database.example", "sslmode=require&channel_binding=require"),
        ("not-neon.tech", "sslmode=require&channel_binding=require"),
        ("db.neon.tech.example", "sslmode=require&channel_binding=require"),
        ("db.neon.tech", "channel_binding=require"),
        ("db.neon.tech", "sslmode=disable&channel_binding=require"),
        ("db.neon.tech", "sslmode=prefer&channel_binding=require"),
        ("db.neon.tech", "sslmode=require&channel_binding=prefer"),
        ("db.neon.tech", "sslmode=require&channel_binding=require&channel_binding=disable"),
        ("db.neon.tech", "sslmode=require&sslmode=disable&channel_binding=require"),
        ("db.neon.tech", "sslmode=require&channel_binding=require&ssl=disable"),
        ("db.neon.tech", "sslmode=require&channel_binding=require&host=other.example"),
        ("db.neon.tech", "sslmode=require&channel_binding=require&hostaddr=127.0.0.1"),
    ],
)
def test_neon_policy_rejects_ambiguous_tls_and_host_overrides(host: str, query: str) -> None:
    with pytest.raises(ValueError) as failure:
        connection_options(f"postgresql://test:PRIVATE_PASSWORD@{host}/feedback?{query}")
    assert "PRIVATE_PASSWORD" not in str(failure.value)
    assert "postgresql://" not in str(failure.value)


@pytest.mark.integration
async def test_transaction_rolls_back_an_orm_operation_that_raises(database: AsyncEngine) -> None:
    def write_then_fail(session: Session) -> None:
        session.add(Workspace(id="rollback-probe", cursor=0, created_at=datetime.now(UTC)))
        session.flush()
        raise RuntimeError("Abort this operation")

    with pytest.raises(RuntimeError, match="Abort this operation"):
        await run_transaction(database, write_then_fail)

    def exists(session: Session) -> bool:
        return session.query(Workspace).filter(Workspace.id == "rollback-probe").first() is not None

    assert not await run_transaction(database, exists)


@pytest.mark.integration
async def test_orm_database_io_yields_to_other_async_tasks(database: AsyncEngine) -> None:
    started = asyncio.Event()
    finished = False

    def query(session: Session) -> None:
        nonlocal finished
        started.set()
        session.query(func.pg_sleep(0.1)).one()
        finished = True

    task = asyncio.create_task(run_transaction(database, query))
    await started.wait()
    try:
        assert not finished
    finally:
        await task
