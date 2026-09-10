import logging
from collections.abc import Mapping
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        fields: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.fields = dict(fields) if fields else None


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    fields: Mapping[str, str] | None = None,
) -> JSONResponse:
    error: dict[str, Any] = {
        "code": code,
        "message": message,
        "request_id": request.state.request_id,
    }
    if fields:
        error["fields"] = fields
    return JSONResponse(status_code=status_code, content={"error": error})


def register_error_handlers(app: FastAPI) -> None:
    @app.middleware("http")
    async def add_request_id(request: Request, call_next: Any):
        request.state.request_id = str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return error_response(
            request, exc.status_code, exc.code, exc.message, exc.fields
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        fields = {
            str(error["loc"][-1]): str(error["msg"])
            for error in exc.errors()
            if error["loc"]
        }
        return error_response(
            request, 422, "VALIDATION_ERROR", "Request is invalid", fields
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(
            "Unhandled request error",
            extra={"request_id": request.state.request_id},
        )
        return error_response(
            request, 500, "INTERNAL_ERROR", "Unexpected server error"
        )
