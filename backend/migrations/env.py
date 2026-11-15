"""Alembic environment for explicit schema management outside API/worker startup."""

import asyncio
from logging.config import fileConfig

from alembic import context
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from migrations.adoption import adopt_unversioned
from workbench.models import Base
from workbench.settings import Settings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)


def run_migrations(connection: Connection) -> None:
    # Lock before inspecting either application tables or Alembic's version table.
    connection.execute(text("SELECT pg_advisory_xact_lock(72100691)"))
    connection.execute(text("SELECT pg_advisory_xact_lock(72100692)"))
    context.configure(
        connection=connection, target_metadata=Base.metadata, compare_server_default=True
    )
    migration = context.get_context()
    if not migration.get_current_heads():
        application_tables = set(inspect(connection).get_table_names()) - {"alembic_version"}
        if application_tables:
            adopt = config.attributes.get("adopt_unversioned", False) or (
                context.get_x_argument(as_dictionary=True).get("adopt") == "true"
            )
            if not adopt:
                raise RuntimeError(
                    "Existing unversioned database requires explicit validated adoption: "
                    "alembic -x adopt=true upgrade head"
                )
            if migration.opts.get("destination_rev") is None:
                raise RuntimeError("Validated adoption is supported only by the upgrade command")
            script = ScriptDirectory.from_config(config)
            revision = adopt_unversioned(connection, script)
            migration.stamp(script, revision)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    engine = create_async_engine(Settings().database_url, poolclass=pool.NullPool)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(run_migrations)
    finally:
        await engine.dispose()


if context.is_offline_mode():
    # Adoption must inspect the real schema; SQL generation is only for known revisions.
    context.configure(
        url=Settings().database_url,
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()
elif (connection := config.attributes.get("connection")) is not None:
    run_migrations(connection)
else:
    asyncio.run(run_async_migrations())
