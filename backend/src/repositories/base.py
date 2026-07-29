"""Base repository with common database access pattern."""

# src/repositories/base.py

import os
import sqlite3
from pathlib import Path

from src.config import settings

# Fallback default path only if no environment or setting override exists
DEFAULT_DB_PATH = str(Path(__file__).parent.parent / "data" / "finance.db")


class BaseRepository:
    """Base class for domain-specific repositories with enterprise-grade path resolution."""

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_path = (
                getattr(settings, "_database_path_override", None)
                or os.getenv("FINANCE_DB_PATH")
                or DEFAULT_DB_PATH
            )
        self.db_path = str(db_path)

    def _get_conn(self) -> sqlite3.Connection:
        """Get an isolated database connection for this repository."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn
