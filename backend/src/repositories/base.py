"""Base repository with common database access pattern."""
from src.common.database import DB_PATH
from src.db import FinanceDB


class BaseRepository:
    """Base class for domain-specific repositories."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or DB_PATH

    def _db(self) -> FinanceDB:
        """Get a FinanceDB instance for this repository."""
        return FinanceDB(self.db_path)
