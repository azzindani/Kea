"""Kernel cleanup - drop obsolete task and checkpoint tables

Revision ID: 004_kernel_cleanup
Revises: 003_missing_tables
Create Date: 2026-02-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004_kernel_cleanup"
down_revision: str | None = "003_missing_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop kernel-specific tables
    op.execute("DROP TABLE IF EXISTS data_pool CASCADE")
    op.drop_table("micro_tasks")
    op.drop_table("execution_batches")
    op.drop_table("graph_checkpoints")


def downgrade() -> None:
    # Recreate execution_batches
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

    # Recreate micro_tasks
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

    # Recreate graph_checkpoints
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
