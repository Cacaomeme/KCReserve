"""Add status_updated_by to reservations

Revision ID: c4f0b2d6a91e
Revises: 7c8e3a2d9b01
Create Date: 2026-06-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4f0b2d6a91e'
down_revision: Union[str, Sequence[str], None] = '7c8e3a2d9b01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('reservations') as batch_op:
        batch_op.add_column(sa.Column('status_updated_by_user_id', sa.Integer(), nullable=True))
        batch_op.create_index(
            batch_op.f('ix_reservations_status_updated_by_user_id'),
            ['status_updated_by_user_id'],
            unique=False,
        )
        batch_op.create_foreign_key(
            'fk_reservations_status_updated_by_user_id_users',
            'users',
            ['status_updated_by_user_id'],
            ['id'],
            ondelete='SET NULL',
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('reservations') as batch_op:
        batch_op.drop_constraint(
            'fk_reservations_status_updated_by_user_id_users',
            type_='foreignkey',
        )
        batch_op.drop_index(batch_op.f('ix_reservations_status_updated_by_user_id'))
        batch_op.drop_column('status_updated_by_user_id')
