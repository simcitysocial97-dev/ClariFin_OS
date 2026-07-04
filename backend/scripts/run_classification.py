#!/usr/bin/env python3
"""
Transaction Classification Persistence Script
=============================================

This script classifies all transactions in the database and persists
the classification results to the 'nature' column.

The classifier uses keyword matching and transaction patterns to
distinguish between real income/expenses and debt recycling activities.

Usage:
    python scripts/run_classification.py [database_path]

    If no database_path is provided, uses 'backend/data/finance.db'
"""

import sys
import os
import sqlite3
from typing import Dict, List, Tuple

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from engines.transaction_classifier import classify_transaction
from logger import log

def run_classification(db_path: str) -> Dict[str, int]:
    """
    Classify all transactions in the database and persist results.

    Args:
        db_path: Path to SQLite database file

    Returns:
        Dictionary with nature counts
    """
    log.info("Starting transaction classification persistence...")

    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        # Fetch all transactions that need classification
        cursor = conn.execute("""
            SELECT id, date, description, amount_paise, type, category,
                   account_id, bank, member, source
            FROM transactions
            WHERE nature IS NULL OR nature = 'unknown'
        """)
        transactions = cursor.fetchall()

        log.info("Found %d transactions to classify", len(transactions))

        if not transactions:
            log.info("No transactions need classification")
            return {}

        # Classify each transaction
        updates = []
        nature_counts = {}

        for txn in transactions:
            txn_dict = dict(txn)
            nature = classify_transaction(txn_dict)
            updates.append((nature, txn['id']))
            nature_counts[nature] = nature_counts.get(nature, 0) + 1

        # Batch update database
        if updates:
            conn.executemany(
                "UPDATE transactions SET nature = ? WHERE id = ?",
                updates
            )
            conn.commit()
            log.info("Persisted classification for %d transactions", len(updates))
        else:
            log.info("No updates needed")

        return nature_counts

    finally:
        conn.close()

def verify_classification(db_path: str) -> None:
    """Verify classification results with detailed breakdown."""
    log.info("Verifying classification results...")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        # Get classification summary
        cursor = conn.execute("""
            SELECT
                nature,
                COUNT(*) as count,
                ROUND(SUM(ABS(amount_paise)) / 100.0, 2) as total_inr
            FROM transactions
            GROUP BY nature
            ORDER BY total_inr DESC
        """)
        results = cursor.fetchall()

        log.info("\n=== CLASSIFICATION SUMMARY ===")
        log.info("%-20s %-10s %-15s", "NATURE", "COUNT", "TOTAL (₹)")
        log.info("-" * 48)

        total_transactions = 0
        total_amount = 0.0

        for row in results:
            nature = row['nature']
            count = row['count']
            amount = row['total_inr']
            log.info("%-20s %-10d %-15.2f", nature, count, amount)
            total_transactions += count
            total_amount += amount

        log.info("-" * 48)
        log.info("%-20s %-10d %-15.2f", "TOTAL", total_transactions, total_amount)

        # Verify specific patterns
        log.info("\n=== REAL INCOME VERIFICATION ===")
        cursor = conn.execute("""
            SELECT date, description, amount_paise/100.0 as amount_inr, nature
            FROM transactions
            WHERE description LIKE '%SALARY%' OR description LIKE '%salary%'
            ORDER BY date DESC
            LIMIT 5
        """)
        salary_txns = cursor.fetchall()
        for txn in salary_txns:
            log.info("%s | %-30s | ₹%-10.2f | %s",
                    txn['date'], txn['description'], txn['amount_inr'], txn['nature'])

        log.info("\n=== RECYCLING VERIFICATION ===")
        cursor = conn.execute("""
            SELECT date, description, amount_paise/100.0 as amount_inr, nature
            FROM transactions
            WHERE description LIKE '%CHEQ%' OR description LIKE '%SPAID%'
               OR description LIKE '%CRED%' OR description LIKE '%CREDIT CARD%'
            ORDER BY date DESC
            LIMIT 5
        """)
        recycling_txns = cursor.fetchall()
        for txn in recycling_txns:
            log.info("%s | %-30s | ₹%-10.2f | %s",
                    txn['date'], txn['description'], txn['amount_inr'], txn['nature'])

    finally:
        conn.close()

def main() -> None:
    """Main entry point."""
    # Determine database path
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'finance.db')

    log.info("Using database: %s", db_path)

    # Run classification
    nature_counts = run_classification(db_path)

    if nature_counts:
        log.info("\n=== CLASSIFICATION RESULTS ===")
        for nature, count in sorted(nature_counts.items(),
                                   key=lambda x: x[1], reverse=True):
            log.info("  %-20s: %d transactions", nature, count)
    else:
        log.info("No transactions were classified (already up to date)")

    # Verify results
    verify_classification(db_path)

    log.info("\n✅ Classification persistence complete!")

if __name__ == "__main__":
    main()