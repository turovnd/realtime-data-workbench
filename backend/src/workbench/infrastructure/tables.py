"""Small PostgreSQL schema. All mutations serialize on one demo workspace counter."""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
)

metadata = MetaData()
state = Table(
    "workspace_state",
    metadata,
    Column("id", String, primary_key=True),
    Column("token_hash", String, unique=True),
    Column("created_at", DateTime(timezone=True)),
    Column("cursor", Integer, nullable=False, default=0),
)
records = Table(
    "feedback",
    metadata,
    Column("id", String, primary_key=True),
    Column("workspace_id", ForeignKey("workspace_state.id"), nullable=False),
    Column("identity", String, nullable=False),
    Column("sequence", Integer, nullable=False),
    UniqueConstraint("workspace_id", "identity"),
    UniqueConstraint("workspace_id", "sequence"),
    Column("text", Text, nullable=False),
    Column("channel", String, nullable=False),
    Column("ingested_at", DateTime(timezone=True), nullable=False),
)
batches = Table(
    "backfills",
    metadata,
    Column("id", String, primary_key=True),
    Column("workspace_id", ForeignKey("workspace_state.id"), nullable=False),
    Column("config", String, nullable=False),
    Column("record_ids", JSON, nullable=False),
    Column("watermark", Integer, nullable=False),
    Column("cancelled", Boolean, nullable=False, default=False),
)
jobs = Table(
    "jobs",
    metadata,
    Column("id", String, primary_key=True),
    Column("workspace_id", ForeignKey("workspace_state.id"), nullable=False),
    Column("record_id", ForeignKey("feedback.id"), nullable=False),
    Column("config", String, nullable=False),
    Column("origin", String, nullable=False),
    Column("provider", String, nullable=False, default="deterministic-rules/1"),
    Column("batch_id", ForeignKey("backfills.id")),
    Column("status", String, nullable=False),
    Column("attempts", Integer, nullable=False, default=0),
    Column("fence", Integer, nullable=False, default=0),
    Column("lease_until", DateTime(timezone=True)),
    Column("available_at", DateTime(timezone=True), nullable=False),
    Column("error", Text),
    UniqueConstraint("record_id", "config", name="uq_job_version"),
)
outputs = Table(
    "enrichments",
    metadata,
    Column("id", String, primary_key=True),
    Column("workspace_id", ForeignKey("workspace_state.id"), nullable=False),
    Column("record_id", ForeignKey("feedback.id"), nullable=False),
    Column("config", String, nullable=False),
    Column("payload", JSON, nullable=False),
    Column("provider", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("record_id", "config", name="uq_output_version"),
)


accounts = Table(
    "accounts",
    metadata,
    Column("id", String, primary_key=True),
    Column("workspace_id", ForeignKey("workspace_state.id"), nullable=False, unique=True),
    Column("email", String, nullable=False, unique=True),
    Column("password_hash", Text, nullable=False),
)
auth_sessions = Table(
    "auth_sessions",
    metadata,
    Column("token_hash", String, primary_key=True),
    Column("workspace_id", ForeignKey("workspace_state.id"), nullable=False),
    Column("account_id", ForeignKey("accounts.id")),
    Column("expires_at", DateTime(timezone=True), nullable=False),
)
auth_buckets = Table(
    "auth_buckets",
    metadata,
    Column("key", String, primary_key=True),
    Column("attempts", Integer, nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
)
feed_views = Table(
    "feed_views",
    metadata,
    Column("id", String, primary_key=True),
    Column("workspace_id", ForeignKey("workspace_state.id"), nullable=False),
    Column("filter_key", String, nullable=False),
    Column("record_ids", JSON, nullable=False),
    Column("watermark", Integer, nullable=False),
    Column("secret", String, nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
)
provider_usage = Table(
    "provider_usage",
    metadata,
    Column("id", String, primary_key=True),
    Column("calls", Integer, nullable=False),
)
