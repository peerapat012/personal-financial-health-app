from datetime import date
from decimal import Decimal
from uuid import UUID

from app.schemas.finance import AccountResponse, FinanceSummaryResponse, TransactionResponse, WireModel
from app.schemas.goals import FinancialGoalResponse, HealthGoalResponse


class AccountBalances(WireModel):
    as_of: date
    total: Decimal
    items: list[AccountResponse]


class BudgetActual(WireModel):
    id: UUID
    category_id: UUID
    category_name: str
    amount: Decimal
    actual: Decimal
    remaining: Decimal


class WeightPoint(WireModel):
    date: date
    weight_kg: Decimal | None


class DashboardHealth(WireModel):
    latest_weight_kg: Decimal | None
    latest_weight_date: date | None
    workout_minutes: int
    recorded_weight_days: int
    average_weight_kg: Decimal | None
    weight_trend: list[WeightPoint]


class DashboardResponse(WireModel):
    month: str
    account_balances: AccountBalances
    finance: FinanceSummaryResponse
    budgets: list[BudgetActual]
    health: DashboardHealth
    goals: list[FinancialGoalResponse | HealthGoalResponse]
    recent_transactions: list[TransactionResponse]
