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
        await conn.run_sync(metadata.create_all)
        await conn.execute(
            text(
                "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS provider TEXT NOT NULL "
                "DEFAULT 'deterministic-rules/1'"
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
