from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import today_bangkok
from app.models.finance import Budget
from app.models.goals import FinancialGoal, HealthGoal
from app.models.health import WeightLog
from app.schemas.dashboard import AccountBalances, BudgetActual, DashboardHealth, DashboardResponse, WeightPoint
from app.services import finance, goals, health


def get_dashboard(db: Session, month: date) -> DashboardResponse:
    today = today_bangkok()
    end = date(month.year, month.month, monthrange(month.year, month.month)[1])
    accounts, _ = finance.list_accounts(db, True, None, 0)
    summary = finance.get_finance_summary(db, month)
    budgets, _ = finance.list_budgets(db, [Budget.month == month], None, 0)
    expenses = {row.category_id: row.amount for row in summary.expense_by_category}
    monthly_health = health.get_health_summary(db, month, end)
    latest = db.execute(select(WeightLog.log_date, WeightLog.weight_kg).where(
        WeightLog.log_date <= today, WeightLog.weight_kg.is_not(None),
    ).order_by(WeightLog.log_date.desc()).limit(1)).one_or_none()
    weights = dict(db.execute(select(WeightLog.log_date, WeightLog.weight_kg).where(
        WeightLog.log_date >= month, WeightLog.log_date <= min(end, today),
    )).all())
    financial_goals, _ = goals.list_goals(db, FinancialGoal, False, None, 0)
    health_goals, _ = goals.list_goals(db, HealthGoal, False, None, 0)
    recent, _ = finance.list_transactions(db, [], 5, 0)
    return DashboardResponse(
        month=month.strftime("%Y-%m"),
        account_balances=AccountBalances(as_of=today, total=sum((item.current_balance for item in accounts), Decimal("0.00")), items=accounts),
        finance=summary,
        budgets=[BudgetActual(
            id=item.id, category_id=item.category_id, category_name=item.category_name, amount=item.amount,
            actual=expenses.get(item.category_id, Decimal("0.00")),
            remaining=item.amount - expenses.get(item.category_id, Decimal("0.00")),
        ) for item in budgets],
        health=DashboardHealth(
            latest_weight_kg=latest[1] if latest else None, latest_weight_date=latest[0] if latest else None,
            workout_minutes=monthly_health.workout_minutes, recorded_weight_days=monthly_health.recorded_weight_days,
            average_weight_kg=monthly_health.average_weight_kg,
            weight_trend=[WeightPoint(date=day, weight_kg=weights.get(day)) for day in
                          (month + timedelta(days=index) for index in range(max(0, (min(end, today) - month).days + 1)))],
        ),
        goals=[*financial_goals, *health_goals], recent_transactions=recent,
    )
