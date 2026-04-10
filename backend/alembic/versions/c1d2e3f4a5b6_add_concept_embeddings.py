"""add_concept_embeddings

Revision ID: c1d2e3f4a5b6
Revises: 559f296a3d4c
Create Date: 2026-04-10 00:00:01.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "559f296a3d4c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "concept_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("canonical_concept", sa.Text(), nullable=False),
        sa.Column("pos_x", sa.Float(), nullable=True),
        sa.Column("pos_y", sa.Float(), nullable=True),
        sa.Column("pos_z", sa.Float(), nullable=True),
        sa.Column("hub_score", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "module_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Add vector column via raw SQL — Alembic does not natively support pgvector type
    op.execute("ALTER TABLE concept_embeddings ADD COLUMN embedding vector(1536)")

    op.create_unique_constraint(
        "uq_concept_embeddings_user_concept",
        "concept_embeddings",
        ["user_id", "canonical_concept"],
    )
    op.create_index(
        "ix_concept_embeddings_user_id",
        "concept_embeddings",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_table("concept_embeddings")
