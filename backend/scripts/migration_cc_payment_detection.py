"""Migration for Credit Card Payment Detection - extends transaction_classifications.

Adds lifecycle_state and outstanding_paise columns for CC payment lifecycle tracking.
Also adds payment_channel for Phase 5 support.

Idempotent: Uses ALTER TABLE IF NOT EXISTS pattern.
"""
import sqlite3
from pathlib import Path


def run_migration(db_path: str) -> None:
    """Add CC payment detection columns to transaction_classifications."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")

    # Add lifecycle_state column (supports lifecycle states)
    try:
        conn.execute("""
            ALTER TABLE transaction_classifications
            ADD COLUMN lifecycle_state TEXT
        """)
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Add outstanding_paise column
    try:
        conn.execute("""
            ALTER TABLE transaction_classifications
            ADD COLUMN outstanding_paise INTEGER DEFAULT 0
        """)
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Add payment_channel for Phase 5 support (DIRECT, CRED, CHEQ, SPAYLATER, NOBROKER, UNKNOWN)
    try:
        conn.execute("""
            ALTER TABLE transaction_classifications
            ADD COLUMN payment_channel TEXT DEFAULT 'DIRECT'
        """)
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Add matched_statement_id to track which statement was matched
    try:
        conn.execute("""
            ALTER TABLE transaction_classifications
            ADD COLUMN matched_statement_id INTEGER
        """)
    except sqlite3.OperationalError:
        pass  # Column already exists

    conn.commit()
    conn.close()
    print("[MIGRATION CC_PAYMENT] Credit card payment detection columns added successfully.")


if __name__ == "__main__":
    run_migration(str(Path(__file__).parent.parent / "data" / "finance.db"))