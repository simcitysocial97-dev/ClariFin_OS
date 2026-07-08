"""Transaction domain repository.

LOC WATCH: No repository file > 200 LOC.
If it grows beyond 200, split by sub-domain.
"""
import hashlib
from collections import defaultdict

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

    def get_all_transactions(self, filters: dict | None = None) -> list[dict]:
        """
        Fetch transactions with optional filters.
        Supported filter keys: date_from, date_to, bank, category, min_amount, max_amount, type
        """
        filters = filters or {}
        conditions = []
        params = []

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
                t.id, t.statement_id, t.date, t.description, t.amount,
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

    def get_all_transactions_with_bank(self, filters: dict | None = None) -> list[dict]:
        """
        JOIN transactions with statements to include bank info.
        Returns list of dicts with all transaction + statement fields.
        Filters (all optional): search, bank, category, type, min_amount, max_amount, member.
        Date filtering is done in Python (dates stored as varied format strings).
        Order: transactions.id ASC (insertion order = chronological per statement).
        """
        filters = filters or {}
        conditions = []
        params = []

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
                t.id, t.sequence_num, t.date, t.description, t.amount,
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

    def insert_transactions(self, statement_id: int, transactions: list[dict]) -> int:
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
                # Derive float for legacy 'amount' column (deprecated)
                amount = amount_paise / 100.0
                date = str(txn.get("date", "")).strip()
                description = str(txn.get("description", "")).strip()
                txn_type = str(txn.get("type", "")).strip()
                category = str(txn.get("category", "Uncategorized")).strip() or "Uncategorized"
                subcategory = str(txn.get("subcategory", "")).strip() or None
                raw_description = description  # preserve original

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
                        (statement_id, sequence_num, date, description, amount, type, category, subcategory, raw_description,
                         amount_paise, date_iso, hash_signature, account_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        raw_description,
                        amount_paise,
                        date_iso,
                        hash_signature,
                        account_id,
                    ),
                )
                inserted += cur.rowcount

            conn.commit()
        return inserted

    def get_transaction_count(self) -> int:
        """Get total count of transactions."""
        with self._get_conn() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM transactions")
            count = cur.fetchone()[0]
        return count

    def get_monthly_summary(self) -> list[dict]:
        """
        Returns monthly aggregates:
          [{month, total_debit, total_credit, transaction_count}]
        Month format: YYYY-MM (derived from date string).
        """
        sql = """
            SELECT
                substr(date, 7, 4) || '-' || substr(date, 4, 2) AS month,
                SUM(CASE WHEN type = 'debit'  THEN amount ELSE 0 END) AS total_debit,
                SUM(CASE WHEN type = 'credit' THEN amount ELSE 0 END) AS total_credit,
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
    ) -> list[dict]:
        """
        Returns per-category aggregates:
          [{category, total_amount, count}]
        """
        conditions = []
        params = []
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
                SUM(amount) AS total_amount,
                COUNT(*) AS count
            FROM transactions
            {where}
            GROUP BY category
            ORDER BY total_amount DESC
        """

        with self._get_conn() as conn:
            cur = conn.execute(sql, params)
            rows = [dict(row) for row in cur.fetchall()]
        return rows

    def get_category_totals_by_month(self) -> list[dict]:
        """
        For stacked bar chart. Returns list of dicts:
        [{month: "2025-04", category: "Food & Dining", total: 2345.67}, ...]
        Uses Python-side date parsing to handle all date formats.
        """
        with self._get_conn() as conn:
            cur = conn.execute(
                "SELECT date, category, amount, type FROM transactions ORDER BY id ASC"
            )
            rows = cur.fetchall()

        data: dict = defaultdict(lambda: defaultdict(float))
        for row in rows:
            if row["type"] != "debit":
                continue
            ymd = _parse_date_to_ymd(row["date"] or "")
            if not ymd:
                continue
            month = ymd[:7]  # YYYY-MM
            data[month][row["category"]] += row["amount"]

        result = []
        for month in sorted(data.keys()):
            for cat, total in data[month].items():
                result.append({"month": month, "category": cat, "total": round(total, 2)})
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

    def get_uncategorized_patterns(self, limit: int = 50) -> list[dict]:
        """
        Returns grouped uncategorized transaction descriptions.
        [{description, count, total_amount}] ordered by count DESC.
        """
        sql = """
            SELECT description, COUNT(*) AS count, SUM(amount) AS total_amount
            FROM transactions
            WHERE category = 'Uncategorized'
            GROUP BY description
            ORDER BY count DESC, total_amount DESC
            LIMIT ?
        """

        with self._get_conn() as conn:
            cur = conn.execute(sql, (limit,))
            rows = [dict(row) for row in cur.fetchall()]
        return rows

    def get_confirmed_transfer_ids(self) -> list[tuple]:
        """
        Returns list of (debit_txn_id, credit_txn_id) for confirmed reconciliations.
        """
        with self._get_conn() as conn:
            cur = conn.execute("""
                SELECT debit_txn_id, credit_txn_id
                FROM reconciliations
                WHERE status = 'confirmed'
            """)
            rows = [(row[0], row[1]) for row in cur.fetchall()]
        return rows

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

        with self._get_conn() as conn:
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
                amount_paise = int(txn.get("amount_paise") or 0)
                if "amount" in txn and not amount_paise:
                    # Handle legacy amount field
                    try:
                        amount_paise = int(float(txn.get("amount", 0)) * 100)
                    except (ValueError, TypeError):
                        amount_paise = 0

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

            conn.commit()
        return inserted
