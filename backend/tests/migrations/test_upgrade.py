import asyncio
import json
import os
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio
from alembic import command
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from workbench.db import migration_config
from workbench.infrastructure.deterministic import generate_demo
from workbench.logic.analysis import start_analysis
from workbench.repositories.inspection import snapshot
from workbench.schemas.analysis import AnalysisInput
from workbench.workers.processing import process_one

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def migration_database() -> AsyncIterator[AsyncEngine]:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to a disposable real PostgreSQL database")
    schema = "migration_" + uuid4().hex
    administrator = create_async_engine(url)
    async with administrator.begin() as connection:
        await connection.execute(text(f"CREATE SCHEMA {schema}"))
    engine = create_async_engine(url, connect_args={"server_settings": {"search_path": schema}})
    try:
        yield engine
    finally:
        await engine.dispose()
        async with administrator.begin() as connection:
            await connection.execute(text(f"DROP SCHEMA {schema} CASCADE"))
        await administrator.dispose()


async def upgrade(engine: AsyncEngine, revision: str = "head", *, adopt: bool = False) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(
            lambda sync: command.upgrade(migration_config(sync, adopt=adopt), revision)
        )


async def downgrade(engine: AsyncEngine, revision: str) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(lambda sync: command.downgrade(migration_config(sync), revision))


async def current_revision(engine: AsyncEngine) -> str | None:
    async with engine.connect() as connection:
        revision = await connection.scalar(text("SELECT version_num FROM alembic_version"))
        return str(revision) if revision is not None else None


async def remove_version(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.execute(text("DROP TABLE alembic_version"))


async def seed_legacy(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.execute(text("INSERT INTO workspace_state(id, cursor) VALUES ('test', 7)"))
        await connection.execute(
            text(
                "INSERT INTO feedback(id, workspace_id, identity, sequence, "
                "text, channel, ingested_at) "
                "VALUES ('record', 'test', 'legacy', 1, "
                "'A synthetic feedback record', 'web', now())"
            )
        )
        for version in ("v1", "v2"):
            await connection.execute(
                text(
                    "INSERT INTO jobs(id, workspace_id, record_id, config, origin, provider, "
                    "status, attempts, fence, available_at) VALUES "
                    "(:id, 'test', 'record', :version, 'backfill', 'deterministic-rules/1', "
                    "'succeeded', 1, 1, now())"
                ),
                {"id": "job-" + version, "version": version},
            )
            await connection.execute(
                text(
                    "INSERT INTO enrichments(id, workspace_id, record_id, config, payload, "
                    "provider, created_at) VALUES (:id, 'test', 'record', :version, "
                    '\'{"topic":"other","intent":"unclear",'
                    '"evidence":["synthetic feedback"],"summary":"Legacy result"}'
                    "'::json, "
                    "'deterministic-rules/1', now())"
                ),
                {"id": "output-" + version, "version": version},
            )
        await connection.execute(
            text("INSERT INTO provider_usage(id, calls) VALUES ('openrouter', 14)")
        )
        await connection.execute(
            text(
                "INSERT INTO accounts(id, workspace_id, email, password_hash) "
                "VALUES ('account', 'test', 'synthetic@example.test', 'synthetic-hash')"
            )
        )
        await connection.execute(
            text(
                "INSERT INTO auth_sessions(token_hash, workspace_id, account_id, expires_at) "
                "VALUES ('synthetic-token', 'test', 'account', now() + interval '1 hour')"
            )
        )


async def stored_rows(engine: AsyncEngine) -> dict[str, list[str]]:
    async with engine.connect() as connection:
        return {
            table: list(
                (
                    await connection.scalars(
                        text(f"SELECT row_to_json(t)::text FROM {table} t ORDER BY 1")
                    )
                ).all()
            )
            for table in (
                "workspace_state",
                "feedback",
                "enrichments",
                "jobs",
                "provider_usage",
                "accounts",
                "auth_sessions",
            )
        }


async def assert_immutable(engine: AsyncEngine) -> None:
    for statement in (
        "UPDATE enrichments SET payload='{}'::json",
        "UPDATE feedback SET text='changed'",
        "DELETE FROM enrichments",
        "DELETE FROM feedback",
    ):
        with pytest.raises(DBAPIError, match="immutable record"):
            async with engine.begin() as connection:
                await connection.execute(text(statement))


async def test_fresh_upgrade_check_and_safe_empty_downgrade(
    migration_database: AsyncEngine,
) -> None:
    await upgrade(migration_database)
    assert await current_revision(migration_database) == "0002"
    async with migration_database.begin() as connection:
        await connection.run_sync(lambda sync: command.check(migration_config(sync)))
    await upgrade(migration_database)
    await downgrade(migration_database, "0001")
    assert await current_revision(migration_database) == "0001"
    await downgrade(migration_database, "base")
    assert await current_revision(migration_database) is None
    await upgrade(migration_database)
    assert await current_revision(migration_database) == "0002"


@pytest.mark.parametrize("unversioned", [False, True])
async def test_legacy_history_survives_upgrade_and_next_run(
    migration_database: AsyncEngine, unversioned: bool
) -> None:
    await upgrade(migration_database, "0001")
    await seed_legacy(migration_database)
    before = await stored_rows(migration_database)
    if unversioned:
        await remove_version(migration_database)
    await upgrade(migration_database, adopt=unversioned)
    after = await stored_rows(migration_database)
    for table in before.keys() - {"jobs", "enrichments"}:
        assert after[table] == before[table]
    for table in ("jobs", "enrichments"):
        old_rows = [json.loads(row) for row in before[table]]
        upgraded_rows = [json.loads(row) for row in after[table]]
        for row in upgraded_rows:
            row.pop("run")
            if table == "jobs":
                row.pop("request_identity")
        assert upgraded_rows == old_rows
    async with migration_database.connect() as connection:
        assert list(
            (await connection.execute(text("SELECT config, run FROM jobs ORDER BY run"))).all()
        ) == [("v1", 1), ("v2", 2)]
        assert list(
            (
                await connection.execute(text("SELECT config, run FROM enrichments ORDER BY run"))
            ).all()
        ) == [("v1", 1), ("v2", 2)]
        assert list(
            (await connection.scalars(text("SELECT payload->>'summary' FROM enrichments"))).all()
        ) == ["Legacy result", "Legacy result"]
    await upgrade(migration_database)
    assert await stored_rows(migration_database) == after
    prior = (await snapshot(migration_database)).records[0]
    pending, inserted = await start_analysis(
        migration_database,
        "test",
        "record",
        AnalysisInput(identity="post-migration"),
        "openrouter/test",
    )
    assert inserted and pending.jobs[-1].run == 3
    assert pending.outputs == prior.outputs
    # Explicit test double verifies provider routing without making a network call.
    assert await process_one(
        migration_database, generators={"openrouter/test": generate_demo}, live_budget=15
    )
    assert len((await snapshot(migration_database)).records[0].outputs) == 3
    await assert_immutable(migration_database)
    with pytest.raises(RuntimeError, match="Cannot downgrade"):
        await downgrade(migration_database, "0001")
    assert await current_revision(migration_database) == "0002"
    assert len((await snapshot(migration_database)).records[0].outputs) == 3


@pytest.mark.parametrize("standalone_indexes", [False, True])
async def test_current_unversioned_adoption_preserves_all_rows(
    migration_database: AsyncEngine, standalone_indexes: bool
) -> None:
    await upgrade(migration_database, "0001")
    await seed_legacy(migration_database)
    await upgrade(migration_database)
    if standalone_indexes:
        async with migration_database.begin() as connection:
            for table, name, columns in (
                ("jobs", "uq_job_run", "record_id, run"),
                ("jobs", "uq_job_request_identity", "record_id, request_identity"),
                ("enrichments", "uq_output_run", "record_id, run"),
            ):
                await connection.execute(text(f"ALTER TABLE {table} DROP CONSTRAINT {name}"))
                await connection.execute(text(f"CREATE UNIQUE INDEX {name} ON {table}({columns})"))
    await remove_version(migration_database)
    before = await stored_rows(migration_database)
    with pytest.raises(RuntimeError, match="explicit validated adoption"):
        await upgrade(migration_database)
    await upgrade(migration_database, adopt=True)
    assert await current_revision(migration_database) == "0002"
    assert await stored_rows(migration_database) == before
    await assert_immutable(migration_database)
    async with migration_database.begin() as connection:
        await connection.run_sync(lambda sync: command.check(migration_config(sync)))
    await upgrade(migration_database)
    assert await stored_rows(migration_database) == before


@pytest.mark.parametrize(
    "change", ["partial", "default", "trigger", "predicate", "predicate_literal", "missing"]
)
async def test_adoption_rejects_drift_without_stamping(
    migration_database: AsyncEngine, change: str
) -> None:
    await upgrade(migration_database)
    await remove_version(migration_database)
    async with migration_database.begin() as connection:
        if change == "partial":
            await connection.execute(text("ALTER TABLE jobs DROP COLUMN request_identity CASCADE"))
        elif change == "default":
            await connection.execute(text("ALTER TABLE jobs ALTER COLUMN run SET DEFAULT 9"))
        elif change == "trigger":
            await connection.execute(text("DROP TRIGGER immutable_guard ON enrichments"))
        elif change in {"predicate", "predicate_literal"}:
            predicate = "origin = 'analysis'" if change == "predicate" else "origin <> 'ana lysis'"
            await connection.execute(text("DROP INDEX uq_job_legacy_config"))
            await connection.execute(
                text(
                    "CREATE UNIQUE INDEX uq_job_legacy_config ON jobs(record_id, config) "
                    f"WHERE {predicate}"
                )
            )
        else:
            await connection.execute(text("ALTER TABLE jobs DROP COLUMN provider"))
    with pytest.raises(RuntimeError, match="Cannot adopt database"):
        await upgrade(migration_database, adopt=True)
    async with migration_database.connect() as connection:
        assert await connection.scalar(text("SELECT to_regclass('alembic_version')")) is None


async def test_known_legacy_provider_representation_is_normalized(
    migration_database: AsyncEngine,
) -> None:
    await upgrade(migration_database, "0001")
    await seed_legacy(migration_database)
    await remove_version(migration_database)
    async with migration_database.begin() as connection:
        await connection.execute(text("ALTER TABLE jobs ALTER COLUMN provider TYPE TEXT"))
        await connection.execute(
            text("ALTER TABLE jobs ALTER COLUMN provider SET DEFAULT 'deterministic-rules/1'")
        )
    await upgrade(migration_database, adopt=True)
    async with migration_database.begin() as connection:
        await connection.run_sync(lambda sync: command.check(migration_config(sync)))
    await assert_immutable(migration_database)


async def test_legacy_only_downgrade_preserves_rows(migration_database: AsyncEngine) -> None:
    await upgrade(migration_database, "0001")
    await seed_legacy(migration_database)
    before = await stored_rows(migration_database)
    await upgrade(migration_database)
    await downgrade(migration_database, "0001")
    assert await stored_rows(migration_database) == before
    await assert_immutable(migration_database)
    with pytest.raises(RuntimeError, match="Refusing to remove a populated database"):
        await downgrade(migration_database, "base")
    assert await current_revision(migration_database) == "0001"
    assert await stored_rows(migration_database) == before


async def test_migration_command_uses_the_direct_url_instead_of_runtime_pool(
    database: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The regular fixture has already prepared only the disposable test database.
    # An unreachable runtime URL proves the online Alembic path uses its own URL.
    direct_url = database.url.set(drivername="postgresql").render_as_string(hide_password=False)
    monkeypatch.setenv("WORKBENCH_DATABASE_URL", "postgresql://unreachable.invalid/runtime")
    monkeypatch.setenv("WORKBENCH_MIGRATION_DATABASE_URL", direct_url)
    await asyncio.to_thread(command.upgrade, migration_config(), "head")
    assert await current_revision(database) == "0002"
