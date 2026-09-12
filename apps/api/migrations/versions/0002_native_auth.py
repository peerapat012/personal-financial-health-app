"""Replace Better Auth with native owner credentials and sessions.

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auth_owner",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=30), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("id = 1", name="auth_owner_singleton_check"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "auth_sessions",
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("token_hash"),
    )
    op.create_index("auth_sessions_expires_at_idx", "auth_sessions", ["expires_at"])
    op.execute("DROP TABLE IF EXISTS auth_verification CASCADE")
    op.execute("DROP TABLE IF EXISTS auth_session CASCADE")
    op.execute("DROP TABLE IF EXISTS auth_account CASCADE")
    op.execute("DROP TABLE IF EXISTS auth_user CASCADE")


def downgrade() -> None:
    op.drop_index("auth_sessions_expires_at_idx", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_table("auth_owner")
