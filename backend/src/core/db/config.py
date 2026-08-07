"""
Database Configuration — Canonical DB Path and PRAGMA Settings
================================================================

Single source of truth for database path resolution and SQLite PRAGMA settings.

All modules must import :func:`get_db_path` from here instead of computing
``Path(__file__)`` chains or hardcoding ``data/finance.db``.

Resolution order:
    1. Explicit ``db_path`` argument (caller-provided, e.g. test fixture)
    2. ``settings._database_path_override`` (runtime override, e.g. tests)
    3. ``FINANCE_DB_PATH`` environment variable
    4. ``DATABASE_PATH`` environment variable
    5. ``data/finance.db`` (default, relative to CWD at runtime)
"""

import os

DEFAULT_DB_FILENAME = "finance.db"
DEFAULT_DB_RELATIVE_PATH = f"data/{DEFAULT_DB_FILENAME}"

# SQLite PRAGMA settings — applied to every connection
JOURNAL_MODE = "WAL"
FOREIGN_KEYS = "ON"


def get_db_path(db_path: str | None = None) -> str:
    """Resolve the canonical database path.

    Args:
        db_path: Explicit override (e.g. from test fixture). If provided,
            this takes precedence over everything else.

    Returns:
        Database path as a string.

    Resolution order:
        1. ``db_path`` argument
        2. ``settings._database_path_override`` (runtime override)
        3. ``FINANCE_DB_PATH`` env var
        4. ``DATABASE_PATH`` env var
        5. ``data/finance.db`` default
    """
    if db_path is not None:
        return str(db_path)

    # Check runtime override (lazy import to avoid circular dependency)
    try:
        from src.config import settings

        override = getattr(settings, "_database_path_override", None)
        if override:
            return str(override)
    except ImportError:
        pass

    env_path = os.getenv("FINANCE_DB_PATH") or os.getenv("DATABASE_PATH")
    if env_path:
        return env_path

    return DEFAULT_DB_RELATIVE_PATH
