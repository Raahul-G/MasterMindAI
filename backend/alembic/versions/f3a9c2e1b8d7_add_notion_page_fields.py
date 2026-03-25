"""add_notion_page_fields

Revision ID: f3a9c2e1b8d7
Revises: dc8bd001fd56
Create Date: 2026-03-25 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'f3a9c2e1b8d7'
down_revision: Union[str, Sequence[str], None] = 'dc8bd001fd56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('notion_workspace_name', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('notion_mastermind_page_id', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'notion_mastermind_page_id')
    op.drop_column('users', 'notion_workspace_name')
