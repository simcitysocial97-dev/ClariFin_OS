"""
Migration 006: Household columns on accounts
=============================================
Adds owner_id and household_id columns to the accounts table
for multi-user / multi-household support.

Run: cd backend && ./venv/bin/python3 scripts/migration_006_household.py
"""

import sqlite3
from pathlib import Path

DB_PATH = str(Path(__file__).parent.parent / "src" / "data" / "finance.db")


def run_migration(db_path: str | None = None) -> None:
    """Add household columns to accounts table idempotently."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys=ON")

    migrations = [
        "ALTER TABLE accounts ADD COLUMN owner_id TEXT DEFAULT 'self'",
        "ALTER TABLE accounts ADD COLUMN household_id TEXT DEFAULT 'primary'",
    ]

    for migration in migrations:
        try:
            conn.execute(migration)
            print(f"✓ {migration}")
        except sqlite3.OperationalError as e:
            # Column may already exist — safe to skip
            print(f"⊘ {migration} - {e}")

    # Backfill only rows where the new columns are still NULL
    backfill_owner = "UPDATE accounts SET owner_id = 'self' WHERE owner_id IS NULL"
    conn.execute(backfill_owner)
    owner_count = conn.execute("SELECT changes()").fetchone()[0]
    print(f"⊘ Backfilled owner_id → {owner_count} rows")

    backfill_household = (
        "UPDATE accounts SET household_id = 'primary' WHERE household_id IS NULL"
    )
    conn.execute(backfill_household)
    household_count = conn.execute("SELECT changes()").fetchone()[0]
    print(f"⊘ Backfilled household_id → {household_count} rows")

    conn.commit()

    # Verify
    cur = conn.execute(
        "SELECT COUNT(*) FROM accounts WHERE owner_id IS NULL OR household_id IS NULL"
    )
    null_count = cur.fetchone()[0]
    if null_count == 0:
        print("✓ All rows have owner_id and household_id populated.")
    else:
        print(f"⚠ {null_count} rows still have NULL household columns.")

    total = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
    print(f"  Total accounts: {total}")

    conn.close()
    print("[MIGRATION 006] Household columns migration complete.")


if __name__ == "__main__":
    run_migration()
