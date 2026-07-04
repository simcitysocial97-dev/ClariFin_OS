"""Database core module for ClariFin.

SQLite database manager for the personal finance tracker.
No ORM - raw sqlite3 only.
"""

import hashlib
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.logger import log
from src.utils import parse_date_to_iso, parse_amount_to_float
from src.db_schema import ensure_schema

# Import repositories (relative imports within db package)
from .repos import accounts_repo
from .repos import cards_repo
from .repos import imports_repo
from .repos import income_sources_repo
from .repos import investments_repo
from .repos import loans_repo
from .repos import members_repo
from .repos import reconciliations_repo
from .repos import statements_repo
from .repos import transactions_repo
from .pagination import PaginatedResult, paginate_query


def _execute_with_timing(
    conn: sqlite3.Connection,
    query: str,
    params: tuple = (),
    slow_threshold_ms: float = 100.0
):
    """Execute a query and log if it exceeds the slow threshold."""
    start = time.perf_counter()
    result = conn.execute(query, params)
    duration_ms = (time.perf_counter() - start) * 1000
    
    if duration_ms > slow_threshold_ms:
        log.warning(
            "Slow query (%.1fms): %s | params: %s",
            duration_ms,
            query[:200],
            str(params)[:100],
        )
    
    return result, duration_ms


def _parse_date_to_ymd(date_str: str) -> str:
    """Parse Indian date formats to YYYY-MM-DD for sorting/grouping."""
    result = parse_date_to_iso(date_str)
    return result if result is not None else ""


def _parse_amount(raw: str) -> float:
    """Convert amount string to float. Removes commas, handles empty."""
    return parse_amount_to_float(raw)


class FinanceDB:
    """SQLite-backed storage for bank statements and transactions."""

    def __init__(self, db_path: str = "data/finance.db"):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._create_tables()

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create a thread-local connection."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA busy_timeout=5000")
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return self._local.conn

    @contextmanager
    def connection(self):
        """Context manager for read-only operations."""
        conn = self._get_connection()
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise

    @contextmanager
    def transaction(self):
        """Context manager for write operations."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def close(self) -> None:
        """Close the thread-local connection if it exists."""
        if hasattr(self._local, 'conn') and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None
            log.info("Database connection closed")

    def _create_tables(self) -> None:
        """Create all database tables and run migrations."""
        with self.transaction() as conn:
            ensure_schema(conn)

    # Statement Methods (delegate to statements_repo)
    def insert_statement(self, bank: str, file_name: str, period_from: str = "", period_to: str = "", card_last4: str = "") -> int:
        """Insert a statement record. Returns statement_id."""
        with self.transaction() as conn:
            return statements_repo.insert_statement(conn, bank, file_name, period_from, period_to, card_last4)

    def get_duplicate_check(self, bank: str, file_name: str) -> bool:
        """Returns True if (bank, file_name) already exists in statements."""
        with self.connection() as conn:
            return statements_repo.get_duplicate_check(conn, bank, file_name)

    def get_statement_by_id(self, statement_id: int) -> Optional[Dict]:
        """Get a single statement by ID."""
        with self.connection() as conn:
            return statements_repo.get_statement_by_id(conn, statement_id)

    # Transaction Methods (delegate to transactions_repo)
    def insert_transactions(self, statement_id: int, transactions: List[Dict]) -> int:
        """Bulk insert transactions. Deduplicates by hash_signature."""
        with self.transaction() as conn:
            return transactions_repo.insert_transactions(conn, statement_id, transactions)

    # Query Methods (delegate to transactions_repo and statements_repo)
    def get_all_transactions(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Fetch transactions with optional filters."""
        with self.connection() as conn:
            return transactions_repo.get_all_transactions(conn, filters)

    def get_transaction_by_id(self, transaction_id: int) -> Optional[Dict]:
        """Get a single transaction by ID."""
        with self.connection() as conn:
            return transactions_repo.get_transaction_by_id(conn, transaction_id)

    def get_transaction_summary_by_category(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict]:
        """Get transaction summary grouped by category."""
        with self.connection() as conn:
            return transactions_repo.get_transaction_summary_by_category(conn, date_from, date_to)

    def get_monthly_totals(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict]:
        """Get monthly debit/credit totals."""
        with self.connection() as conn:
            return transactions_repo.get_monthly_totals(conn, date_from, date_to)

    def get_banks(self) -> List[str]:
        """Returns list of distinct bank names."""
        with self.connection() as conn:
            return transactions_repo.get_banks(conn)

    def get_statement_count(self) -> int:
        """Returns total number of imported statements."""
        with self.connection() as conn:
            return statements_repo.get_statement_count(conn)

    def get_transaction_count(self) -> int:
        """Returns total number of transactions."""
        with self.connection() as conn:
            return transactions_repo.get_transaction_count(conn)

    # Accounts Methods (delegate to accounts_repo)
    def get_accounts(self, include_inactive: bool = False) -> List[Dict]:
        """Get all accounts."""
        with self.connection() as conn:
            return accounts_repo.get_accounts(conn, include_inactive)

    def get_account(self, account_id: int) -> Optional[Dict]:
        """Get a single account by ID."""
        with self.connection() as conn:
            return accounts_repo.get_account(conn, account_id)

    def create_account(self, account: Dict) -> int:
        """Create a new account."""
        with self.transaction() as conn:
            return accounts_repo.create_account(conn, account)

    def update_account(self, account_id: int, account: Dict) -> bool:
        """Update an existing account."""
        with self.transaction() as conn:
            return accounts_repo.update_account(conn, account_id, account)

    def delete_account(self, account_id: int) -> bool:
        """Soft-delete an account."""
        with self.transaction() as conn:
            return accounts_repo.delete_account(conn, account_id)

    # Cards Methods (delegate to cards_repo)
    def get_cards(self, account_id: Optional[int] = None, include_inactive: bool = False) -> List[Dict]:
        """Get all cards."""
        with self.connection() as conn:
            return cards_repo.get_cards(conn, account_id, include_inactive)

    def get_card(self, card_id: int) -> Optional[Dict]:
        """Get a single card by ID."""
        with self.connection() as conn:
            return cards_repo.get_card(conn, card_id)

    def create_card(self, card: Dict) -> int:
        """Create a new card."""
        with self.transaction() as conn:
            return cards_repo.create_card(conn, card)

    def update_card(self, card_id: int, card: Dict) -> bool:
        """Update an existing card."""
        with self.transaction() as conn:
            return cards_repo.update_card(conn, card_id, card)

    def delete_card(self, card_id: int) -> bool:
        """Soft-delete a card."""
        with self.transaction() as conn:
            return cards_repo.delete_card(conn, card_id)

    # Investments Methods (delegate to investments_repo)
    def get_investments(self, active_only: bool = True) -> List[Dict]:
        """Get all investments."""
        with self.connection() as conn:
            return investments_repo.get_investments(conn, active_only)

    def get_investment(self, investment_id: int) -> Optional[Dict]:
        """Get a single investment by ID."""
        with self.connection() as conn:
            return investments_repo.get_investment(conn, investment_id)

    def insert_investment(self, investment: Dict) -> int:
        """Create a new investment."""
        with self.transaction() as conn:
            return investments_repo.insert_investment(conn, investment)

    def update_investment(self, investment_id: int, investment: Dict) -> bool:
        """Update an existing investment."""
        with self.transaction() as conn:
            return investments_repo.update_investment(conn, investment_id, investment)

    def delete_investment(self, investment_id: int) -> bool:
        """Soft-delete an investment."""
        with self.transaction() as conn:
            return investments_repo.delete_investment(conn, investment_id)

    # Income Sources Methods (delegate to income_sources_repo)
    def get_income_sources(self, active_only: bool = False) -> List[Dict]:
        """Get all income sources."""
        with self.connection() as conn:
            return income_sources_repo.get_income_sources(conn, active_only)

    def get_income_source(self, source_id: int) -> Optional[Dict]:
        """Get a single income source by ID."""
        with self.connection() as conn:
            return income_sources_repo.get_income_source(conn, source_id)

    def insert_income_source(self, source: Dict) -> int:
        """Create a new income source."""
        with self.transaction() as conn:
            return income_sources_repo.insert_income_source(conn, source)

    def update_income_source(self, source_id: int, source: Dict) -> bool:
        """Update an existing income source."""
        with self.transaction() as conn:
            return income_sources_repo.update_income_source(conn, source_id, source)

    def delete_income_source(self, source_id: int) -> bool:
        """Soft-delete an income source."""
        with self.transaction() as conn:
            return income_sources_repo.delete_income_source(conn, source_id)

    # Members Methods (delegate to members_repo)
    def get_members(self) -> List[Dict]:
        """Get all family members."""
        with self.connection() as conn:
            return members_repo.get_members(conn)

    def get_member(self, member_id: int) -> Optional[Dict]:
        """Get a single member by ID."""
        with self.connection() as conn:
            return members_repo.get_member(conn, member_id)

    def add_member(self, name: str, color: str = "#6366F1") -> int:
        """Add a new family member."""
        with self.transaction() as conn:
            return members_repo.add_member(conn, name, color)

    def update_member(self, member_id: int, name: Optional[str] = None, color: Optional[str] = None) -> bool:
        """Update an existing member."""
        with self.transaction() as conn:
            return members_repo.update_member(conn, member_id, name, color)

    def delete_member(self, member_id: int) -> bool:
        """Delete a member."""
        with self.transaction() as conn:
            return members_repo.delete_member(conn, member_id)

    # Loans Methods (delegate to loans_repo)
    def get_loans(self, status: str | None = None) -> list[dict]:
        """Get all loans."""
        with self.connection() as conn:
            return loans_repo.get_loans(conn, status)

    def get_loan(self, loan_id: int) -> dict | None:
        """Get a single loan by ID."""
        with self.connection() as conn:
            return loans_repo.get_loan(conn, loan_id)

    def insert_loan(self, data: dict) -> int:
        """Insert a new loan."""
        with self.transaction() as conn:
            return loans_repo.insert_loan(conn, data)

    def update_loan(self, loan_id: int, data: dict) -> bool:
        """Update an existing loan."""
        with self.transaction() as conn:
            return loans_repo.update_loan(conn, loan_id, data)

    def delete_loan(self, loan_id: int) -> bool:
        """Delete a loan."""
        with self.transaction() as conn:
            return loans_repo.delete_loan(conn, loan_id)

    def delete_loan_with_payments(self, loan_id: int) -> bool:
        """Delete a loan and all its payments."""
        with self.transaction() as conn:
            return loans_repo.delete_loan_with_payments(conn, loan_id)

    def get_loan_payments(self, loan_id: int) -> list[dict]:
        """Get all payments for a specific loan."""
        with self.connection() as conn:
            return loans_repo.get_loan_payments(conn, loan_id)

    def insert_loan_payment(self, data: dict) -> int:
        """Insert a new loan payment."""
        with self.transaction() as conn:
            return loans_repo.insert_loan_payment(conn, data)

    def get_all_loan_payments_grouped(self) -> dict[int, list[dict]]:
        """Fetch all payments for active loans, grouped by loan_id."""
        with self.connection() as conn:
            return loans_repo.get_all_loan_payments_grouped(conn)

    # Reconciliations Methods (delegate to reconciliations_repo)
    def get_reconciliations(self, status: Optional[str] = None) -> List[Dict]:
        """Get all reconciliations with optional status filter."""
        with self.connection() as conn:
            return reconciliations_repo.get_reconciliations(conn, status)

    def get_reconciliations_paginated(
        self,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 50
    ) -> PaginatedResult:
        """Get reconciliations with pagination."""
        with self.connection() as conn:
            return reconciliations_repo.get_reconciliations_paginated(conn, status, page, per_page)

    def get_pending_reconciliations(self) -> List[Dict]:
        """Get all pending reconciliations."""
        with self.connection() as conn:
            return reconciliations_repo.get_pending_reconciliations(conn)

    def get_reconciliation(self, reconciliation_id: int) -> Optional[Dict]:
        """Get a single reconciliation by ID."""
        with self.connection() as conn:
            return reconciliations_repo.get_reconciliation(conn, reconciliation_id)

    def insert_reconciliation(
        self,
        debit_txn_id: int,
        credit_txn_id: int,
        debit_account_id: str,
        credit_account_id: str,
        amount: float,
        date_diff_days: int = 0,
        match_confidence: float = 0.5,
        match_type: str = "auto"
    ) -> int:
        """Create a new reconciliation."""
        with self.transaction() as conn:
            return reconciliations_repo.insert_reconciliation(
                conn, debit_txn_id, credit_txn_id, debit_account_id,
                credit_account_id, amount, date_diff_days, match_confidence, match_type
            )

    def confirm_reconciliation(self, reconciliation_id: int) -> bool:
        """Confirm a reconciliation."""
        with self.transaction() as conn:
            return reconciliations_repo.confirm_reconciliation(conn, reconciliation_id)

    def reject_reconciliation(self, reconciliation_id: int) -> bool:
        """Reject a reconciliation."""
        with self.transaction() as conn:
            return reconciliations_repo.reject_reconciliation(conn, reconciliation_id)

    # Recurring Transactions Methods
    def get_recurring_transactions(self, active_only: bool = True) -> List[Dict]:
        """Get all recurring transactions."""
        with self.connection() as conn:
            query = "SELECT * FROM recurring_transactions"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY next_due_date"
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def insert_recurring_transaction(self, data: dict) -> int:
        """Insert a new recurring transaction."""
        with self.transaction() as conn:
            columns = [
                "description", "amount_paise", "type", "category", "frequency",
                "account_id", "next_due_date", "last_detected_date", "occurrence_count",
                "is_active", "auto_detected", "notes"
            ]

            placeholders = ", ".join(["?"] * len(columns))
            columns_str = ", ".join(columns)

            query = f"""
                INSERT INTO recurring_transactions ({columns_str})
                VALUES ({placeholders})
            """

            params = [
                data.get("description"),
                data.get("amount_paise"),
                data.get("type", "debit"),
                data.get("category", "Uncategorized"),
                data.get("frequency", "monthly"),
                data.get("account_id"),
                data.get("next_due_date"),
                data.get("last_detected_date"),
                data.get("occurrence_count", 0),
                data.get("is_active", 1),
                data.get("auto_detected", 0),
                data.get("notes", "")
            ]

            cursor = conn.execute(query, params)
            return cursor.lastrowid

    # Dashboard Methods (delegate to repositories)
    def get_overview_stats(self) -> Dict:
        """Get overview statistics for dashboard."""
        with self.connection() as conn:
            # Get basic counts
            total_expense_query = "SELECT COALESCE(SUM(amount_paise), 0) FROM transactions WHERE type = 'debit'"
            total_income_query = "SELECT COALESCE(SUM(amount_paise), 0) FROM transactions WHERE type = 'credit'"
            transaction_count_query = "SELECT COUNT(*) FROM transactions"
            category_count_query = "SELECT COUNT(DISTINCT category) FROM transactions WHERE category IS NOT NULL AND category != ''"

            total_expense = conn.execute(total_expense_query).fetchone()[0]
            total_income = conn.execute(total_income_query).fetchone()[0]
            transaction_count = conn.execute(transaction_count_query).fetchone()[0]
            category_count = conn.execute(category_count_query).fetchone()[0]

            # Get earliest and latest dates
            earliest_date_query = "SELECT MIN(date_iso) FROM transactions"
            latest_date_query = "SELECT MAX(date_iso) FROM transactions"

            earliest_date = conn.execute(earliest_date_query).fetchone()[0]
            latest_date = conn.execute(latest_date_query).fetchone()[0]

            # Calculate net cashflow
            net_cashflow = total_income - total_expense

            return {
                "total_expense_paise": total_expense,
                "total_income_paise": total_income,
                "transaction_count": transaction_count,
                "category_count": category_count,
                "earliest_date": earliest_date,
                "latest_date": latest_date,
                "net_cashflow_paise": net_cashflow
            }

    def get_all_transactions_with_bank(self, filters: dict = None, page: int = 1, per_page: int = 50) -> Dict:
        """Get all transactions with bank information and pagination."""
        with self.connection() as conn:
            # Build query with filters
            query = "SELECT t.*, s.bank FROM transactions t LEFT JOIN statements s ON t.statement_id = s.id"
            params = []

            # Apply filters
            conditions = []
            if filters:
                if filters.get("search"):
                    conditions.append("(t.description LIKE ? OR t.original_description LIKE ?)")
                    params.extend([f"%{filters['search']}%", f"%{filters['search']}%"])
                if filters.get("bank"):
                    conditions.append("s.bank = ?")
                    params.append(filters["bank"])
                if filters.get("category"):
                    conditions.append("t.category = ?")
                    params.append(filters["category"])
                if filters.get("type"):
                    conditions.append("t.type = ?")
                    params.append(filters["type"])
                if filters.get("member"):
                    conditions.append("t.member = ?")
                    params.append(filters["member"])

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY t.date_iso DESC"

            # Add pagination
            offset = (page - 1) * per_page
            query += f" LIMIT {per_page} OFFSET {offset}"

            # Get total count for pagination
            count_query = "SELECT COUNT(*) FROM transactions t LEFT JOIN statements s ON t.statement_id = s.id"
            if conditions:
                count_query += " WHERE " + " AND ".join(conditions)

            total = conn.execute(count_query, params).fetchone()[0]

            # Get paginated results
            cursor = conn.execute(query, params)
            items = [dict(row) for row in cursor.fetchall()]

            # Calculate has_next
            has_next = (page * per_page) < total

            return {
                "items": items,
                "page": page,
                "per_page": per_page,
                "total": total,
                "has_next": has_next
            }

    def get_monthly_summary(self) -> List[Dict]:
        """Get monthly transaction summary for dashboard charts."""
        with self.connection() as conn:
            query = """
                SELECT
                    strftime('%Y-%m', date_iso) as month,
                    SUM(CASE WHEN type = 'debit' THEN amount_paise ELSE 0 END) as total_debit,
                    SUM(CASE WHEN type = 'credit' THEN amount_paise ELSE 0 END) as total_credit,
                    SUM(amount_paise) as net_amount
                FROM transactions
                GROUP BY strftime('%Y-%m', date_iso)
                ORDER BY month DESC
            """
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def get_category_summary(self, date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Dict]:
        """Get category-wise transaction summary with optional date filtering."""
        with self.connection() as conn:
            query = """
                SELECT
                    category,
                    SUM(amount_paise) as total_amount,
                    COUNT(*) as transaction_count
                FROM transactions
                WHERE type = 'debit' AND category IS NOT NULL AND category != ''
            """
            params = []
            if date_from:
                query += " AND date_iso >= ?"
                params.append(date_from)
            if date_to:
                query += " AND date_iso <= ?"
                params.append(date_to)
            query += " GROUP BY category ORDER BY total_amount DESC"

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_category_totals_by_month(self) -> List[Dict]:
        """Get category totals by month for trend analysis."""
        with self.connection() as conn:
            query = """
                SELECT
                    strftime('%Y-%m', date_iso) as month,
                    category,
                    SUM(amount_paise) as total
                FROM transactions
                WHERE type = 'debit' AND category IS NOT NULL AND category != ''
                GROUP BY month, category
                ORDER BY month DESC, total DESC
            """
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def get_uncategorized_patterns(self, limit: int = 20) -> List[Dict]:
        """Get uncategorized transaction patterns for categorization suggestions."""
        with self.connection() as conn:
            query = """
                SELECT
                    description,
                    COUNT(*) as count,
                    SUM(amount_paise) as total_amount
                FROM transactions
                WHERE type = 'debit' AND (category IS NULL OR category = '' OR category = 'Uncategorized')
                GROUP BY description
                ORDER BY count DESC, total_amount DESC
                LIMIT ?
            """
            cursor = conn.execute(query, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_bank_transaction_totals(self) -> List[Dict]:
        """Get bank-wise transaction totals."""
        with self.connection() as conn:
            query = """
                SELECT
                    s.bank,
                    SUM(CASE WHEN t.type = 'debit' THEN t.amount_paise ELSE 0 END) as total_debit,
                    SUM(CASE WHEN t.type = 'credit' THEN t.amount_paise ELSE 0 END) as total_credit
                FROM transactions t
                LEFT JOIN statements s ON t.statement_id = s.id
                WHERE s.bank IS NOT NULL
                GROUP BY s.bank
                ORDER BY total_debit DESC
            """
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def get_statements_paginated(self, page: int = 1, per_page: int = 50) -> Dict:
        """Get statements with pagination."""
        with self.connection() as conn:
            # Get total count
            count_query = "SELECT COUNT(*) FROM statements"
            total = conn.execute(count_query).fetchone()[0]

            # Get paginated results
            offset = (page - 1) * per_page
            query = f"SELECT * FROM statements ORDER BY imported_at DESC LIMIT {per_page} OFFSET {offset}"
            cursor = conn.execute(query)
            items = [dict(row) for row in cursor.fetchall()]

            # Calculate has_next
            has_next = (page * per_page) < total

            return {
                "items": items,
                "page": page,
                "per_page": per_page,
                "total": total,
                "has_next": has_next,
            }

    def get_monthly_snapshots(self, limit: int = 24) -> List[Dict]:
        """Get monthly financial snapshots."""
        with self.connection() as conn:
            query = "SELECT * FROM monthly_snapshots ORDER BY month DESC LIMIT ?"
            cursor = conn.execute(query, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def list_statement_imports(self, status: str = None, page: int = 1, per_page: int = 50) -> Dict:
        """List statement imports with pagination."""
        from .repos.imports_repo import list_statement_imports
        with self.connection() as conn:
            return list_statement_imports(conn, status=status, page=page, per_page=per_page)
