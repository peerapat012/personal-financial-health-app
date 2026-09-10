import re
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from app.core.time import today_bangkok

ActivityType = Literal["walk", "run", "cycle", "strength", "other"]


def not_future(value: date) -> date:
    if value > today_bangkok():
        raise ValueError("Date cannot be in the future")
    return value


def parse_weight(value: object) -> object:
    if isinstance(value, Decimal):
        return value
    if not isinstance(value, str) or not re.fullmatch(r"\d+(?:\.\d{1,2})?", value):
        raise ValueError("Weight must be a plain decimal string with at most two decimal places")
    return value


def clean_note(value: object) -> object:
    if isinstance(value, str):
        return value.strip() or None
    return value


PastDate = Annotated[date, AfterValidator(not_future)]
Weight = Annotated[Decimal, BeforeValidator(parse_weight), Field(ge=1, le=500, max_digits=5, decimal_places=2)]
Note = Annotated[str, BeforeValidator(clean_note), Field(max_length=2000)]


class WireModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class WeightLogPut(WireModel):
    weight_kg: Weight | None = None
    note: Note | None = None

    @model_validator(mode="after")
    def require_content(self) -> "WeightLogPut":
        if self.weight_kg is None and not self.note:
            raise ValueError("Weight or a non-empty note is required")
        return self


class WeightLogResponse(WireModel):
    id: UUID
    log_date: date
    weight_kg: Decimal | None
    note: str | None
    created_at: datetime
    updated_at: datetime


class WorkoutCreate(WireModel):
    id: UUID
    occurred_on: PastDate
    activity_type: ActivityType
    duration_minutes: Annotated[int, Field(ge=1, le=1440)]
    note: Note | None = None


class WorkoutPatch(WireModel):
    occurred_on: PastDate | None = None
    activity_type: ActivityType | None = None
    duration_minutes: Annotated[int, Field(ge=1, le=1440)] | None = None
    note: Note | None = None

    @model_validator(mode="after")
    def require_change(self) -> "WorkoutPatch":
        if not self.model_fields_set:
            raise ValueError("At least one field is required")
        required = {"occurred_on", "activity_type", "duration_minutes"}
        if any(getattr(self, field) is None for field in self.model_fields_set & required):
            raise ValueError("Required workout fields cannot be null")
        return self


class WorkoutResponse(WireModel):
    id: UUID
    occurred_on: date
    activity_type: ActivityType
    duration_minutes: int
    note: str | None
    created_at: datetime
    updated_at: datetime


T = TypeVar("T")


class ListResponse(WireModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


class HealthSummaryResponse(WireModel):
    from_date: date
    to_date: date
    latest_weight_kg: Decimal | None
    latest_weight_date: date | None
    average_weight_kg: Decimal | None
    recorded_weight_days: int
    workout_minutes: int
