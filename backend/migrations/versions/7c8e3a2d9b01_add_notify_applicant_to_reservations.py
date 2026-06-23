"""Add notify_applicant to reservations

Revision ID: 7c8e3a2d9b01
Revises: 62341d6d83fa
Create Date: 2026-06-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c8e3a2d9b01'
down_revision: Union[str, Sequence[str], None] = '62341d6d83fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'reservations',
        sa.Column('notify_applicant', sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    bind = op.get_bind()
    if bind.engine.name != 'sqlite':
        op.alter_column('reservations', 'notify_applicant', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('reservations', 'notify_applicant')
