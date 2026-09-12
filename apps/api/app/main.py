from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import get_http_settings
from app.core.errors import register_error_handlers
from app.core.request_size import RequestSizeLimitMiddleware
from app.routes.finance import router as finance_router
from app.routes.health import router as health_router
from app.routes.goals import router as goals_router
from app.routes.dashboard import router as dashboard_router
from app.routes.auth import router as auth_router
from app.routes.export import router as export_router
from app.routes.system import router as system_router


def create_app() -> FastAPI:
    http = get_http_settings()
    app = FastAPI(title="Personal Financial Health API", version="0.1.0")
    app.add_middleware(RequestSizeLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            origin.strip()
            for origin in http.cors_origins.split(",")
        ],
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Accept", "Authorization", "Content-Type"],
    )
    if http.app_env == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=[host.strip() for host in http.allowed_hosts.split(",")],
        )
        app.add_middleware(HTTPSRedirectMiddleware)
    register_error_handlers(app)
    app.include_router(system_router)
    app.include_router(finance_router)
    app.include_router(health_router)
    app.include_router(goals_router)
    app.include_router(dashboard_router)
    app.include_router(auth_router)
    app.include_router(export_router)
    return app


app = create_app()
