"""Add ApplicationStatus enum

Revision ID: 0c7cc139782e
Revises: d77f1e1449bc
Create Date: 2025-11-06 03:21:56.712623

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0c7cc139782e'
down_revision: Union[str, Sequence[str], None] = 'd77f1e1449bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    application_status_enum = postgresql.ENUM(
        "pending", "approved", "rejected",
        name="status",
        create_type=True
    )
    application_status_enum.create(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TYPE IF EXISTS status;")
