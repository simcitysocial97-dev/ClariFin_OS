"""
Transaction Helpers — Atomic Database Transaction Management
=============================================================

Provides a context manager for atomic database operations.

Usage::

    from src.core.db.transaction import db_transaction

    with db_transaction() as conn:
        conn.execute("INSERT ...")
        conn.execute("UPDATE ...")
    # Commits on success, rolls back on exception, closes connection
"""

import contextlib
import sqlite3
from collections.abc import Iterator

from src.core.db.config import get_db_path
from src.core.db.connection import get_connection


@contextlib.contextmanager
def db_transaction(
    db_path: str | None = None,
) -> Iterator[sqlite3.Connection]:
    """Context manager for a single atomic database transaction.

    Opens a connection, yields it, then commits on normal exit or
    rolls back on exception. The connection is always closed.

    Args:
        db_path: Optional explicit path. Falls back to canonical path.

    Yields:
        A sqlite3.Connection with WAL + foreign_keys PRAGMAs applied.
    """
    path = db_path or get_db_path()
    conn = get_connection(path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
