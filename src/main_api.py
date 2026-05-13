"""
main_api.py
FastAPI application for the AI Dataset Cleaning & Validation Pipeline.

Startup
-------
    # Development (auto-reload on file change):
    uvicorn src.main_api:app --reload

    # Explicit host/port:
    uvicorn src.main_api:app --host 0.0.0.0 --port 8000

    # Production (multiple workers — requires gunicorn or uvicorn process manager):
    uvicorn src.main_api:app --host 0.0.0.0 --port 8000 --workers 4

Interactive docs
----------------
    http://localhost:8000/docs        (Swagger UI)
    http://localhost:8000/redoc       (ReDoc)
    http://localhost:8000/openapi.json

CORS
----
    All origins are allowed by default (suitable for local development and
    single-origin deployments).  Restrict in production by setting the
    ALLOWED_ORIGINS environment variable to a comma-separated list:

        ALLOWED_ORIGINS=https://app.example.com uvicorn src.main_api:app
"""

from __future__ import annotations

import os
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

# Ensure src/ is importable so existing pipeline modules resolve without installation
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from api.routes.analyze import router as analyze_router
from api.routes.download import router as download_router
from api.routes.health import router as health_router
from api.routes.report import router as report_router
from api.routes.upload import router as upload_router
from api.services.storage import StorageManager
from logger import get_logger

logger = get_logger("main_api")

# ── Storage bootstrap ─────────────────────────────────────────────────────────
# Directories must exist before StaticFiles is mounted (done at import time).

_storage = StorageManager()
_storage.ensure_dirs()


# ── Lifespan ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def _lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("AI Dataset Pipeline API — starting up (version 1.0.0)")
    _storage.ensure_dirs()
    yield
    logger.info("AI Dataset Pipeline API — shutting down")


# ── Application ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Dataset Cleaning & Validation Pipeline",
    description=(
        "REST API for the AI Dataset Cleaning & Validation Pipeline.\n\n"
        "**Workflow**\n\n"
        "1. `POST /upload` — upload a CSV file, receive an `upload_id`\n"
        "2. `POST /analyze/{upload_id}` — run the full pipeline, receive a quality report\n"
        "3. `GET /report/{upload_id}` — view the HTML report in a browser\n"
        "4. `GET /download-cleaned/{upload_id}` — download the cleaned dataset\n"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=_lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

_allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files ──────────────────────────────────────────────────────────────
# Serve the storage root at /files/ so chart images embedded in HTML reports
# resolve correctly when the report is opened in a browser.

app.mount("/files", StaticFiles(directory=str(_storage.root)), name="storage")

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(health_router)
app.include_router(upload_router)
app.include_router(analyze_router)
app.include_router(report_router)
app.include_router(download_router)


# ── Exception handlers ────────────────────────────────────────────────────────


@app.exception_handler(FileNotFoundError)
async def _file_not_found(request: Request, exc: FileNotFoundError) -> JSONResponse:
    logger.warning("FileNotFoundError: %s", exc)
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ValueError)
async def _value_error(request: Request, exc: ValueError) -> JSONResponse:
    logger.warning("ValueError: %s", exc)
    return JSONResponse(status_code=422, content={"detail": str(exc)})
