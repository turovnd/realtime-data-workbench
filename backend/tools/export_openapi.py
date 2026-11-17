"""Export the current contract to a temporary CI artifact without starting the API."""

import argparse
import json
from pathlib import Path

from modules.api.app import app


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the FastAPI OpenAPI contract")
    parser.add_argument("output", type=Path)
    target = parser.parse_args().output
    target.write_text(json.dumps(app.openapi(), indent=2) + "\n")
    print(f"Exported {len(app.openapi()['paths'])} API paths.")


if __name__ == "__main__":
    main()
