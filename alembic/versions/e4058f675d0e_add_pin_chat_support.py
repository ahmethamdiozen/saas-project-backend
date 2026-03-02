"""add pin chat support

Revision ID: e4058f675d0e
Revises: 95844977cfe0
Create Date: 2026-03-01 18:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4058f675d0e'
down_revision: Union[str, None] = '95844977cfe0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add column as nullable first
    op.add_column('chat_sessions', sa.Column('is_pinned', sa.Boolean(), nullable=True))
    
    # 2. Fill existing rows with False
    op.execute("UPDATE chat_sessions SET is_pinned = FALSE")
    
    # 3. Alter column to be NOT NULL
    op.alter_column('chat_sessions', 'is_pinned', nullable=False)


def downgrade() -> None:
    op.drop_column('chat_sessions', 'is_pinned')
