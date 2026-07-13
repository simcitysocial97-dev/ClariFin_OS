"""Migration for EMI Detection - loan_amortization_schedule and transaction_classifications tables.

Idempotent: Uses CREATE TABLE IF NOT EXISTS pattern.
"""
import sqlite3


def run_migration(db_path: str) -> None:
    """Create tables for EMI detection functionality."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")

    # Create loan_amortization_schedule table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS loan_amortization_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INTEGER NOT NULL REFERENCES loans(id),
            due_date TEXT NOT NULL,
            emi_amount_paise INTEGER NOT NULL,
            principal_paise INTEGER NOT NULL,
            interest_paise INTEGER NOT NULL,
            outstanding_after_paise INTEGER NOT NULL,
            source TEXT DEFAULT 'computed',
            UNIQUE(loan_id, due_date)
        )
    """)

    # Index for efficient lookups
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_loan_amortization_loan_date
        ON loan_amortization_schedule(loan_id, due_date)
    """)

    # Create transaction_classifications table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transaction_classifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL REFERENCES transactions(id),
            classification TEXT NOT NULL,
            sub_classification TEXT,
            classifier TEXT DEFAULT 'loan_emi_detector',
            classifier_version INTEGER DEFAULT 1,
            confidence_bps INTEGER NOT NULL,
            source TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(transaction_id, classification)
        )
    """)

    # Index for efficient lookups
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_transaction_classifications_txn
        ON transaction_classifications(transaction_id)
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    import sys
    from pathlib import Path
    if len(sys.argv) > 1:
        run_migration(sys.argv[1])
    else:
        # Default path
        run_migration(str(Path(__file__).parent.parent / "data" / "finance.db"))
