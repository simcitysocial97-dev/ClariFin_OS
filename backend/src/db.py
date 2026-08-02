"""
db.py
=====
SQLite database manager for ClariFin_OS (backward-compatible wrapper).

Initialization is a single atomic sequence:
  1. Connect
  2. Create all base tables (CREATE TABLE IF NOT EXISTS)
  3. Create all indexes (CREATE INDEX IF NOT EXISTS)
  4. Create all triggers (CREATE TRIGGER IF NOT EXISTS)
  5. Run schema migrations (ALTER TABLE ADD COLUMN, data backfill)
  6. Verify schema integrity

The initialization is idempotent — running it multiple times
produces the same schema.

Usage:
  db = FinanceDB()
  # db is fully initialized after construction
  # Use repository classes for data access

.. deprecated::
    New code should import from ``src.core.db`` directly:
    - ``src.core.db.get_connection`` for connections
    - ``src.core.db.get_db_path`` for path resolution
    - ``src.core.db.schema.create_all`` for initialization
"""

import logging
import sqlite3
import types
from pathlib import Path
from typing import Literal

from src.core.db.config import get_db_path
from src.core.db.connection import get_connection
from src.core.db.schema import (
    create_all,
    run_migrations,
    verify_schema,
)

logger = logging.getLogger(__name__)


# Backward-compatible re-export of money parsing utility
from src.common.calculations import _parse_amount_paise as _parse_amount_paise


class FinanceDB:
    """
    SQLite-backed storage for ClariFin_OS.

    Initialization is a single atomic sequence:
      1. Connect
      2. Create all base tables (CREATE TABLE IF NOT EXISTS)
      3. Create all indexes (CREATE INDEX IF NOT EXISTS)
      4. Create all triggers (CREATE TRIGGER IF NOT EXISTS)
      5. Run schema migrations (ALTER TABLE ADD COLUMN, data backfill)
      6. Verify schema integrity

    The initialization is idempotent.
    Supports context manager protocol for automatic connection management.
    """

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_path = get_db_path()

        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

        create_all(self.db_path)
        run_migrations(self.db_path)
        verify_schema(self.db_path)

    # ----------------------------------------------------------
    # Connection Management
    # ----------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Create a new connection with canonical PRAGMA settings."""
        return get_connection(self.db_path)

    def _get_conn(self) -> sqlite3.Connection:
        """Return active connection or open a new one."""
        if self._conn is not None:
            return self._conn
        return self._connect()

    def __enter__(self) -> "FinanceDB":
        self._conn = self._connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> Literal[False]:
        if self._conn:
            if exc_type is None:
                self._conn.commit()
            else:
                self._conn.rollback()
            self._conn.close()
            self._conn = None
        return False  # Don't suppress exceptions


if __name__ == "__main__":
    db = FinanceDB()
    print(f"Database: {db.db_path}")
    print("Database schema initialized successfully.")
