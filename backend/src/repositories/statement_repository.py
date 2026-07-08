"""Statement domain repository."""
from src.engines.balance_engine import validate_statement_balance
from src.repositories.base import BaseRepository


class StatementRepository(BaseRepository):
    """Repository for statement operations."""

    def get_all_statements(self) -> list[dict]:
        """Get all statements with computed transaction counts and totals."""
        return self._db().get_all_statements()

    def get_all_statements_with_metadata(self) -> list[dict]:
        """
        Returns all statements with metadata + computed transaction counts and totals.
        Includes: total_amount_due, minimum_amount_due, payment_due_date,
                  validation_status, validation_difference, card_last4.
        """
        return self._db().get_all_statements_with_metadata()

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
        return self._db().insert_statement(
            bank=bank,
            file_name=file_name,
            period_from=period_from,
            period_to=period_to,
            card_last4=card_last4,
        )

    def update_statement_metadata(self, statement_id: int, metadata: dict) -> None:
        """Update statement with all extracted metadata."""
        return self._db().update_statement_metadata(statement_id, metadata)

    def update_validation_status(self, statement_id: int, status: str, difference: float) -> None:
        """Update validation status after comparing extracted sum vs total_due."""
        return self._db().update_validation_status(statement_id, status, difference)

    def get_statement_validation_summary(self) -> list[dict]:
        """Returns list of dicts for each statement with validation info."""
        return self._db().get_statement_validation_summary()

    def delete_statement(self, statement_id: int) -> None:
        """Delete a statement and all its transactions."""
        return self._db().delete_statement(statement_id)

    def get_statement_pdf_path(self, statement_id: int) -> str | None:
        """Get the file_name for a statement."""
        return self._db().get_statement_pdf_path(statement_id)

    def validate_statement(self, statement_id: int, claimed_balance_paise: int) -> dict:
        """Validate a statement's closing balance against computed balance."""
        return validate_statement_balance(self.db_path, statement_id, claimed_balance_paise)

    def get_duplicate_check_by_filename(self, file_name: str) -> bool:
        """Returns True if file_name already exists in statements (any bank)."""
        return self._db().get_duplicate_check_by_filename(file_name)
