"""add franchise and franchise_entry

Revision ID: bfa83de987ec
Revises: 260420feb5c9
Create Date: 2026-08-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfa83de987ec'
down_revision: Union[str, Sequence[str], None] = '260420feb5c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'franchise',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_franchise_slug'), 'franchise', ['slug'], unique=True)

    op.create_table(
        'franchise_entry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('franchise_id', sa.Integer(), nullable=False),
        sa.Column('anime_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('entry_type', sa.String(length=20), nullable=False),
        sa.Column('release_order', sa.Integer(), nullable=False),
        sa.Column('chronological_order', sa.Integer(), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['franchise_id'], ['franchise.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['anime_id'], ['anime.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_franchise_entry_franchise_id'), 'franchise_entry', ['franchise_id'], unique=False
    )
    op.create_index(
        op.f('ix_franchise_entry_anime_id'), 'franchise_entry', ['anime_id'], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_franchise_entry_anime_id'), table_name='franchise_entry')
    op.drop_index(op.f('ix_franchise_entry_franchise_id'), table_name='franchise_entry')
    op.drop_table('franchise_entry')

    op.drop_index(op.f('ix_franchise_slug'), table_name='franchise')
    op.drop_table('franchise')
