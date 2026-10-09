import asyncio
import logging
import signal

import httpx

from workbench.infrastructure.database import create_engine
from workbench.infrastructure.deterministic import generate_demo
from workbench.infrastructure.providers import openrouter_generator
from workbench.logic.enrichment import Generate
from workbench.repositories.coordination import lock_workspace
from workbench.repositories.retention import cleanup_expired
from workbench.settings import Settings
from workbench.workers.processing import process_one


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = Settings()
    engine = create_engine(settings.database_url)
    client = httpx.AsyncClient()
    generators: dict[str, Generate] = {"deterministic-rules/1": generate_demo}
    if settings.openrouter_calls_enabled:
        generators[f"openrouter/{settings.openrouter_model}"] = openrouter_generator(
            settings, client
        )
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for name in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(name, stop.set)
    try:
        last_cleanup = 0.0
        while not stop.is_set():
            if loop.time() - last_cleanup > 60:
                async with engine.begin() as conn:
                    await lock_workspace(conn)
                    await cleanup_expired(conn)
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
