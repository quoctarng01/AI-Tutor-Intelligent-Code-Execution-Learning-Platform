"""
Structured logging with request ID tracking.
"""

import logging
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Any

import structlog

from backend.config import settings


# Context variable for request ID
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
session_id_var: ContextVar[str | None] = ContextVar("session_id", default=None)


def get_request_id() -> str | None:
    """Get current request ID from context."""
    return request_id_var.get()


def get_session_id() -> str | None:
    """Get current session ID from context."""
    return session_id_var.get()


def set_request_context(request_id: str, session_id: str | None = None) -> None:
    """Set request context for logging."""
    request_id_var.set(request_id)
    if session_id:
        session_id_var.set(session_id)


def clear_request_context() -> None:
    """Clear request context."""
    request_id_var.set(None)
    session_id_var.set(None)


def add_request_context(logger: logging.Logger, method_name: str, event_dict: dict) -> dict:
    """Add request context to log entries."""
    request_id = get_request_id()
    session_id = get_session_id()
    if request_id:
        event_dict["request_id"] = request_id
    if session_id:
        event_dict["session_id"] = session_id
    return event_dict


def configure_logging() -> None:
    """Configure structured logging."""

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if settings.debug else logging.INFO,
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            add_request_context,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests with timing."""

    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        start_time = time.perf_counter()

        # Set context
        set_request_context(request_id)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Log request
        logger = get_logger("http")
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
        )

        try:
            response = await call_next(request)
            process_time = time.perf_counter() - start_time

            # Log response
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(process_time * 1000, 2),
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            process_time = time.perf_counter() - start_time
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration_ms=round(process_time * 1000, 2),
            )
            raise


# Create singleton logger for use across the application
logger = get_logger("ai_tutor")
