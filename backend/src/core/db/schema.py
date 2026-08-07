"""
Database Schema — Canonical DDL, Initialization, Migrations, and Verification
=============================================================================

This module is the single source of truth for all database schema definitions,
initialization logic, migrations, and integrity verification.

Extracted from ``db.py`` (FinanceDB god-file) to enforce separation of
responsibilities:

    core/db/config.py      ← path resolution, pragma settings
    core/db/connection.py  ← sqlite3.connect + PRAGMAs
    core/db/schema.py      ← DDL, create_all, migrations, verification  ← **THIS FILE**
    core/db/transaction.py ← transaction helpers
    core/db/health.py      ← health checks

All monetary columns use ``INTEGER`` with ``_paise`` suffix.
No floating-point arithmetic for financial data.
"""

import contextlib
import logging
import sqlite3
from typing import Any

from src.core.db.config import get_db_path

logger = logging.getLogger(__name__)

# ============================================================
# Authoritative Schema Manifest
# ============================================================

_REQUIRED_TABLES: set[str] = {
    "statements",
    "transactions",
    "members",
    "import_mappings",
    "reconciliations",
    "accounts",
    "loans",
    "investments",
    "loan_payments",
    "loan_prepayments",
    "loan_rate_changes",
    "account_balance_history",
    "account_links",
    "credit_cards",
    "credit_card_statements",
    "institutions",
    "reconciliation_audit_log",
    "behaviour_snapshots",
    "behaviour_patterns",
    "behaviour_alerts",
    "financial_profiles",
    "financial_events",
    "financial_goals",
    "loan_amortization_schedule",
    "transaction_classifications",
    "financial_event_lifecycle_log",
    "financial_event_links",
    "liquidity_provider_patterns",
    "liquidity_purpose_patterns",
}

_REQUIRED_INDEXES: set[str] = {
    "idx_txn_date",
    "idx_txn_category",
    "idx_txn_statement",
    "idx_txn_type",
    "idx_txn_date_iso",
    "idx_account_date_iso",
    "idx_transaction_hash",
    "idx_loan_payments_loan_id",
    "idx_loan_payments_date",
    "idx_loan_prepayments_loan_id",
    "idx_loan_prepayments_date",
    "idx_loan_rate_changes_loan_id",
    "idx_loan_rate_changes_date",
    "idx_loan_payments_loan_date",
    "idx_loan_prepayments_loan_date",
    "idx_loan_rate_changes_loan_date",
    "idx_abh_account_id",
    "idx_abh_account_date",
    "idx_audit_log_reconciliation_id",
    "idx_las_loan_id",
    "idx_las_due_date",
    "idx_tc_transaction_id",
    "idx_fel_event_id",
    "idx_felinks_event_id",
    "idx_felinks_linked_id",
}

_REQUIRED_TRIGGERS: set[str] = {
    "prevent_transaction_update",
    "prevent_transaction_delete",
}

# ============================================================
# DDL — Base Tables
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
    credit INTEGER GENERATED ALWAYS AS (CASE WHEN type = 'credit' THEN amount_paise ELSE 0 END) STORED,
    debit INTEGER GENERATED ALWAYS AS (CASE WHEN type = 'debit' THEN amount_paise ELSE 0 END) STORED,
    UNIQUE(statement_id, date, description, amount_paise, sequence_num)
);
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

_DDL_RECONCILIATIONS = """
CREATE TABLE IF NOT EXISTS reconciliations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    debit_txn_id INTEGER NOT NULL,
    credit_txn_id INTEGER NOT NULL,
    debit_account_id TEXT NOT NULL,
    credit_account_id TEXT NOT NULL,
    amount_paise INTEGER NOT NULL,
    date_diff_days INTEGER NOT NULL DEFAULT 0,
    confidence_bps INTEGER NOT NULL DEFAULT 0,
    match_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    deterministic_key TEXT NOT NULL UNIQUE,
    created_at TEXT DEFAULT (datetime('now')),
    confirmed_at TEXT,
    FOREIGN KEY(debit_txn_id) REFERENCES transactions(id),
    FOREIGN KEY(credit_txn_id) REFERENCES transactions(id)
);
"""

_DDL_ACCOUNTS = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    bank TEXT NOT NULL,
    account_type TEXT NOT NULL DEFAULT 'savings',
    balance_paise INTEGER NOT NULL DEFAULT 0,
    account_number_last4 TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    owner_id TEXT DEFAULT 'self',
    household_id TEXT DEFAULT 'primary',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

_DDL_LOANS = """
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
"""

_DDL_INVESTMENTS = """
CREATE TABLE IF NOT EXISTS investments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
"""

_DDL_LOAN_PAYMENTS = """
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
"""

_DDL_LOAN_PREPAYMENTS = """
CREATE TABLE IF NOT EXISTS loan_prepayments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER NOT NULL REFERENCES loans(id),
    amount_paise INTEGER NOT NULL,
    prepayment_date TEXT NOT NULL,
    mode TEXT DEFAULT 'reduce_tenure',
    created_at TEXT DEFAULT (datetime('now'))
);
"""

_DDL_LOAN_RATE_CHANGES = """
CREATE TABLE IF NOT EXISTS loan_rate_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER NOT NULL REFERENCES loans(id),
    change_date TEXT NOT NULL,
    new_rate_bps INTEGER NOT NULL,
    mode TEXT DEFAULT 'adjust_emi',
    created_at TEXT DEFAULT (datetime('now'))
);
"""

_DDL_ACCOUNT_BALANCE_HISTORY = """
CREATE TABLE IF NOT EXISTS account_balance_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    timestamp TEXT NOT NULL,
    date_iso TEXT,
    balance_paise INTEGER NOT NULL,
    source TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(account_id, date_iso)
);
"""

_DDL_ACCOUNT_LINKS = """
CREATE TABLE IF NOT EXISTS account_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    linked_account_id INTEGER NOT NULL REFERENCES accounts(id),
    relationship_type TEXT DEFAULT 'TRANSFER',
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(account_id, linked_account_id)
);
"""

_DDL_CREDIT_CARDS = """
CREATE TABLE IF NOT EXISTS credit_cards (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    name TEXT NOT NULL,
    bank TEXT NOT NULL,
    card_last4 TEXT,
    credit_limit_paise INTEGER NOT NULL,
    annual_fee_paise INTEGER DEFAULT 0,
    interest_rate_bps INTEGER NOT NULL,
    billing_day INTEGER,
    due_day_offset INTEGER DEFAULT 21,
    is_active INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

_DDL_CREDIT_CARD_STATEMENTS = """
CREATE TABLE IF NOT EXISTS credit_card_statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id TEXT NOT NULL REFERENCES credit_cards(id),
    statement_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    total_outstanding_paise INTEGER NOT NULL,
    minimum_due_paise INTEGER NOT NULL,
    payment_date TEXT,
    payment_amount_paise INTEGER,
    interest_charged_paise INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(card_id, statement_date)
);
"""

_DDL_INSTITUTIONS = """
CREATE TABLE IF NOT EXISTS institutions (
    institution_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('BANK','WALLET','BROKER','OTHER')),
    interest_rate_bps INTEGER,
    supported_features_json TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

_DDL_RECONCILIATION_AUDIT_LOG = """
CREATE TABLE IF NOT EXISTS reconciliation_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reconciliation_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    actor TEXT NOT NULL,
    timestamp TEXT DEFAULT (datetime('now')),
    reason TEXT,
    previous_state TEXT,
    new_state TEXT,
    FOREIGN KEY (reconciliation_id) REFERENCES reconciliations(id) ON DELETE CASCADE
);
"""

_DDL_BEHAVIOUR_SNAPSHOTS = """
CREATE TABLE IF NOT EXISTS behaviour_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    household_id TEXT NOT NULL DEFAULT 'default',
    snapshot_date TEXT NOT NULL,
    savings_discipline_score_bps INTEGER,
    cashflow_stability_score_bps INTEGER,
    salary_dependence_ratio_bps INTEGER,
    expense_diversity_score_bps INTEGER,
    debt_health_score_bps INTEGER,
    lifestyle_creep_score_bps INTEGER,
    version INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(household_id, snapshot_date)
);
"""

_DDL_BEHAVIOUR_PATTERNS = """
CREATE TABLE IF NOT EXISTS behaviour_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_type TEXT NOT NULL,
    pattern_key TEXT NOT NULL,
    household_id TEXT NOT NULL DEFAULT 'default',
    strength_bps INTEGER NOT NULL,
    first_observed TEXT,
    last_observed TEXT,
    transaction_count INTEGER DEFAULT 1,
    total_amount_paise INTEGER NOT NULL DEFAULT 0,
    metadata_json TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(pattern_type, pattern_key, household_id)
);
"""

_DDL_BEHAVIOUR_ALERTS = """
CREATE TABLE IF NOT EXISTS behaviour_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL,
    alert_code TEXT NOT NULL,
    household_id TEXT NOT NULL DEFAULT 'default',
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    action_url TEXT,
    is_acknowledged INTEGER DEFAULT 0,
    metadata_json TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

_DDL_FINANCIAL_PROFILES = """
CREATE TABLE IF NOT EXISTS financial_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    household_id TEXT NOT NULL DEFAULT 'default',
    profile_type TEXT NOT NULL,
    profile_data_json TEXT,
    score_bps INTEGER,
    calculated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(household_id, profile_type)
);
"""

_DDL_FINANCIAL_EVENTS = """
CREATE TABLE IF NOT EXISTS financial_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    event_subtype TEXT,
    date_iso TEXT NOT NULL,
    amount_paise INTEGER NOT NULL,
    account_id TEXT,
    provider TEXT,
    description TEXT,
    month_bucket TEXT,
    household_id TEXT DEFAULT 'primary',
    owner_id TEXT DEFAULT 'self',
    lifecycle_state TEXT DEFAULT 'open',
    settled_by_event_id INTEGER,
    outstanding_paise INTEGER,
    superseded_by INTEGER,
    metadata_json TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(event_type, date_iso, amount_paise, description)
);
"""

_DDL_FINANCIAL_GOALS = """
CREATE TABLE IF NOT EXISTS financial_goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    household_id TEXT NOT NULL DEFAULT 'primary',
    owner_id TEXT DEFAULT 'self',
    goal_type TEXT NOT NULL,
    name TEXT NOT NULL,
    target_amount_paise INTEGER NOT NULL,
    current_amount_paise INTEGER DEFAULT 0,
    target_date TEXT,
    status TEXT DEFAULT 'active',
    category TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
"""


_DDL_LOAN_AMORTIZATION_SCHEDULE = """
CREATE TABLE IF NOT EXISTS loan_amortization_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER NOT NULL REFERENCES loans(id),
    due_date TEXT NOT NULL,
    emi_amount_paise INTEGER NOT NULL,
    principal_paise INTEGER NOT NULL,
    interest_paise INTEGER NOT NULL,
    outstanding_after_paise INTEGER NOT NULL,
    source TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(loan_id, due_date)
);
"""

_DDL_TRANSACTION_CLASSIFICATIONS = """
CREATE TABLE IF NOT EXISTS transaction_classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER NOT NULL REFERENCES transactions(id),
    classification TEXT NOT NULL,
    sub_classification TEXT,
    confidence_bps INTEGER NOT NULL,
    source TEXT NOT NULL,
    classifier TEXT DEFAULT 'loan_emi_detector',
    classifier_version INTEGER DEFAULT 1,
    lifecycle_state TEXT,
    outstanding_paise INTEGER DEFAULT 0,
    payment_channel TEXT DEFAULT 'DIRECT',
    matched_statement_id INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(transaction_id, classification)
);
"""

_DDL_FINANCIAL_EVENT_LIFECYCLE_LOG = """
CREATE TABLE IF NOT EXISTS financial_event_lifecycle_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL REFERENCES financial_events(id),
    previous_lifecycle_state TEXT,
    new_lifecycle_state TEXT NOT NULL,
    previous_outstanding_paise INTEGER,
    new_outstanding_paise INTEGER,
    caused_by_event_id INTEGER,
    actor TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

_DDL_FINANCIAL_EVENT_LINKS = """
CREATE TABLE IF NOT EXISTS financial_event_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL REFERENCES financial_events(id),
    linked_event_id INTEGER NOT NULL REFERENCES financial_events(id),
    link_type TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

_DDL_LIQUIDITY_PROVIDER_PATTERNS = """
CREATE TABLE IF NOT EXISTS liquidity_provider_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_name TEXT NOT NULL,
    description_pattern TEXT NOT NULL,
    fee_min_bps INTEGER NOT NULL,
    fee_max_bps INTEGER NOT NULL,
    review_fee_min_bps INTEGER NOT NULL,
    review_fee_max_bps INTEGER NOT NULL,
    typical_settlement_days INTEGER NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    confirmed_by_user INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

_DDL_LIQUIDITY_PURPOSE_PATTERNS = """
CREATE TABLE IF NOT EXISTS liquidity_purpose_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purpose TEXT NOT NULL,
    description_pattern TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

# ============================================================
# DDL — Indexes
# ============================================================

_DDL_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_txn_date        ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_txn_category    ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_txn_statement   ON transactions(statement_id);
CREATE INDEX IF NOT EXISTS idx_txn_type        ON transactions(type);
CREATE INDEX IF NOT EXISTS idx_txn_date_iso    ON transactions(date_iso);
CREATE INDEX IF NOT EXISTS idx_account_date_iso ON transactions(account_id, date_iso, id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_transaction_hash ON transactions(hash_signature);
CREATE INDEX IF NOT EXISTS idx_loan_payments_loan_id ON loan_payments(loan_id);
CREATE INDEX IF NOT EXISTS idx_loan_payments_date ON loan_payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_loan_prepayments_loan_id ON loan_prepayments(loan_id);
CREATE INDEX IF NOT EXISTS idx_loan_prepayments_date ON loan_prepayments(prepayment_date);
CREATE INDEX IF NOT EXISTS idx_loan_rate_changes_loan_id ON loan_rate_changes(loan_id);
CREATE INDEX IF NOT EXISTS idx_loan_rate_changes_date ON loan_rate_changes(change_date);
CREATE INDEX IF NOT EXISTS idx_loan_payments_loan_date ON loan_payments(loan_id, payment_date);
CREATE INDEX IF NOT EXISTS idx_loan_prepayments_loan_date ON loan_prepayments(loan_id, prepayment_date);
CREATE INDEX IF NOT EXISTS idx_loan_rate_changes_loan_date ON loan_rate_changes(loan_id, change_date);
CREATE INDEX IF NOT EXISTS idx_abh_account_id ON account_balance_history(account_id);
CREATE INDEX IF NOT EXISTS idx_abh_account_date ON account_balance_history(account_id, date_iso);
CREATE INDEX IF NOT EXISTS idx_audit_log_reconciliation_id ON reconciliation_audit_log(reconciliation_id);
CREATE INDEX IF NOT EXISTS idx_las_loan_id ON loan_amortization_schedule(loan_id);
CREATE INDEX IF NOT EXISTS idx_las_due_date ON loan_amortization_schedule(due_date);
CREATE INDEX IF NOT EXISTS idx_tc_transaction_id ON transaction_classifications(transaction_id);
CREATE INDEX IF NOT EXISTS idx_fel_event_id ON financial_event_lifecycle_log(event_id);
CREATE INDEX IF NOT EXISTS idx_felinks_event_id ON financial_event_links(event_id);
CREATE INDEX IF NOT EXISTS idx_felinks_linked_id ON financial_event_links(linked_event_id);
"""

# ============================================================
# DDL — Triggers
# ============================================================

_DDL_TRIGGERS = """
CREATE TRIGGER IF NOT EXISTS prevent_transaction_update
BEFORE UPDATE ON transactions
BEGIN
    SELECT RAISE(ABORT, 'Transactions are immutable. Cannot update.');
END;

CREATE TRIGGER IF NOT EXISTS prevent_transaction_delete
BEFORE DELETE ON transactions
BEGIN
    SELECT RAISE(ABORT, 'Transactions are immutable. Cannot delete.');
END;
"""

# ============================================================
# Migration Columns
# ============================================================

_MIGRATION_COLUMNS: list[tuple[str, str, str]] = [
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
    ("statements", "source", "TEXT DEFAULT 'pdf'"),
    ("behaviour_alerts", "acknowledged_at", "TEXT"),
    ("behaviour_alerts", "resolved_at", "TEXT"),
    ("behaviour_alerts", "resolution_notes", "TEXT"),
    ("behaviour_snapshots", "lifestyle_inflation_rate_bps", "INTEGER"),
    ("behaviour_snapshots", "subscription_burn_rate_bps", "INTEGER"),
    ("behaviour_snapshots", "resilience_index_bps", "INTEGER"),
    ("behaviour_snapshots", "wellness_score_bps", "INTEGER"),
]

# ============================================================
# Module-level Utilities
# ============================================================


def _parse_date_to_ymd(date_str: str) -> str:
    """
    Parse Indian date formats to YYYY-MM-DD for sorting/grouping.
    Returns empty string if unparseable.
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


def _row_to_dict(cursor: sqlite3.Cursor, row: tuple[Any, ...]) -> dict[str, Any]:
    """Convert a sqlite3 row to a dict using cursor.description."""
    return {col[0]: row[i] for i, col in enumerate(cursor.description)}


# ============================================================
# DDL Registry
# ============================================================

_ALL_DDL_TABLES: list[tuple[str, str]] = [
    ("statements", _DDL_STATEMENTS),
    ("transactions", _DDL_TRANSACTIONS),
    ("members", _DDL_MEMBERS),
    ("import_mappings", _DDL_IMPORT_MAPPINGS),
    ("reconciliations", _DDL_RECONCILIATIONS),
    ("accounts", _DDL_ACCOUNTS),
    ("loans", _DDL_LOANS),
    ("investments", _DDL_INVESTMENTS),
    ("loan_payments", _DDL_LOAN_PAYMENTS),
    ("loan_prepayments", _DDL_LOAN_PREPAYMENTS),
    ("loan_rate_changes", _DDL_LOAN_RATE_CHANGES),
    ("account_balance_history", _DDL_ACCOUNT_BALANCE_HISTORY),
    ("account_links", _DDL_ACCOUNT_LINKS),
    ("credit_cards", _DDL_CREDIT_CARDS),
    ("credit_card_statements", _DDL_CREDIT_CARD_STATEMENTS),
    ("institutions", _DDL_INSTITUTIONS),
    ("reconciliation_audit_log", _DDL_RECONCILIATION_AUDIT_LOG),
    ("behaviour_snapshots", _DDL_BEHAVIOUR_SNAPSHOTS),
    ("behaviour_patterns", _DDL_BEHAVIOUR_PATTERNS),
    ("behaviour_alerts", _DDL_BEHAVIOUR_ALERTS),
    ("financial_profiles", _DDL_FINANCIAL_PROFILES),
    ("financial_events", _DDL_FINANCIAL_EVENTS),
    ("financial_goals", _DDL_FINANCIAL_GOALS),
    ("loan_amortization_schedule", _DDL_LOAN_AMORTIZATION_SCHEDULE),
    ("transaction_classifications", _DDL_TRANSACTION_CLASSIFICATIONS),
    ("financial_event_lifecycle_log", _DDL_FINANCIAL_EVENT_LIFECYCLE_LOG),
    ("financial_event_links", _DDL_FINANCIAL_EVENT_LINKS),
    ("liquidity_provider_patterns", _DDL_LIQUIDITY_PROVIDER_PATTERNS),
    ("liquidity_purpose_patterns", _DDL_LIQUIDITY_PURPOSE_PATTERNS),
]


# ============================================================
# Schema Initialization
# ============================================================


def create_all(db_path: str | None = None) -> None:
    """Create all base tables, indexes, and triggers.

    Only uses CREATE IF NOT EXISTS — safe to run multiple times.
    """
    from src.core.db.connection import get_connection_context

    path = db_path or get_db_path()
    with get_connection_context(path) as conn:
        for _table_name, ddl in _ALL_DDL_TABLES:
            conn.execute(ddl)

        for stmt in _DDL_INDEXES.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    conn.execute(stmt)
                except sqlite3.OperationalError as e:
                    logger.warning("Index creation skipped (may already exist): %s", e)

        try:
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS prevent_transaction_update
                BEFORE UPDATE ON transactions
                BEGIN
                    SELECT RAISE(ABORT, 'Transactions are immutable. Cannot update.');
                END
            """)
        except sqlite3.OperationalError as e:
            logger.warning("Trigger creation skipped: %s", e)

        try:
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS prevent_transaction_delete
                BEFORE DELETE ON transactions
                BEGIN
                    SELECT RAISE(ABORT, 'Transactions are immutable. Cannot delete.');
                END
            """)
        except sqlite3.OperationalError as e:
            logger.warning("Trigger creation skipped: %s", e)

        conn.execute("""
            INSERT OR IGNORE INTO members (name, color) VALUES ('Self', '#6366F1')
        """)


def run_migrations(db_path: str | None = None) -> None:
    """Run schema and data migrations.

    ALTER TABLE ADD COLUMN and data backfill operations that may be
    needed when upgrading from an older schema version. Idempotent.
    """
    from src.core.db.connection import get_connection_context

    path = db_path or get_db_path()
    with get_connection_context(path) as conn:
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
            if (
                "account_number_masked" in columns
                and "account_number_last4" not in columns
            ):
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
                logger.info(
                    "Migration: backfilled date_iso for %d transactions", len(rows)
                )
        except sqlite3.OperationalError:
            pass

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
                conn.execute(
                    "ALTER TABLE accounts ADD COLUMN owner_id TEXT DEFAULT 'self'"
                )
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


def verify_schema(db_path: str | None = None) -> None:
    """Verify that all required database objects exist after initialization.

    Raises RuntimeError if any required table or trigger is missing.
    """
    from src.core.db.connection import get_connection_context

    path = db_path or get_db_path()
    with get_connection_context(path) as conn:
        row = conn.execute("PRAGMA foreign_keys").fetchone()
        if not row or row[0] != 1:
            raise RuntimeError(
                "Database initialized with PRAGMA foreign_keys=OFF. "
                "All ClariFin databases must have foreign key enforcement enabled."
            )

        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cur.fetchall()}

        missing_tables = _REQUIRED_TABLES - existing_tables
        if missing_tables:
            raise RuntimeError(
                f"Schema verification failed — missing tables: "
                f"{', '.join(sorted(missing_tables))}"
            )

        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        existing_indexes = {row[0] for row in cur.fetchall()}

        missing_indexes = _REQUIRED_INDEXES - existing_indexes
        if missing_indexes:
            logger.warning(
                "Schema verification — missing indexes (non-fatal): %s",
                ", ".join(sorted(missing_indexes)),
            )

        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
        existing_triggers = {row[0] for row in cur.fetchall()}

        missing_triggers = _REQUIRED_TRIGGERS - existing_triggers
        if missing_triggers:
            raise RuntimeError(
                f"Schema verification failed — missing triggers: "
                f"{', '.join(sorted(missing_triggers))}"
            )

        violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            logger.warning(
                "Schema verification — foreign key violations found: %s",
                violations,
            )

        logger.info(
            "Schema verified: %d tables, %d indexes, %d triggers",
            len(existing_tables & _REQUIRED_TABLES),
            len(existing_indexes & _REQUIRED_INDEXES),
            len(existing_triggers & _REQUIRED_TRIGGERS),
        )
