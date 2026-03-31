"""add_passage_status_and_quiz_passage_id

Revision ID: a2d5f8c91e30
Revises: f9c2e5b31a70
Create Date: 2026-03-30 01:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = 'a2d5f8c91e30'
down_revision: Union[str, Sequence[str], None] = 'f9c2e5b31a70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'passages',
        sa.Column('status', sa.String(50), nullable=False, server_default='in_progress'),
    )
    op.add_column(
        'quizzes',
        sa.Column(
            'passage_id',
            UUID(as_uuid=True),
            sa.ForeignKey('passages.id', ondelete='SET NULL'),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column('quizzes', 'passage_id')
    op.drop_column('passages', 'status')
