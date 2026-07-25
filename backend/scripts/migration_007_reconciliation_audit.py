"""
Migration 007: confidence_bps on reconciliations + reconciliation_audit_log table
=================================================================================
Adds confidence_bps (INTEGER) column to the reconciliations table for authoritative
precision, and creates the reconciliation_audit_log table for tracking all actions.

Run: cd backend && ./venv/bin/python3 scripts/migration_007_reconciliation_audit.py
"""

import sqlite3
from pathlib import Path

DB_PATH = str(Path(__file__).parent.parent / "src" / "data" / "finance.db")


def run_migration(db_path: str | None = None) -> None:
    """Add confidence_bps column and create audit log table idempotently."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys=ON")

    # ── Step 1: Add confidence_bps column ──────────────────────────────────
    try:
        conn.execute("ALTER TABLE reconciliations ADD COLUMN confidence_bps INTEGER")
        print("✓ ALTER TABLE reconciliations ADD COLUMN confidence_bps INTEGER")
    except sqlite3.OperationalError as e:
        print(f"⊘ ALTER TABLE reconciliations ADD COLUMN confidence_bps INTEGER - {e}")

    # ── Step 2: Backfill confidence_bps from match_confidence ──────────────
    # First, find and report problematic rows
    null_rows = conn.execute(
        "SELECT COUNT(*) FROM reconciliations WHERE match_confidence IS NULL"
    ).fetchone()[0]

    out_of_range_rows = conn.execute(
        "SELECT COUNT(*) FROM reconciliations WHERE match_confidence IS NOT NULL AND (match_confidence < 0.0 OR match_confidence > 1.0)"
    ).fetchone()[0]

    if null_rows > 0:
        print(
            f"⚠ Found {null_rows} rows where match_confidence IS NULL — left for manual review"
        )
        # Show the affected rows (fetchall returns tuples without row_factory set)
        problem_rows = conn.execute(
            "SELECT id, debit_txn_id, credit_txn_id, match_confidence FROM reconciliations WHERE match_confidence IS NULL"
        ).fetchall()
        for row in problem_rows:
            print(
                f"   NULL confidence: reconciliation id={row[0]} (txns {row[1]}↔{row[2]})"
            )

    if out_of_range_rows > 0:
        print(
            f"⚠ Found {out_of_range_rows} rows where match_confidence is outside [0.0, 1.0] — left for manual review"
        )
        problem_rows = conn.execute(
            "SELECT id, debit_txn_id, credit_txn_id, match_confidence FROM reconciliations WHERE match_confidence IS NOT NULL AND (match_confidence < 0.0 OR match_confidence > 1.0)"
        ).fetchall()
        for row in problem_rows:
            print(
                f"   Out-of-range confidence={row[3]}: reconciliation id={row[0]} (txns {row[1]}↔{row[2]})"
            )

    # Backfill only valid rows
    backfill = """
        UPDATE reconciliations
        SET confidence_bps = ROUND(match_confidence * 10000)
        WHERE match_confidence IS NOT NULL
          AND match_confidence >= 0.0
          AND match_confidence <= 1.0
          AND confidence_bps IS NULL
    """
    conn.execute(backfill)
    backfill_count = conn.execute("SELECT changes()").fetchone()[0]
    print(f"⊘ Backfilled confidence_bps → {backfill_count} rows")

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
    backfilled = conn.execute(
        "SELECT COUNT(*) FROM reconciliations WHERE confidence_bps IS NOT NULL"
    ).fetchone()[0]
    still_null = conn.execute(
        "SELECT COUNT(*) FROM reconciliations WHERE confidence_bps IS NULL"
    ).fetchone()[0]

    print("\n[MIGRATION 007] Summary:")
    print(f"  Total reconciliations:      {total}")
    print(f"  Backfilled confidence_bps:  {backfilled}")
    print(f"  Still NULL (left for review): {still_null}")

    conn.close()
    print("[MIGRATION 007] Reconciliation audit migration complete.")


if __name__ == "__main__":
    run_migration()
