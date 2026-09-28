"""Migration 002 — household sentinel unification (M04, DB-002).

Unifies the "no household" sentinel to ``'primary'`` across the four
tables whose DDL defaults to ``'default'``:
``behaviour_snapshots`` / ``behaviour_patterns`` / ``behaviour_alerts`` /
``financial_profiles``.

Per D11, the DDL-level ``DEFAULT 'default'`` clause itself is NOT
rewritten here — a full table rebuild is out of scope. The M04-T4 guard
test (``test_no_raw_household_default.py``) is the explicit, permanent
record of this compromise's boundary: it inserts via raw DDL defaults
and therefore keeps failing until the DDL default itself is corrected.
"""

from __future__ import annotations

import logging
import sqlite3

logger = logging.getLogger(__name__)

_TABLES = (
    "behaviour_snapshots",
    "behaviour_patterns",
    "behaviour_alerts",
    "financial_profiles",
)

DESCRIPTION = "household sentinel unify"


def migrate(conn: sqlite3.Connection) -> None:
    """Move every ``'default'`` household_id to ``'primary'``.

    Logs pre-migration counts, performs the UPDATEs, then re-counts and
    asserts zero ``'default'`` rows remain — before commit.
    """
    pre_counts: dict[str, int] = {}
    for table in _TABLES:
        cur = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE household_id = 'default'"
        )
        pre_counts[table] = cur.fetchone()[0]
    logger.info("Migration 002 pre-counts ('default' rows): %s", pre_counts)

    for table in _TABLES:
        conn.execute(
            f"UPDATE {table} SET household_id = 'primary' "
            "WHERE household_id = 'default'"
        )

    for table in _TABLES:
        cur = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE household_id = 'default'"
        )
        remaining = cur.fetchone()[0]
        assert remaining == 0, (
            f"Migration 002 aborted: {remaining} rows with "
            f"household_id='default' remain in {table}"
        )
    logger.info("Migration 002 post-check: zero 'default' rows remain")
