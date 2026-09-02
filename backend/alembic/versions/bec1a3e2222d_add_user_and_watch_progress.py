"""add user and watch_progress

Revision ID: bec1a3e2222d
Revises: bfa83de987ec
Create Date: 2026-09-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bec1a3e2222d'
down_revision: Union[str, Sequence[str], None] = 'bfa83de987ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)

    op.create_table(
        'watch_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('anime_id', sa.Integer(), nullable=False),
        sa.Column('checkpoint', sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['anime_id'], ['anime.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'anime_id', name='uq_watch_progress_user_anime'),
    )
    op.create_index(
        op.f('ix_watch_progress_user_id'), 'watch_progress', ['user_id'], unique=False
    )
    op.create_index(
        op.f('ix_watch_progress_anime_id'), 'watch_progress', ['anime_id'], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_watch_progress_anime_id'), table_name='watch_progress')
    op.drop_index(op.f('ix_watch_progress_user_id'), table_name='watch_progress')
    op.drop_table('watch_progress')

    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
