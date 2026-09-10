from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Account(TimestampMixin, Base):
    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("kind IN ('cash', 'bank', 'ewallet')", name="accounts_kind_check"),
        CheckConstraint(
            "char_length(btrim(name)) BETWEEN 1 AND 100",
            name="accounts_name_length_check",
        ),
        UniqueConstraint("name", name="accounts_name_key"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    opening_date: Mapped[date] = mapped_column(Date, nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Category(TimestampMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint("kind IN ('income', 'expense')", name="categories_kind_check"),
        CheckConstraint(
            "char_length(btrim(name)) BETWEEN 1 AND 100",
            name="categories_name_length_check",
        ),
        UniqueConstraint("kind", "name", name="categories_kind_name_key"),
        UniqueConstraint("id", "kind", name="categories_id_kind_key"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Transaction(TimestampMixin, Base):
    __tablename__ = "transactions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["category_id", "kind"],
            ["categories.id", "categories.kind"],
            name="transactions_category_kind_fkey",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "kind IN ('income', 'expense', 'transfer')",
            name="transactions_kind_check",
        ),
        CheckConstraint("amount > 0", name="transactions_amount_check"),
        CheckConstraint(
            "(kind = 'transfer' AND to_account_id IS NOT NULL "
            "AND to_account_id <> account_id AND category_id IS NULL) OR "
            "(kind IN ('income', 'expense') AND to_account_id IS NULL "
            "AND category_id IS NOT NULL)",
            name="transactions_shape_check",
        ),
        CheckConstraint(
            "note IS NULL OR char_length(note) <= 2000",
            name="transactions_note_length_check",
        ),
        Index("transactions_occurred_id_idx", "occurred_on", "id"),
        Index("transactions_account_occurred_idx", "account_id", "occurred_on"),
        Index(
            "transactions_to_account_occurred_idx",
            "to_account_id",
            "occurred_on",
            postgresql_where=text("to_account_id IS NOT NULL"),
        ),
        Index("transactions_category_occurred_idx", "category_id", "occurred_on"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    account_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False
    )
    to_account_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("accounts.id", ondelete="RESTRICT")
    )
    category_id: Mapped[UUID | None] = mapped_column(Uuid)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)


class Budget(TimestampMixin, Base):
    __tablename__ = "budgets"
    __table_args__ = (
        CheckConstraint("amount > 0", name="budgets_amount_check"),
        CheckConstraint(
            "EXTRACT(DAY FROM month) = 1",
            name="budgets_month_start_check",
        ),
        UniqueConstraint("category_id", "month", name="budgets_category_month_key"),
        Index("budgets_month_category_idx", "month", "category_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    category_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False
    )
    month: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
