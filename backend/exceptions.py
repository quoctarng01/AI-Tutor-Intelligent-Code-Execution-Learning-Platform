"""
Global exception handling and standardized error responses.
"""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from pydantic_core import PydanticCustomError

from backend.services.logging_service import get_logger, get_request_id


logger = get_logger("errors")


class APIError(Exception):
    """Base API error with standardized structure."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(APIError):
    """Resource not found error."""

    def __init__(self, resource: str, identifier: str | None = None):
        details = {"resource": resource}
        if identifier:
            details["identifier"] = identifier
        super().__init__(
            code="NOT_FOUND",
            message=f"{resource} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class UnauthorizedError(APIError):
    """Authentication required error."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ForbiddenError(APIError):
    """Permission denied error."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class RateLimitError(APIError):
    """Rate limit exceeded error."""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message="Too many requests. Please try again later.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after": retry_after},
        )


class ValidationAPIError(APIError):
    """Validation error with field-level details."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class LLMServiceError(APIError):
    """LLM service error."""

    def __init__(self, message: str = "AI service temporarily unavailable"):
        super().__init__(
            code="LLM_SERVICE_ERROR",
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class SandboxError(APIError):
    """Code execution sandbox error."""

    def __init__(self, message: str = "Code execution failed"):
        super().__init__(
            code="SANDBOX_ERROR",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


def create_error_response(
    code: str,
    message: str,
    details: dict | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Create a standardized error response."""
    response = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if details:
        response["error"]["details"] = details
    if request_id:
        response["error"]["request_id"] = request_id
    return response


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle APIError exceptions."""
    request_id = get_request_id()
    logger.warning(
        "api_error",
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request_id=request_id,
        ),
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI validation errors."""
    request_id = get_request_id()

    # Extract field errors
    errors = []
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
        })

    logger.warning(
        "validation_error",
        errors=errors,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"errors": errors},
            request_id=request_id,
        ),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled exceptions."""
    request_id = get_request_id()

    logger.error(
        "unhandled_exception",
        error_type=type(exc).__name__,
        error_message=str(exc),
        path=request.url.path,
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            request_id=request_id,
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    # Don't register generic handler in debug mode to show tracebacks
    if not app.debug:
        app.add_exception_handler(Exception, generic_exception_handler)
