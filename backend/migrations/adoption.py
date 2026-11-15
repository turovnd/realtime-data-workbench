"""Validate the two historical, unversioned schemas before one-time adoption."""

import sqlalchemy as sa
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.engine import Connection
from sqlalchemy.engine.interfaces import ReflectedIndex

# PostgreSQL's reflected form for the supported VARCHAR origin column.
# Keep literal contents intact: SQL whitespace can be part of a string value.
LEGACY_CONFIG_PREDICATES = {"((origin)::text <> 'analysis'::text)"}

RUN_KEYS = {
    "jobs": {
        "uq_job_run": ["record_id", "run"],
        "uq_job_request_identity": ["record_id", "request_identity"],
    },
    "enrichments": {"uq_output_run": ["record_id", "run"]},
}


def expected_schema(script: ScriptDirectory, revision: str) -> sa.MetaData:
    baseline = script.get_revision("0001")
    assert baseline is not None
    metadata = sa.MetaData()
    baseline_metadata: sa.MetaData = baseline.module.metadata
    for table in baseline_metadata.sorted_tables:
        table.to_metadata(metadata)
    if revision == "0001":
        return metadata
    for table_name in ("jobs", "enrichments"):
        table = metadata.tables[table_name]
        for constraint in list(table.constraints):
            if isinstance(constraint, sa.UniqueConstraint):
                table.constraints.remove(constraint)
        table.append_column(sa.Column("run", sa.Integer(), nullable=False, server_default="1"))
    metadata.tables["jobs"].append_column(sa.Column("request_identity", sa.String()))
    for table_name, constraints in RUN_KEYS.items():
        for name, columns in constraints.items():
            metadata.tables[table_name].append_constraint(sa.UniqueConstraint(*columns, name=name))
    sa.Index(
        "uq_job_legacy_config",
        metadata.tables["jobs"].c.record_id,
        metadata.tables["jobs"].c.config,
        unique=True,
        postgresql_where=metadata.tables["jobs"].c.origin != "analysis",
    )
    return metadata


def validate_triggers(connection: Connection, script: ScriptDirectory) -> None:
    baseline = script.get_revision("0001")
    assert baseline is not None
    body = " ".join(baseline.module.IMMUTABLE_BODY.split())
    triggers = (
        connection.execute(
            sa.text(
                "SELECT c.relname, t.tgname, t.tgtype, t.tgenabled::text AS tgenabled, "
                "t.tgqual IS NULL AS no_condition, "
                "t.tgnargs, p.proname, p.prosrc, p.prosecdef, p.proconfig, "
                "p.pronargs, p.prorettype = 'trigger'::regtype AS returns_trigger, l.lanname "
                "FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid "
                "JOIN pg_namespace n ON n.oid = c.relnamespace "
                "JOIN pg_proc p ON p.oid = t.tgfoid JOIN pg_language l ON l.oid = p.prolang "
                "WHERE n.nspname = current_schema() AND NOT t.tgisinternal"
            )
        )
        .mappings()
        .all()
    )
    if len(triggers) != 2 or {row["relname"] for row in triggers} != {"feedback", "enrichments"}:
        raise RuntimeError("Cannot adopt database: unexpected immutable triggers")
    for row in triggers:
        if (
            row["tgname"] != "immutable_guard"
            or row["tgtype"] != 27
            or row["tgenabled"] != "O"
            or not row["no_condition"]
            or row["tgnargs"] != 0
            or row["proname"] != "reject_immutable_change"
            or " ".join(row["prosrc"].split()) != body
            or row["prosecdef"]
            or row["proconfig"] is not None
            or row["pronargs"] != 0
            or not row["returns_trigger"]
            or row["lanname"] != "plpgsql"
        ):
            raise RuntimeError("Cannot adopt database: immutable trigger definition differs")


def adopt_unversioned(connection: Connection, script: ScriptDirectory) -> str:
    inspector = sa.inspect(connection)
    columns = {
        table: {column["name"] for column in inspector.get_columns(table)}
        for table in ("jobs", "enrichments")
        if inspector.has_table(table)
    }
    markers = (
        "run" in columns.get("jobs", set()),
        "request_identity" in columns.get("jobs", set()),
        "run" in columns.get("enrichments", set()),
    )
    if any(markers) and not all(markers):
        raise RuntimeError("Cannot adopt database: partial analysis-run schema")
    revision = "0002" if all(markers) else "0001"
    expected = expected_schema(script, revision)
    if set(inspector.get_table_names()) - {"alembic_version"} != set(expected.tables):
        raise RuntimeError("Cannot adopt database: unknown or missing application tables")
    if inspector.get_view_names() or inspector.get_materialized_view_names():
        raise RuntimeError("Cannot adopt database: unexpected database views")

    attach: list[tuple[str, str]] = []
    provider_columns = inspector.get_columns("jobs")
    provider = next((column for column in provider_columns if column["name"] == "provider"), None)
    if provider is None:
        raise RuntimeError("Cannot adopt database: jobs.provider is missing")
    provider_default = provider["default"]
    if provider_default not in (
        None,
        "'deterministic-rules/1'::text",
        "'deterministic-rules/1'::character varying",
    ):
        raise RuntimeError("Cannot adopt database: unexpected provider default")
    provider_type = provider["type"]
    if not isinstance(provider_type, sa.String) or provider_type.length is not None:
        raise RuntimeError("Cannot adopt database: unexpected provider type")
    expected.tables["jobs"].c.provider.type = provider_type
    if provider_default is not None:
        expected.tables["jobs"].c.provider.server_default = sa.DefaultClause(
            sa.text(provider_default)
        )

    for table_name, table in expected.tables.items():
        actual_primary = inspector.get_pk_constraint(table_name)
        if actual_primary["constrained_columns"] != [column.name for column in table.primary_key]:
            raise RuntimeError(f"Cannot adopt database: primary key differs on {table_name}")
        if inspector.get_check_constraints(table_name):
            raise RuntimeError(
                f"Cannot adopt database: unexpected check constraint on {table_name}"
            )
        actual_unique = {item["name"] for item in inspector.get_unique_constraints(table_name)}
        indexes: dict[str, ReflectedIndex] = {}
        for index in inspector.get_indexes(table_name):
            index_name = index["name"]
            if index_name is None:
                raise RuntimeError(f"Cannot adopt database: unnamed index on {table_name}")
            indexes[index_name] = index
        if table_name == "jobs" and revision == "0002":
            legacy_index = indexes.get("uq_job_legacy_config")
            if legacy_index is None:
                raise RuntimeError("Cannot adopt database: legacy configuration index is missing")
            predicate = legacy_index.get("dialect_options", {}).get("postgresql_where", "")
            if (
                not legacy_index.get("unique")
                or legacy_index.get("column_names") != ["record_id", "config"]
                or predicate not in LEGACY_CONFIG_PREDICATES
                or legacy_index.get("include_columns")
            ):
                raise RuntimeError("Cannot adopt database: legacy configuration index differs")
        for name, key_columns in RUN_KEYS.get(table_name, {}).items():
            if revision != "0002" or name in actual_unique or name not in indexes:
                continue
            index = indexes[name]
            if (
                not index["unique"]
                or index["column_names"] != key_columns
                or index.get("expressions")
                or index.get("include_columns")
                or index.get("dialect_options", {}).get("postgresql_where")
            ):
                raise RuntimeError(f"Cannot adopt database: unique index {name} differs")
            for constraint in list(table.constraints):
                if constraint.name == name:
                    table.constraints.remove(constraint)
            sa.Index(name, *(table.c[column] for column in key_columns), unique=True)
            attach.append((table_name, name))
    differences = compare_metadata(
        MigrationContext.configure(connection, opts={"compare_server_default": True}), expected
    )
    if differences:
        raise RuntimeError(f"Cannot adopt database: schema drift detected ({differences!r})")
    validate_triggers(connection, script)
    if revision == "0001":
        for table_name in ("jobs", "enrichments"):
            if connection.scalar(
                sa.text(
                    f"SELECT EXISTS (SELECT 1 FROM {table_name} WHERE config NOT IN ('v1', 'v2'))"
                )
            ):
                raise RuntimeError("Cannot adopt database: unknown legacy configuration")

    # These are known physical representations of the same historical schema.
    # Normalize only after every validation has passed, in the caller's transaction.
    for table_name, name in attach:
        connection.execute(
            sa.text(f"ALTER TABLE {table_name} ADD CONSTRAINT {name} UNIQUE USING INDEX {name}")
        )
    if isinstance(provider_type, sa.Text):
        connection.execute(sa.text("ALTER TABLE jobs ALTER COLUMN provider TYPE VARCHAR"))
    if provider_default is not None:
        connection.execute(sa.text("ALTER TABLE jobs ALTER COLUMN provider DROP DEFAULT"))
    return revision
