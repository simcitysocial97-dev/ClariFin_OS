"""
Core Database Infrastructure Package
=====================================

Single source of truth for all database-related infrastructure:

    config.py      ← DB path resolution, PRAGMA settings
    connection.py  ← sqlite3 connection factory (WAL + foreign keys)
    schema.py      ← DDL, create_all, migrations, verify_schema
    transaction.py ← atomic transaction context manager
    health.py      ← connectivity and schema health checks

Usage::

    from src.core.db import get_connection, get_db_path, create_all

    # Get a canonical connection
    with get_connection() as conn:
        conn.execute("SELECT ...")

    # Resolve the canonical DB path
    path = get_db_path()

    # Initialize schema (idempotent)
    create_all()
"""

from src.core.db.config import (
    DEFAULT_DB_FILENAME,
    DEFAULT_DB_RELATIVE_PATH,
    FOREIGN_KEYS,
    JOURNAL_MODE,
    get_db_path,
)
from src.core.db.connection import get_connection, get_connection_context
from src.core.db.transaction import db_transaction

__all__ = [
    "DEFAULT_DB_FILENAME",
    "DEFAULT_DB_RELATIVE_PATH",
    "FOREIGN_KEYS",
    "JOURNAL_MODE",
    "get_db_path",
    "get_connection",
    "get_connection_context",
    "db_transaction",
]
