"""
AI Tutor API - Main Application Entry Point

A FastAPI-based tutoring system with:
- 4-level progressive hint system (pre-authored + LLM-generated)
- Secure code execution sandbox
- Pre/post assessment quizzes
- Likert scale surveys for research data collection
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.config import settings
from backend.routers import auth, exercises, hints, quiz, submit, survey
from backend.exceptions import (
    register_exception_handlers,
    ValidationAPIError,
)
from backend.services.logging_service import (
    configure_logging,
    RequestLoggingMiddleware,
    get_logger,
)
from backend.services.rate_limiter import limiter, rate_limit_exceeded_handler
from backend.services.metrics import get_metrics, get_metrics_collector


# Configure logging on startup
configure_logging()
logger = get_logger("startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info("application_starting", app_name=settings.app_name, debug=settings.debug)
    yield
    # Shutdown
    logger.info("application_shutting_down")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI-powered Python programming tutor with 4-level progressive hints",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add CORS middleware with configurable origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    max_age=600,
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Register exception handlers
register_exception_handlers(app)

# Include routers with API prefix
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(exercises.router, prefix=settings.api_prefix)
app.include_router(hints.router, prefix=settings.api_prefix)
app.include_router(submit.router, prefix=settings.api_prefix)
app.include_router(quiz.router, prefix=settings.api_prefix)
app.include_router(survey.router, prefix=settings.api_prefix)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": settings.app_name}


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "disabled",
    }


@app.get("/metrics", tags=["monitoring"])
async def metrics() -> Response:
    """
    Prometheus metrics endpoint.
    Returns metrics in Prometheus exposition format.
    """
    metrics_data, content_type = get_metrics()
    return Response(content=metrics_data, media_type=content_type)


@app.exception_handler(ValidationAPIError)
async def validation_error_handler(request: Request, exc: ValidationAPIError):
    """Handle custom validation errors."""
    from fastapi.responses import JSONResponse
    from backend.services.logging_service import get_request_id

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": get_request_id(),
            },
        },
    )
