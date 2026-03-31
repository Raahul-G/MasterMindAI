"""add_summary_use_cases_to_passages

Revision ID: f9c2e5b31a70
Revises: b1f4d2a83e90
Create Date: 2026-03-30 00:01:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'f9c2e5b31a70'
down_revision: Union[str, Sequence[str], None] = 'b1f4d2a83e90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('passages', sa.Column('summary', sa.Text(), nullable=True))
    op.add_column('passages', sa.Column('use_cases', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('passages', 'use_cases')
    op.drop_column('passages', 'summary')
