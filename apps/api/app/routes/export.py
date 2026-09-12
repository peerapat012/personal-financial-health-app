from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.auth import require_snapshot_session
from app.core.errors import AppError
from app.db import get_db
from app.services.export import get_export

router = APIRouter(
    prefix="/api/v1", dependencies=[Depends(require_snapshot_session)]
)


@router.get("/export")
def export_data(db: Annotated[Session, Depends(get_db)]):
    try:
        return get_export(db)
    except SQLAlchemyError as error:
        db.rollback()
        raise AppError(
            503, "DATABASE_UNAVAILABLE", "Export is temporarily unavailable"
        ) from error
