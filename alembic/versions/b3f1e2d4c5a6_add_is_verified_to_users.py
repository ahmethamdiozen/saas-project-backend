"""add is_verified to users

Revision ID: b3f1e2d4c5a6
Revises: e4058f675d0e
Create Date: 2026-05-07 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b3f1e2d4c5a6'
down_revision: Union[str, None] = 'e4058f675d0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('users', 'is_verified')
