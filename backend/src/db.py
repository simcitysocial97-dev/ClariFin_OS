"""
db.py
=====
SQLite database manager for the personal finance tracker.
No ORM — raw sqlite3 only.

Database: data/finance.db (relative to CWD when instantiated)

Tables:
  statements   — one row per imported PDF
  transactions — one row per transaction, FK → statements

Usage:
  db = FinanceDB()
  with db:
      stmt_id = db.insert_statement("HDFC Bank", "hdfc_jun.pdf", "01/06/2025", "30/06/2025")
      db.insert_transactions(stmt_id, transactions)
"""

import contextlib
import sqlite3
import types
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Literal

# ============================================================
# Schema
# ============================================================

_DDL_STATEMENTS = """
CREATE TABLE IF NOT EXISTS statements (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    bank                 TEXT NOT NULL,
    card_last4           TEXT,
    statement_period_from TEXT,
    statement_period_to  TEXT,
    file_name            TEXT NOT NULL,
    imported_at          TEXT DEFAULT (datetime('now')),
    UNIQUE(bank, file_name)
);
"""

_DDL_TRANSACTIONS = """
CREATE TABLE IF NOT EXISTS transactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    statement_id    INTEGER NOT NULL REFERENCES statements(id),
    sequence_num    INTEGER NOT NULL DEFAULT 0,
    date            TEXT NOT NULL,
    description     TEXT,
    amount_paise    INTEGER NOT NULL DEFAULT 0,
    type            TEXT CHECK(type IN ('debit', 'credit', '')),
    category        TEXT DEFAULT 'Uncategorized',
    subcategory     TEXT,
    raw_description TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    date_iso        TEXT,
    hash_signature  TEXT,
    account_id      TEXT,
    member          TEXT DEFAULT 'Self',
    source          TEXT DEFAULT 'pdf',
    original_description TEXT,
    loan_id         INTEGER,
    investment_id   INTEGER,
    recurring_id    INTEGER,
    is_transfer     INTEGER DEFAULT 0,
    counterparty    TEXT,
    nature          TEXT DEFAULT 'unknown',
    credit INTEGER GENERATED ALWAYS AS (CASE WHEN type = 'credit' THEN amount_paise ELSE 0 END),
    debit INTEGER GENERATED ALWAYS AS (CASE WHEN type = 'debit' THEN amount_paise ELSE 0 END),
    UNIQUE(statement_id, date, description, amount_paise, sequence_num)
);
"""

_DDL_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_txn_date        ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_txn_category    ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_txn_statement   ON transactions(statement_id);
CREATE INDEX IF NOT EXISTS idx_txn_type        ON transactions(type);
"""

_DDL_MEMBERS = """
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    color TEXT DEFAULT '#6366F1',
    created_at TEXT DEFAULT (datetime('now'))
);
"""

_DDL_IMPORT_MAPPINGS = """
CREATE TABLE IF NOT EXISTS import_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mapping_name TEXT NOT NULL,
    date_column TEXT,
    description_column TEXT,
    amount_column TEXT,
    type_column TEXT,
    debit_value TEXT DEFAULT 'DR',
    credit_value TEXT DEFAULT 'CR',
    date_format TEXT DEFAULT '%d/%m/%Y',
    skip_rows INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

# Phase 2B.1: Reconciliation table (metadata-only, no ledger mutation)
# Enhanced schema with deterministic_key and confidence scoring
_DDL_RECONCILIATIONS = """
CREATE TABLE IF NOT EXISTS reconciliations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    debit_txn_id INTEGER NOT NULL REFERENCES transactions(id),
    credit_txn_id INTEGER NOT NULL REFERENCES transactions(id),

    debit_account_id TEXT NOT NULL,
    credit_account_id TEXT NOT NULL,

    amount_paise INTEGER NOT NULL,
    date_diff_days INTEGER NOT NULL DEFAULT 0,

    match_confidence REAL NOT NULL DEFAULT 0.0,
    match_type TEXT NOT NULL,  -- 'exact', 'window', 'fuzzy', 'manual'

    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'confirmed', 'rejected'

    deterministic_key TEXT NOT NULL UNIQUE,

    created_at TEXT DEFAULT (datetime('now')),
    confirmed_at TEXT,

    FOREIGN KEY(debit_txn_id) REFERENCES transactions(id),
    FOREIGN KEY(credit_txn_id) REFERENCES transactions(id)
);
"""


# ============================================================
# Module-level Utilities
# ============================================================


def _parse_date_to_ymd(date_str: str) -> str:
    """
    Parse Indian date formats to YYYY-MM-DD for sorting/grouping.
    Returns empty string if unparseable.
    Handles: DD/MM/YYYY, DD-MM-YYYY, DD/MM/YY, DD-MM-YY,
             DD Mon YYYY, DD Mon YY, DD-Mon-YYYY, DD-Mon-YY
    """
    from datetime import datetime

    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d/%m/%y",
        "%d-%m-%y",
        "%d %b %Y",
        "%d %b %y",
        "%d-%b-%Y",
        "%d-%b-%y",
    ]
    s = date_str.strip()
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""


# ============================================================
# Helpers
# ============================================================


def _parse_amount_paise(amount_str: str | int | float) -> int:
    """
    Parse amount to integer paise (1 rupee = 100 paise).
    Raises ValueError on invalid input (no silent failures).

    Accepts:
        - String amounts: "Rs 1,234.56", "₹1234.56", "1234"
        - Numeric amounts: 1234, 1234.56, 1234.0

    Examples:
        "Rs 1,234.56" -> 123456
        "₹1234.56"    -> 123456
        "1234"        -> 123400
        1234          -> 123400
        1234.56       -> 123456
    """
    # Convert to string if numeric
    if isinstance(amount_str, (int, float)):
        # For integers, treat as rupees
        if isinstance(amount_str, int):
            return amount_str * 100
        # For floats, use Decimal to avoid precision loss
        paise = Decimal(str(amount_str)) * Decimal("100")
        return int(paise.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    # Handle string input
    cleaned = (
        str(amount_str).replace("Rs", "").replace("₹", "").replace(",", "").strip()
    )

    if not cleaned:
        raise ValueError(f"Empty amount string: {amount_str!r}")

    try:
        rupees = Decimal(cleaned)
        # Financial Standard: Use quantization to guarantee safe integer conversion
        paise = (rupees * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return int(paise)
    except (ValueError, InvalidOperation) as e:
        raise ValueError(f"Invalid amount format '{amount_str}': {e}") from e


def _row_to_dict(cursor: sqlite3.Cursor, row: tuple[Any, ...]) -> dict[str, Any]:
    """Convert a sqlite3 row to a dict using cursor.description."""
    return {col[0]: row[i] for i, col in enumerate(cursor.description)}


# ============================================================
# FinanceDB
# ============================================================


class FinanceDB:
    """
    SQLite-backed storage for bank statements and transactions.
    Supports context manager protocol for automatic connection management.
    """

    def __init__(self, db_path: str = "data/finance.db"):
        self.db_path = str(db_path)
        # Ensure parent directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._create_tables()
        self._run_migrations()  # Phase 4: Add schema drift columns + new tables

    # ----------------------------------------------------------
    # Connection Management
    # ----------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self) -> None:
        with self._connect() as conn:
            conn.execute(_DDL_STATEMENTS)
            conn.execute(_DDL_TRANSACTIONS)
            for stmt in _DDL_INDEXES.strip().split(";"):
                stmt = stmt.strip()
                if stmt:
                    conn.execute(stmt)

            # Create new tables for members and import mappings
            conn.execute(_DDL_MEMBERS)
            conn.execute(_DDL_IMPORT_MAPPINGS)

            # Phase 2B.1: Create reconciliations table
            conn.execute(_DDL_RECONCILIATIONS)

            # Migration: add metadata columns if they don't exist
            _migration_columns = [
                ("statements", "total_amount_due", "REAL"),
                ("statements", "minimum_amount_due", "REAL"),
                ("statements", "payment_due_date", "TEXT"),
                ("statements", "statement_date", "TEXT"),
                ("statements", "credit_limit", "REAL"),
                ("statements", "opening_balance", "REAL"),
                ("statements", "bill_cycle_start", "TEXT"),
                ("statements", "bill_cycle_end", "TEXT"),
                ("statements", "validation_status", "TEXT DEFAULT 'pending'"),
                ("statements", "validation_difference", "REAL"),
                # New columns for source tracking
                ("statements", "source", "TEXT DEFAULT 'pdf'"),
                # New columns for member support
                ("transactions", "member", "TEXT DEFAULT 'Self'"),
                ("transactions", "source", "TEXT DEFAULT 'pdf'"),
                ("transactions", "original_description", "TEXT"),
                # Phase 2A: Financial determinism - paise columns
                ("transactions", "debit", "INTEGER DEFAULT 0"),
                ("transactions", "credit", "INTEGER DEFAULT 0"),
                ("transactions", "amount_paise", "INTEGER DEFAULT 0"),
                # Phase 2A.1: Determinism hardening
                ("transactions", "date_iso", "TEXT"),
                ("transactions", "hash_signature", "TEXT"),
                # Phase 2A.2: Account-scoped determinism
                ("transactions", "account_id", "TEXT"),
            ]
            for table, col, col_type in _migration_columns:
                try:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
                except Exception:
                    pass  # column already exists

            # Insert default member if not exists
            conn.execute("""
                INSERT OR IGNORE INTO members (name, color) VALUES ('Self', '#6366F1')
            """)

            # Phase 2A.1: Migrate date_iso column
            # Parse existing dates to ISO format (YYYY-MM-DD)
            try:
                # Fetch all transactions with dates but no date_iso
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
            except Exception:
                pass  # Migration already done or no data

            # Phase 2A.1: Compute hash_signature for existing transactions
            try:
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
            except Exception:
                pass  # Migration already done or no data

            # Phase 2A.1: Add deterministic indexes
            with contextlib.suppress(Exception):
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_txn_date_iso ON transactions(date_iso)"
                )

            # Phase 2A.2: Account-scoped determinism
            # Backfill account_id from statements.bank for existing transactions
            try:
                conn.execute("""
                    UPDATE transactions SET
                        account_id = (SELECT bank FROM statements WHERE id = statement_id)
                    WHERE account_id IS NULL OR account_id = ''
                """)
            except Exception:
                pass  # Migration already done or no data

            # Phase 2A.2: Drop old statement-scoped index, create account-scoped index
            try:
                conn.execute("DROP INDEX IF EXISTS idx_account_date_iso")
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_account_date_iso ON transactions(account_id, date_iso, id)"
                )
            except Exception:
                pass

            # Phase 2A.1: Add unique index on hash_signature (if not exists)
            try:
                conn.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_transaction_hash ON transactions(hash_signature)"
                )
            except Exception:
                pass  # May fail if duplicates exist

            # Phase 6C: Add loan-related indexes for query performance
            _loan_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_loan_payments_loan_id ON loan_payments(loan_id)",
                "CREATE INDEX IF NOT EXISTS idx_loan_payments_date ON loan_payments(payment_date)",
                "CREATE INDEX IF NOT EXISTS idx_loan_prepayments_loan_id ON loan_prepayments(loan_id)",
                "CREATE INDEX IF NOT EXISTS idx_loan_prepayments_date ON loan_prepayments(prepayment_date)",
                "CREATE INDEX IF NOT EXISTS idx_loan_rate_changes_loan_id ON loan_rate_changes(loan_id)",
                "CREATE INDEX IF NOT EXISTS idx_loan_rate_changes_date ON loan_rate_changes(change_date)",
                "CREATE INDEX IF NOT EXISTS idx_loan_payments_loan_date ON loan_payments(loan_id, payment_date)",
                "CREATE INDEX IF NOT EXISTS idx_loan_prepayments_loan_date ON loan_prepayments(loan_id, prepayment_date)",
                "CREATE INDEX IF NOT EXISTS idx_loan_rate_changes_loan_date ON loan_rate_changes(loan_id, change_date)",
            ]
            for idx_stmt in _loan_indexes:
                with contextlib.suppress(Exception):
                    conn.execute(idx_stmt)

            # Phase 2A.1: Add immutability triggers
            try:
                conn.execute("""
                    CREATE TRIGGER IF NOT EXISTS prevent_transaction_update
                    BEFORE UPDATE ON transactions
                    BEGIN
                        SELECT RAISE(ABORT, 'Transactions are immutable. Cannot update.');
                    END
                """)
                conn.execute("""
                    CREATE TRIGGER IF NOT EXISTS prevent_transaction_delete
                    BEFORE DELETE ON transactions
                    BEGIN
                        SELECT RAISE(ABORT, 'Transactions are immutable. Cannot delete.');
                    END
                """)
            except Exception:
                pass  # Triggers already exist

            conn.commit()

    # Context manager support
    def __enter__(self) -> "FinanceDB":
        self._conn = self._connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> Literal[False]:
        if self._conn:
            if exc_type is None:
                self._conn.commit()
            else:
                self._conn.rollback()
            self._conn.close()
            self._conn = None
        return False  # Don't suppress exceptions

    def _get_conn(self) -> sqlite3.Connection:
        """Return active connection or open a new one."""
        if self._conn is not None:
            return self._conn
        return self._connect()

    def _run_migrations(self) -> None:
        """
        Run database migrations for schema evolution.
        Creates accounts, loans, and investments tables.
        Handles column renames for backward compatibility.
        Safe to run on every startup.
        """
        conn = self._get_conn()

        # Create accounts, loans, and investments tables
        # These are not in DDL as they are Phase 2 additions
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                bank TEXT NOT NULL,
                account_type TEXT NOT NULL DEFAULT 'savings',
                balance_paise INTEGER NOT NULL DEFAULT 0,
                account_number_last4 TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS loans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                lender TEXT NOT NULL,
                loan_type TEXT NOT NULL,
                principal_paise INTEGER NOT NULL,
                outstanding_paise INTEGER NOT NULL,
                interest_rate REAL NOT NULL,
                tenure_months INTEGER,
                emi_paise INTEGER,
                disbursed_date TEXT NOT NULL,
                next_emi_date TEXT,
                gold_weight_grams REAL,
                gold_purity TEXT,
                interest_type TEXT DEFAULT 'reducing',
                is_active INTEGER NOT NULL DEFAULT 1,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS investments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                investment_type TEXT NOT NULL,
                units REAL,
                buy_price_paise INTEGER,
                current_price_paise INTEGER,
                invested_paise INTEGER NOT NULL,
                current_value_paise INTEGER NOT NULL,
                as_of_date TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS loan_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                loan_id INTEGER NOT NULL REFERENCES loans(id),
                payment_date TEXT NOT NULL,
                amount_paise INTEGER NOT NULL,
                principal_paise INTEGER,
                interest_paise INTEGER,
                late_fee_paise INTEGER DEFAULT 0,
                source_account_id TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS loan_prepayments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                loan_id INTEGER NOT NULL REFERENCES loans(id),
                amount_paise INTEGER NOT NULL,
                prepayment_date TEXT NOT NULL,
                mode TEXT DEFAULT 'reduce_tenure',
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS loan_rate_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                loan_id INTEGER NOT NULL REFERENCES loans(id),
                change_date TEXT NOT NULL,
                new_rate_bps INTEGER NOT NULL,
                mode TEXT DEFAULT 'adjust_emi',
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)

        # Migration: Rename columns in accounts table if they exist with old names
        # Handles backward compatibility for early schema versions
        try:
            cur = conn.execute("PRAGMA table_info(accounts)")
            columns = [row[1] for row in cur.fetchall()]
            if "bank_name" in columns and "bank" not in columns:
                conn.execute("ALTER TABLE accounts RENAME COLUMN bank_name TO bank")
            if (
                "account_number_masked" in columns
                and "account_number_last4" not in columns
            ):
                conn.execute(
                    "ALTER TABLE accounts RENAME COLUMN account_number_masked TO account_number_last4"
                )
            conn.commit()
        except Exception:
            pass  # SQLite version may not support RENAME COLUMN or already migrated


# ============================================================
# CLI / Quick Test
# ============================================================

if __name__ == "__main__":
    from src.db import FinanceDB

    db = FinanceDB()
    print(f"Database: {db.db_path}")
    print("Database schema initialized successfully.")
