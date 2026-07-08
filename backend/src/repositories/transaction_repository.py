"""Transaction domain repository."""
from src.repositories.base import BaseRepository


class TransactionRepository(BaseRepository):
    """Repository for transaction operations."""

    def get_all_transactions(self, filters: dict | None = None) -> list[dict]:
        """
        Fetch transactions with optional filters.
        Supported filter keys: date_from, date_to, bank, category, min_amount, max_amount, type
        """
        return self._db().get_all_transactions(filters=filters)

    def get_all_transactions_with_bank(self, filters: dict | None = None) -> list[dict]:
        """
        JOIN transactions with statements to include bank info.
        Returns list of dicts with all transaction + statement fields.
        Filters (all optional): search, bank, category, type, min_amount, max_amount, member.
        Date filtering is done in Python (dates stored as varied format strings).
        Order: transactions.id ASC (insertion order = chronological per statement).
        """
        return self._db().get_all_transactions_with_bank(filters=filters)

    def insert_transactions(self, statement_id: int, transactions: list[dict]) -> int:
        """
        Bulk insert transactions. Deduplicates by hash_signature.
        Phase 2A.1: Uses hash_signature for deduplication.
        Hash = SHA256(account_id | date_iso | description | debit | credit)
        Phase 2A: Also populates debit, credit, amount_paise columns for financial determinism.
        Returns count of rows actually inserted.
        """
        return self._db().insert_transactions(statement_id=statement_id, transactions=transactions)

    def get_monthly_summary(self) -> list[dict]:
        """
        Returns monthly aggregates:
          [{month, total_debit, total_credit, transaction_count}]
        Month format: YYYY-MM (derived from date string).
        """
        return self._db().get_monthly_summary()

    def get_category_summary(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict]:
        """
        Returns per-category aggregates:
          [{category, total_amount, count}]
        """
        return self._db().get_category_summary(date_from=date_from, date_to=date_to)

    def get_category_totals_by_month(self) -> list[dict]:
        """
        For stacked bar chart. Returns list of dicts:
        [{month: "2025-04", category: "Food & Dining", total: 2345.67}, ...]
        Uses Python-side date parsing to handle all date formats.
        """
        return self._db().get_category_totals_by_month()

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
        return self._db().bulk_update_category(
            transaction_ids=transaction_ids,
            category=category,
            subcategory=subcategory,
        )

    def get_uncategorized_patterns(self, limit: int = 50) -> list[dict]:
        """
        Returns grouped uncategorized transaction descriptions.
        [{description, count, total_amount}] ordered by count DESC.
        """
        return self._db().get_uncategorized_patterns(limit=limit)

    def get_confirmed_transfer_ids(self) -> list[tuple]:
        """
        Returns list of (debit_txn_id, credit_txn_id) for confirmed reconciliations.
        """
        return self._db().get_confirmed_transfer_ids()

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
        return self._db().insert_csv_transactions(
            transactions=transactions,
            member=member,
            source=source,
            bank=bank,
            file_name=file_name,
        )

