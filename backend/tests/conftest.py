"""
Shared pytest configuration for ClariFin_OS tests.
This file is automatically loaded by pytest.
"""
import pytest
import sqlite3
from pathlib import Path

# Single source of truth for database location
# Uses absolute path based on this file's location
# Works regardless of where pytest is run from
DB_PATH = str(
    Path(__file__).parent.parent / "data" / "finance.db"
)


def get_db_path() -> str:
    """Return absolute path to the test database."""
    return DB_PATH


@pytest.fixture(scope="session")
def db_path() -> str:
    """
    Pytest fixture providing absolute database path.
    scope="session" means this is computed once per test run.
    """
    path = Path(DB_PATH)
    if not path.exists():
        pytest.skip(
            f"Database not found at {DB_PATH}. "
            f"Run the application first to create the database."
        )
    return DB_PATH


@pytest.fixture(scope="session")
def db_connection(db_path):
    """
    Pytest fixture providing a read-only database connection.
    Shared across all tests in the session for performance.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture(scope="session")  
def finance_db(db_path):
    """
    Pytest fixture providing a FinanceDB instance.
    """
    from src.db.core import FinanceDB
    return FinanceDB(db_path)