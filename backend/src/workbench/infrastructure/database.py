import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from workbench.infrastructure.tables import metadata
from workbench.settings import Settings


def create_engine(url: str) -> AsyncEngine:
    return create_async_engine(url, pool_size=3, max_overflow=1, pool_pre_ping=True)


async def check_database(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def migrate(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.execute(text("SELECT pg_advisory_xact_lock(72100691)"))
        await conn.execute(text("SELECT pg_advisory_xact_lock(72100692)"))
        await conn.run_sync(metadata.create_all)
        await conn.execute(
            text(
                "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS provider TEXT NOT NULL "
                "DEFAULT 'deterministic-rules/1'"
            )
        )
        # Existing immutable payloads stay unchanged; only new revision metadata is filled.
        await conn.execute(text("DROP TRIGGER IF EXISTS immutable_guard ON enrichments"))
        for table, old_constraint, new_index in (
            ("jobs", "uq_job_version", "uq_job_run"),
            ("enrichments", "uq_output_version", "uq_output_run"),
        ):
            await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS run INTEGER"))
            await conn.execute(
                text(
                    f"UPDATE {table} SET run=CASE WHEN config='v2' THEN 2 ELSE 1 END "
                    "WHERE run IS NULL"
                )
            )
            await conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN run SET DEFAULT 1"))
            await conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN run SET NOT NULL"))
            await conn.execute(
                text(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {old_constraint}")
            )
            await conn.execute(
                text(f"CREATE UNIQUE INDEX IF NOT EXISTS {new_index} ON {table}(record_id,run)")
            )
        await conn.execute(
            text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS request_identity VARCHAR")
        )
        await conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_job_request_identity "
                "ON jobs(record_id,request_identity)"
            )
        )
        await conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_job_legacy_config ON jobs(record_id,config) "
                "WHERE origin != 'analysis'"
            )
        )
        await conn.execute(
            text("INSERT INTO workspace_state(id,cursor) VALUES ('test',0) ON CONFLICT DO NOTHING")
        )
        await conn.execute(
            text("""
            CREATE OR REPLACE FUNCTION reject_immutable_change() RETURNS trigger AS $$
            BEGIN
              IF current_setting('workbench.maintenance', true) = 'on' THEN RETURN OLD; END IF;
              RAISE EXCEPTION 'immutable record';
            END;
            $$ LANGUAGE plpgsql
        """)
        )
        for table in ("feedback", "enrichments"):
            await conn.execute(text(f"DROP TRIGGER IF EXISTS immutable_guard ON {table}"))
            await conn.execute(
                text(
                    f"CREATE TRIGGER immutable_guard BEFORE UPDATE OR DELETE ON {table} "
                    "FOR EACH ROW EXECUTE FUNCTION reject_immutable_change()"
                )
            )


async def main() -> None:
    engine = create_engine(Settings().database_url)
    try:
        await migrate(engine)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
