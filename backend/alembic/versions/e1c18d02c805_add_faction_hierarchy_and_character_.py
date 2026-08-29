"""add faction hierarchy and character dossier metadata

Revision ID: e1c18d02c805
Revises: cb93834dfeed
Create Date: 2026-08-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1c18d02c805'
down_revision: Union[str, Sequence[str], None] = 'cb93834dfeed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('faction', sa.Column('parent_id', sa.Integer(), nullable=True))
    with op.batch_alter_table('faction') as batch_op:
        batch_op.create_index(op.f('ix_faction_parent_id'), ['parent_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_faction_parent_id_faction', 'faction', ['parent_id'], ['id'], ondelete='CASCADE'
        )

    op.add_column('character', sa.Column('role', sa.String(length=100), nullable=True))
    op.add_column('character', sa.Column('height', sa.String(length=50), nullable=True))
    op.add_column('character', sa.Column('avatar_url', sa.String(length=500), nullable=True))
    op.add_column('character', sa.Column('bounty', sa.String(length=100), nullable=True))
    op.add_column('character', sa.Column('power', sa.String(length=255), nullable=True))
    op.add_column('character', sa.Column('backstory', sa.Text(), nullable=True))
    op.add_column(
        'character',
        sa.Column('first_revealed_at', sa.String(length=20), nullable=False, server_default='S1E1'),
    )
    with op.batch_alter_table('character') as batch_op:
        batch_op.alter_column('first_revealed_at', server_default=None)
        batch_op.create_index(
            op.f('ix_character_first_revealed_at'), ['first_revealed_at'], unique=False
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('character') as batch_op:
        batch_op.drop_index(op.f('ix_character_first_revealed_at'))
    op.drop_column('character', 'first_revealed_at')
    op.drop_column('character', 'backstory')
    op.drop_column('character', 'power')
    op.drop_column('character', 'bounty')
    op.drop_column('character', 'avatar_url')
    op.drop_column('character', 'height')
    op.drop_column('character', 'role')

    with op.batch_alter_table('faction') as batch_op:
        batch_op.drop_constraint('fk_faction_parent_id_faction', type_='foreignkey')
        batch_op.drop_index(op.f('ix_faction_parent_id'))
    op.drop_column('faction', 'parent_id')
