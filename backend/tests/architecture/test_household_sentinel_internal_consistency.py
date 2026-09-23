"""Characterization test — household-sentinel internal consistency (M01-T2a).

Sanity/regression guard for the four-table group affected by DB-002:
`behaviour_snapshots`, `behaviour_patterns`, `behaviour_alerts`,
`financial_profiles`. Each row is inserted using its table's own DDL default
(`household_id` omitted), and all four resulting values must agree with each
other.

Expected state: PASSES today (all four DDL defaults are the same literal,
`'default'`) — this is a regression guard for the group, NOT a
characterization of DB-002. If it ever fails, that is a different,
pre-existing problem to report separately. Must not be weakened.
"""

from __future__ import annotations

import sqlite3


def test_four_tables_agree_on_household_default(temp_db: str) -> None:
    """All four DB-002 tables resolve the same household default."""
    conn = sqlite3.connect(temp_db)
    try:
        conn.execute(
            "INSERT INTO behaviour_snapshots (snapshot_date) "
            "VALUES ('2025-01-15')"
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
            "INSERT INTO financial_profiles (profile_type) "
            "VALUES ('wellness')"
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

    distinct = set(values.values())
    assert len(distinct) == 1, (
        "Household-sentinel internal inconsistency: "
        f"DDL defaults disagree across the four tables: {values}"
    )
