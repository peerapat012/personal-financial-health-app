from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.finance import Account, Budget, Category, Transaction
from app.models.goals import FinancialGoal, HealthGoal
from app.models.health import WeightLog, Workout

TABLES = (
    Account,
    Category,
    Transaction,
    Budget,
    WeightLog,
    Workout,
    FinancialGoal,
    HealthGoal,
)


def _wire(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def get_export(db: Session) -> dict:
    data = {}
    for model in TABLES:
        rows = db.scalars(select(model).order_by(*model.__table__.primary_key.columns))
        data[model.__tablename__] = [
            {column.name: _wire(getattr(row, column.name)) for column in model.__table__.columns}
            for row in rows
        ]
    return {
        "schema_version": "1",
        "exported_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "data": data,
    }
