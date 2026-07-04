"""Exception handlers for the FastAPI application."""

from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.logger import log
from src.errors import ClariFinError


def setup_exception_handlers(app: FastAPI) -> None:
    """Configure exception handlers for the application."""
    
    @app.exception_handler(ClariFinError)
    async def clarifin_error_handler(request: Request, exc: ClariFinError):
        log.warning(
            "API error [%s]: %s | %s %s",
            exc.error_code,
            exc.message,
            request.method,
            request.url.path
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.message,
                "error_code": exc.error_code,
                "detail": exc.detail,
                "path": str(request.url.path),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        log.error(
            "Unhandled: %s | %s %s",
            str(exc),
            request.method,
            request.url.path,
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "detail": str(exc),
                "path": str(request.url.path),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
