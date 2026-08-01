"""Base repository with common database access pattern."""

# src/repositories/base.py

import sqlite3

from src.core.db.config import get_db_path
from src.core.db.connection import get_connection


class BaseRepository:
    """Base class for domain-specific repositories.

    Owns connection lifecycle and PRAGMA setup for all data-access code.
    Repositories MUST only query, persist, and coordinate transactions here.
    """

    def __init__(self, db_path: str | None = None):
        self.db_path = get_db_path(db_path)

    def _get_conn(self) -> sqlite3.Connection:
        """Get a database connection with canonical PRAGMA settings."""
        return get_connection(self.db_path)
