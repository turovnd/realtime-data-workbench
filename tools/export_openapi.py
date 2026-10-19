"""Export the actual FastAPI contract without connecting to the database."""

import json
from pathlib import Path

from workbench.api import app


def main() -> None:
    target = Path(__file__).resolve().parents[1] / "openapi.json"
    target.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n")
    print(f"Exported {len(app.openapi()['paths'])} API paths to {target.name}")


if __name__ == "__main__":
    main()
