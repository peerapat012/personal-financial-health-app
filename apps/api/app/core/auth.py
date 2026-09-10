import hashlib
import hmac
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.core.errors import AppError

bearer = HTTPBearer(auto_error=False)


def require_personal_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    supplied = credentials.credentials if credentials else ""
    digest = hashlib.sha256(supplied.encode()).hexdigest()
    if not hmac.compare_digest(digest, settings.personal_api_token_sha256):
        raise AppError(401, "UNAUTHORIZED", "Invalid credentials")
