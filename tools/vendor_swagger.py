"""Reproduce the locally hosted Swagger assets from the pinned official npm package."""

import argparse
import hashlib
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path

ASSETS = ("swagger-ui-bundle.js", "swagger-ui.css", "favicon-32x32.png", "LICENSE", "NOTICE")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="5.33.1")
    version = parser.parse_args().version
    if not all(part.isdigit() for part in version.split(".")) or len(version.split(".")) != 3:
        parser.error("Use an explicit stable semantic version")
    target = Path(__file__).resolve().parents[1] / "backend/src/workbench/static/swagger"
    with tempfile.TemporaryDirectory(prefix="feedback-swagger-") as directory:
        result = subprocess.run(
            ["npm", "pack", f"swagger-ui-dist@{version}", "--ignore-scripts", "--silent"],
            cwd=directory,
            capture_output=True,
            text=True,
            check=True,
        )
        archive = Path(directory) / result.stdout.strip().splitlines()[-1]
        with tarfile.open(archive) as package:
            contents = {}
            for name in ASSETS:
                member = package.extractfile(f"package/{name}")
                if member is None:
                    raise RuntimeError(f"Missing upstream asset: {name}")
                contents[name] = member.read()
        target.mkdir(parents=True, exist_ok=True)
        for name, content in contents.items():
            (target / name).write_bytes(content)
        manifest = {
            "package": "swagger-ui-dist",
            "version": version,
            "source": f"https://www.npmjs.com/package/swagger-ui-dist/v/{version}",
            "sha256": {
                name: hashlib.sha256(content).hexdigest() for name, content in contents.items()
            },
        }
        (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
