"""
Health & Diagnostics Endpoints
==============================

Lightweight operational endpoints for monitoring application health.

Endpoints:
  - /health — confirms the application is running
  - /ready — confirms database connectivity and essential services
"""

import sqlite3
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException

from src.config import settings
from src.logger import log_error, log_info

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, Any]:
    """
    Basic health check endpoint.

    Returns 200 OK if the application is running.
    This is a lightweight check that doesn't verify database connectivity.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "message": "ClariFin_OS is running"
    }


@router.get("/ready")
def readiness_check() -> dict[str, Any]:
    """
    Readiness check endpoint.

    Verifies:
    - Database is reachable
    - Required directories exist
    - Essential files are present

    Returns 200 OK if all checks pass, 503 otherwise.
    """
    checks: dict[str, bool] = {
        "database": False,
        "upload_dir": False,
        "data_dir": False,
    }
    errors: list[str] = []

    # Check database connectivity
    try:
        db_path = settings.database_path
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            conn.execute("SELECT 1 FROM transactions LIMIT 1")
            conn.close()
            checks["database"] = True
        else:
            # Database doesn't exist yet - that's OK for first run
            checks["database"] = True
            log_info("Database not found - will be created on first use")
    except Exception as e:
        errors.append(f"Database error: {str(e)}")
        log_error("Readiness check failed: database", error=e)

    # Check upload directory
    try:
        upload_dir = settings.upload_dir
        if upload_dir.exists() or upload_dir.parent.exists():
            checks["upload_dir"] = True
        else:
            errors.append(f"Upload directory not accessible: {upload_dir}")
    except Exception as e:
        errors.append(f"Upload directory error: {str(e)}")

    # Check data directory
    try:
        data_dir = settings.database_path.parent
        if data_dir.exists() or data_dir.parent.exists():
            checks["data_dir"] = True
        else:
            errors.append(f"Data directory not accessible: {data_dir}")
    except Exception as e:
        errors.append(f"Data directory error: {str(e)}")

    all_healthy = all(checks.values())

    if all_healthy:
        return {
            "status": "ready",
            "checks": checks,
            "message": "All systems operational"
        }
    else:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "checks": checks,
                "errors": errors
            }
        )


def register_health_routes(app: FastAPI) -> None:
    """
    Register health routes with the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    app.include_router(router)
