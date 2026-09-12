from collections import deque
from threading import Lock
from time import monotonic
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import Field
from sqlalchemy.orm import Session

from app.core.auth import bearer, create_session, require_session, revoke_session
from app.core.errors import AppError
from app.db import get_db
from app.schemas.finance import WireModel

router = APIRouter(prefix="/api/v1/auth")
Db = Annotated[Session, Depends(get_db)]
attempts: deque[float] = deque()
attempts_lock = Lock()


class SignIn(WireModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_.]+$")
    password: str = Field(min_length=1, max_length=128)


class SignInResponse(WireModel):
    token: str


@router.post("/sign-in", response_model=SignInResponse)
def sign_in(data: SignIn, db: Db, response: Response):
    response.headers["Cache-Control"] = "no-store"
    now = monotonic()
    with attempts_lock:
        while attempts and attempts[0] <= now - 60:
            attempts.popleft()
        if len(attempts) >= 5:
            raise AppError(429, "RATE_LIMITED", "Too many sign-in attempts. Try again later.")
    try:
        token = create_session(db, data.username, data.password)
    except AppError as error:
        # ponytail: one API process uses a global limit; move attempts to the database before adding replicas.
        if error.status_code == 401:
            with attempts_lock:
                attempts.append(now)
        raise
    with attempts_lock:
        attempts.clear()
    return SignInResponse(token=token)


@router.post("/sign-out", status_code=204)
def sign_out(
    db: Db,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    _: Annotated[None, Depends(require_session)],
):
    token = credentials.credentials if credentials else ""
    revoke_session(db, token)
    return Response(status_code=204)
