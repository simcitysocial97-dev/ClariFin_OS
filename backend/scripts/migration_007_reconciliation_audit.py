"""
Migration 007: amount_paise and confidence_bps standardization on reconciliations + audit log table
=============================================================================================
Ensures amount_paise and confidence_bps (INTEGER) columns exist on the reconciliations table,
and creates the reconciliation_audit_log table for tracking all actions.

Run: cd backend && ./venv/bin/python3 scripts/migration_007_reconciliation_audit.py
"""

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = str(Path(__file__).parent.parent / "src" / "data" / "finance.db")


def run_migration(db_path: str | None = None) -> None:
    """Ensure amount_paise, confidence_bps columns and create audit log table idempotently."""
    path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys=ON")

    # ── Step 1: Add amount_paise column if missing ───────────────────────────
    try:
        conn.execute("ALTER TABLE reconciliations ADD COLUMN amount_paise INTEGER")
        print("✓ ALTER TABLE reconciliations ADD COLUMN amount_paise INTEGER")
    except sqlite3.OperationalError as e:
        print(f"⊘ ALTER TABLE reconciliations ADD COLUMN amount_paise INTEGER - {e}")

    # Backfill amount_paise from legacy amount if amount column exists
    try:
        conn.execute("""
            UPDATE reconciliations
            SET amount_paise = CAST(ROUND(amount * 100) AS INTEGER)
            WHERE amount_paise IS NULL AND amount IS NOT NULL
        """)
        print("✓ Backfilled amount_paise from legacy amount column")
    except sqlite3.OperationalError:
        pass  # legacy amount column might not exist, which is fine

    # ── Step 2: Add confidence_bps column if missing ─────────────────────────
    try:
        conn.execute("ALTER TABLE reconciliations ADD COLUMN confidence_bps INTEGER")
        print("✓ ALTER TABLE reconciliations ADD COLUMN confidence_bps INTEGER")
    except sqlite3.OperationalError as e:
        print(f"⊘ ALTER TABLE reconciliations ADD COLUMN confidence_bps INTEGER - {e}")

    # Backfill confidence_bps from match_confidence if match_confidence column exists
    try:
        null_rows = conn.execute(
            "SELECT COUNT(*) FROM reconciliations WHERE match_confidence IS NULL"
        ).fetchone()[0]

        if null_rows > 0:
            print(
                f"⚠ Found {null_rows} rows where match_confidence IS NULL — left for manual review"
            )

        conn.execute("""
            UPDATE reconciliations
            SET confidence_bps = ROUND(match_confidence * 10000)
            WHERE match_confidence IS NOT NULL
              AND match_confidence >= 0.0
              AND match_confidence <= 1.0
              AND confidence_bps IS NULL
        """)
        backfill_count = conn.execute("SELECT changes()").fetchone()[0]
        print(f"✓ Backfilled confidence_bps → {backfill_count} rows")
    except sqlite3.OperationalError:
        pass  # match_confidence column might not exist in clean environments

    # ── Step 3: Create reconciliation_audit_log table ──────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reconciliation_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reconciliation_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            actor TEXT NOT NULL,
            timestamp TEXT DEFAULT (datetime('now')),
            reason TEXT,
            previous_state TEXT,
            new_state TEXT,
            FOREIGN KEY (reconciliation_id) REFERENCES reconciliations(id) ON DELETE CASCADE
        )
    """)
    print("✓ reconciliation_audit_log table created")

    # Create index for fast lookups
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_reconciliation_id
        ON reconciliation_audit_log(reconciliation_id)
    """)
    print("✓ idx_audit_log_reconciliation_id index created")

    conn.commit()

    # ── Summary ────────────────────────────────────────────────────────────
    total = conn.execute("SELECT COUNT(*) FROM reconciliations").fetchone()[0]
    backfilled_amt = conn.execute(
        "SELECT COUNT(*) FROM reconciliations WHERE amount_paise IS NOT NULL"
    ).fetchone()[0]
    backfilled_bps = conn.execute(
        "SELECT COUNT(*) FROM reconciliations WHERE confidence_bps IS NOT NULL"
    ).fetchone()[0]

    print("\n[MIGRATION 007] Summary:")
    print(f"  Total reconciliations:      {total}")
    print(f"  Populated amount_paise:     {backfilled_amt}")
    print(f"  Populated confidence_bps:   {backfilled_bps}")

    conn.close()
    print("[MIGRATION 007] Reconciliation audit migration complete.")


if __name__ == "__main__":
    run_migration()
