"""add cancellation_requested to enum

Revision ID: 62341d6d83fa
Revises: 10f21a303d6e
Create Date: 2025-11-24 22:54:39.567671

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62341d6d83fa'
down_revision: Union[str, Sequence[str], None] = '10f21a303d6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    if bind.engine.name == 'postgresql':
        # PostgreSQL requires explicit addition of the enum value.
        # This cannot run inside a transaction block.
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE reservationstatus ADD VALUE IF NOT EXISTS 'cancellation_requested'")
    else:
        # For SQLite, Enums are typically VARCHARs. 
        # Updating the CHECK constraint is complex (requires table recreation), 
        # so we skip it here assuming the application layer handles validation.
        pass


def downgrade() -> None:
    """Downgrade schema."""
    # PostgreSQL does not support removing values from Enums easily.
    pass
