"""Core Database Connection Manager

Centralized SQLite connection management with context managers
for the audit system.
"""

import sqlite3
from contextlib import contextmanager
from typing import Iterator
from pathlib import Path

class DatabaseConnection:
    """SQLite connection manager for audit system."""

    def __init__(self, db_path: str = "backend/data/finance.db"):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager for read-only database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Context manager for write transactions."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()