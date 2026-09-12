import json
from datetime import datetime, timezone
from http.client import HTTPConnection, HTTPSConnection, HTTPException
from urllib.parse import urlsplit

from app.core.config import Settings
from app.core.errors import AppError


def auth_request(settings: Settings, path: str, token: str = "", body: dict | None = None):
    parsed = urlsplit(settings.better_auth_url or "")
    connection = (HTTPSConnection if parsed.scheme == "https" else HTTPConnection)(parsed.hostname, parsed.port, timeout=5)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        connection.request("POST" if body is not None else "GET", f"{parsed.path.rstrip('/')}/api/auth/{path}", body=json.dumps(body) if body is not None else None, headers=headers)
        response = connection.getresponse()
        if response.status == 429:
            raise AppError(429, "RATE_LIMITED", "Too many sign-in attempts. Try again later.")
        if response.status in {400, 401, 403}:
            raise AppError(401, "UNAUTHORIZED", "Invalid credentials")
        if response.status != 200:
            raise AppError(503, "AUTH_UNAVAILABLE", "Sign-in service is unavailable")
        # Bound the untrusted upstream response; credentials are never logged or persisted here.
        payload = response.read(1_048_577)
        if len(payload) > 1_048_576:
            raise ValueError("Response too large")
        return json.loads(payload)
    except (OSError, HTTPException, ValueError) as error:
        raise AppError(503, "AUTH_UNAVAILABLE", "Sign-in service is unavailable") from error
    finally:
        connection.close()


def verify_session(settings: Settings, token: str) -> None:
    if not token or len(token) > 4096 or any(ord(char) < 32 or ord(char) > 126 for char in token):
        raise AppError(401, "UNAUTHORIZED", "Invalid credentials")
    data = auth_request(settings, "get-session?disableCookieCache=true", token)
    try:
        user_id = data["user"]["id"]
        session = data["session"]
        expires = datetime.fromisoformat(session["expiresAt"].replace("Z", "+00:00"))
        valid = user_id == settings.owner_user_id and session["userId"] == user_id and expires > datetime.now(timezone.utc)
    except (KeyError, TypeError, ValueError, AttributeError):
        valid = False
    if not valid:
        raise AppError(401, "UNAUTHORIZED", "Invalid credentials")
