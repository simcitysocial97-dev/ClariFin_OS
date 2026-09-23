"""Guard test for the D11 compromise — DDL-level household defaults (M04-T4).

Per D11, migration 002 unifies *stored rows* to ``'primary'`` but does NOT
rewrite the DDL-level ``DEFAULT 'default'`` clause on the four tables
(``behaviour_snapshots`` / ``behaviour_patterns`` / ``behaviour_alerts`` /
``financial_profiles``) — a full table rebuild is out of scope.

This test inserts a row into each of the four tables via a raw ``INSERT``
that OMITS ``household_id`` (relying purely on the DDL default, bypassing
``resolve_household_id``) and asserts the resulting value is ``'primary'``.

**This test is expected to fail** until/unless the DDL default itself is
corrected — its failure is the intended, visible tripwire. It must exist
and must not be silently deleted or weakened.
"""

from __future__ import annotations

import sqlite3


def test_no_raw_household_default(temp_db: str) -> None:
    """Raw DDL defaults on the four tables must yield 'primary'."""
    conn = sqlite3.connect(temp_db)
    try:
        conn.execute(
            "INSERT INTO behaviour_snapshots (snapshot_date) " "VALUES ('2025-01-15')"
        )
        conn.execute(
            "INSERT INTO behaviour_patterns "
            "(pattern_type, pattern_key, strength_bps) "
            "VALUES ('spending', 'groceries', 5000)"
        )
        conn.execute(
            "INSERT INTO behaviour_alerts "
            "(alert_type, alert_code, severity, title) "
            "VALUES ('spending', 'HIGH_SPEND', 'high', 'High spend')"
        )
        conn.execute(
            "INSERT INTO financial_profiles (profile_type) " "VALUES ('wellness')"
        )
        conn.commit()

        values = {}
        for table in (
            "behaviour_snapshots",
            "behaviour_patterns",
            "behaviour_alerts",
            "financial_profiles",
        ):
            cur = conn.execute(f"SELECT household_id FROM {table}")
            values[table] = cur.fetchone()[0]
    finally:
        conn.close()

    for table, value in values.items():
        assert value == "primary", (
            f"D11 tripwire: {table} DDL default still yields "
            f"{value!r} instead of 'primary' — raw INSERTs bypass "
            "resolve_household_id"
        )
