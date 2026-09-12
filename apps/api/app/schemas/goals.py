from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import model_validator

from app.schemas.finance import Money, Name, PastDate, WireModel
from app.schemas.health import Weight


class GoalCreate(WireModel):
    id: UUID
    name: Name
    start_date: PastDate
    due_date: date | None = None

    @model_validator(mode="after")
    def date_order(self):
        if self.due_date is not None and self.due_date < self.start_date:
            raise ValueError("Due date cannot precede start date")
        return self


class FinancialGoalCreate(GoalCreate):
    account_id: UUID
    baseline_amount: Money
    target_amount: Money

    @model_validator(mode="after")
    def target_order(self):
        if self.target_amount <= self.baseline_amount:
            raise ValueError("Target amount must be greater than baseline")
        return self


class HealthGoalCreate(GoalCreate):
    baseline_weight_kg: Weight
    target_weight_kg: Weight

    @model_validator(mode="after")
    def different_target(self):
        if self.target_weight_kg == self.baseline_weight_kg:
            raise ValueError("Target weight must differ from baseline")
        return self


class GoalPatch(WireModel):
    name: Name | None = None
    due_date: date | None = None
    archived: bool | None = None

    @model_validator(mode="after")
    def require_change(self):
        if not self.model_fields_set:
            raise ValueError("At least one field is required")
        if any(getattr(self, field) is None for field in self.model_fields_set & {"name", "archived"}):
            raise ValueError("Name and archived cannot be null")
        return self


class GoalResponse(WireModel):
    id: UUID
    name: str
    start_date: date
    due_date: date | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime
    progress_ratio: Decimal | None
    progress_percent: Decimal | None
    achieved: bool


class FinancialGoalResponse(GoalResponse):
    account_id: UUID
    account_name: str
    baseline_amount: Decimal
    target_amount: Decimal
    current_amount: Decimal


class HealthGoalResponse(GoalResponse):
    baseline_weight_kg: Decimal
    target_weight_kg: Decimal
    current_weight_kg: Decimal | None
    current_weight_date: date | None
