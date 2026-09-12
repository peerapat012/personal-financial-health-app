import hashlib
import hmac
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.better_auth import verify_session

bearer = HTTPBearer(auto_error=False)


def require_personal_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    supplied = credentials.credentials if credentials else ""
    if settings.auth_mode == "better_auth":
        verify_session(settings, supplied)
        return
    digest = hashlib.sha256(supplied.encode()).hexdigest()
    if not supplied or not hmac.compare_digest(digest, settings.personal_api_token_sha256 or ""):
        raise AppError(401, "UNAUTHORIZED", "Invalid credentials")
