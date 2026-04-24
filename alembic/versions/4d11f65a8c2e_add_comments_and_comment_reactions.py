"""Add comments and comment reactions tables

Revision ID: 4d11f65a8c2e
Revises: 122ab2d9b93d
Create Date: 2026-04-20 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d11f65a8c2e'
down_revision: Union[str, Sequence[str], None] = '122ab2d9b93d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('material_id', sa.Integer(), nullable=True),
        sa.Column('test_id', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_anonymous', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.CheckConstraint(
            '(material_id IS NOT NULL AND test_id IS NULL) OR (material_id IS NULL AND test_id IS NOT NULL)',
            name='ck_comments_exactly_one_target'
        ),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['test_id'], ['tests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comments_user_id'), 'comments', ['user_id'], unique=False)
    op.create_index(op.f('ix_comments_material_id'), 'comments', ['material_id'], unique=False)
    op.create_index(op.f('ix_comments_test_id'), 'comments', ['test_id'], unique=False)

    op.create_table(
        'comment_reactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('comment_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('is_like', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['comment_id'], ['comments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('comment_id', 'user_id', name='uq_comment_reactions_comment_user')
    )
    op.create_index(op.f('ix_comment_reactions_comment_id'), 'comment_reactions', ['comment_id'], unique=False)
    op.create_index(op.f('ix_comment_reactions_user_id'), 'comment_reactions', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_comment_reactions_user_id'), table_name='comment_reactions')
    op.drop_index(op.f('ix_comment_reactions_comment_id'), table_name='comment_reactions')
    op.drop_table('comment_reactions')

    op.drop_index(op.f('ix_comments_test_id'), table_name='comments')
    op.drop_index(op.f('ix_comments_material_id'), table_name='comments')
    op.drop_index(op.f('ix_comments_user_id'), table_name='comments')
    op.drop_table('comments')
