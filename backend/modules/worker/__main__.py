"""Separate durable-worker process entrypoint; no HTTP routes."""

import asyncio

from modules.worker.runner import main

if __name__ == "__main__":
    asyncio.run(main())
