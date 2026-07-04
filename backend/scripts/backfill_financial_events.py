"""
Backfill Financial Events Ledger
==================================
Convert existing transactions into immutable financial_events.

This script is idempotent — safe to run multiple times.
It skips transactions that already have corresponding events.

Usage:
    python backend/scripts/backfill_financial_events.py
"""

import sqlite3
import sys
from pathlib import Path
from src.logger import log


# Reports directory
FINANCE_DB = Path(__file__).parent.parent / "data" / "finance.db"


def backfill_events(db_path: Path = FINANCE_DB) -> None:
    """Backfill financial_events from existing transactions."""
    if not db_path.exists():
        log.error("Database not found: %s", db_path)
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))

    # Ensure schema is up to date
    from src.db_schema import ensure_schema
    ensure_schema(conn)

    # Count source transactions
    cur = conn.execute("SELECT COUNT(*) FROM transactions WHERE amount_paise IS NOT NULL AND amount_paise != 0")
    source_count = cur.fetchone()[0]

    # Count already-backfilled events
    cur = conn.execute("SELECT COUNT(*) FROM financial_events WHERE event_type = 'transaction' AND metadata_json LIKE '%backfilled%'")
    existing_count = cur.fetchone()[0]

    log.info("Source transactions with amount_paise: %d", source_count)
    log.info("Already backfilled events: %d", existing_count)

    if source_count == 0:
        log.info("No transactions to backfill. Nothing to do.")
        conn.close()
        return

    # Backfill
    inserted = 0
    skipped = 0

    try:
        cur = conn.execute("""
            INSERT OR IGNORE INTO financial_events (
                event_type, entity_type, entity_id, amount_paise, direction, metadata_json
            )
            SELECT
                'transaction',
                'transaction',
                id,
                amount_paise,
                CASE
                    WHEN type = 'debit' THEN 'debit'
                    WHEN type = 'credit' THEN 'credit'
                    ELSE 'neutral'
                END,
                '{"backfilled": true, "original_type": "' || COALESCE(type, '') || '"}'
            FROM transactions
            WHERE amount_paise IS NOT NULL AND amount_paise != 0
        """)
        inserted = cur.rowcount
        conn.commit()
    except Exception as e:
        log.error("Backfill failed: %s", e)
        conn.rollback()
        conn.close()
        sys.exit(1)

    # Verify
    cur = conn.execute("SELECT COUNT(*) FROM financial_events WHERE event_type = 'transaction'")
    final_count = cur.fetchone()[0]

    conn.close()

    log.info("Backfill complete:")
    log.info("  Inserted: %d", inserted)
    log.info("  Final financial_events count: %d", final_count)
    log.info("Zero data loss: %s", "YES" if final_count >= source_count else "NO — investigate")


if __name__ == "__main__":
    backfill_events()