"""
Error Handling Module
=====================

Standardized error responses for ClariFin_OS API.
Provides consistent error formatting and logging.

Usage:
    from errors import AppError, DatabaseError, ValidationError
    raise AppError("Something went wrong", status_code=400)
"""

import traceback
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.logger import log_error

# ============================================================
# Custom Exception Classes
# ============================================================

class AppError(Exception):
    """
    Base application error.

    Attributes:
        message: Human-readable error message
        status_code: HTTP status code
        details: Optional additional details
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AppError):
    """Input validation error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, status_code=400, details=details)


class DatabaseError(AppError):
    """Database operation error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, status_code=500, details=details)


class FileError(AppError):
    """File operation error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, status_code=400, details=details)


class ImportError(AppError):
    """Data import error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, status_code=400, details=details)


class NotFoundError(AppError):
    """Resource not found error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, status_code=404, details=details)


# ============================================================
# Error Response Formatting
# ============================================================

def format_error_response(
    status_code: int,
    message: str,
    details: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Format an error response.

    Args:
        status_code: HTTP status code
        message: Error message
        details: Optional additional details

    Returns:
        Formatted error response dictionary
    """
    response: dict[str, Any] = {
        "error": {
            "message": message,
            "status_code": status_code,
        }
    }

    if details:
        response["error"]["details"] = details

    return response


# ============================================================
# Exception Handlers
# ============================================================

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """
    Handle application errors.

    Args:
        request: FastAPI request
        exc: Application error

    Returns:
        JSON error response
    """
    log_error(
        f"Application error: {exc.message}",
        details=exc.details
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(exc.status_code, exc.message, exc.details)
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTP exceptions.

    Args:
        request: FastAPI request
        exc: HTTP exception

    Returns:
        JSON error response
    """
    log_error(
        f"HTTP error: {exc.detail}",
        extra={"status_code": exc.status_code}
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(exc.status_code, exc.detail)
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.

    Logs the full traceback for debugging but returns a generic message to the client.

    Args:
        request: FastAPI request
        exc: Unexpected exception

    Returns:
        JSON error response
    """
    # Log full traceback for debugging
    log_error(
        f"Unexpected error: {str(exc)}",
        error=exc,
        extra={"path": request.url.path}
    )

    # In development, you might want to include the traceback
    # In production, keep it generic
    details: dict[str, Any] = {}
    from src.config import settings
    if settings.log_level == "DEBUG":
        details["traceback"] = traceback.format_exc()

    return JSONResponse(
        status_code=500,
        content=format_error_response(
            500,
            "Internal server error",
            details if details else None
        )
    )


# ============================================================
# Error Handler Registration
# ============================================================

def register_error_handlers(app: FastAPI) -> None:
    """
    Register all error handlers with the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore
    app.add_exception_handler(Exception, generic_exception_handler)


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Args:
        request: FastAPI request
        exc: Validation error

    Returns:
        JSON error response with field-level details
    """
    errors: list[dict[str, str]] = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    log_error(
        "Validation error",
        extra={"errors": errors, "path": request.url.path}
    )

    return JSONResponse(
        status_code=422,
        content=format_error_response(
            422,
            "Validation failed",
            {"errors": errors}
        )
    )