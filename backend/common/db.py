"""Compatibility command for the separately run Alembic migration service."""

import argparse
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Connection


def migration_config(connection: Connection | None = None, *, adopt: bool = False) -> Config:
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.attributes["adopt_unversioned"] = adopt
    if connection is not None:
        config.attributes["connection"] = connection
    return config


def upgrade_database(connection: Connection, *, adopt: bool = False) -> None:
    """Use an existing transaction for isolated database fixtures."""
    command.upgrade(migration_config(connection, adopt=adopt), "head")


def main() -> None:
    parser = argparse.ArgumentParser(description="Upgrade the database with Alembic")
    parser.add_argument(
        "--adopt", action="store_true", help="Validate and adopt a known unversioned schema"
    )
    arguments = parser.parse_args()
    command.upgrade(migration_config(adopt=arguments.adopt), "head")


if __name__ == "__main__":
    main()
