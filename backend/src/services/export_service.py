"""Service for exporting transactions to CSV."""

import csv
import tempfile

from src.repositories.transaction_repository import TransactionRepository
from src.services.base import BaseService


class ExportService(BaseService):
    """Service for exporting transactions to CSV."""

    def __init__(self, db_path: str | None = None):
        super().__init__(db_path)
        self.transaction_repo = TransactionRepository(db_path)

    def export_csv(
        self,
        search: str | None = None,
        bank: str | None = "All",
        category: str | None = "All",
        type: str | None = "All",
        member: str | None = "All",
    ) -> str:
        """Export transactions to CSV.

        Args:
            search: Optional search string to filter transactions.
            bank: Optional bank filter. Defaults to "All".
            category: Optional category filter. Defaults to "All".
            type: Optional transaction type filter. Defaults to "All".
            member: Optional member filter. Defaults to "All".

        Returns:
            Path to the generated CSV file.
        """
        filters = {
            "search": search,
            "bank": bank if bank != "All" else None,
            "category": category if category != "All" else None,
            "type": type if type != "All" else None,
            "member": member if member != "All" else None,
        }

        transactions = self.transaction_repo.get_all_transactions_with_bank(filters)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as tmp_file:
            writer = csv.writer(tmp_file)
            writer.writerow(
                [
                    "Date",
                    "Description",
                    "Bank",
                    "Type",
                    "Category",
                    "Subcategory",
                    "Member",
                    "Amount (₹)",
                    "Statement Period From",
                    "Statement Period To",
                ]
            )

            for txn in transactions:
                writer.writerow(
                    [
                        txn.get("date", ""),
                        txn.get("description", ""),
                        txn.get("bank", ""),
                        txn.get("type", ""),
                        txn.get("category", ""),
                        txn.get("subcategory", ""),
                        txn.get("member", ""),
                        float(txn.get("amount_paise", 0)) / 100,
                        txn.get("statement_period_from", ""),
                        txn.get("statement_period_to", ""),
                    ]
                )

        return tmp_file.name
