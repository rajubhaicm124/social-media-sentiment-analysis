"""SocialScope AI — FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.analysis import sentiment as sentiment_module
from app.api import analysis as analysis_router
from app.api import export as export_router
from app.api import history as history_router
from app.config import settings
from app.core.errors import SocialScopeError
from app.database import init_db
from app.platforms import PLATFORM_SPECS

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger("socialscope")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_directories()
    init_db()
    logger.info("%s API ready — %s", settings.app_name, settings.app_tagline)
    yield


DESCRIPTION = """
**SocialScope AI** turns a public social-media URL into a clean, analysable
dataset with sentiment, engagement metrics, statistics and downloadable exports.

### Data integrity
* Collection uses **official platform APIs only** (YouTube Data API v3, Meta Graph API).
* No authentication, privacy or anti-bot control is bypassed, and nothing is scraped.
* A metric that an API does not return is reported as
  *\"Data unavailable through the current platform API.\"* — never estimated.
* Demo mode uses a bundled **synthetic** dataset that is labelled as such
  everywhere it appears, including inside every export.
"""

app = FastAPI(
    title=f"{settings.app_name} API",
    description=DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(analysis_router.router, prefix="/api")
app.include_router(history_router.router, prefix="/api")
app.include_router(export_router.router, prefix="/api")


# --- error handling: never leak a stack trace ------------------------------
@app.exception_handler(SocialScopeError)
async def socialscope_error_handler(_: Request, exc: SocialScopeError) -> JSONResponse:
    if exc.status_code >= 500:
        logger.error("%s: %s", exc.code, exc.message)
    return JSONResponse(status_code=exc.status_code, content=exc.to_payload())


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(part) for part in first.get("loc", [])[1:]) or "request"
    message = first.get("msg", "The request could not be validated.")
    message = message.removeprefix("Value error, ")
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": f"{field}: {message}",
                "detail": {"field": field},
            }
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    friendly = {
        404: "The requested endpoint or analysis could not be found.",
        405: "That method is not allowed for this endpoint.",
        413: "The uploaded content is too large.",
    }.get(exc.status_code, "The request could not be completed.")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": friendly, "detail": {}}},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "Something went wrong while processing your request. Please try again.",
                "detail": {},
            }
        },
    )


@app.get("/api/health", tags=["system"])
def health() -> dict[str, Any]:
    """Service health and configuration status. No secrets are returned."""
    credentials = settings.platform_credentials()
    return {
        "status": "ok",
        "app": settings.app_name,
        "tagline": settings.app_tagline,
        "environment": settings.environment,
        "version": "1.0.0",
        "database": settings.database_url.split("://", 1)[0],
        "platforms": [
            {"key": key, "configured": credentials.get(key, False)} for key in PLATFORM_SPECS
        ],
        "sentiment": sentiment_module.engine_status(),
        "demo_mode_enabled": settings.enable_demo_mode,
        "rate_limit": {
            "max_requests": settings.rate_limit_requests,
            "window_seconds": settings.rate_limit_window_seconds,
        },
    }


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {
        "app": settings.app_name,
        "tagline": settings.app_tagline,
        "docs": "/docs",
        "api": "/api/health",
    }
