"""Preserve v1/v2 history and allow subsequent analysis runs."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TRIGGER immutable_guard ON enrichments")
    for table, old_name, new_name in (
        ("jobs", "uq_job_version", "uq_job_run"),
        ("enrichments", "uq_output_version", "uq_output_run"),
    ):
        op.add_column(table, sa.Column("run", sa.Integer(), nullable=True))
        op.execute(f"UPDATE {table} SET run = CASE WHEN config = 'v2' THEN 2 ELSE 1 END")
        op.alter_column(table, "run", nullable=False, server_default="1")
        op.drop_constraint(old_name, table, type_="unique")
        op.create_unique_constraint(new_name, table, ["record_id", "run"])
    op.add_column("jobs", sa.Column("request_identity", sa.String(), nullable=True))
    op.create_unique_constraint(
        "uq_job_request_identity", "jobs", ["record_id", "request_identity"]
    )
    op.create_index(
        "uq_job_legacy_config",
        "jobs",
        ["record_id", "config"],
        unique=True,
        postgresql_where=sa.text("origin != 'analysis'"),
    )
    op.execute(
        "CREATE TRIGGER immutable_guard BEFORE UPDATE OR DELETE ON enrichments "
        "FOR EACH ROW EXECUTE FUNCTION reject_immutable_change()"
    )


def downgrade() -> None:
    connection = op.get_bind()
    for table in ("jobs", "enrichments"):
        invalid = connection.scalar(
            sa.text(
                f"SELECT EXISTS (SELECT 1 FROM {table} WHERE config NOT IN ('v1', 'v2') "
                "OR run != CASE WHEN config = 'v2' THEN 2 ELSE 1 END)"
            )
        )
        if invalid:
            raise RuntimeError("Cannot downgrade: analysis run history is incompatible with v1/v2")
    if connection.scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM jobs "
            "WHERE request_identity IS NOT NULL OR origin = 'analysis')"
        )
    ):
        raise RuntimeError("Cannot downgrade: analysis request identities must be preserved")
    op.drop_index("uq_job_legacy_config", table_name="jobs")
    op.drop_constraint("uq_job_request_identity", "jobs", type_="unique")
    op.drop_column("jobs", "request_identity")
    for table, old_name, new_name in (
        ("jobs", "uq_job_version", "uq_job_run"),
        ("enrichments", "uq_output_version", "uq_output_run"),
    ):
        op.drop_constraint(new_name, table, type_="unique")
        op.drop_column(table, "run")
        op.create_unique_constraint(old_name, table, ["record_id", "config"])
