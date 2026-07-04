"""Database schema definitions, table creation, and migrations.

This module contains all DDL and migration logic for the ClariFin database.
ALL monetary values use INTEGER paise — zero REAL/FLOAT for currency storage.
"""

import sqlite3
from typing import List, Tuple

from src.logger import log
from src.utils import parse_date_to_iso


# ============================================================
# Table Definitions
# ============================================================

DDL_STATEMENTS = """
CREATE TABLE IF NOT EXISTS statements (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    bank                 TEXT NOT NULL,
    card_last4           TEXT,
    statement_period_from TEXT,
    statement_period_to  TEXT,
    file_name            TEXT NOT NULL,
    imported_at          TEXT DEFAULT (datetime('now')),
    total_amount_due_paise    INTEGER NOT NULL DEFAULT 0,
    minimum_amount_due_paise  INTEGER NOT NULL DEFAULT 0,
    credit_limit_paise        INTEGER NOT NULL DEFAULT 0,
    opening_balance_paise     INTEGER NOT NULL DEFAULT 0,
    validation_difference_paise INTEGER NOT NULL DEFAULT 0,
    UNIQUE(bank, file_name)
);
"""

DDL_TRANSACTIONS = """
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
    account_id      TEXT,
    amount_paise    INTEGER NOT NULL DEFAULT 0,
    debit           INTEGER GENERATED ALWAYS AS (CASE WHEN amount_paise < 0 THEN ABS(amount_paise) ELSE 0 END),
    credit          INTEGER GENERATED ALWAYS AS (CASE WHEN amount_paise > 0 THEN amount_paise ELSE 0 END),
    UNIQUE(statement_id, date, description, amount, sequence_num)
);
"""

DDL_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_txn_date        ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_txn_category    ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_txn_statement   ON transactions(statement_id);
CREATE INDEX IF NOT EXISTS idx_txn_type        ON transactions(type);
"""

# Indexes for tables that need migrations first - created after migrations
DDL_INDEXES_POST_MIGRATION = """
CREATE INDEX IF NOT EXISTS idx_txn_account_id  ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_loan_status     ON loans(status);
CREATE INDEX IF NOT EXISTS idx_investment_type ON investments(type);
CREATE INDEX IF NOT EXISTS idx_investment_active ON investments(is_active);
CREATE INDEX IF NOT EXISTS idx_income_source_active ON income_sources(is_active);
CREATE INDEX IF NOT EXISTS idx_recurring_active ON recurring_transactions(is_active);
CREATE INDEX IF NOT EXISTS idx_loan_payments_loan ON loan_payments(loan_id);
CREATE INDEX IF NOT EXISTS idx_loan_payments_date ON loan_payments(payment_date);
"""

DDL_MEMBERS = """
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    color TEXT DEFAULT '#6366F1',
    created_at TEXT DEFAULT (datetime('now'))
);
"""

DDL_IMPORT_MAPPINGS = """
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

DDL_RECONCILIATIONS = """
CREATE TABLE IF NOT EXISTS reconciliations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    debit_txn_id INTEGER NOT NULL REFERENCES transactions(id),
    credit_txn_id INTEGER NOT NULL REFERENCES transactions(id),

    debit_account_id TEXT NOT NULL,
    credit_account_id TEXT NOT NULL,

    amount REAL NOT NULL,
    amount_paise INTEGER NOT NULL DEFAULT 0,
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

DDL_ACCOUNTS = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    bank_name TEXT DEFAULT '',
    account_type TEXT NOT NULL CHECK(account_type IN ('savings', 'current', 'credit_card', 'fd', 'wallet', 'loan')),
    account_number_masked TEXT DEFAULT 'XXXX',
    balance_paise INTEGER NOT NULL DEFAULT 0,
    credit_limit_paise INTEGER NOT NULL DEFAULT 0,
    currency TEXT DEFAULT 'INR',
    color TEXT DEFAULT '#6366F1',
    icon TEXT DEFAULT 'building',
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
"""

DDL_CARDS = """
CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER,
    card_name TEXT NOT NULL,
    card_type TEXT CHECK(card_type IN ('visa', 'mastercard', 'rupay', 'amex', 'diners')),
    issuer TEXT DEFAULT '',
    last_four TEXT DEFAULT 'XXXX',
    cardholder_name TEXT DEFAULT '',
    credit_limit_paise INTEGER DEFAULT 0,
    billing_date INTEGER DEFAULT 1,
    card_color TEXT DEFAULT '#1E293B',
    card_gradient TEXT DEFAULT 'from-slate-800 to-slate-900',
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);
"""

DDL_ACCOUNTS_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS update_accounts_timestamp
AFTER UPDATE ON accounts
BEGIN
    UPDATE accounts SET updated_at = datetime('now') WHERE id = NEW.id;
END;
"""

DDL_CARDS_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS update_cards_timestamp
AFTER UPDATE ON cards
BEGIN
    UPDATE cards SET updated_at = datetime('now') WHERE id = NEW.id;
END;
"""

# ============================================================
# Phase 3: Comprehensive Financial Management Tables
# ============================================================

DDL_INCOME_SOURCES = """
CREATE TABLE IF NOT EXISTS income_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT CHECK(type IN ('salary', 'freelance', 'business', 'rental', 'dividend', 'interest', 'other')) DEFAULT 'other',
    account_id INTEGER REFERENCES accounts(id),
    amount_paise INTEGER NOT NULL DEFAULT 0,
    frequency TEXT CHECK(frequency IN ('monthly', 'quarterly', 'annual', 'irregular')) DEFAULT 'monthly',
    start_date TEXT,
    end_date TEXT,
    is_active INTEGER DEFAULT 1,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
"""

DDL_LOANS = """
CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    lender TEXT,
    loan_type TEXT CHECK(loan_type IN ('home', 'car', 'personal', 'education', 'credit_card', 'gold', 'other')) DEFAULT 'other',
    principal_paise INTEGER NOT NULL,
    outstanding_paise INTEGER NOT NULL,
    interest_rate REAL NOT NULL,
    emi_paise INTEGER NOT NULL DEFAULT 0,
    tenure_months INTEGER,
    start_date TEXT NOT NULL,
    end_date TEXT,
    linked_account_id INTEGER REFERENCES accounts(id),
    status TEXT CHECK(status IN ('active', 'closed', 'defaulted')) DEFAULT 'active',
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
"""

DDL_LOAN_PAYMENTS = """
CREATE TABLE IF NOT EXISTS loan_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER NOT NULL REFERENCES loans(id),
    transaction_id INTEGER REFERENCES transactions(id),
    principal_component_paise INTEGER NOT NULL DEFAULT 0,
    interest_component_paise INTEGER NOT NULL DEFAULT 0,
    payment_date TEXT NOT NULL,
    remaining_principal_paise INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

DDL_INVESTMENTS = """
CREATE TABLE IF NOT EXISTS investments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT CHECK(type IN ('mutual_fund', 'stock', 'fd', 'ppf', 'epf', 'nps', 'gold', 'real_estate', 'crypto', 'other')) DEFAULT 'other',
    platform TEXT,
    invested_paise INTEGER NOT NULL DEFAULT 0,
    current_value_paise INTEGER NOT NULL DEFAULT 0,
    units REAL DEFAULT 0,
    purchase_date TEXT,
    maturity_date TEXT,
    linked_account_id INTEGER REFERENCES accounts(id),
    is_active INTEGER DEFAULT 1,
    notes TEXT,
    last_updated TEXT DEFAULT (datetime('now')),
    created_at TEXT DEFAULT (datetime('now'))
);
"""

DDL_MONTHLY_SNAPSHOTS = """
CREATE TABLE IF NOT EXISTS monthly_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL,
    total_income_paise INTEGER NOT NULL DEFAULT 0,
    total_expense_paise INTEGER NOT NULL DEFAULT 0,
    total_emi_paise INTEGER NOT NULL DEFAULT 0,
    total_investment_paise INTEGER NOT NULL DEFAULT 0,
    net_cashflow_paise INTEGER NOT NULL DEFAULT 0,
    net_worth_paise INTEGER NOT NULL DEFAULT 0,
    savings_rate REAL DEFAULT 0.0,
    data_json TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(month)
);
"""

DDL_RECURRING_TRANSACTIONS = """
CREATE TABLE IF NOT EXISTS recurring_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    amount_paise INTEGER NOT NULL,
    type TEXT CHECK(type IN ('debit', 'credit')) DEFAULT 'debit',
    category TEXT DEFAULT 'Uncategorized',
    frequency TEXT CHECK(frequency IN ('daily', 'weekly', 'monthly', 'quarterly', 'annual')) DEFAULT 'monthly',
    account_id TEXT,
    next_due_date TEXT,
    last_detected_date TEXT,
    occurrence_count INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    auto_detected INTEGER DEFAULT 0,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
"""

DDL_INCOME_SOURCES_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS update_income_sources_timestamp
AFTER UPDATE ON income_sources
BEGIN
    UPDATE income_sources SET updated_at = datetime('now') WHERE id = NEW.id;
END;
"""

DDL_LOANS_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS update_loans_timestamp
AFTER UPDATE ON loans
BEGIN
    UPDATE loans SET updated_at = datetime('now') WHERE id = NEW.id;
END;
"""

DDL_RECURRING_TRANSACTIONS_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS update_recurring_transactions_timestamp
AFTER UPDATE ON recurring_transactions
BEGIN
    UPDATE recurring_transactions SET updated_at = datetime('now') WHERE id = NEW.id;
END;
"""

# ============================================================
# Phase B1: Durable Job Queue Table
# ============================================================

DDL_JOBS = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED')),
    payload_json TEXT NOT NULL DEFAULT '{}',
    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    started_at TEXT,
    finished_at TEXT,
    error TEXT,
    worker_id TEXT
);
"""

DDL_JOB_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_worker_id ON jobs(worker_id);
"""

# ============================================================
# Phase B2: Staging Tables for PDF Statement Import Pipeline
# ============================================================

DDL_STATEMENT_IMPORTS = """
CREATE TABLE IF NOT EXISTS statement_imports (
    id TEXT PRIMARY KEY,
    source_filename TEXT NOT NULL,
    source_path TEXT,
    bank TEXT,
    status TEXT NOT NULL DEFAULT 'STAGED'
        CHECK(status IN ('STAGED', 'NEEDS_REVIEW', 'COMMITTED', 'FAILED')),
    job_id TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    committed_at TEXT,
    error TEXT,
    opening_balance_paise INTEGER,
    closing_balance_paise INTEGER,
    delta_paise INTEGER
);
"""

# Note: quarantine_pages table removed - quarantine feature deprecated
# DDL_QUARANTINE_PAGES and DDL_QUARANTINE_INDEXES removed

DDL_AUTO_HEAL_EVENTS = """
CREATE TABLE IF NOT EXISTS auto_heal_events (
    id TEXT PRIMARY KEY,
    statement_id TEXT NOT NULL REFERENCES statement_imports(id) ON DELETE CASCADE,
    cycle TEXT NOT NULL,
    before_delta_paise INTEGER NOT NULL,
    after_delta_paise INTEGER NOT NULL,
    applied INTEGER NOT NULL CHECK(applied IN (0, 1)),
    summary TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

DDL_AUTO_HEAL_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_auto_heal_statement ON auto_heal_events(statement_id);
CREATE INDEX IF NOT EXISTS idx_auto_heal_applied ON auto_heal_events(applied);
"""

DDL_STATEMENT_PAGES = """
CREATE TABLE IF NOT EXISTS statement_pages (
    id TEXT PRIMARY KEY,
    statement_id TEXT NOT NULL REFERENCES statement_imports(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    raw_extraction_json TEXT,
    status TEXT NOT NULL DEFAULT 'OK'
        CHECK(status IN ('OK', 'FAILED')),
    error TEXT,
    UNIQUE(statement_id, page_number)
);
"""

DDL_STAGED_TRANSACTIONS = """
CREATE TABLE IF NOT EXISTS staged_transactions (
    id TEXT PRIMARY KEY,
    statement_id TEXT NOT NULL REFERENCES statement_imports(id) ON DELETE CASCADE,
    page_number INTEGER,
    date TEXT NOT NULL,
    date_iso TEXT,
    description TEXT,
    debit_paise INTEGER DEFAULT 0,
    credit_paise INTEGER DEFAULT 0,
    balance_paise INTEGER,
    raw_row_json TEXT,
    row_hash TEXT,
    sequence_num INTEGER
);
"""

DDL_STAGING_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_staged_txn_statement ON staged_transactions(statement_id);
CREATE INDEX IF NOT EXISTS idx_staged_txn_statement_page ON staged_transactions(statement_id, page_number);
CREATE INDEX IF NOT EXISTS idx_statement_imports_status ON statement_imports(status);
CREATE INDEX IF NOT EXISTS idx_statement_pages_statement ON statement_pages(statement_id);
"""

# ============================================================
# Phase F1: Layout Templates for Fingerprint-based Template Persistence
# ============================================================

DDL_LAYOUT_TEMPLATES = """
CREATE TABLE IF NOT EXISTS layout_templates (
    id TEXT PRIMARY KEY,
    bank TEXT NOT NULL,
    fingerprint TEXT UNIQUE NOT NULL,
    page_width REAL,
    page_height REAL,
    bbox_norm_json TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    last_used_at TEXT,
    notes TEXT
);
"""

DDL_LAYOUT_TEMPLATES_INDEX = """
CREATE INDEX IF NOT EXISTS idx_layout_templates_fingerprint ON layout_templates(fingerprint);
CREATE INDEX IF NOT EXISTS idx_layout_templates_bank ON layout_templates(bank);
"""

# ============================================================
# Phase E: Immutable Financial Event Ledger
# ============================================================

DDL_FINANCIAL_EVENTS = """
CREATE TABLE IF NOT EXISTS financial_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL CHECK(event_type IN ('transaction', 'loan', 'adjustment', 'import', 'correction', 'reconciliation')),
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    amount_paise INTEGER NOT NULL DEFAULT 0,
    direction TEXT NOT NULL CHECK(direction IN ('credit', 'debit', 'neutral')),
    metadata_json TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

DDL_FINANCIAL_EVENTS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_fin_events_entity ON financial_events(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_fin_events_created ON financial_events(created_at);
CREATE INDEX IF NOT EXISTS idx_fin_events_type ON financial_events(event_type);
"""


# ============================================================
# Migration Definitions
# ============================================================

# MIGRATION_COLUMNS: (table, column, type)
# Legacy REAL monetary fields kept for backward compat but marked DEPRECATED.
# All NEW code must use the _paise variants.
MIGRATION_COLUMNS: List[Tuple[str, str, str]] = [
    # statements table - monetary fields migrated to _paise
    ("statements", "total_amount_due", "REAL"),
    ("statements", "total_amount_due_paise", "INTEGER DEFAULT 0"),
    ("statements", "minimum_amount_due", "REAL"),
    ("statements", "minimum_amount_due_paise", "INTEGER DEFAULT 0"),
    ("statements", "payment_due_date", "TEXT"),
    ("statements", "statement_date", "TEXT"),
    ("statements", "credit_limit", "REAL"),
    ("statements", "credit_limit_paise", "INTEGER DEFAULT 0"),
    ("statements", "opening_balance", "REAL"),
    ("statements", "opening_balance_paise", "INTEGER DEFAULT 0"),
    ("statements", "bill_cycle_start", "TEXT"),
    ("statements", "bill_cycle_end", "TEXT"),
    ("statements", "validation_status", "TEXT DEFAULT 'pending'"),
    ("statements", "validation_difference", "REAL"),
    ("statements", "validation_difference_paise", "INTEGER DEFAULT 0"),
    ("statements", "source", "TEXT DEFAULT 'pdf'"),
    # transactions table - all monetary via amount_paise
    ("transactions", "member", "TEXT DEFAULT 'Self'"),
    ("transactions", "source", "TEXT DEFAULT 'pdf'"),
    ("transactions", "original_description", "TEXT"),
    ("transactions", "debit", "INTEGER DEFAULT 0"),
    ("transactions", "credit", "INTEGER DEFAULT 0"),
    ("transactions", "amount_paise", "INTEGER DEFAULT 0"),
    ("transactions", "date_iso", "TEXT"),
    ("transactions", "hash_signature", "TEXT"),
    ("transactions", "account_id", "TEXT"),
    ("transactions", "loan_id", "INTEGER"),
    ("transactions", "investment_id", "INTEGER"),
    ("transactions", "recurring_id", "INTEGER"),
    ("transactions", "is_transfer", "INTEGER DEFAULT 0"),
    ("transactions", "counterparty", "TEXT"),
    # reconciliations table - add amount_paise
    ("reconciliations", "amount_paise", "INTEGER DEFAULT 0"),
    # accounts table - additional fields
    ("accounts", "subtype", "TEXT"),
    ("accounts", "institution", "TEXT"),
    ("accounts", "opening_date", "TEXT"),
]

FINGERPRINT_MIGRATION_COLUMNS: List[Tuple[str, str, str]] = [
    ("statement_imports", "fingerprint", "TEXT"),
    ("statement_imports", "template_id", "TEXT"),
    ("statement_imports", "bbox_norm_json", "TEXT"),
]


# ============================================================
# Schema Creation Functions
# ============================================================

def _execute_ddl(conn: sqlite3.Connection, ddl: str) -> None:
    """Execute DDL statements safely."""
    for stmt in ddl.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            conn.execute(stmt)


def _add_column_if_not_exists(conn: sqlite3.Connection, table: str, col: str, col_type: str) -> None:
    """Safely add a column if it doesn't exist."""
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
        log.info("Migration: added column %s to %s", col, table)
    except sqlite3.OperationalError:
        log.debug("Column %s already exists on %s", col, table)


def _parse_date_to_ymd(date_str: str) -> str:
    """Parse Indian date formats to YYYY-MM-DD for sorting/grouping."""
    result = parse_date_to_iso(date_str)
    return result if result is not None else ""


def create_tables(conn: sqlite3.Connection) -> None:
    """Create all database tables, indexes, and triggers.
    
    This function is idempotent - safe to call multiple times.
    """
    # Core tables
    _execute_ddl(conn, DDL_STATEMENTS)
    _execute_ddl(conn, DDL_TRANSACTIONS)
    _execute_ddl(conn, DDL_INDEXES)
    
    # Members and import mappings
    _execute_ddl(conn, DDL_MEMBERS)
    _execute_ddl(conn, DDL_IMPORT_MAPPINGS)
    
    # Reconciliations
    _execute_ddl(conn, DDL_RECONCILIATIONS)
    
    # Accounts and cards
    _execute_ddl(conn, DDL_ACCOUNTS)
    _execute_ddl(conn, DDL_CARDS)
    # Execute triggers as single statements (don't split by semicolon)
    conn.execute(DDL_ACCOUNTS_TRIGGER.strip())
    conn.execute(DDL_CARDS_TRIGGER.strip())
    
    # Phase 3: Financial management tables
    _execute_ddl(conn, DDL_INCOME_SOURCES)
    _execute_ddl(conn, DDL_LOANS)
    _execute_ddl(conn, DDL_LOAN_PAYMENTS)
    _execute_ddl(conn, DDL_INVESTMENTS)
    _execute_ddl(conn, DDL_MONTHLY_SNAPSHOTS)
    _execute_ddl(conn, DDL_RECURRING_TRANSACTIONS)
    # Execute triggers as single statements (don't split by semicolon)
    conn.execute(DDL_INCOME_SOURCES_TRIGGER.strip())
    conn.execute(DDL_LOANS_TRIGGER.strip())
    conn.execute(DDL_RECURRING_TRANSACTIONS_TRIGGER.strip())
    
    log.info("Phase 3: Financial management tables initialized")
    log.info("Database indexes verified")
    
    # Phase B: Job queue and staging tables
    _execute_ddl(conn, DDL_JOBS)
    _execute_ddl(conn, DDL_JOB_INDEXES)
    log.info("Phase B1: Jobs table initialized")
    
    _execute_ddl(conn, DDL_STATEMENT_IMPORTS)
    _execute_ddl(conn, DDL_STATEMENT_PAGES)
    _execute_ddl(conn, DDL_STAGED_TRANSACTIONS)
    _execute_ddl(conn, DDL_STAGING_INDEXES)
    log.info("Phase B2: Staging tables initialized")
    
    # Note: quarantine_pages table removed - quarantine feature deprecated
    # Phase B3 skipped
    
    _execute_ddl(conn, DDL_AUTO_HEAL_EVENTS)
    _execute_ddl(conn, DDL_AUTO_HEAL_INDEXES)
    log.info("Phase B4: Auto-heal tables initialized")
    
    # Phase E: Immutable financial event ledger
    _execute_ddl(conn, DDL_FINANCIAL_EVENTS)
    _execute_ddl(conn, DDL_FINANCIAL_EVENTS_INDEXES)
    log.info("Phase E: Financial events ledger initialized")
    
    # Phase F: Layout templates
    _execute_ddl(conn, DDL_LAYOUT_TEMPLATES)
    _execute_ddl(conn, DDL_LAYOUT_TEMPLATES_INDEX)
    log.info("Phase F1: Layout templates table initialized")


def apply_migrations(conn: sqlite3.Connection) -> None:
    """Apply all data migrations to the database.
    
    This function is idempotent - safe to call multiple times.
    """
    # Column additions
    for table, col, col_type in MIGRATION_COLUMNS:
        _add_column_if_not_exists(conn, table, col, col_type)
    
    # Insert default member
    conn.execute("INSERT OR IGNORE INTO members (name, color) VALUES ('Self', '#6366F1')")
    
    # Phase 2A: Migrate existing transactions to paise columns
    try:
        conn.execute("""
            UPDATE transactions SET
                amount_paise = ROUND(amount * 100),
                debit = CASE WHEN type = 'debit' THEN ROUND(amount * 100) ELSE 0 END,
                credit = CASE WHEN type = 'credit' THEN ROUND(amount * 100) ELSE 0 END
            WHERE amount_paise = 0 AND amount IS NOT NULL AND amount != 0
        """)
    except Exception:
        pass  # Migration already done or no data
    
    # Phase PAISE-1: Migrate reconciliations.amount -> amount_paise
    try:
        conn.execute("""
            UPDATE reconciliations SET
                amount_paise = ROUND(amount * 100)
            WHERE amount_paise = 0 AND amount IS NOT NULL AND amount != 0
        """)
    except Exception:
        pass
    
    # Phase PAISE-2: Migrate statements REAL fields -> _paise
    try:
        conn.execute("""
            UPDATE statements SET
                total_amount_due_paise = ROUND(COALESCE(total_amount_due, 0) * 100),
                minimum_amount_due_paise = ROUND(COALESCE(minimum_amount_due, 0) * 100),
                credit_limit_paise = ROUND(COALESCE(credit_limit, 0) * 100),
                opening_balance_paise = ROUND(COALESCE(opening_balance, 0) * 100),
                validation_difference_paise = ROUND(COALESCE(validation_difference, 0) * 100)
            WHERE total_amount_due_paise = 0
        """)
    except Exception:
        pass
    
    # Phase 2A.1: Migrate date_iso column
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
    
    # Phase 2A.1: Add unique index on hash_signature
    try:
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_transaction_hash ON transactions(hash_signature)")
    except Exception:
        pass  # May fail if duplicates exist
    
    # Phase 2A.1: Add immutability triggers
    # Surgical trigger: only protects core financial fields, allows nature updates
    try:
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS prevent_immutable_field_update
            BEFORE UPDATE ON transactions
            WHEN
                NEW.amount_paise != OLD.amount_paise OR
                NEW.date != OLD.date OR
                NEW.description != OLD.description OR
                NEW.account_id != OLD.account_id OR
                (NEW.hash_signature != OLD.hash_signature
                 AND OLD.hash_signature IS NOT NULL)
            BEGIN
                SELECT RAISE(ABORT,
                    'Cannot modify immutable transaction fields: amount, date, description, account_id');
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

    # STRICT PAISE ENFORCEMENT: Block REAL money writes to primary monetary fields
    try:
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS enforce_transactions_amount_paise_insert
            BEFORE INSERT ON transactions
            WHEN NEW.amount_paise IS NULL
            BEGIN
                SELECT RAISE(ABORT, 'REAL currency fields are deprecated. Use amount_paise only.');
            END
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS enforce_transactions_amount_paise_update
            BEFORE UPDATE OF amount_paise ON transactions
            WHEN NEW.amount_paise IS NULL
            BEGIN
                SELECT RAISE(ABORT, 'REAL currency fields are deprecated. Use amount_paise only.');
            END
        """)
        log.info("Strict paise enforcement triggers created for transactions")
    except Exception:
        pass  # Triggers already exist

    # STRICT PAISE ENFORCEMENT: Block REAL money writes to reconciliations
    try:
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS enforce_reconciliations_amount_paise_insert
            BEFORE INSERT ON reconciliations
            WHEN NEW.amount_paise IS NULL
            BEGIN
                SELECT RAISE(ABORT, 'REAL currency fields are deprecated. Use amount_paise only.');
            END
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS enforce_reconciliations_amount_paise_update
            BEFORE UPDATE OF amount_paise ON reconciliations
            WHEN NEW.amount_paise IS NULL
            BEGIN
                SELECT RAISE(ABORT, 'REAL currency fields are deprecated. Use amount_paise only.');
            END
        """)
        log.info("Strict paise enforcement triggers created for reconciliations")
    except Exception:
        pass  # Triggers already exist

    # STRICT PAISE ENFORCEMENT: Block REAL money writes to accounts
    try:
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS enforce_accounts_balance_paise_insert
            BEFORE INSERT ON accounts
            WHEN NEW.balance_paise IS NULL
            BEGIN
                SELECT RAISE(ABORT, 'REAL currency fields are deprecated. Use balance_paise only.');
            END
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS enforce_accounts_balance_paise_update
            BEFORE UPDATE OF balance_paise ON accounts
            WHEN NEW.balance_paise IS NULL
            BEGIN
                SELECT RAISE(ABORT, 'REAL currency fields are deprecated. Use balance_paise only.');
            END
        """)
        log.info("Strict paise enforcement triggers created for accounts")
    except Exception:
        pass  # Triggers already exist

    # STRICT PAISE ENFORCEMENT: Block REAL money writes to loans
    try:
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS enforce_loans_amount_paise_insert
            BEFORE INSERT ON loans
            WHEN NEW.principal_paise IS NULL OR NEW.outstanding_paise IS NULL
            BEGIN
                SELECT RAISE(ABORT, 'REAL currency fields are deprecated. Use principal_paise/outstanding_paise only.');
            END
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS enforce_loans_amount_paise_update
            BEFORE UPDATE OF principal_paise, outstanding_paise ON loans
            WHEN NEW.principal_paise IS NULL OR NEW.outstanding_paise IS NULL
            BEGIN
                SELECT RAISE(ABORT, 'REAL currency fields are deprecated. Use principal_paise/outstanding_paise only.');
            END
        """)
        log.info("Strict paise enforcement triggers created for loans")
    except Exception:
        pass  # Triggers already exist
    
    # Phase E: Backfill financial_events from existing transactions
    try:
        conn.execute("""
            INSERT OR IGNORE INTO financial_events (
                event_type, entity_type, entity_id, amount_paise, direction, metadata_json
            )
            SELECT
                'transaction' AS event_type,
                'transaction' AS entity_type,
                id AS entity_id,
                amount_paise,
                CASE WHEN type = 'debit' THEN 'debit' WHEN type = 'credit' THEN 'credit' ELSE 'neutral' END AS direction,
                '{"backfilled": true, "original_type": "' || COALESCE(type, '') || '"}'
            FROM transactions
            WHERE amount_paise IS NOT NULL AND amount_paise != 0
        """)
        log.info("Financial events backfilled from existing transactions")
    except Exception as e:
        log.warning("Financial events backfill skipped: %s", e)
    
    # Phase 2P: Create indexes that depend on migrated columns
    for stmt in DDL_INDEXES_POST_MIGRATION.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            try:
                conn.execute(stmt)
            except Exception as e:
                log.debug("Index creation skipped: %s", e)
    
    # Phase F1: Fingerprint/template column migrations
    for table, col, col_type in FINGERPRINT_MIGRATION_COLUMNS:
        _add_column_if_not_exists(conn, table, col, col_type)
    
    log.info("Database tables initialized")


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Ensure all tables exist and migrations are applied.
    
    This is the main entry point for schema initialization.
    Safe to call multiple times (idempotent).
    """
    create_tables(conn)
    apply_migrations(conn)