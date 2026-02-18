"""Add missing runtime tables: execution_batches, micro_tasks, graph_checkpoints,
audit_trail, scheduled_tasks, human_interventions

Revision ID: 003_missing_tables
Revises: 002_knowledge_registry
Create Date: 2026-02-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003_missing_tables"
down_revision: str | None = "002_knowledge_registry"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Dispatcher tables (shared/dispatcher.py)
    # ------------------------------------------------------------------
    op.create_table(
        "execution_batches",
        sa.Column(
            "batch_id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("batch_type", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("(NOW() AT TIME ZONE 'utc')"),
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "micro_tasks",
        sa.Column(
            "task_id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column(
            "batch_id",
            sa.UUID(),
            sa.ForeignKey("execution_batches.batch_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tool_name", sa.Text(), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("artifact_id", sa.Text(), nullable=True),
        sa.Column("error_log", sa.Text(), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("resource_cost", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        sa.Column("dependency_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("(NOW() AT TIME ZONE 'utc')"),
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("idx_batch_lookup", "micro_tasks", ["batch_id", "status"])
    op.create_index("idx_task_governance", "micro_tasks", ["status", "priority", "created_at"])

    # ------------------------------------------------------------------
    # Vault checkpointing (services/vault/core/checkpointing.py)
    # ------------------------------------------------------------------
    op.create_table(
        "graph_checkpoints",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("job_id", sa.String(64), nullable=False),
        sa.Column("node_name", sa.String(64), nullable=False),
        sa.Column("state", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.UniqueConstraint("job_id", "node_name", name="uq_checkpoint_job_node"),
    )
    op.create_index("idx_checkpoints_job_id", "graph_checkpoints", ["job_id"])

    # ------------------------------------------------------------------
    # Vault audit trail (services/vault/core/postgres_audit.py) — table name: audit_trail
    # ------------------------------------------------------------------
    op.create_table(
        "audit_trail",
        sa.Column("entry_id", sa.Text(), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("actor", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("resource", sa.Text(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True, server_default="{}"),
        sa.Column("parent_id", sa.Text(), nullable=True),
        sa.Column("session_id", sa.Text(), nullable=True),
        sa.Column("checksum", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("idx_audit_trail_ts", "audit_trail", ["timestamp"])
    op.create_index("idx_audit_trail_type", "audit_trail", ["event_type"])
    op.create_index("idx_audit_trail_session", "audit_trail", ["session_id"])

    # ------------------------------------------------------------------
    # Chronos scheduled tasks (services/chronos/main.py)
    # ------------------------------------------------------------------
    op.create_table(
        "scheduled_tasks",
        sa.Column("task_id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("cron_expr", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("idx_scheduled_tasks_next_run", "scheduled_tasks", ["enabled", "next_run_at"])

    # ------------------------------------------------------------------
    # HITL human interventions (services/api_gateway/routes/interventions.py)
    # ------------------------------------------------------------------
    op.create_table(
        "human_interventions",
        sa.Column("intervention_id", sa.Text(), primary_key=True),
        sa.Column("job_id", sa.Text(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("options", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("response", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_interventions_status", "human_interventions", ["status"])
    op.create_index("idx_interventions_job", "human_interventions", ["job_id"])


def downgrade() -> None:
    op.drop_table("human_interventions")
    op.drop_table("scheduled_tasks")
    op.drop_table("audit_trail")
    op.drop_table("graph_checkpoints")
    op.drop_table("micro_tasks")
    op.drop_table("execution_batches")
