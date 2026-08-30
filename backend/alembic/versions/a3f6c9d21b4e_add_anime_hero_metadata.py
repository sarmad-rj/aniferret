"""add anime hero metadata (cover image, genres, synopsis, score)

Revision ID: a3f6c9d21b4e
Revises: e1c18d02c805
Create Date: 2026-08-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3f6c9d21b4e'
down_revision: Union[str, Sequence[str], None] = 'e1c18d02c805'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('anime', sa.Column('cover_image_url', sa.String(length=500), nullable=True))
    op.add_column(
        'anime',
        sa.Column('genres', sa.JSON(), nullable=False, server_default='[]'),
    )
    op.add_column('anime', sa.Column('synopsis', sa.Text(), nullable=True))
    op.add_column('anime', sa.Column('score', sa.Float(), nullable=True))
    with op.batch_alter_table('anime') as batch_op:
        batch_op.alter_column('genres', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('anime', 'score')
    op.drop_column('anime', 'synopsis')
    op.drop_column('anime', 'genres')
    op.drop_column('anime', 'cover_image_url')
