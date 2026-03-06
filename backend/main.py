"""FastAPI application entry point."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import modules, utils


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="iKy OSINT API", version="2.0.0")

    cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:4200").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Utils router first — its fixed routes (/tasklist, /state/...,
    # /result/..., /apikey, /testing) must not be captured by the
    # dynamic /{module} handler in the modules router.
    app.include_router(utils.router)
    app.include_router(modules.router)

    return app


app = create_app()
