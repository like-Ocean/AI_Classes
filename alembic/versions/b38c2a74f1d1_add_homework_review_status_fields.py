"""Add homework review and status fields

Revision ID: b38c2a74f1d1
Revises: 7a1e5c3d9b2f
Create Date: 2026-04-24 12:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b38c2a74f1d1'
down_revision: Union[str, Sequence[str], None] = '7a1e5c3d9b2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('homework_submissions', sa.Column('status', sa.String(length=32), server_default=sa.text("'pending_review'"), nullable=False))
    op.add_column('homework_submissions', sa.Column('review_result', sa.String(length=32), nullable=True))
    op.add_column('homework_submissions', sa.Column('review_comment', sa.Text(), nullable=True))
    op.add_column('homework_submissions', sa.Column('reviewed_by', sa.Integer(), nullable=True))
    op.add_column('homework_submissions', sa.Column('reviewed_at', sa.DateTime(), nullable=True))

    op.create_foreign_key(
        'fk_homework_submissions_reviewed_by_users',
        'homework_submissions', 'users',
        ['reviewed_by'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index(op.f('ix_homework_submissions_reviewed_by'), 'homework_submissions', ['reviewed_by'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_homework_submissions_reviewed_by'), table_name='homework_submissions')
    op.drop_constraint('fk_homework_submissions_reviewed_by_users', 'homework_submissions', type_='foreignkey')

    op.drop_column('homework_submissions', 'reviewed_at')
    op.drop_column('homework_submissions', 'reviewed_by')
    op.drop_column('homework_submissions', 'review_comment')
    op.drop_column('homework_submissions', 'review_result')
    op.drop_column('homework_submissions', 'status')
