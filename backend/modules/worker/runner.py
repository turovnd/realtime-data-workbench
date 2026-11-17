import asyncio
import logging
import signal

import httpx

from common.infrastructure.database import create_engine, session_scope
from common.repositories.coordination import lock_workspace
from common.repositories.retention import cleanup_expired
from common.settings import Settings
from modules.worker.processing import process_one
from modules.worker.providers import build_generators


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = Settings()
    engine = create_engine(settings.database_url)
    client = httpx.AsyncClient()
    generators = build_generators(settings, client)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for name in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(name, stop.set)
    try:
        last_cleanup = 0.0
        while not stop.is_set():
            if loop.time() - last_cleanup > 60:
                async with session_scope(engine) as session:
                    await session.run_sync(lock_workspace)
                    await session.run_sync(cleanup_expired)
                last_cleanup = loop.time()
            worked = await process_one(
                engine,
                lease_seconds=settings.lease_seconds,
                timeout_seconds=settings.provider_timeout_seconds,
                generators=generators,
                live_budget=settings.live_call_budget,
            )
            if not worked:
                try:
                    await asyncio.wait_for(stop.wait(), timeout=0.5)
                except TimeoutError:
                    pass
    finally:
        await client.aclose()
        await engine.dispose()
