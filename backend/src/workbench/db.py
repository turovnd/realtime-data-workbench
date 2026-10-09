"""Compatibility entrypoint for the deployment migration command."""

import asyncio

from workbench.infrastructure.database import main

if __name__ == "__main__":
    asyncio.run(main())
