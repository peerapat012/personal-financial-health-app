from collections.abc import Iterable
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.health import WeightLog, Workout
from app.schemas.health import (
    HealthSummaryResponse,
    WeightLogPut,
    WeightLogResponse,
    WorkoutCreate,
    WorkoutPatch,
    WorkoutResponse,
)


def _commit(db: Session, message: str) -> None:
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise AppError(409, "CONFLICT", message) from error


def list_weight_logs(db: Session, filters: list, limit: int, offset: int):
    total = db.scalar(select(func.count()).select_from(WeightLog).where(*filters)) or 0
    items = list(db.scalars(select(WeightLog).where(*filters).order_by(WeightLog.log_date.desc()).limit(limit).offset(offset)))
    return [WeightLogResponse.model_validate(item) for item in items], total


def get_weight_log(db: Session, log_date: date) -> WeightLogResponse:
    item = db.scalar(select(WeightLog).where(WeightLog.log_date == log_date))
    if not item:
        raise AppError(404, "NOT_FOUND", "Weight log not found")
    return WeightLogResponse.model_validate(item)


def put_weight_log(db: Session, log_date: date, data: WeightLogPut) -> WeightLogResponse:
    statement = insert(WeightLog).values(id=uuid4(), log_date=log_date, **data.model_dump())
    statement = statement.on_conflict_do_update(
        index_elements=[WeightLog.log_date],
        set_={
            "weight_kg": statement.excluded.weight_kg,
            "note": statement.excluded.note,
            "updated_at": func.now(),
        },
    ).returning(WeightLog.id)
    try:
        item_id = db.scalar(statement)
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise AppError(409, "CONFLICT", "Weight log could not be saved") from error
    item = db.get(WeightLog, item_id)
    return WeightLogResponse.model_validate(item)


def delete_weight_log(db: Session, log_date: date) -> None:
    item = db.scalar(select(WeightLog).where(WeightLog.log_date == log_date))
    if not item:
        raise AppError(404, "NOT_FOUND", "Weight log not found")
    db.delete(item)
    _commit(db, "Weight log could not be deleted")


def list_workouts(db: Session, filters: list, limit: int, offset: int):
    total = db.scalar(select(func.count()).select_from(Workout).where(*filters)) or 0
    items = list(db.scalars(select(Workout).where(*filters).order_by(Workout.occurred_on.desc(), Workout.created_at.desc()).limit(limit).offset(offset)))
    return [WorkoutResponse.model_validate(item) for item in items], total


def get_workout(db: Session, workout_id: UUID) -> WorkoutResponse:
    item = db.get(Workout, workout_id)
    if not item:
        raise AppError(404, "NOT_FOUND", "Workout not found")
    return WorkoutResponse.model_validate(item)


def create_workout(db: Session, data: WorkoutCreate) -> WorkoutResponse:
    existing = db.get(Workout, data.id)
    if existing:
        if all(getattr(existing, field) == value for field, value in data.model_dump().items()):
            return WorkoutResponse.model_validate(existing)
        raise AppError(409, "CONFLICT", "Workout ID is already in use")
    item = Workout(**data.model_dump())
    db.add(item)
    _commit(db, "Workout conflicts with existing data")
    return WorkoutResponse.model_validate(item)


def update_workout(db: Session, workout_id: UUID, data: WorkoutPatch) -> WorkoutResponse:
    item = db.get(Workout, workout_id)
    if not item:
        raise AppError(404, "NOT_FOUND", "Workout not found")
    values = {column.name: getattr(item, column.name) for column in Workout.__table__.columns}
    values.update(data.model_dump(exclude_unset=True))
    complete = WorkoutCreate(**{field: values[field] for field in WorkoutCreate.model_fields})
    for field, value in complete.model_dump(exclude={"id"}).items():
        setattr(item, field, value)
    _commit(db, "Workout conflicts with existing data")
    return WorkoutResponse.model_validate(item)


def delete_workout(db: Session, workout_id: UUID) -> None:
    item = db.get(Workout, workout_id)
    if not item:
        raise AppError(404, "NOT_FOUND", "Workout not found")
    db.delete(item)
    _commit(db, "Workout could not be deleted")


def health_totals(
    weights: Iterable[tuple[date, Decimal | None]],
    workout_minutes: int,
    from_date: date,
    to_date: date,
) -> HealthSummaryResponse:
    recorded = [(log_date, value) for log_date, value in weights if value is not None]
    latest = max(recorded, default=None, key=lambda item: item[0])
    average = (
        (sum((value for _, value in recorded), Decimal("0")) / len(recorded)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if recorded
        else None
    )
    return HealthSummaryResponse(
        from_date=from_date,
        to_date=to_date,
        latest_weight_kg=latest[1] if latest else None,
        latest_weight_date=latest[0] if latest else None,
        average_weight_kg=average,
        recorded_weight_days=len(recorded),
        workout_minutes=workout_minutes,
    )


def get_health_summary(db: Session, from_date: date, to_date: date) -> HealthSummaryResponse:
    weights = db.execute(
        select(WeightLog.log_date, WeightLog.weight_kg).where(
            WeightLog.log_date >= from_date,
            WeightLog.log_date <= to_date,
        )
    ).all()
    workout_minutes = db.scalar(
        select(func.coalesce(func.sum(Workout.duration_minutes), 0)).where(
            Workout.occurred_on >= from_date,
            Workout.occurred_on <= to_date,
        )
    ) or 0
    return health_totals(weights, workout_minutes, from_date, to_date)
