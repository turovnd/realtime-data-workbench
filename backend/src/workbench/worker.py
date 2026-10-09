"""Separate durable-worker process entrypoint; no HTTP routes."""

import asyncio

from workbench.workers.runner import main

if __name__ == "__main__":
    asyncio.run(main())
