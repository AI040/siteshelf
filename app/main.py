"""FastAPI application factory.

Run:  uvicorn app.main:app --reload
Docs: http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import health, upload
from app.core.config import get_settings
from app.core.database import get_engine
from app.core.exceptions import AppError
from app.core.init_db import init_db
from app.core.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(get_settings().log_level)
    init_db()
    yield
    get_engine().dispose()


def create_app() -> FastAPI:
    app = FastAPI(title=get_settings().app_name, version="1.0.0", lifespan=lifespan)

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    app.include_router(health.router)
    app.include_router(upload.router, prefix="/api/v1")
    return app


app = create_app()
