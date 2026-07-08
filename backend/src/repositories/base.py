"""Base repository with common database access pattern."""
import sqlite3
from pathlib import Path

# Default database path (relative to this file)
DB_PATH = str(Path(__file__).parent.parent / "data" / "finance.db")


class BaseRepository:
    """Base class for domain-specific repositories."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or DB_PATH

    def _get_conn(self) -> sqlite3.Connection:
        """Get a database connection for this repository."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn