"""
Database Connection Factory — Canonical sqlite3 Connection Creation
=====================================================================

The single owner of ``sqlite3.connect()`` + PRAGMA setup.

All data-access code must obtain connections through :func:`get_connection`
or :func:`get_connection_context` rather than calling ``sqlite3.connect``
directly.

Usage::

    from src.core.db.connection import get_connection

    with get_connection() as conn:
        rows = conn.execute("SELECT ...").fetchall()
"""

import contextlib
import sqlite3
from collections.abc import Iterator

from src.core.db.config import FOREIGN_KEYS, JOURNAL_MODE, get_db_path


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Create a sqlite3 connection with canonical PRAGMA settings.

    Args:
        db_path: Optional explicit path. If ``None``, the canonical
            path from :func:`core.db.config.get_db_path` is used.

    Returns:
        A ``sqlite3.Connection`` with ``journal_mode=WAL``,
        ``foreign_keys=ON``, and ``row_factory=sqlite3.Row``.
    """
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    conn.execute(f"PRAGMA journal_mode={JOURNAL_MODE}")
    conn.execute(f"PRAGMA foreign_keys={FOREIGN_KEYS}")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


@contextlib.contextmanager
def get_connection_context(
    db_path: str | None = None,
) -> Iterator[sqlite3.Connection]:
    """Context manager that opens and closes a canonical connection.

    The connection is committed on normal exit and rolled back on
    exception, then always closed.

    Usage::

        with get_connection_context() as conn:
            conn.execute("INSERT ...")
    """
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
