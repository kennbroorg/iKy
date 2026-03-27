"""FastAPI application entry point."""

import os
import shutil
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import modules, utils


def _ensure_apikeys() -> None:
    """Copy apikeys_default.json → apikeys.json if it doesn't exist yet."""
    here = Path(__file__).resolve().parent
    api_keys_file = here / "factories" / "apikeys.json"
    api_keys_default = here / "factories" / "apikeys_default.json"
    if not api_keys_file.is_file() and api_keys_default.is_file():
        shutil.copy(api_keys_default, api_keys_file)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="iKy OSINT API", version="2.0.0")

    cors_origins = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:4200,http://localhost:4300,http://127.0.0.1:4200,http://127.0.0.1:4300",
    ).split(",")
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


_ensure_apikeys()
app = create_app()
