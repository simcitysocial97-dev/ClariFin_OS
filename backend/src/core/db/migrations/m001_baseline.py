"""Migration 001 — baseline (M03).

This is a *move*, not a rewrite: the unmodified body of
`schema.py::run_migrations()` (column renames, `date_iso` backfill,
household column additions, the SHA256()/HEX() block left as-is),
adapted only to take an open connection instead of a db path.
"""

from __future__ import annotations

import contextlib
import logging
import sqlite3

from src.core.db.schema import _MIGRATION_COLUMNS, _parse_date_to_ymd

logger = logging.getLogger(__name__)


def migrate(conn: sqlite3.Connection) -> None:
    """Run baseline migrations. Idempotent."""
    for table, col, col_type in _MIGRATION_COLUMNS:
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
            logger.info("Migration: added column %s.%s", table, col)
        except sqlite3.OperationalError:
            pass

    try:
        cur = conn.execute("PRAGMA table_info(accounts)")
        columns = [row[1] for row in cur.fetchall()]
        if "bank_name" in columns and "bank" not in columns:
            conn.execute("ALTER TABLE accounts RENAME COLUMN bank_name TO bank")
            logger.info("Migration: renamed accounts.bank_name -> bank")
        if "account_number_masked" in columns and "account_number_last4" not in columns:
            conn.execute(
                "ALTER TABLE accounts RENAME COLUMN account_number_masked TO account_number_last4"
            )
            logger.info(
                "Migration: renamed accounts.account_number_masked -> account_number_last4"
            )
    except sqlite3.OperationalError as e:
        logger.warning("Migration: column rename skipped: %s", e)

    try:
        cur = conn.execute("""
            SELECT id, date FROM transactions
            WHERE date IS NOT NULL AND date != '' AND (date_iso IS NULL OR date_iso = '')
        """)
        rows = cur.fetchall()
        for row in rows:
            txn_id = row[0]
            date_str = row[1]
            date_iso = _parse_date_to_ymd(date_str)
            if date_iso:
                conn.execute(
                    "UPDATE transactions SET date_iso = ? WHERE id = ?",
                    (date_iso, txn_id),
                )
        if rows:
            logger.info("Migration: backfilled date_iso for %d transactions", len(rows))
    except sqlite3.OperationalError:
        pass

    # NOTE: see DB-003 investigation
    with contextlib.suppress(sqlite3.OperationalError):
        conn.execute("""
            UPDATE transactions SET
                hash_signature = LOWER(HEX(SHA256(
                    COALESCE((SELECT bank FROM statements WHERE id = statement_id), '') || '|' ||
                    COALESCE(date_iso, '') || '|' ||
                    COALESCE(description, '') || '|' ||
                    COALESCE(debit, 0) || '|' ||
                    COALESCE(credit, 0)
                )))
            WHERE hash_signature IS NULL AND date_iso IS NOT NULL
        """)

    with contextlib.suppress(sqlite3.OperationalError):
        conn.execute("""
            UPDATE transactions SET
                account_id = (SELECT bank FROM statements WHERE id = statement_id)
            WHERE account_id IS NULL OR account_id = ''
        """)

    # Apply household column migrations
    try:
        cur = conn.execute("PRAGMA table_info(accounts)")
        account_columns = {row[1] for row in cur.fetchall()}
        if "owner_id" not in account_columns:
            conn.execute("ALTER TABLE accounts ADD COLUMN owner_id TEXT DEFAULT 'self'")
            logger.info("Migration: added accounts.owner_id")
        if "household_id" not in account_columns:
            conn.execute(
                "ALTER TABLE accounts ADD COLUMN household_id TEXT DEFAULT 'primary'"
            )
            logger.info("Migration: added accounts.household_id")

        conn.execute("UPDATE accounts SET owner_id = 'self' WHERE owner_id IS NULL")
        conn.execute(
            "UPDATE accounts SET household_id = 'primary' WHERE household_id IS NULL"
        )
    except sqlite3.OperationalError as e:
        logger.warning("Migration: household columns skipped: %s", e)
