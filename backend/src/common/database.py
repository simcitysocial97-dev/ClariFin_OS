"""Database access utilities."""
from pathlib import Path

from src.config import settings
from src.db import FinanceDB

# Global database path constant
DB_PATH = str(Path(__file__).parent.parent / "data" / "finance.db")


def get_db() -> FinanceDB:
    """
    Get database instance.

    Returns:
        FinanceDB instance connected to the main database
    """
    return FinanceDB(db_path=str(settings.database_path) or DB_PATH)
