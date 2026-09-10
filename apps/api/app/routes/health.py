from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.auth import require_personal_token
from app.core.errors import AppError
from app.core.time import today_bangkok
from app.db import get_db
from app.models.health import WeightLog, Workout
from app.schemas.health import (
    ActivityType,
    ListResponse,
    WeightLogPut,
    WeightLogResponse,
    WorkoutCreate,
    WorkoutPatch,
    WorkoutResponse,
)
from app.services import health

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_personal_token)])
Db = Annotated[Session, Depends(get_db)]
PageLimit = Annotated[int, Query(ge=1, le=200)]
PageOffset = Annotated[int, Query(ge=0)]


def date_filters(column, from_date: date | None, to_date: date | None):
    if from_date and to_date and from_date > to_date:
        raise AppError(422, "INVALID_DATE_RANGE", "From date cannot be after to date")
    filters = []
    if from_date:
        filters.append(column >= from_date)
    if to_date:
        filters.append(column <= to_date)
    return filters


@router.get("/weight-logs", response_model=ListResponse[WeightLogResponse])
def weight_logs(
    db: Db,
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: date | None = None,
    limit: PageLimit = 50,
    offset: PageOffset = 0,
):
    items, total = health.list_weight_logs(db, date_filters(WeightLog.log_date, from_, to), limit, offset)
    return ListResponse[WeightLogResponse](items=items, total=total, limit=limit, offset=offset)


@router.put("/weight-logs/{log_date}", response_model=WeightLogResponse)
def put_weight_log(log_date: date, data: WeightLogPut, db: Db):
    if log_date > today_bangkok():
        raise AppError(422, "FUTURE_DATE", "Weight log date cannot be in the future")
    return health.put_weight_log(db, log_date, data)


@router.get("/weight-logs/{log_date}", response_model=WeightLogResponse)
def weight_log(log_date: date, db: Db):
    return health.get_weight_log(db, log_date)


@router.delete("/weight-logs/{log_date}", status_code=status.HTTP_204_NO_CONTENT)
def delete_weight_log(log_date: date, db: Db) -> Response:
    health.delete_weight_log(db, log_date)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/workouts", response_model=ListResponse[WorkoutResponse])
def workouts(
    db: Db,
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: date | None = None,
    activity_type: ActivityType | None = None,
    limit: PageLimit = 50,
    offset: PageOffset = 0,
):
    filters = date_filters(Workout.occurred_on, from_, to)
    if activity_type:
        filters.append(Workout.activity_type == activity_type)
    items, total = health.list_workouts(db, filters, limit, offset)
    return ListResponse[WorkoutResponse](items=items, total=total, limit=limit, offset=offset)


@router.post("/workouts", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
def create_workout(data: WorkoutCreate, db: Db):
    return health.create_workout(db, data)


@router.get("/workouts/{workout_id}", response_model=WorkoutResponse)
def workout(workout_id: UUID, db: Db):
    return health.get_workout(db, workout_id)


@router.patch("/workouts/{workout_id}", response_model=WorkoutResponse)
def update_workout(workout_id: UUID, data: WorkoutPatch, db: Db):
    return health.update_workout(db, workout_id, data)


@router.delete("/workouts/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(workout_id: UUID, db: Db) -> Response:
    health.delete_workout(db, workout_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
