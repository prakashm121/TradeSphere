"""order_book_v2_fix_columns

Revision ID: fd5c169441ea
Revises: 61247afbc73e
Create Date: 2026-05-07 12:34:04.869777

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fd5c169441ea'
down_revision: Union[str, Sequence[str], None] = '61247afbc73e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('stocks', sa.Column('last_traded_price', sa.Float(), nullable=True))
    op.add_column('stocks', sa.Column('bid_price', sa.Float(), nullable=True))
    op.add_column('stocks', sa.Column('ask_price', sa.Float(), nullable=True))

    op.add_column('users', sa.Column('margin_held', sa.Float(), server_default='0', nullable=False))

    op.add_column('portfolio', sa.Column('avg_entry_price', sa.Float(), server_default='0', nullable=False))
    op.add_column('portfolio', sa.Column('margin_held', sa.Float(), server_default='0', nullable=False))

    op.execute("UPDATE stocks SET last_traded_price = price WHERE last_traded_price IS NULL")

    op.alter_column('users', 'margin_held', server_default=None)
    op.alter_column('portfolio', 'avg_entry_price', server_default=None)
    op.alter_column('portfolio', 'margin_held', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('portfolio', 'margin_held')
    op.drop_column('portfolio', 'avg_entry_price')
    op.drop_column('users', 'margin_held')
    op.drop_column('stocks', 'ask_price')
    op.drop_column('stocks', 'bid_price')
    op.drop_column('stocks', 'last_traded_price')
