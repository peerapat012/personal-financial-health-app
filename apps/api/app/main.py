from fastapi import FastAPI

from app.core.errors import register_error_handlers
from app.routes.system import router as system_router


def create_app() -> FastAPI:
    app = FastAPI(title="Personal Financial Health API", version="0.1.0")
    register_error_handlers(app)
    app.include_router(system_router)
    return app


app = create_app()
