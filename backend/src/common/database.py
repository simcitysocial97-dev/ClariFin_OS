"""
Database access utilities.

Legacy module — kept for runtime compatibility.
New code should instantiate repositories directly via their __init__.

The only remaining use of FinanceDB is for schema/migration management
in db.py itself.
"""

from pathlib import Path

from src.db import FinanceDB

# Global database path constant (kept for backward compatibility)
DB_PATH = str(Path(__file__).parent.parent / "data" / "finance.db")


def get_db() -> FinanceDB:
    """
    DEPRECATED: Returns a FinanceDB instance.

    FinanceDB now only handles schema management and migrations.
    Domain queries should use repository classes directly.
    """
    return FinanceDB()
