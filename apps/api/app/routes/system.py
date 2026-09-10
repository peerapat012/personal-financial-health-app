from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.auth import require_personal_token
from app.schemas.system import HealthResponse, SessionResponse

router = APIRouter()


@router.get("/healthz", response_model=HealthResponse, include_in_schema=False)
def healthcheck() -> HealthResponse:
    return HealthResponse()


@router.get("/api/v1/session", response_model=SessionResponse)
def session(_: Annotated[None, Depends(require_personal_token)]) -> SessionResponse:
    return SessionResponse()
