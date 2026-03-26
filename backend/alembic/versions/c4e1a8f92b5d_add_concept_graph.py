"""add_concept_graph

Revision ID: c4e1a8f92b5d
Revises: f3a9c2e1b8d7
Create Date: 2026-03-26 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from alembic import op

revision: str = 'c4e1a8f92b5d'
down_revision: Union[str, Sequence[str], None] = 'f3a9c2e1b8d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'concept_graph',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_module_id', UUID(as_uuid=True), sa.ForeignKey('modules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('topic', sa.Text(), nullable=False),
        sa.Column('learned_concepts', JSONB(), nullable=False),
        sa.Column('recommended_concepts', JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_concept_graph_user_id', 'concept_graph', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_concept_graph_user_id', table_name='concept_graph')
    op.drop_table('concept_graph')
