"""add_topic_graph

Revision ID: e7b3f9a12c84
Revises: c4e1a8f92b5d
Create Date: 2026-03-26 00:01:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from alembic import op

revision: str = 'e7b3f9a12c84'
down_revision: Union[str, Sequence[str], None] = 'c4e1a8f92b5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'topic_nodes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('canonical_name', sa.Text(), nullable=False),
        sa.Column('display_name', sa.Text(), nullable=False),
        sa.Column('domain', sa.Text(), nullable=True),
        sa.Column('source_module_id', UUID(as_uuid=True), sa.ForeignKey('modules.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='in_progress'),
        sa.Column('concept_hints', JSONB(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint('user_id', 'canonical_name', name='uq_topic_nodes_user_canonical'),
    )
    op.create_index('ix_topic_nodes_user_id', 'topic_nodes', ['user_id'])

    op.create_table(
        'topic_edges',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_node_id', UUID(as_uuid=True), sa.ForeignKey('topic_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_node_id', UUID(as_uuid=True), sa.ForeignKey('topic_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relationship_type', sa.String(50), nullable=False, server_default='related'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('user_id', 'source_node_id', 'target_node_id', name='uq_topic_edges_user_src_tgt'),
    )
    op.create_index('ix_topic_edges_user_id', 'topic_edges', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_topic_edges_user_id', table_name='topic_edges')
    op.drop_table('topic_edges')
    op.drop_index('ix_topic_nodes_user_id', table_name='topic_nodes')
    op.drop_table('topic_nodes')
