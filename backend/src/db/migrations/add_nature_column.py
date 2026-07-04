"""
Migration script to add nature column to transactions table.

This migration adds the 'nature' column for transaction classification
and creates the necessary index.
"""

import sqlite3
from src.logger import log
from src.db.core import FinanceDB

def add_nature_column(conn: sqlite3.Connection) -> None:
    """Add nature column to transactions table if it doesn't exist."""
    try:
        # Add the nature column
        conn.execute("""
            ALTER TABLE transactions ADD COLUMN nature TEXT DEFAULT 'unknown'
        """)
        log.info("Added 'nature' column to transactions table")
    except sqlite3.OperationalError:
        log.debug("'nature' column already exists on transactions table")

    # Create index for nature column
    try:
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_nature ON transactions(nature)
        """)
        log.info("Created index idx_transactions_nature")
    except sqlite3.OperationalError:
        log.debug("Index idx_transactions_nature already exists")

def classify_existing_transactions(db: FinanceDB) -> None:
    """
    Classify all existing transactions and update their nature column.

    This function is idempotent - can be run multiple times safely.
    """
    from src.engines.transaction_classifier import classify_transaction

    log.info("Starting transaction classification...")

    # Get all transactions that haven't been classified yet
    transactions = db.get_all_transactions()

    classified_count = 0
    updated_count = 0

    with db.transaction() as conn:
        for txn in transactions:
            # Skip if already classified
            if txn.get('nature') and txn['nature'] != 'unknown':
                continue

            # Classify the transaction
            nature = classify_transaction(txn, db)
            classified_count += 1

            # Update the nature column
            if nature != txn.get('nature'):
                conn.execute("""
                    UPDATE transactions SET nature = ? WHERE id = ?
                """, (nature, txn['id']))
                updated_count += 1

    log.info("Transaction classification complete: %d classified, %d updated", classified_count, updated_count)

def run_migration() -> None:
    """Run the complete migration."""
    log.info("Starting transaction nature migration...")

    # Initialize database
    db = FinanceDB()

    with db.connection() as conn:
        add_nature_column(conn)

    # Classify existing transactions
    classify_existing_transactions(db)

    log.info("Transaction nature migration completed successfully")

if __name__ == "__main__":
    run_migration()