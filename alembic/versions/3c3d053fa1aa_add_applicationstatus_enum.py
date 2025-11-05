"""Add ApplicationStatus enum

Revision ID: 3c3d053fa1aa
Revises: 0c7cc139782e
Create Date: 2025-11-06 03:22:09.728009

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3c3d053fa1aa'
down_revision: Union[str, Sequence[str], None] = '0c7cc139782e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'course_applications', 'status',
        existing_type=sa.VARCHAR(length=20),
        existing_nullable=False,
        server_default=None
    )

    op.alter_column(
        'course_applications', 'status',
        existing_type=sa.VARCHAR(length=20),
        type_=postgresql.ENUM('pending', 'approved', 'rejected', name='status'),
        existing_nullable=False,
        postgresql_using='status::status'
    )

    op.alter_column(
        'course_applications', 'status',
        server_default='pending'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'course_applications', 'status',
        server_default=None
    )

    op.alter_column(
        'course_applications', 'status',
        existing_type=postgresql.ENUM('pending', 'approved', 'rejected', name='status'),
        type_=sa.VARCHAR(length=20),
        existing_nullable=False,
        postgresql_using='status::text'
    )

    op.alter_column(
        'course_applications', 'status',
        server_default=sa.text("'pending'::character varying")
    )
