



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

import hashlib
import sqlite3
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

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
    amount          REAL NOT NULL,
    type            TEXT CHECK(type IN ('debit', 'credit', '')),
    category        TEXT DEFAULT 'Uncategorized',
    subcategory     TEXT,
    raw_description TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    amount_paise    INTEGER NOT NULL DEFAULT 0,
    date_iso        TEXT,
    hash_signature  TEXT,
    account_id      TEXT,
    member          TEXT DEFAULT 'Self',
    source          TEXT DEFAULT 'pdf',
    original_description TEXT,
    credit INTEGER GENERATED ALWAYS AS (CASE WHEN type = 'credit' THEN amount_paise ELSE 0 END),
    debit INTEGER GENERATED ALWAYS AS (CASE WHEN type = 'debit' THEN amount_paise ELSE 0 END),
    UNIQUE(statement_id, date, description, amount, sequence_num)
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

    amount REAL NOT NULL,
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
        "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y",
        "%d %b %Y", "%d %b %y", "%d-%b-%Y", "%d-%b-%y",
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

def _parse_amount_paise(amount_str) -> int:
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
        paise = Decimal(str(amount_str)) * Decimal('100')
        return int(paise.quantize(Decimal('1'), rounding=ROUND_HALF_UP))

    # Handle string input
    cleaned = (str(amount_str)
               .replace("Rs", "")
               .replace("₹", "")
               .replace(",", "")
               .strip())

    if not cleaned:
        raise ValueError(f"Empty amount string: {amount_str!r}")

    try:
        rupees = Decimal(cleaned)
        # Financial Standard: Use quantization to guarantee safe integer conversion
        paise = (rupees * Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        return int(paise)
    except (ValueError, InvalidOperation) as e:
        raise ValueError(f"Invalid amount format '{amount_str}': {e}") from e

def _row_to_dict(cursor: sqlite3.Cursor, row: tuple) -> dict:
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

            # Phase 2A: Migrate existing transactions to paise columns
            # This runs once when the new columns are added
            try:
                conn.execute("""
                    UPDATE transactions SET
                        amount_paise = ROUND(amount * 100),
                        debit = CASE WHEN type = 'debit' THEN ROUND(amount * 100) ELSE 0 END,
                        credit = CASE WHEN type = 'credit' THEN ROUND(amount * 100) ELSE 0 END
                    WHERE amount_paise = 0 AND amount IS NOT NULL
                """)
            except Exception:
                pass  # Migration already done or no data

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
                        conn.execute("UPDATE transactions SET date_iso = ? WHERE id = ?", (date_iso, txn_id))
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
            try:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_txn_date_iso ON transactions(date_iso)")
            except Exception:
                pass

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
                conn.execute("CREATE INDEX IF NOT EXISTS idx_account_date_iso ON transactions(account_id, date_iso, id)")
            except Exception:
                pass

            # Phase 2A.1: Add unique index on hash_signature (if not exists)
            try:
                conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_transaction_hash ON transactions(hash_signature)")
            except Exception:
                pass  # May fail if duplicates exist

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
    def __enter__(self):
        self._conn = self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
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
        Run database migrations to bring schema up to date.
        Safe to run on every startup — uses ADD COLUMN IF NOT EXISTS pattern.
        Never drops existing data.
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        migrations = [
            # Phase 1: Add columns that enrich_transaction computes at runtime
            # These were always being set but never formally in schema
            ("transactions", "amount_paise", "INTEGER"),
            ("transactions", "debit", "INTEGER DEFAULT 0"),
            ("transactions", "credit", "INTEGER DEFAULT 0"),
            ("transactions", "date_iso", "TEXT"),
            ("transactions", "member", "TEXT"),
            ("transactions", "account_id", "TEXT"),
            ("transactions", "hash_signature", "TEXT"),
        ]

        for table, column, col_type in migrations:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
                conn.commit()
            except Exception:
                # Column already exists — safe to ignore
                pass

        # Create new tables
        cursor.executescript("""
            -- Persistent accounts table
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

            -- Loans table
            CREATE TABLE IF NOT EXISTS loans (
                id TEXT PRIMARY KEY,
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

            -- Investments table
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
        """)

        # Migration: Rename columns in accounts table if they exist with old names
        # This handles the case where accounts table was created with bank_name/account_number_masked
        try:
            # Check if old columns exist
            cur = conn.execute("PRAGMA table_info(accounts)")
            columns = [row[1] for row in cur.fetchall()]
            if 'bank_name' in columns and 'bank' not in columns:
                # Need to migrate: rename columns
                conn.execute("ALTER TABLE accounts RENAME COLUMN bank_name TO bank")
            if 'account_number_masked' in columns and 'account_number_last4' not in columns:
                conn.execute("ALTER TABLE accounts RENAME COLUMN account_number_masked TO account_number_last4")
            conn.commit()
        except Exception:
            # SQLite version may not support RENAME COLUMN, or already migrated
            pass

        conn.commit()

    # ----------------------------------------------------------
    # Statement Methods
    # ----------------------------------------------------------

    def insert_statement(
        self,
        bank: str,
        file_name: str,
        period_from: str = "",
        period_to: str = "",
        card_last4: str = "",
    ) -> int:
        """
        Insert a statement record. If (bank, file_name) already exists,
        return the existing id without inserting.
        Returns statement_id (int).
        """
        conn = self._get_conn()
        # Check if already exists
        cur = conn.execute(
            "SELECT id FROM statements WHERE bank = ? AND file_name = ?",
            (bank, file_name),
        )
        row = cur.fetchone()
        if row:
            return row[0]

        cur = conn.execute(
            """
            INSERT INTO statements (bank, card_last4, statement_period_from, statement_period_to, file_name)
            VALUES (?, ?, ?, ?, ?)
            """,
            (bank, card_last4 or None, period_from or None, period_to or None, file_name),
        )
        if self._conn is None:
            conn.commit()
            conn.close()
        return cur.lastrowid

    def get_duplicate_check(self, bank: str, file_name: str) -> bool:
        """Returns True if (bank, file_name) already exists in statements."""
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT 1 FROM statements WHERE bank = ? AND file_name = ?",
            (bank, file_name),
        )
        result = cur.fetchone() is not None
        if self._conn is None:
            conn.close()
        return result

    def get_all_statements(self) -> list[dict]:
        """Get all statements with computed transaction counts and totals."""
        from src.repositories.statement_repository import StatementRepository
        return StatementRepository(self.db_path).get_all_statements()

    def get_statement_count(self) -> int:
        """Get total count of statements."""
        conn = self._get_conn()
        cur = conn.execute("SELECT COUNT(*) FROM statements")
        count = cur.fetchone()[0]
        if self._conn is None:
            conn.close()
        return count

    def get_transaction_count(self) -> int:
        """Get total count of transactions."""
        conn = self._get_conn()
        cur = conn.execute("SELECT COUNT(*) FROM transactions")
        count = cur.fetchone()[0]
        if self._conn is None:
            conn.close()
        return count

    def get_banks(self) -> list[str]:
        """Get distinct list of banks from statements."""
        conn = self._get_conn()
        cur = conn.execute("SELECT DISTINCT bank FROM statements ORDER BY bank")
        banks = [row[0] for row in cur.fetchall()]
        if self._conn is None:
            conn.close()
        return banks

    # ----------------------------------------------------------
    # Transaction Methods
    # ----------------------------------------------------------

    def insert_transactions(
        self, statement_id: int, transactions: list[dict]
    ) -> int:
        """
        Bulk insert transactions. Deduplicates by hash_signature.

        Phase 2A.1: Uses hash_signature for deduplication.
        Hash = SHA256(account_id | date_iso | description | debit | credit)

        Phase 2A: Also populates debit, credit, amount_paise columns for financial determinism.

        Returns count of rows actually inserted.
        """
        from src.repositories.transaction_repository import TransactionRepository
        return TransactionRepository(self.db_path).insert_transactions(statement_id=statement_id, transactions=transactions)



    def get_all_transactions(self, filters: dict | None = None) -> list[dict]:
        """
        Fetch transactions with optional filters.
        Supported filter keys: date_from, date_to, bank, category, min_amount, max_amount, type
        """
        from src.repositories.transaction_repository import TransactionRepository
        return TransactionRepository(self.db_path).get_all_transactions(filters=filters)



    def get_all_transactions_with_bank(self, filters: dict | None = None) -> list[dict]:
        """
        JOIN transactions with statements to include bank info.
        Returns list of dicts with all transaction + statement fields.
        Filters (all optional): search, bank, category, type, min_amount, max_amount, member.
        Date filtering is done in Python (dates stored as varied format strings).
        Order: transactions.id ASC (insertion order = chronological per statement).
        """
        from src.repositories.transaction_repository import TransactionRepository
        return TransactionRepository(self.db_path).get_all_transactions_with_bank(filters=filters)



    def bulk_update_category(
        self,
        transaction_ids: list[int],
        category: str,
        subcategory: str | None = None,
    ) -> int:
        """
        UPDATE transactions SET category=?, subcategory=? WHERE id IN (...).
        Returns number of rows updated.
        """
        from src.repositories.transaction_repository import TransactionRepository
        return TransactionRepository(self.db_path).bulk_update_category(
            transaction_ids=transaction_ids,
            category=category,
            subcategory=subcategory,
        )



    def get_uncategorized_patterns(self, limit: int = 50) -> list[dict]:
        """
        Returns grouped uncategorized transaction descriptions.
        [{description, count, total_amount}] ordered by count DESC.
        """
        from src.repositories.transaction_repository import TransactionRepository
        return TransactionRepository(self.db_path).get_uncategorized_patterns(limit=limit)

    def get_category_totals_by_month(self) -> list[dict]:
        """
        For stacked bar chart. Returns list of dicts:
        [{month: "2025-04", category: "Food & Dining", total: 2345.67}, ...]
        Uses Python-side date parsing to handle all date formats.
        """
        from src.repositories.transaction_repository import TransactionRepository
        return TransactionRepository(self.db_path).get_category_totals_by_month()

    def get_monthly_summary(self) -> list[dict]:
        """
        Returns monthly aggregates:
          [{month, total_debit, total_credit, transaction_count}]
        Month format: YYYY-MM (derived from date string).
        """
        from src.repositories.transaction_repository import TransactionRepository
        return TransactionRepository(self.db_path).get_monthly_summary()

    def get_category_summary(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict]:
        """
        Returns per-category aggregates:
          [{category, total_amount, count}]
        """
        from src.repositories.transaction_repository import TransactionRepository
        return TransactionRepository(self.db_path).get_category_summary(
            date_from=date_from,
            date_to=date_to,
        )

    # ----------------------------------------------------------
    # Cashflow Methods (new)
    # ----------------------------------------------------------

    def get_monthly_cashflow(
        self,
        months: int = 6,
        member: str | None = None,
    ) -> list[dict]:
        """
        Returns month-by-month income and expense aggregation.
        All monetary values in paise (INTEGER).
        Uses date_iso for proper month grouping.
        """
        from src.repositories.cashflow_repository import CashflowRepository
        return CashflowRepository(self.db_path).get_monthly_cashflow(months=months, member=member)


    # ----------------------------------------------------------
    # Metadata & Validation Methods (new)
    # ----------------------------------------------------------

    def update_statement_metadata(self, statement_id: int, metadata: dict) -> None:
        """Update statement with all extracted metadata."""
        from src.repositories.statement_repository import StatementRepository
        return StatementRepository(self.db_path).update_statement_metadata(statement_id, metadata)

    def update_validation_status(self, statement_id: int, status: str, difference: float) -> None:
        """Update validation status after comparing extracted sum vs total_due."""
        from src.repositories.statement_repository import StatementRepository
        return StatementRepository(self.db_path).update_validation_status(statement_id, status, difference)

    def get_statement_validation_summary(self) -> list[dict]:
        """Returns list of dicts for each statement with validation info."""
        from src.repositories.statement_repository import StatementRepository
        return StatementRepository(self.db_path).get_statement_validation_summary()

    def delete_statement(self, statement_id: int) -> None:
        """Delete a statement and all its transactions."""
        from src.repositories.statement_repository import StatementRepository
        return StatementRepository(self.db_path).delete_statement(statement_id)

    def get_statement_pdf_path(self, statement_id: int) -> str | None:
        """Get the file_name for a statement."""
        from src.repositories.statement_repository import StatementRepository
        return StatementRepository(self.db_path).get_statement_pdf_path(statement_id)

    def get_duplicate_check_by_filename(self, file_name: str) -> bool:
        """Returns True if file_name already exists in statements (any bank)."""
        from src.repositories.statement_repository import StatementRepository
        return StatementRepository(self.db_path).get_duplicate_check_by_filename(file_name)

    def get_all_statements_with_metadata(self) -> list[dict]:
        """
        Returns all statements with metadata + computed transaction counts and totals.
        Includes: total_amount_due, minimum_amount_due, payment_due_date,
                  validation_status, validation_difference, card_last4.
        """
        from src.repositories.statement_repository import StatementRepository
        return StatementRepository(self.db_path).get_all_statements_with_metadata()


    # ----------------------------------------------------------
    # Member Methods (new)
    # ----------------------------------------------------------

    def get_members(self) -> list[dict]:
        """Return all members as list of dicts."""
        from src.repositories.member_repository import MemberRepository
        return MemberRepository(self.db_path).get_all()

    def add_member(self, name: str, color: str = "#6366F1") -> int:
        """Add new family member. Return id."""
        from src.repositories.member_repository import MemberRepository
        return MemberRepository(self.db_path).create(name, color)

    # ----------------------------------------------------------
    # CSV/Excel Import Methods (new)
    # ----------------------------------------------------------

    def insert_csv_transactions(
        self,
        transactions: list[dict],
        member: str = "Self",
        source: str = "csv",
        bank: str = "Manual Import",
        file_name: str = "",
    ) -> int:
        """
        Insert transactions from CSV/Excel import.
        Each transaction dict: date, description, amount, type, category, subcategory.
        Creates a statement record with source='csv' and the filename.

        Phase 2A: Also populates debit, credit, amount_paise columns for financial determinism.

        Returns count of inserted transactions.
        """
        if not transactions:
            return 0

        conn = self._get_conn()

        # Create a statement record for this import
        cur = conn.execute(
            """
            INSERT INTO statements (bank, file_name, source)
            VALUES (?, ?, ?)
            """,
            (bank, file_name or f"{source}_import_{len(transactions)}_txns", source),
        )
        statement_id = cur.lastrowid

        inserted = 0
        for seq, txn in enumerate(transactions):
            # Parse amount to paise (source of truth)
            amount_paise = _parse_amount_paise(txn.get("amount", "0"))
            # Derive float for backward compatibility
            amount = amount_paise / 100.0
            date = str(txn.get("date", "")).strip()
            description = str(txn.get("description", "")).strip()
            original_description = str(txn.get("original_description", description)).strip()
            txn_type = str(txn.get("type", "")).strip()
            category = str(txn.get("category", "Uncategorized")).strip() or "Uncategorized"
            subcategory = str(txn.get("subcategory", "")).strip() or None

            # Phase 2A: Compute debit/credit paise values
            debit_paise = amount_paise if txn_type == 'debit' else 0
            credit_paise = amount_paise if txn_type == 'credit' else 0

            # Phase 2A.1: Compute date_iso
            date_iso = _parse_date_to_ymd(date) if date else ""

            # Phase 2A.1: Compute hash_signature
            hash_input = f"{bank}|{date_iso}|{description}|{debit_paise}|{credit_paise}"
            hash_signature = hashlib.sha256(hash_input.encode()).hexdigest().lower()

            if not date:
                continue

            cur = conn.execute(
                """
                INSERT OR IGNORE INTO transactions
                    (statement_id, sequence_num, date, description, amount, type,
                     category, subcategory, member, source, original_description,
                     amount_paise, date_iso, hash_signature, account_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    statement_id,
                    seq,
                    date,
                    description,
                    amount,
                    txn_type,
                    category,
                    subcategory,
                    member,
                    source,
                    original_description,
                    amount_paise,
                    date_iso,
                    hash_signature,
                    bank,  # account_id = bank for CSV imports
                ),
            )
            inserted += cur.rowcount

        if self._conn is None:
            conn.commit()
            conn.close()

        return inserted

    # ----------------------------------------------------------
    # Import Mapping Methods (new)
    # ----------------------------------------------------------

    def save_import_mapping(self, mapping: dict) -> int:
        """Save a column mapping configuration for reuse."""
        conn = self._get_conn()
        cur = conn.execute(
            """
            INSERT INTO import_mappings
                (mapping_name, date_column, description_column, amount_column,
                 type_column, debit_value, credit_value, date_format, skip_rows)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mapping.get("mapping_name", "Unnamed"),
                mapping.get("date_column"),
                mapping.get("description_column"),
                mapping.get("amount_column"),
                mapping.get("type_column"),
                mapping.get("debit_value", "DR"),
                mapping.get("credit_value", "CR"),
                mapping.get("date_format", "%d/%m/%Y"),
                mapping.get("skip_rows", 0),
            ),
        )
        if self._conn is None:
            conn.commit()
            conn.close()
        return cur.lastrowid

    def get_import_mappings(self) -> list[dict]:
        """Get all saved import mappings."""
        conn = self._get_conn()
        cur = conn.execute("""
            SELECT id, mapping_name, date_column, description_column, amount_column,
                   type_column, debit_value, credit_value, date_format, skip_rows, created_at
            FROM import_mappings
            ORDER BY created_at DESC
        """)
        rows = [dict(row) for row in cur.fetchall()]
        if self._conn is None:
            conn.close()
        return rows

    # ----------------------------------------------------------
    # Reconciliation Methods (Phase 2B)
    # ----------------------------------------------------------

    def insert_reconciliation(
        self,
        debit_txn_id: int,
        credit_txn_id: int,
        debit_account_id: str,
        credit_account_id: str,
        amount: float,
        date_diff_days: int,
        match_confidence: float,
        match_type: str,
    ) -> bool:
        """
        Insert a reconciliation record using INSERT OR IGNORE for idempotency.

        Phase 2B: Metadata-only, no ledger mutation.
        Uses deterministic_key to prevent duplicates.

        Args:
            debit_txn_id: Transaction ID with debit
            credit_txn_id: Transaction ID with credit
            debit_account_id: Account ID of debit transaction
            credit_account_id: Account ID of credit transaction
            amount: Matched amount in rupees
            date_diff_days: Days between transaction dates
            match_confidence: Confidence score (0.0-1.0)
            match_type: 'exact', 'window', 'fuzzy', or 'manual'

        Returns:
            True if inserted, False if already exists (ignored)
        """
        from src.repositories.reconciliation_repository import ReconciliationRepository
        return ReconciliationRepository(self.db_path).insert_reconciliation(
            debit_txn_id=debit_txn_id,
            credit_txn_id=credit_txn_id,
            debit_account_id=debit_account_id,
            credit_account_id=credit_account_id,
            amount=amount,
            date_diff_days=date_diff_days,
            match_confidence=match_confidence,
            match_type=match_type,
        )

    def get_reconciliations(self, status: str | None = None) -> list[dict]:
        """
        Get all reconciliations with transaction details.

        Args:
            status: Optional filter by status ('pending', 'confirmed', 'rejected')

        Returns:
            List of reconciliation records with transaction details including bank names
        """
        from src.repositories.reconciliation_repository import ReconciliationRepository
        return ReconciliationRepository(self.db_path).get_reconciliations(status=status)

    def confirm_reconciliation(self, reconciliation_id: int) -> bool:
        """
        Confirm a pending reconciliation.

        Phase 2B: Updates reconciliation.status only. No ledger mutation.

        Returns:
            True if updated, False if not found or not pending
        """
        from src.repositories.reconciliation_repository import ReconciliationRepository
        return ReconciliationRepository(self.db_path).confirm_reconciliation(reconciliation_id)

    def reject_reconciliation(self, reconciliation_id: int) -> bool:
        """
        Reject a pending reconciliation.

        Phase 2B: Updates reconciliation.status only. No ledger mutation.

        Returns:
            True if updated, False if not found or not pending
        """
        from src.repositories.reconciliation_repository import ReconciliationRepository
        return ReconciliationRepository(self.db_path).reject_reconciliation(reconciliation_id)

    def get_pending_reconciliations(self) -> list[dict]:
        """Get all pending reconciliations."""
        from src.repositories.reconciliation_repository import ReconciliationRepository
        return ReconciliationRepository(self.db_path).get_pending_reconciliations()

    def get_confirmed_transfer_ids(self) -> list[tuple]:
        """
        Get all transaction IDs involved in confirmed transfers.

        Returns list of (debit_txn_id, credit_txn_id) tuples for confirmed reconciliations.
        Used by analytics to exclude transfers from spending totals.
        """
        from src.repositories.reconciliation_repository import ReconciliationRepository
        return ReconciliationRepository(self.db_path).get_confirmed_transfer_ids()

    # ─── ACCOUNTS ─────────────────────────────────────────────────────────────

    def get_all_accounts(self) -> list[dict]:
        """Get all active persistent accounts."""
        from src.repositories.account_repository import AccountRepository
        return AccountRepository(self.db_path).get_all_accounts()

    def create_account(self, account_id: int | str, name: str, bank: str,
                       account_type: str, balance_paise: int,
                       account_number_last4: str | None = None,
                       notes: str | None = None) -> dict:
        """Create a new persistent account."""
        from src.repositories.account_repository import AccountRepository
        return AccountRepository(self.db_path).create_account(
            name, bank, account_type, balance_paise, account_number_last4, notes
        )

    def get_account_by_id(self, account_id: int | str) -> dict | None:
        """Get a single account by ID."""
        from src.repositories.account_repository import AccountRepository
        return AccountRepository(self.db_path).get_account_by_id(account_id)

    def update_account(self, account_id: int | str, **kwargs) -> dict | None:
        """Update account fields. Only updates provided fields."""
        from src.repositories.account_repository import AccountRepository
        return AccountRepository(self.db_path).update_account(account_id, **kwargs)

    def delete_account(self, account_id: int | str) -> bool:
        """Soft delete an account."""
        from src.repositories.account_repository import AccountRepository
        return AccountRepository(self.db_path).delete_account(account_id)


    # ─── LOANS ────────────────────────────────────────────────────────────────

    def get_all_loans(self) -> list[dict]:
        """Get all active loans."""
        from src.repositories.loan_repository import LoanRepository
        return LoanRepository(self.db_path).get_all()

    def create_loan(self, loan_id: int | str, name: str, lender: str,
                    loan_type: str, principal_paise: int,
                    outstanding_paise: int, interest_rate: float,
                    disbursed_date: str, tenure_months: int | None = None,
                    emi_paise: int | None = None,
                    next_emi_date: str | None = None,
                    gold_weight_grams: float | None = None,
                    gold_purity: str | None = None,
                    interest_type: str = 'reducing',
                    notes: str | None = None) -> dict:
        """Create a new loan record."""
        from src.repositories.loan_repository import LoanRepository
        return LoanRepository(self.db_path).create(
            name, lender, loan_type, principal_paise,
            outstanding_paise, interest_rate, disbursed_date,
            tenure_months, emi_paise, next_emi_date,
            gold_weight_grams, gold_purity, interest_type, notes
        )

    def get_loan_by_id(self, loan_id: int | str) -> dict | None:
        """Get a single loan by ID."""
        from src.repositories.loan_repository import LoanRepository
        return LoanRepository(self.db_path).get_by_id(loan_id)

    def update_loan(self, loan_id: int | str, **kwargs) -> dict | None:
        """Update loan fields. Only updates provided fields."""
        from src.repositories.loan_repository import LoanRepository
        return LoanRepository(self.db_path).update(loan_id, **kwargs)

    def delete_loan(self, loan_id: int | str) -> bool:
        """Soft delete a loan (set is_active to 0)."""
        from src.repositories.loan_repository import LoanRepository
        return LoanRepository(self.db_path).delete(loan_id)

    # ─── INVESTMENTS ─────────────────────────────────────────────────────────

    def get_all_investments(self) -> list[dict]:
        """Get all active investments."""
        from src.repositories.investment_repository import InvestmentRepository
        return InvestmentRepository(self.db_path).get_all()

    def create_investment(self, investment_id: int | str, name: str,
                          investment_type: str, invested_paise: int,
                          current_value_paise: int,
                          platform: str | None = None, units: float | None = None,
                          purchase_date: str | None = None,
                          maturity_date: str | None = None,
                          linked_account_id: int | None = None,
                          notes: str | None = None) -> dict:
        """Create a new investment record."""
        conn = self._get_conn()
        # Use auto-increment for existing schema (id is INTEGER PRIMARY KEY)
        cur = conn.execute("""
            INSERT INTO investments (name, type, platform, invested_paise,
                                     current_value_paise, units, purchase_date,
                                     maturity_date, linked_account_id, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, investment_type, platform, invested_paise,
              current_value_paise, units, purchase_date,
              maturity_date, linked_account_id, notes))
        conn.commit()
        if self._conn is None:
            conn.close()
        return self.get_investment_by_id(cur.lastrowid)

    def get_investment_by_id(self, investment_id: int | str) -> dict | None:
        """Get a single investment by ID."""
        from src.repositories.investment_repository import InvestmentRepository
        return InvestmentRepository(self.db_path).get_by_id(investment_id)

    def update_investment(self, investment_id: int | str, **kwargs) -> dict | None:
        """Update investment fields. Only updates provided fields."""
        from src.repositories.investment_repository import InvestmentRepository
        return InvestmentRepository(self.db_path).update(investment_id, **kwargs)

    def delete_investment(self, investment_id: int | str) -> bool:
        """Soft delete an investment."""
        from src.repositories.investment_repository import InvestmentRepository
        return InvestmentRepository(self.db_path).delete(investment_id)

    def get_networth_data(self) -> dict:
        """
        Get all data needed for net worth calculation.
        Returns accounts, loans, investments, and statements for the networth endpoint.
        """
        from src.repositories.networth_repository import NetWorthRepository
        return NetWorthRepository(self.db_path).get_networth_data()

    def get_net_worth(self) -> dict:
        """
        Calculate net worth from accounts, loans, and investments.
        Returns:
            {
                total_assets_paise: int,
                total_liabilities_paise: int,
                net_worth_paise: int,
                accounts_total_paise: int,
                loans_total_paise: int,
                investments_total_paise: int
            }
        """
        from src.repositories.networth_repository import NetWorthRepository
        return NetWorthRepository(self.db_path).get_net_worth()


# ============================================================
# CLI / Quick Test
# ============================================================

if __name__ == "__main__":

    db = FinanceDB()
    print(f"Database: {db.db_path}")
    print(f"Statements: {db.get_statement_count()}")
    print(f"Transactions: {db.get_transaction_count()}")
    print(f"Banks: {db.get_banks()}")

    summary = db.get_category_summary()
    if summary:
        print("\nCategory Summary:")
        for row in summary[:10]:
            print(f"  {row['category']:30s} ₹{row['total_amount']:>12,.2f}  ({row['count']} txns)")
    else:
        print("\nNo transactions yet. Run ingest.py to import PDFs.")
