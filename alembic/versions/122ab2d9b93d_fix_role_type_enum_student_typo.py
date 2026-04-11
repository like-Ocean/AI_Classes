"""Fix role_type enum student typo

Revision ID: 122ab2d9b93d
Revises: 9f2b7c1d4e6a
Create Date: 2026-04-10 04:52:50.306647

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '122ab2d9b93d'
down_revision: Union[str, Sequence[str], None] = '9f2b7c1d4e6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("ALTER TYPE role_type RENAME VALUE 'students' TO 'student'")

def downgrade():
    op.execute("ALTER TYPE role_type RENAME VALUE 'student' TO 'students'")
