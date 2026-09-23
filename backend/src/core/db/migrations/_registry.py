"""Versioned migration registry (M03).

Pre-assigned version numbers (program-wide, to avoid registry-list merge
conflicts): 1 = baseline (M03), 2 = household sentinel (M04),
3 = transaction hash v2 (M05), 4 = import_runs (M08).
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Callable

logger = logging.getLogger(__name__)

_DDL_SCHEMA_MIGRATIONS = """CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TEXT DEFAULT (datetime('now'))
)"""

MigrationFn = Callable[[sqlite3.Connection], None]

MIGRATIONS: list[tuple[int, str, MigrationFn]] = []

try:
    from src.core.db.migrations.m001_baseline import migrate as _m001

    MIGRATIONS.append((1, "baseline", _m001))
except ImportError:  # pragma: no cover - defensive; m001 ships with M03
    logger.warning("Migration 001 (baseline) unavailable")

try:
    from src.core.db.migrations.m002_household_sentinel_unify import (
        migrate as _m002,
    )

    MIGRATIONS.append((2, "household sentinel unify", _m002))
except ImportError:  # pragma: no cover - defensive; m002 ships with M04
    logger.warning("Migration 002 (household sentinel unify) unavailable")

try:
    from src.core.db.migrations.m003_transaction_hash_v2 import migrate as _m003

    MIGRATIONS.append((3, "transaction hash v2", _m003))
except ImportError:  # pragma: no cover - defensive; m003 ships with M05
    logger.warning("Migration 003 (transaction hash v2) unavailable")


def apply_pending_migrations(conn: sqlite3.Connection) -> list[int]:
    """Apply unapplied migrations in ascending version order.

    Each migration runs inside its own transaction; a `schema_migrations`
    row is recorded only on success.

    Args:
        conn: Open sqlite3 connection (schema tables must already exist
            via `create_all`, which includes `schema_migrations`).

    Returns:
        List of applied version numbers, in the order applied.
    """
    conn.execute(_DDL_SCHEMA_MIGRATIONS)
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    applied = {row[0] for row in rows}
    result: list[int] = []
    for version, description, fn in sorted(MIGRATIONS, key=lambda m: m[0]):
        if version in applied:
            continue
        try:
            fn(conn)
            conn.execute(
                "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                (version, description),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        result.append(version)
        logger.info("Migration %d applied: %s", version, description)
    return result
