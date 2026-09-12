from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.time import today_bangkok
from app.models.finance import Account
from app.models.goals import FinancialGoal, HealthGoal
from app.schemas.goals import FinancialGoalCreate, FinancialGoalResponse, GoalPatch, HealthGoalCreate, HealthGoalResponse
from app.services.finance import get_account
from app.services.health import get_health_summary

Goal = FinancialGoal | HealthGoal
GoalModel = type[FinancialGoal] | type[HealthGoal]


def progress(baseline: Decimal, target: Decimal, current: Decimal | None) -> dict:
    if current is None:
        return {"progress_ratio": None, "progress_percent": None, "achieved": False}
    ratio = (current - baseline) / (target - baseline)
    return {
        "progress_ratio": ratio,
        "progress_percent": min(Decimal(1), max(Decimal(0), ratio)) * 100,
        "achieved": ratio >= 1,
    }


def _response(db: Session, item: Goal):
    values = {column.name: getattr(item, column.name) for column in item.__table__.columns}
    if isinstance(item, FinancialGoal):
        account = get_account(db, item.account_id)
        return FinancialGoalResponse(
            **values, account_name=account.name, current_amount=account.current_balance,
            **progress(item.baseline_amount, item.target_amount, account.current_balance),
        )
    summary = get_health_summary(db, item.start_date, today_bangkok())
    return HealthGoalResponse(
        **values, current_weight_kg=summary.latest_weight_kg, current_weight_date=summary.latest_weight_date,
        **progress(item.baseline_weight_kg, item.target_weight_kg, summary.latest_weight_kg),
    )


def _get(db: Session, model: GoalModel, goal_id: UUID) -> Goal:
    item = db.get(model, goal_id)
    if item is None:
        raise AppError(404, "NOT_FOUND", "Goal not found")
    return item


def _commit(db: Session):
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise AppError(409, "CONFLICT", "Goal conflicts with existing data") from error


def get_goal(db: Session, model: GoalModel, goal_id: UUID):
    return _response(db, _get(db, model, goal_id))


def list_goals(db: Session, model: GoalModel, include_archived: bool, limit: int | None, offset: int):
    filters = [] if include_archived else [model.archived_at.is_(None)]
    total = db.scalar(select(func.count()).select_from(model).where(*filters)) or 0
    items = db.scalars(select(model).where(*filters).order_by(model.created_at.desc(), model.id.desc()).limit(limit).offset(offset))
    # ponytail: a few personal goals reuse existing summaries per row; batch queries if goal counts make this slow.
    return [_response(db, item) for item in items], total


def create_goal(db: Session, data: FinancialGoalCreate | HealthGoalCreate):
    model = FinancialGoal if isinstance(data, FinancialGoalCreate) else HealthGoal
    existing = db.get(model, data.id)
    if existing is not None:
        if all(getattr(existing, field) == value for field, value in data.model_dump().items()):
            return _response(db, existing)
        raise AppError(409, "CONFLICT", "Goal ID is already in use")
    if isinstance(data, FinancialGoalCreate) and db.get(Account, data.account_id) is None:
        raise AppError(422, "INVALID_ACCOUNT", "Account does not exist", {"account_id": "Select an existing account"})
    item = model(**data.model_dump())
    db.add(item)
    _commit(db)
    return _response(db, item)


def update_goal(db: Session, model: GoalModel, goal_id: UUID, data: GoalPatch):
    item = _get(db, model, goal_id)
    changes = data.model_dump(exclude_unset=True)
    due_date = changes.get("due_date", item.due_date)
    if due_date is not None and due_date < item.start_date:
        raise AppError(422, "INVALID_DATE_RANGE", "Due date cannot precede start date", {"due_date": "Must be on or after start date"})
    for field, value in changes.items():
        if field == "archived":
            item.archived_at = datetime.now(timezone.utc) if value else None
        else:
            setattr(item, field, value)
    _commit(db)
    return _response(db, item)


def delete_goal(db: Session, model: GoalModel, goal_id: UUID):
    db.delete(_get(db, model, goal_id))
    _commit(db)
