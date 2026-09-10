from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class FinancialGoal(TimestampMixin, Base):
    __tablename__ = "financial_goals"
    __table_args__ = (
        CheckConstraint(
            "char_length(btrim(name)) BETWEEN 1 AND 100",
            name="financial_goals_name_length_check",
        ),
        CheckConstraint(
            "target_amount > baseline_amount",
            name="financial_goals_target_check",
        ),
        CheckConstraint(
            "due_date IS NULL OR due_date >= start_date",
            name="financial_goals_due_date_check",
        ),
        Index("financial_goals_account_idx", "account_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    account_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False
    )
    baseline_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class HealthGoal(TimestampMixin, Base):
    __tablename__ = "health_goals"
    __table_args__ = (
        CheckConstraint(
            "char_length(btrim(name)) BETWEEN 1 AND 100",
            name="health_goals_name_length_check",
        ),
        CheckConstraint(
            "baseline_weight_kg BETWEEN 1 AND 500",
            name="health_goals_baseline_weight_check",
        ),
        CheckConstraint(
            "target_weight_kg BETWEEN 1 AND 500 "
            "AND target_weight_kg <> baseline_weight_kg",
            name="health_goals_target_weight_check",
        ),
        CheckConstraint(
            "due_date IS NULL OR due_date >= start_date",
            name="health_goals_due_date_check",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    baseline_weight_kg: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    target_weight_kg: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
