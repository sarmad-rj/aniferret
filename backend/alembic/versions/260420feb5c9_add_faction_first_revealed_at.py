"""add faction first_revealed_at

Revision ID: 260420feb5c9
Revises: a3f6c9d21b4e
Create Date: 2026-08-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '260420feb5c9'
down_revision: Union[str, Sequence[str], None] = 'a3f6c9d21b4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('faction', sa.Column('first_revealed_at', sa.String(length=20), nullable=True))
    with op.batch_alter_table('faction') as batch_op:
        batch_op.create_index(
            op.f('ix_faction_first_revealed_at'), ['first_revealed_at'], unique=False
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('faction') as batch_op:
        batch_op.drop_index(op.f('ix_faction_first_revealed_at'))
    op.drop_column('faction', 'first_revealed_at')
