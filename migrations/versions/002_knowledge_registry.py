"""Add knowledge_registry table for context engineering

Revision ID: 002_knowledge_registry
Revises: 001_initial
Create Date: 2026-02-08

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002_knowledge_registry"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Ensure pgvector extension exists
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Knowledge registry table
    op.create_table(
        "knowledge_registry",
        sa.Column("knowledge_id", sa.Text, primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("domain", sa.Text, nullable=False, server_default="general"),
        sa.Column("category", sa.Text, nullable=False, server_default="skill"),
        sa.Column("tags", sa.ARRAY(sa.Text), server_default="{}"),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("content_hash", sa.Text, nullable=False),
        sa.Column("metadata", sa.JSON, server_default="{}"),
        # embedding column added via raw SQL (pgvector type)
        sa.Column("last_seen", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Add vector column (not supported by SQLAlchemy directly)
    op.execute("ALTER TABLE knowledge_registry ADD COLUMN IF NOT EXISTS embedding vector(1024)")

    # Indexes
    op.create_index("ix_knowledge_domain", "knowledge_registry", ["domain"])
    op.create_index("ix_knowledge_category", "knowledge_registry", ["category"])
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_knowledge_tags ON knowledge_registry USING gin (tags)"
    )

    # HNSW index for vector similarity search
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_knowledge_embedding "
        "ON knowledge_registry USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.drop_table("knowledge_registry")
