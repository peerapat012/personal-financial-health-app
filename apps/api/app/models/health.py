from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, Index, Integer, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class WeightLog(TimestampMixin, Base):
    __tablename__ = "weight_logs"
    __table_args__ = (
        CheckConstraint(
            "weight_kg IS NULL OR weight_kg BETWEEN 1 AND 500",
            name="weight_logs_weight_check",
        ),
        CheckConstraint(
            "weight_kg IS NOT NULL OR NULLIF(btrim(note), '') IS NOT NULL",
            name="weight_logs_content_check",
        ),
        CheckConstraint(
            "note IS NULL OR char_length(note) <= 2000",
            name="weight_logs_note_length_check",
        ),
        UniqueConstraint("log_date", name="weight_logs_log_date_key"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    note: Mapped[str | None] = mapped_column(Text)


class Workout(TimestampMixin, Base):
    __tablename__ = "workouts"
    __table_args__ = (
        CheckConstraint(
            "activity_type IN ('walk', 'run', 'cycle', 'strength', 'other')",
            name="workouts_activity_type_check",
        ),
        CheckConstraint(
            "duration_minutes BETWEEN 1 AND 1440",
            name="workouts_duration_check",
        ),
        CheckConstraint(
            "note IS NULL OR char_length(note) <= 2000",
            name="workouts_note_length_check",
        ),
        Index("workouts_occurred_id_idx", "occurred_on", "id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    activity_type: Mapped[str] = mapped_column(String(16), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
