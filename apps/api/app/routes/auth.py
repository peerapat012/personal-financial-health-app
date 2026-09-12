from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import Field

from app.core.auth import bearer
from app.core.better_auth import auth_request, verify_session
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.schemas.finance import WireModel

router = APIRouter(prefix="/api/v1/auth")
Config = Annotated[Settings, Depends(get_settings)]


class SignIn(WireModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_.]+$")
    password: str = Field(min_length=1, max_length=128)


class SignInResponse(WireModel):
    token: str


@router.get("/config")
def auth_config(settings: Config):
    return {"mode": settings.auth_mode}


@router.post("/sign-in", response_model=SignInResponse)
def sign_in(data: SignIn, settings: Config, response: Response):
    response.headers["Cache-Control"] = "no-store"
    if settings.auth_mode != "better_auth":
        raise AppError(404, "NOT_FOUND", "Username sign-in is not enabled")
    result = auth_request(settings, "sign-in/username", body=data.model_dump())
    token = result.get("token") if isinstance(result, dict) else None
    if not isinstance(token, str):
        raise AppError(503, "AUTH_UNAVAILABLE", "Sign-in service returned an invalid response")
    verify_session(settings, token)
    return SignInResponse(token=token)


@router.post("/sign-out", status_code=204)
def sign_out(settings: Config, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    token = credentials.credentials if credentials else ""
    if settings.auth_mode == "better_auth" and token:
        verify_session(settings, token)
        auth_request(settings, "sign-out", token=token, body={})
    return Response(status_code=204)
