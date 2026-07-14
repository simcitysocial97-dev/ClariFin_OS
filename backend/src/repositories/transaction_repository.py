"""Transaction domain repository.

LOC WATCH: No repository file > 200 LOC.
If it grows beyond 200, split by sub-domain.
"""
import hashlib
from collections import defaultdict
from typing import Any

from src.models.transaction import Transaction
from src.repositories.base import BaseRepository


def _parse_date_to_ymd(date_str: str) -> str:
    """Parse Indian date formats to YYYY-MM-DD for sorting/grouping.

    Returns the input unchanged if it is already in YYYY-MM-DD form.
    Returns '' for any value that cannot be normalized.
    """
    from datetime import datetime
    s = (date_str or "").strip()
    if not s:
        return ""
    # Already ISO — pass through unchanged (accepts YYYY-MM-DD and YYYY/MM/DD)
    for iso_fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, iso_fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y",
        "%d %b %Y", "%d %b %y", "%d-%b-%Y", "%d-%b-%y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""


class TransactionRepository(BaseRepository):
    """Repository for transaction operations."""

    def get_all(self) -> list[Transaction]:
        """
        Return all transactions as Transaction domain models.

        Maps the canonical `amount_paise` column into the `Money` value object.
        """
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT
                    t.id, t.statement_id, t.date, t.description,
                    t.amount_paise, t.category, t.member, s.bank
                FROM transactions t
                LEFT JOIN statements s ON t.statement_id = s.id
                ORDER BY t.date DESC, t.id DESC
                """
            ).fetchall()
        return [
            Transaction.from_db_row({**dict(row), "date": _parse_date_to_ymd(row["date"])})
            for row in rows
        ]

    def get_all_with_bank(self) -> list[Transaction]:
        """
        Return all transactions joined with statement bank info as Transaction models.

        Mirrors get_all_transactions_with_bank but wraps rows in Transaction.
        """
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT
                    t.id, t.statement_id, t.date, t.description,
                    t.amount_paise, t.category, t.member, s.bank
                FROM transactions t
                LEFT JOIN statements s ON t.statement_id = s.id
                ORDER BY t.id ASC
                """
            ).fetchall()
        return [
            Transaction.from_db_row({**dict(row), "date": _parse_date_to_ymd(row["date"])})
            for row in rows
        ]

    def get_all_transactions(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """
        Fetch transactions with optional filters.
        Supported filter keys: date_from, date_to, bank, category, min_amount, max_amount, type
        """
        filters = filters or {}
        conditions: list[str] = []
        params: list[Any] = []

        if filters.get("date_from"):
            conditions.append("t.date >= ?")
            params.append(filters["date_from"])
        if filters.get("date_to"):
            conditions.append("t.date <= ?")
            params.append(filters["date_to"])
        if filters.get("bank"):
            conditions.append("s.bank = ?")
            params.append(filters["bank"])
        if filters.get("category"):
            conditions.append("t.category = ?")
            params.append(filters["category"])
        if filters.get("min_amount") is not None:
            conditions.append("t.amount_paise >= ?")
            params.append(int(filters["min_amount"] * 100))
        if filters.get("max_amount") is not None:
            conditions.append("t.amount_paise <= ?")
            params.append(int(filters["max_amount"] * 100))
        if filters.get("type"):
            conditions.append("t.type = ?")
            params.append(filters["type"])

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        sql = f"""
            SELECT
                t.id, t.statement_id, t.date, t.description, t.amount_paise,
                t.type, t.category, t.subcategory, t.raw_description, t.created_at,
                s.bank, s.file_name, s.statement_period_from, s.statement_period_to
            FROM transactions t
            JOIN statements s ON t.statement_id = s.id
            {where}
            ORDER BY t.date DESC, t.id DESC
        """

        with self._get_conn() as conn:
            cur = conn.execute(sql, params)
            rows = [dict(row) for row in cur.fetchall()]
        return rows

    def get_all_transactions_with_bank(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """
        JOIN transactions with statements to include bank info.
        Returns list of dicts with all transaction + statement fields.
        Filters (all optional): search, bank, category, type, min_amount, max_amount, member.
        Date filtering is done in Python (dates stored as varied format strings).
        Order: transactions.id ASC (insertion order = chronological per statement).
        """
        filters = filters or {}
        conditions: list[str] = []
        params: list[Any] = []

        if filters.get("search"):
            conditions.append("t.description LIKE ?")
            params.append(f"%{filters['search']}%")
        if filters.get("bank") and filters["bank"] != "All":
            conditions.append("s.bank = ?")
            params.append(filters["bank"])
        if filters.get("category") and filters["category"] != "All":
            conditions.append("t.category = ?")
            params.append(filters["category"])
        if filters.get("type") and filters["type"] != "All":
            conditions.append("t.type = ?")
            params.append(filters["type"])
        if filters.get("min_amount") is not None:
            conditions.append("t.amount_paise >= ?")
            params.append(int(filters["min_amount"] * 100))
        if filters.get("max_amount") is not None:
            conditions.append("t.amount_paise <= ?")
            params.append(int(filters["max_amount"] * 100))
        if filters.get("member") and filters["member"] != "All":
            conditions.append("t.member = ?")
            params.append(filters["member"])

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        sql = f"""
            SELECT
                t.id, t.sequence_num, t.date, t.description,
                t.amount_paise, t.debit, t.credit,
                t.type, t.category, t.subcategory, t.raw_description, t.member,
                s.bank, s.file_name AS statement_file,
                s.statement_period_from, s.statement_period_to
            FROM transactions t
            JOIN statements s ON t.statement_id = s.id
            {where}
            ORDER BY t.id ASC
        """

        with self._get_conn() as conn:
            cur = conn.execute(sql, params)
            rows = [dict(row) for row in cur.fetchall()]
        return rows

    def insert_transactions(self, statement_id: int, transactions: list[dict[str, Any]]) -> int:
        """
        Bulk insert transactions. Deduplicates by hash_signature.
        Phase 2A.1: Uses hash_signature for deduplication.
        Hash = SHA256(account_id | date_iso | description | debit | credit)
        Phase 2A: Also populates debit, credit, amount_paise columns for financial determinism.
        Returns count of rows actually inserted.
        """
        if not transactions:
            return 0

        with self._get_conn() as conn:
            inserted = 0

            # Get bank (account_id) for this statement
            cur = conn.execute("SELECT bank FROM statements WHERE id = ?", (statement_id,))
            row = cur.fetchone()
            account_id = row["bank"] if row else ""

            for seq, txn in enumerate(transactions):
                # Amount should already be in paise from parsing (source of truth)
                amount_paise = int(txn.get("amount_paise") or 0)
                date = str(txn.get("date", "")).strip()
                description = str(txn.get("description", "")).strip()
                txn_type = str(txn.get("type", "")).strip()
                category = str(txn.get("category", "Uncategorized")).strip() or "Uncategorized"
                subcategory = str(txn.get("subcategory", "")).strip() or None

                # Phase 2A: Compute debit/credit paise values
                debit_paise = amount_paise if txn_type == 'debit' else 0
                credit_paise = amount_paise if txn_type == 'credit' else 0

                # Phase 2A.1: Compute date_iso
                date_iso = _parse_date_to_ymd(date) if date else ""

                if not date:
                    continue

                # Phase 2A.1: Compute hash_signature
                hash_input = f"{account_id}|{date_iso}|{description}|{debit_paise}|{credit_paise}"
                hash_signature = hashlib.sha256(hash_input.encode()).hexdigest().lower()

                cur = conn.execute(
                    """
                    INSERT OR IGNORE INTO transactions
                        (statement_id, sequence_num, date, description, type, category, subcategory,
                         amount_paise, date_iso, hash_signature, account_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        statement_id,
                        seq,
                        date,
                        description,
                        txn_type,
                        category,
                        subcategory,
                        amount_paise,
                        date_iso,
                        hash_signature,
                        account_id,
                    ),
                )
                inserted += cur.rowcount

            conn.commit()
        return inserted

    # ============================================================
    # Behaviour Engine Aggregation Methods
    # ============================================================

    def get_recent_transactions(self, limit: int = 500) -> list[dict[str, Any]]:
        """Get most recent N transactions for performance.

        Used by behaviour engine for temporal pattern analysis.

        Args:
            limit: Maximum number of transactions to return (default 500).

        Returns:
            List of transaction dicts sorted by date ascending.
        """
        with self._get_conn() as conn:
            cur = conn.execute("""
                SELECT
                    t.id, t.date, t.date_iso, t.description, t.amount_paise,
                    t.type, t.category, t.debit, t.credit, t.account_id
                FROM transactions t
                ORDER BY t.date_iso DESC
                LIMIT ?
            """, (limit,))

            rows = [dict(row) for row in cur.fetchall()]

        # Return in ascending order for time-series calculations
        return sorted(rows, key=lambda r: r.get("date_iso", ""))

    def get_transactions_last_90_days(self) -> list[dict[str, Any]]:
        """Get transactions from last 90 days for temporal analysis.

        Returns:
            List of transaction dicts from the last 90 days.
        """
        from datetime import datetime, timedelta

        cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

        with self._get_conn() as conn:
            cur = conn.execute("""
                SELECT
                    t.id, t.date, t.date_iso, t.description, t.amount_paise,
                    t.type, t.category, t.debit, t.credit, t.account_id
                FROM transactions t
                WHERE t.date_iso >= ?
                ORDER BY t.date_iso ASC
            """, (cutoff,))

            rows = [dict(row) for row in cur.fetchall()]

        return rows

    def get_daily_spending(self, cutoff_date: str) -> dict[str, float]:
        """Get daily spending totals using SQL aggregation.

        Much faster than Python loops for large datasets.

        Args:
            cutoff_date: Date string (YYYY-MM-DD) to filter from.

        Returns:
            Dict mapping date_iso to daily total in paise.
        """
        with self._get_conn() as conn:
            cur = conn.execute("""
                SELECT
                    date_iso,
                    SUM(amount_paise) as daily_total_paise
                FROM transactions
                WHERE type = 'debit' AND date_iso >= ?
                GROUP BY date_iso
                ORDER BY date_iso ASC
            """, (cutoff_date,))

            rows = [dict(row) for row in cur.fetchall()]

        return {row["date_iso"]: float(row["daily_total_paise"] or 0) for row in rows}

    def get_monthly_category_totals(self, cutoff_date: str) -> dict[str, dict[str, float]]:
        """Get monthly category spending using SQL aggregation.

        Returns: {month: {category: total_paise}}

        Args:
            cutoff_date: Date string (YYYY-MM-DD) to filter from.

        Returns:
            Dict of monthly category spending totals.
        """
        with self._get_conn() as conn:
            cur = conn.execute("""
                SELECT
                    substr(date_iso, 1, 7) as month,
                    category,
                    SUM(amount_paise) as category_total_paise
                FROM transactions
                WHERE type = 'debit' AND date_iso >= ?
                GROUP BY month, category
                ORDER BY month ASC
            """, (cutoff_date,))

            rows = [dict(row) for row in cur.fetchall()]

        result: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for row in rows:
            month = row["month"]
            category = row["category"] or "Uncategorized"
            result[month][category] = float(row["category_total_paise"] or 0)

        return dict(result)

    def get_monthly_income_expenses(self, cutoff_date: str) -> dict[str, dict[str, int]]:
        """Get monthly income vs expenses using SQL aggregation.

        Returns: {month: {"income_paise": total, "expenses_paise": total}}

        Args:
            cutoff_date: Date string (YYYY-MM-DD) to filter from.

        Returns:
            Dict of monthly income/expense totals.
        """
        with self._get_conn() as conn:
            cur = conn.execute("""
                SELECT
                    substr(date_iso, 1, 7) as month,
                    type,
                    SUM(amount_paise) as total_paise
                FROM transactions
                WHERE date_iso >= ?
                GROUP BY month, type
                ORDER BY month ASC
            """, (cutoff_date,))

            rows = [dict(row) for row in cur.fetchall()]

        result: dict[str, dict[str, int]] = defaultdict(lambda: {"income_paise": 0, "expenses_paise": 0})
        for row in rows:
            month = row["month"]
            txn_type = row["type"]
            total = int(row["total_paise"] or 0)
            if txn_type == "credit":
                result[month]["income_paise"] = total
            else:
                result[month]["expenses_paise"] = total

        return dict(result)

    def get_transaction_stats(self, cutoff_date: str) -> dict[str, Any]:
        """Get transaction statistics using SQL aggregation.

        Returns counts and totals for various metrics.

        Args:
            cutoff_date: Date string (YYYY-MM-DD) to filter from.

        Returns:
            Dict with transaction statistics including weekend/weekday splits.
        """
        with self._get_conn() as conn:

            # Get basic stats
            cur = conn.execute("""
                SELECT
                    COUNT(*) as total_count,
                    SUM(CASE WHEN type = 'debit' THEN 1 ELSE 0 END) as debit_count,
                    SUM(CASE WHEN type = 'credit' THEN 1 ELSE 0 END) as credit_count,
                    SUM(CASE WHEN type = 'debit' AND amount_paise < 50000 THEN 1 ELSE 0 END) as micro_txn_count,
                    SUM(CASE WHEN type = 'debit' THEN amount_paise ELSE 0 END) as total_debit_paise,
                    SUM(CASE WHEN type = 'credit' THEN amount_paise ELSE 0 END) as total_credit_paise
                FROM transactions
                WHERE date_iso >= ?
            """, (cutoff_date,))

            row = cur.fetchone()
            stats: dict[str, Any] = {
                "total_count": int(row["total_count"] or 0),
                "debit_count": int(row["debit_count"] or 0),
                "credit_count": int(row["credit_count"] or 0),
                "micro_txn_count": int(row["micro_txn_count"] or 0),
                "total_debit_paise": int(row["total_debit_paise"] or 0),
                "total_credit_paise": int(row["total_credit_paise"] or 0),
            }

            # Get weekend vs weekday spending
            cur = conn.execute("""
                SELECT
                    CASE WHEN CAST(substr(date_iso, 9, 2) AS INTEGER) % 7 >= 5 THEN 'weekend' ELSE 'weekday' END as day_type,
                    SUM(amount_paise) as total_paise
                FROM transactions
                WHERE type = 'debit' AND date_iso >= ?
                GROUP BY day_type
            """, (cutoff_date,))

            weekend_stats = {"weekend": 0, "weekday": 0}
            for row in cur.fetchall():
                day_type = row["day_type"]
                weekend_stats[day_type] = int(row["total_paise"] or 0)

            stats["weekend_spend_paise"] = weekend_stats["weekend"]
            stats["weekday_spend_paise"] = weekend_stats["weekday"]

            return stats

    def get_transaction_by_id(self, txn_id: int) -> dict[str, Any] | None:
        """Get a single transaction by ID as a plain dict."""
        with self._get_conn() as conn:
            cur = conn.execute(
                "SELECT * FROM transactions WHERE id = ?",
                (txn_id,),
            )
            row = cur.fetchone()
        return dict(row) if row else None

    def get_transaction_count(self) -> int:
        """Get total count of transactions."""
        with self._get_conn() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM transactions")
            count = cur.fetchone()[0]
        return int(count)

    def get_monthly_summary(self) -> list[dict[str, Any]]:
        """
        Returns monthly aggregates:
          [{month, total_debit_paise, total_credit_paise, transaction_count}]
        Month format: YYYY-MM (derived from date string).
        """
        sql = """
            SELECT
                substr(date, 7, 4) || '-' || substr(date, 4, 2) AS month,
                SUM(CASE WHEN type = 'debit'  THEN amount_paise ELSE 0 END) AS total_debit_paise,
                SUM(CASE WHEN type = 'credit' THEN amount_paise ELSE 0 END) AS total_credit_paise,
                COUNT(*) AS transaction_count
            FROM transactions
            WHERE date LIKE '__/__/____'
            GROUP BY month
            ORDER BY month DESC
        """

        with self._get_conn() as conn:
            cur = conn.execute(sql)
            rows = [dict(row) for row in cur.fetchall()]
        return rows

    def get_category_summary(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Returns per-category aggregates:
          [{category, total_amount_paise, count}]
        """
        conditions: list[str] = []
        params: list[Any] = []
        if date_from:
            conditions.append("date >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("date <= ?")
            params.append(date_to)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        sql = f"""
            SELECT
                category,
                SUM(amount_paise) AS total_amount_paise,
                COUNT(*) AS count
            FROM transactions
            {where}
            GROUP BY category
            ORDER BY total_amount_paise DESC
        """

        with self._get_conn() as conn:
            cur = conn.execute(sql, params)
            rows = [dict(row) for row in cur.fetchall()]
        return rows

    def get_category_totals_by_month(self) -> list[dict[str, Any]]:
        """
        For stacked bar chart. Returns list of dicts:
        [{month: "2025-04", category: "Food & Dining", total_paise: 234567}, ...]
        Uses Python-side date parsing to handle all date formats.
        """
        with self._get_conn() as conn:
            cur = conn.execute(
                "SELECT date, category, amount_paise, type FROM transactions ORDER BY id ASC"
            )
            rows = cur.fetchall()

        data: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for row in rows:
            if row["type"] != "debit":
                continue
            ymd = _parse_date_to_ymd(row["date"] or "")
            if not ymd:
                continue
            month = ymd[:7]  # YYYY-MM
            data[month][row["category"]] += row["amount_paise"]

        result = []
        for month in sorted(data.keys()):
            for cat, total in data[month].items():
                result.append({"month": month, "category": cat, "total_paise": total})
        return result

    def update_category(
        self,
        transaction_id: int,
        category: str,
        subcategory: str | None = None,
    ) -> bool:
        """
        Manually re-categorize a transaction.
        Returns True if a row was updated.
        """
        with self._get_conn() as conn:
            cur = conn.execute(
                "UPDATE transactions SET category = ?, subcategory = ? WHERE id = ?",
                (category, subcategory, transaction_id),
            )
            updated = cur.rowcount > 0
            conn.commit()
        return updated

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
        if not transaction_ids:
            return 0

        with self._get_conn() as conn:
            placeholders = ",".join("?" * len(transaction_ids))
            params = [category, subcategory] + list(transaction_ids)
            cur = conn.execute(
                f"UPDATE transactions SET category=?, subcategory=? WHERE id IN ({placeholders})",
                params,
            )
            updated = cur.rowcount
            conn.commit()
        return updated

    def get_uncategorized_patterns(self, limit: int = 50) -> list[dict[str, Any]]:
        """
        Returns grouped uncategorized transaction descriptions.
        [{description, count, total_amount_paise}] ordered by count DESC.
        """
        sql = """
            SELECT description, COUNT(*) AS count, SUM(amount_paise) AS total_amount_paise
            FROM transactions
            WHERE category = 'Uncategorized'
            GROUP BY description
            ORDER BY count DESC, total_amount_paise DESC
            LIMIT ?
        """

        with self._get_conn() as conn:
            cur = conn.execute(sql, (limit,))
            rows = [dict(row) for row in cur.fetchall()]
        return rows

    def get_confirmed_transfer_ids(self) -> list[tuple[int, int]]:
        """
        Returns list of (debit_txn_id, credit_txn_id) tuples for confirmed reconciliations.
        """
        with self._get_conn() as conn:
            cur = conn.execute("""
                SELECT debit_txn_id, credit_txn_id
                FROM reconciliations
                WHERE status = 'confirmed'
            """)
            rows = [(int(row[0]), int(row[1])) for row in cur.fetchall()]
        return rows

    def insert_csv_transactions(
        self,
        transactions: list[dict[str, Any]],
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

        with self._get_conn() as conn:
            # Create a statement record for this import
            cur = conn.execute(
                """
                INSERT INTO statements (bank, file_name, source)
                VALUES (?, ?, ?)
                """,
                (bank, file_name or f"{source}_import_{len(transactions)}_txns", source),
            )
            statement_id = cur.lastrowid or 0

            inserted = 0
            for seq, txn in enumerate(transactions):
                # Parse amount to paise (source of truth)
                amount_paise = int(txn.get("amount_paise") or 0)
                if "amount" in txn and not amount_paise:
                    # Handle legacy amount field - convert to paise
                    try:
                        amount_paise = int(float(txn.get("amount", 0)) * 100)
                    except (ValueError, TypeError):
                        amount_paise = 0

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
                        (statement_id, sequence_num, date, description, type,
                         category, subcategory, member, source, original_description,
                         amount_paise, date_iso, hash_signature, account_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        statement_id,
                        seq,
                        date,
                        description,
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

            conn.commit()
        return inserted
