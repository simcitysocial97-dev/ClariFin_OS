"""
Database Health Check — Connectivity and Schema Validation
===========================================================

Provides :func:`check_database_health` which verifies that the database
is reachable and contains the required core tables.

Used by the ``/ready`` endpoint and startup validation.
"""

import logging
from typing import Any

from src.core.db.config import get_db_path
from src.core.db.connection import get_connection_context

logger = logging.getLogger(__name__)

_REQUIRED_HEALTH_TABLES = {"transactions", "accounts", "statements"}


def check_database_health(db_path: str | None = None) -> dict[str, Any]:
    """Verify database connectivity and core table presence.

    Args:
        db_path: Optional explicit path. Falls back to canonical path.

    Returns:
        Dict with ``healthy`` (bool), ``db_path`` (str),
        ``missing_tables`` (list[str]), and optionally ``error`` (str).
    """
    path = db_path or get_db_path()
    result: dict[str, Any] = {
        "healthy": False,
        "db_path": path,
        "missing_tables": [],
    }

    try:
        with get_connection_context(path) as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            existing = {r[0] for r in rows}
            missing = _REQUIRED_HEALTH_TABLES - existing
            if missing:
                result["missing_tables"] = sorted(missing)
                result["error"] = f"Missing tables: {', '.join(sorted(missing))}"
            else:
                result["healthy"] = True
    except Exception as e:
        result["error"] = str(e)
        logger.error("Database health check failed: %s", e)

    return result
