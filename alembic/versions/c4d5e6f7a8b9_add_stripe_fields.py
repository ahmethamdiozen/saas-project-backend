"""add stripe fields

Revision ID: c4d5e6f7a8b9
Revises: b3f1e2d4c5a6
Create Date: 2026-05-08 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, None] = 'b3f1e2d4c5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('stripe_customer_id', sa.String(), nullable=True))
    op.add_column('subscriptions', sa.Column('stripe_price_id', sa.String(), nullable=True))
    op.add_column('user_subscriptions', sa.Column('stripe_subscription_id', sa.String(), nullable=True))
    op.create_index('ix_user_subscriptions_stripe_subscription_id', 'user_subscriptions', ['stripe_subscription_id'])


def downgrade() -> None:
    op.drop_index('ix_user_subscriptions_stripe_subscription_id', 'user_subscriptions')
    op.drop_column('user_subscriptions', 'stripe_subscription_id')
    op.drop_column('subscriptions', 'stripe_price_id')
    op.drop_column('users', 'stripe_customer_id')
