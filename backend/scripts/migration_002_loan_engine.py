"""
Database migration for Loan Engine enhancements.
Adds new columns and tables as per PRD.
"""

import sqlite3
from pathlib import Path

DB_PATH = str(Path(__file__).parent.parent / "src" / "data" / "finance.db")


def migrate() -> None:
    """Run loan engine migration."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")

    # Extend loans table
    migrations = [
        "ALTER TABLE loans ADD COLUMN interest_type TEXT DEFAULT 'fixed'",
        "ALTER TABLE loans ADD COLUMN floating_baselined_rate REAL",
        "ALTER TABLE loans ADD COLUMN last_rate_reset_date TEXT",
        "ALTER TABLE loans ADD COLUMN prepayment_mode TEXT DEFAULT 'reduce_tenure'",
    ]

    for migration in migrations:
        try:
            conn.execute(migration)
            print(f"✓ {migration}")
        except sqlite3.OperationalError as e:
            # Column may already exist
            print(f"⊘ {migration} - {e}")

    # Create loan_payments table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS loan_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id TEXT NOT NULL REFERENCES loans(id),
            payment_date TEXT NOT NULL,
            amount_paise INTEGER NOT NULL,
            principal_paise INTEGER NOT NULL,
            interest_paise INTEGER NOT NULL,
            late_fee_paise INTEGER DEFAULT 0,
            source_account_id TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    print("✓ loan_payments table created")

    # Note: loan_scenarios table removed - scenarios are temporary calculations
    # and should not be persisted per Phase 3 architecture

    conn.commit()
    conn.close()
    print("\nMigration complete!")


if __name__ == "__main__":
    migrate()
