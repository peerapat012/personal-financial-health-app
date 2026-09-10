"""Create V1 schema.

Revision ID: 0001
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("opening_balance", sa.Numeric(14, 2), nullable=False),
        sa.Column("opening_date", sa.Date(), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "kind IN ('cash', 'bank', 'ewallet')", name="accounts_kind_check"
        ),
        sa.CheckConstraint(
            "char_length(btrim(name)) BETWEEN 1 AND 100",
            name="accounts_name_length_check",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="accounts_name_key"),
    )
    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "kind IN ('income', 'expense')", name="categories_kind_check"
        ),
        sa.CheckConstraint(
            "char_length(btrim(name)) BETWEEN 1 AND 100",
            name="categories_name_length_check",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("kind", "name", name="categories_kind_name_key"),
        sa.UniqueConstraint("id", "kind", name="categories_id_kind_key"),
    )
    op.create_table(
        "weight_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("weight_kg", sa.Numeric(5, 2), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "weight_kg IS NULL OR weight_kg BETWEEN 1 AND 500",
            name="weight_logs_weight_check",
        ),
        sa.CheckConstraint(
            "weight_kg IS NOT NULL OR NULLIF(btrim(note), '') IS NOT NULL",
            name="weight_logs_content_check",
        ),
        sa.CheckConstraint(
            "note IS NULL OR char_length(note) <= 2000",
            name="weight_logs_note_length_check",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("log_date", name="weight_logs_log_date_key"),
    )
    op.create_table(
        "workouts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("activity_type", sa.String(length=16), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "activity_type IN ('walk', 'run', 'cycle', 'strength', 'other')",
            name="workouts_activity_type_check",
        ),
        sa.CheckConstraint(
            "duration_minutes BETWEEN 1 AND 1440",
            name="workouts_duration_check",
        ),
        sa.CheckConstraint(
            "note IS NULL OR char_length(note) <= 2000",
            name="workouts_note_length_check",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "workouts_occurred_id_idx", "workouts", ["occurred_on", "id"]
    )
    op.create_table(
        "financial_goals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("baseline_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("target_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "char_length(btrim(name)) BETWEEN 1 AND 100",
            name="financial_goals_name_length_check",
        ),
        sa.CheckConstraint(
            "target_amount > baseline_amount",
            name="financial_goals_target_check",
        ),
        sa.CheckConstraint(
            "due_date IS NULL OR due_date >= start_date",
            name="financial_goals_due_date_check",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["accounts.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "financial_goals_account_idx", "financial_goals", ["account_id"]
    )
    op.create_table(
        "health_goals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("baseline_weight_kg", sa.Numeric(5, 2), nullable=False),
        sa.Column("target_weight_kg", sa.Numeric(5, 2), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "char_length(btrim(name)) BETWEEN 1 AND 100",
            name="health_goals_name_length_check",
        ),
        sa.CheckConstraint(
            "baseline_weight_kg BETWEEN 1 AND 500",
            name="health_goals_baseline_weight_check",
        ),
        sa.CheckConstraint(
            "target_weight_kg BETWEEN 1 AND 500 "
            "AND target_weight_kg <> baseline_weight_kg",
            name="health_goals_target_weight_check",
        ),
        sa.CheckConstraint(
            "due_date IS NULL OR due_date >= start_date",
            name="health_goals_due_date_check",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("to_account_id", sa.Uuid(), nullable=True),
        sa.Column("category_id", sa.Uuid(), nullable=True),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "kind IN ('income', 'expense', 'transfer')",
            name="transactions_kind_check",
        ),
        sa.CheckConstraint("amount > 0", name="transactions_amount_check"),
        sa.CheckConstraint(
            "(kind = 'transfer' AND to_account_id IS NOT NULL "
            "AND to_account_id <> account_id AND category_id IS NULL) OR "
            "(kind IN ('income', 'expense') AND to_account_id IS NULL "
            "AND category_id IS NOT NULL)",
            name="transactions_shape_check",
        ),
        sa.CheckConstraint(
            "note IS NULL OR char_length(note) <= 2000",
            name="transactions_note_length_check",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["accounts.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["to_account_id"], ["accounts.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["category_id", "kind"],
            ["categories.id", "categories.kind"],
            name="transactions_category_kind_fkey",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "transactions_occurred_id_idx", "transactions", ["occurred_on", "id"]
    )
    op.create_index(
        "transactions_account_occurred_idx",
        "transactions",
        ["account_id", "occurred_on"],
    )
    op.create_index(
        "transactions_to_account_occurred_idx",
        "transactions",
        ["to_account_id", "occurred_on"],
        postgresql_where=sa.text("to_account_id IS NOT NULL"),
    )
    op.create_index(
        "transactions_category_occurred_idx",
        "transactions",
        ["category_id", "occurred_on"],
    )
    op.create_table(
        "budgets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        *timestamps(),
        sa.CheckConstraint("amount > 0", name="budgets_amount_check"),
        sa.CheckConstraint(
            "EXTRACT(DAY FROM month) = 1",
            name="budgets_month_start_check",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "category_id", "month", name="budgets_category_month_key"
        ),
    )
    op.create_index(
        "budgets_month_category_idx", "budgets", ["month", "category_id"]
    )

    categories = sa.table(
        "categories",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.Text()),
        sa.column("kind", sa.String()),
    )
    op.bulk_insert(
        categories,
        [
            {"id": "00000000-0000-4000-8000-000000000001", "name": "Salary", "kind": "income"},
            {"id": "00000000-0000-4000-8000-000000000002", "name": "Other", "kind": "income"},
            {"id": "00000000-0000-4000-8000-000000000101", "name": "Food", "kind": "expense"},
            {"id": "00000000-0000-4000-8000-000000000102", "name": "Transport", "kind": "expense"},
            {"id": "00000000-0000-4000-8000-000000000103", "name": "Housing", "kind": "expense"},
            {"id": "00000000-0000-4000-8000-000000000104", "name": "Health", "kind": "expense"},
            {"id": "00000000-0000-4000-8000-000000000105", "name": "Other", "kind": "expense"},
        ],
    )


def downgrade() -> None:
    op.drop_index("budgets_month_category_idx", table_name="budgets")
    op.drop_table("budgets")
    op.drop_index("transactions_category_occurred_idx", table_name="transactions")
    op.drop_index("transactions_to_account_occurred_idx", table_name="transactions")
    op.drop_index("transactions_account_occurred_idx", table_name="transactions")
    op.drop_index("transactions_occurred_id_idx", table_name="transactions")
    op.drop_table("transactions")
    op.drop_table("health_goals")
    op.drop_index("financial_goals_account_idx", table_name="financial_goals")
    op.drop_table("financial_goals")
    op.drop_index("workouts_occurred_id_idx", table_name="workouts")
    op.drop_table("workouts")
    op.drop_table("weight_logs")
    op.drop_table("categories")
    op.drop_table("accounts")
