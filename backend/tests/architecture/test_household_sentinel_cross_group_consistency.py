"""Regression test for DB-002 — household-sentinel cross-group split (M01-T2b).

DB-002: the "no household" sentinel is split — `behaviour_snapshots` (and its
sibling tables) default `household_id` to `'default'` while `financial_goals`
(and the `accounts`/`financial_events` group) default it to `'primary'`. Rows
created through each table's own default therefore disagree, so a
household-scoped query cannot see a consistent household.

This test inserts a row into `financial_goals` (own default) alongside a row
in `behaviour_snapshots` (own default) and asserts `SELECT DISTINCT
household_id` across both returns exactly one value.

Expected state: FAILS until M04 unifies the sentinel (tracked as a known
expected failure in BASELINE.md; resolved by M04).
"""

from __future__ import annotations

import sqlite3


def test_household_sentinel_agrees_across_groups(temp_db: str) -> None:
    """DB-002: financial_goals and behaviour_snapshots must share one default."""
    conn = sqlite3.connect(temp_db)
    try:
        conn.execute(
            "INSERT INTO behaviour_snapshots (snapshot_date) "
            "VALUES ('2025-01-15')"
        )
        conn.execute(
            "INSERT INTO financial_goals (goal_type, name, target_amount_paise) "
            "VALUES ('savings', 'Emergency', 100000)"
        )
        conn.commit()

        cur = conn.execute("SELECT household_id FROM behaviour_snapshots")
        snapshot_household = cur.fetchone()[0]
        cur = conn.execute("SELECT household_id FROM financial_goals")
        goals_household = cur.fetchone()[0]
    finally:
        conn.close()

    assert snapshot_household == goals_household, (
        f"DB-002: household sentinel is split — behaviour_snapshots defaults "
        f"to {snapshot_household!r} but financial_goals defaults to "
        f"{goals_household!r}"
    )
