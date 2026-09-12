import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy import delete, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db import get_db
from app.models.auth import AuthOwner, AuthSession

bearer = HTTPBearer(auto_error=False)
password_hash = PasswordHash.recommended()
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc"
SESSION_TTL = timedelta(hours=12)


def session_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(db: Session, username: str, password: str) -> str:
    try:
        owner = db.get(AuthOwner, 1)
        candidate_hash = (
            owner.password_hash
            if owner and owner.username == username.lower()
            else DUMMY_HASH
        )
        if (
            not password_hash.verify(password, candidate_hash)
            or not owner
            or owner.username != username.lower()
        ):
            raise AppError(401, "UNAUTHORIZED", "Invalid credentials")

        now = datetime.now(timezone.utc)
        db.execute(delete(AuthSession).where(AuthSession.expires_at <= now))
        token = secrets.token_urlsafe(32)
        db.add(
            AuthSession(token_hash=session_digest(token), expires_at=now + SESSION_TTL)
        )
        db.commit()
        return token
    except SQLAlchemyError as error:
        db.rollback()
        raise AppError(503, "DATABASE_UNAVAILABLE", "Database is unavailable") from error


def revoke_session(db: Session, token: str) -> None:
    if token:
        try:
            db.execute(
                delete(AuthSession).where(
                    AuthSession.token_hash == session_digest(token)
                )
            )
            db.commit()
        except SQLAlchemyError as error:
            db.rollback()
            raise AppError(503, "DATABASE_UNAVAILABLE", "Database is unavailable") from error


def require_session(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    token = credentials.credentials if credentials else ""
    _validate_session(db, token)


def require_snapshot_session(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    if db.get_bind().dialect.name == "postgresql":
        db.connection(execution_options={"isolation_level": "REPEATABLE READ"})
        db.execute(text("SET TRANSACTION READ ONLY"))
    _validate_session(db, credentials.credentials if credentials else "")


def _validate_session(db: Session, token: str) -> None:
    if len(token) != 43:
        raise AppError(401, "UNAUTHORIZED", "Invalid credentials")
    try:
        session = db.scalar(
            select(AuthSession).where(
                AuthSession.token_hash == session_digest(token),
                AuthSession.expires_at > datetime.now(timezone.utc),
            )
        )
    except SQLAlchemyError as error:
        raise AppError(503, "DATABASE_UNAVAILABLE", "Database is unavailable") from error
    if session is None:
        raise AppError(401, "UNAUTHORIZED", "Invalid credentials")
