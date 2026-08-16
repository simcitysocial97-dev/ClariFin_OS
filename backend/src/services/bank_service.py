"""Bank Service - Orchestration layer for bank operations.

Coordinates BankRepository to implement business logic around bank data.
No direct database access — uses repositories only.
"""

from typing import Any

from src.repositories.bank_repository import BankRepository
from src.services.base import BaseService


class BankService(BaseService):
    """Orchestrates bank-related operations.

    Delegates persistence to BankRepository.
    """

    def __init__(self, db_path: str | None = None) -> None:
        super().__init__(db_path)
        self.bank_repo = BankRepository(self.db_path)

    def get_banks(self) -> list[str]:
        """List all known banks from uploaded statements."""
        return self.bank_repo.get_all()

    def get_bank_by_id(self, bank_id: int) -> dict[str, Any] | None:
        """Get bank details by ID."""
        return self.bank_repo.get_by_id(bank_id)

    def create_bank(
        self, name: str, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Create a new bank record."""
        return self.bank_repo.create(name, metadata)

    def update_bank(
        self,
        bank_id: int,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Update bank details."""
        return self.bank_repo.update(bank_id, name, metadata)

    def delete_bank(self, bank_id: int) -> bool:
        """Delete a bank record."""
        return self.bank_repo.delete(bank_id)
