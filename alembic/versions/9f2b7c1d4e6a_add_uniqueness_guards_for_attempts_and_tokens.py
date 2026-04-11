"""Add uniqueness guards for active test attempts and refresh tokens

Revision ID: 9f2b7c1d4e6a
Revises: 8c4382cc8efb
Create Date: 2026-04-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '9f2b7c1d4e6a'
down_revision: Union[str, Sequence[str], None] = '8c4382cc8efb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Keep only one active attempt per (user_id, test_id) before creating partial unique index.
    op.execute(
        """
        WITH ranked AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY user_id, test_id
                    ORDER BY started_at DESC, id DESC
                ) AS rn
            FROM test_attempts
            WHERE finished_at IS NULL
        )
        UPDATE test_attempts AS ta
        SET finished_at = NOW()
        FROM ranked AS r
        WHERE ta.id = r.id
          AND r.rn > 1;
        """
    )

    # Remove duplicate tokens before adding uniqueness.
    op.execute(
        """
        DELETE FROM refresh_tokens AS a
        USING refresh_tokens AS b
        WHERE a.token = b.token
          AND a.id > b.id;
        """
    )

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_test_attempt_active_user_test
        ON test_attempts (user_id, test_id)
        WHERE finished_at IS NULL;
        """
    )

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_refresh_tokens_token
        ON refresh_tokens (token);
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS uq_refresh_tokens_token;")
    op.execute("DROP INDEX IF EXISTS uq_test_attempt_active_user_test;")
