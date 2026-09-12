from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.auth import require_session
from app.core.errors import AppError
from app.db import get_db
from app.schemas.dashboard import DashboardResponse
from app.schemas.finance import Month
from app.services.dashboard import get_dashboard

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_session)])


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(month: Annotated[Month, Query()], db: Annotated[Session, Depends(get_db)]):
    try:
        # Set isolation before the first query so every card sees the same committed snapshot.
        if db.get_bind().dialect.name == "postgresql":
            db.connection(execution_options={"isolation_level": "REPEATABLE READ"})
        return get_dashboard(db, month)
    except SQLAlchemyError as error:
        db.rollback()
        raise AppError(503, "DATABASE_UNAVAILABLE", "Dashboard is temporarily unavailable") from error
