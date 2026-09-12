from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_cors_origins
from app.core.errors import register_error_handlers
from app.routes.finance import router as finance_router
from app.routes.health import router as health_router
from app.routes.goals import router as goals_router
from app.routes.system import router as system_router


def create_app() -> FastAPI:
    app = FastAPI(title="Personal Financial Health API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            origin.strip()
            for origin in get_cors_origins().split(",")
        ],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    app.include_router(system_router)
    app.include_router(finance_router)
    app.include_router(health_router)
    app.include_router(goals_router)
    return app


app = create_app()
