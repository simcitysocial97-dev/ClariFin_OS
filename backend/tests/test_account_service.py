"""
Account Service Tests
======================
Tests for AccountService orchestration methods.

Uses mocks to verify engine and repository delegation.
Run: cd backend && ./venv/bin/python3 -m pytest tests/test_account_service.py -v
"""

import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ============================================================
# Test: Account CRUD Operations
# ============================================================


@pytest.fixture
def mock_repos() -> Any:
    """Create mocked repositories for testing."""
    with patch("src.services.account_service.AccountRepository") as MockAccountRepo, \
         patch("src.services.account_service.AccountBalanceRepository") as MockBalanceRepo, \
         patch("src.services.account_service.InstitutionRepository") as MockInstRepo, \
         patch("src.services.account_service.AccountLinkRepository") as MockLinkRepo:
        yield {
            "account": MockAccountRepo.return_value,
            "balance": MockBalanceRepo.return_value,
            "institution": MockInstRepo.return_value,
            "link": MockLinkRepo.return_value,
        }


def test_create_account() -> None:
    """Verify create_account delegates to repository."""
    with patch("src.services.account_service.AccountRepository") as MockAccountRepo, \
         patch("src.services.account_service.AccountBalanceRepository"), \
         patch("src.services.account_service.InstitutionRepository"), \
         patch("src.services.account_service.AccountLinkRepository"):
        mock_repo = MockAccountRepo.return_value
        mock_repo.create_account.return_value = {"id": "ACC001", "name": "Test"}

        from src.services.account_service import AccountService
        service = AccountService()

        result = service.create_account(name="Test", bank="Bank")

        mock_repo.create_account.assert_called_once()
        assert result is not None
        assert result["name"] == "Test"


def test_get_account() -> None:
    """Verify get_account delegates to repository."""
    with patch("src.services.account_service.AccountRepository") as MockAccountRepo, \
         patch("src.services.account_service.AccountBalanceRepository"), \
         patch("src.services.account_service.InstitutionRepository"), \
         patch("src.services.account_service.AccountLinkRepository"):
        mock_repo = MockAccountRepo.return_value
        mock_repo.get_account_by_id.return_value = {"id": "ACC001"}

        from src.services.account_service import AccountService
        service = AccountService()

        result = service.get_account("ACC001")

        mock_repo.get_account_by_id.assert_called_once_with("ACC001")
        assert result is not None
        assert result["id"] == "ACC001"


def test_deactivate_account() -> None:
    """Verify deactivate_account delegates to repository."""
    with patch("src.services.account_service.AccountRepository") as MockAccountRepo, \
         patch("src.services.account_service.AccountBalanceRepository"), \
         patch("src.services.account_service.InstitutionRepository"), \
         patch("src.services.account_service.AccountLinkRepository"):
        mock_repo = MockAccountRepo.return_value
        mock_repo.deactivate_account.return_value = True

        from src.services.account_service import AccountService
        service = AccountService()

        result = service.deactivate_account("ACC001")

        mock_repo.deactivate_account.assert_called_once_with("ACC001")
        assert result is True


# ============================================================
# Test: Balance Snapshot Operations
# ============================================================


def test_insert_balance_snapshot_validates_account_exists() -> None:
    """Verify insert_balance_snapshot validates account exists."""
    with patch("src.services.account_service.AccountRepository") as MockAccountRepo, \
         patch("src.services.account_service.AccountBalanceRepository") as MockBalanceRepo, \
         patch("src.services.account_service.InstitutionRepository"), \
         patch("src.services.account_service.AccountLinkRepository"):
        mock_account_repo = MockAccountRepo.return_value
        mock_account_repo.get_account_by_id.return_value = None  # Account not found

        from src.services.account_service import AccountService
        service = AccountService()

        with pytest.raises(ValueError, match="not found"):
            service.insert_balance_snapshot("NONEXISTENT", 100000, "2026-01-01")

        # Balance repo should NOT be called
        mock_balance_repo = MockBalanceRepo.return_value
        mock_balance_repo.insert_balance_snapshot.assert_not_called()


def test_insert_balance_snapshot_validates_non_negative() -> None:
    """Verify insert_balance_snapshot validates non-negative balance."""
    with patch("src.services.account_service.AccountRepository") as MockAccountRepo, \
         patch("src.services.account_service.AccountBalanceRepository"), \
         patch("src.services.account_service.InstitutionRepository"), \
         patch("src.services.account_service.AccountLinkRepository"):
        mock_account_repo = MockAccountRepo.return_value
        mock_account_repo.get_account_by_id.return_value = {"id": "ACC001", "is_active": 1}

        from src.services.account_service import AccountService
        service = AccountService()

        with pytest.raises(ValueError, match="negative"):
            service.insert_balance_snapshot("ACC001", -100, "2026-01-01")


def test_insert_balance_snapshot_validates_iso_date() -> None:
    """Verify insert_balance_snapshot validates ISO date format."""
    with patch("src.services.account_service.AccountRepository") as MockAccountRepo, \
         patch("src.services.account_service.AccountBalanceRepository"), \
         patch("src.services.account_service.InstitutionRepository"), \
         patch("src.services.account_service.AccountLinkRepository"):
        mock_account_repo = MockAccountRepo.return_value
        mock_account_repo.get_account_by_id.return_value = {"id": "ACC001", "is_active": 1}

        from src.services.account_service import AccountService
        service = AccountService()

        with pytest.raises(ValueError):  # date.fromisoformat raises ValueError
            service.insert_balance_snapshot("ACC001", 100000, "invalid-date")


def test_insert_balance_snapshot_success() -> None:
    """Verify insert_balance_snapshot succeeds with valid data."""
    with patch("src.services.account_service.AccountRepository") as MockAccountRepo, \
         patch("src.services.account_service.AccountBalanceRepository") as MockBalanceRepo, \
         patch("src.services.account_service.InstitutionRepository"), \
         patch("src.services.account_service.AccountLinkRepository"):
        mock_account_repo = MockAccountRepo.return_value
        mock_account_repo.get_account_by_id.return_value = {"id": "ACC001", "is_active": 1}
        mock_balance_repo = MockBalanceRepo.return_value
        mock_balance_repo.insert_balance_snapshot.return_value = 1

        from src.services.account_service import AccountService
        service = AccountService()

        result = service.insert_balance_snapshot("ACC001", 100000, "2026-01-01")

        mock_balance_repo.insert_balance_snapshot.assert_called_once_with(
            account_id="ACC001",
            balance_paise=100000,
            date_iso="2026-01-01",
            source="actual",
        )
        assert result == 1


# ============================================================
# Test: Balance Analytics (Engine Delegation)
# ============================================================


def test_calculate_average_balance() -> None:
    """Verify calculate_average_balance delegates to engine."""
    with patch("src.services.account_service.AccountRepository"), \
         patch("src.services.account_service.AccountBalanceRepository") as MockBalanceRepo, \
         patch("src.services.account_service.InstitutionRepository"), \
         patch("src.services.account_service.AccountLinkRepository"):
        mock_balance_repo = MockBalanceRepo.return_value
        mock_balance_repo.get_balance_history.return_value = [
            {"balance_paise": 100000},
            {"balance_paise": 150000},
            {"balance_paise": 200000},
        ]

        from src.services.account_service import AccountService
        service = AccountService()

        result = service.calculate_average_balance("ACC001")

        # Engine computes average: (100000 + 150000 + 200000) / 3 = 150000
        assert result == 150000


def test_calculate_balance_trend() -> None:
    """Verify calculate_balance_trend delegates to engine."""
    with patch("src.services.account_service.AccountRepository"), \
         patch("src.services.account_service.AccountBalanceRepository") as MockBalanceRepo, \
         patch("src.services.account_service.InstitutionRepository"), \
         patch("src.services.account_service.AccountLinkRepository"):
        mock_balance_repo = MockBalanceRepo.return_value
        mock_balance_repo.get_balance_history.return_value = [
            {"balance_paise": 100000},
            {"balance_paise": 150000},
            {"balance_paise": 200000},
        ]

        from src.services.account_service import AccountService
        service = AccountService()

        result = service.calculate_balance_trend("ACC001")

        # Engine returns "IMPROVING" for increasing balances
        assert result == "IMPROVING"


# ============================================================
# Test: Account Status (Engine Delegation)
# ============================================================


def test_get_account_status_active() -> None:
    """Verify get_account_status returns ACTIVE for active account with recent activity."""
    with patch("src.services.account_service.AccountRepository") as MockAccountRepo, \
         patch("src.services.account_service.AccountBalanceRepository") as MockBalanceRepo, \
         patch("src.services.account_service.InstitutionRepository"), \
         patch("src.services.account_service.AccountLinkRepository"):
        mock_account_repo = MockAccountRepo.return_value
        mock_account_repo.get_account_by_id.return_value = {
            "id": "ACC001",
            "is_active": 1,
            "balance_paise": 100000,
        }
        mock_balance_repo = MockBalanceRepo.return_value
        mock_balance_repo.get_balance_history.return_value = [
            {"date_iso": "2026-06-01"},  # Recent activity
        ]

        from src.services.account_service import AccountService
        service = AccountService()

        result = service.get_account_status("ACC001")

        assert result == "ACTIVE"


def test_get_account_status_dormant() -> None:
    """Verify get_account_status returns DORMANT for old activity."""
    with patch("src.services.account_service.AccountRepository") as MockAccountRepo, \
         patch("src.services.account_service.AccountBalanceRepository") as MockBalanceRepo, \
         patch("src.services.account_service.InstitutionRepository"), \
         patch("src.services.account_service.AccountLinkRepository"):
        mock_account_repo = MockAccountRepo.return_value
        mock_account_repo.get_account_by_id.return_value = {
            "id": "ACC001",
            "is_active": 1,
            "balance_paise": 100000,
        }
        mock_balance_repo = MockBalanceRepo.return_value
        mock_balance_repo.get_balance_history.return_value = [
            {"date_iso": "2024-01-01"},  # Old activity (over 365 days)
        ]

        from src.services.account_service import AccountService
        service = AccountService()

        result = service.get_account_status("ACC001")

        assert result == "DORMANT"


def test_is_account_dormant() -> None:
    """Verify is_account_dormant delegates to engine."""
    with patch("src.services.account_service.AccountRepository"), \
         patch("src.services.account_service.AccountBalanceRepository") as MockBalanceRepo, \
         patch("src.services.account_service.InstitutionRepository"), \
         patch("src.services.account_service.AccountLinkRepository"):
        mock_balance_repo = MockBalanceRepo.return_value
        mock_balance_repo.get_balance_history.return_value = [
            {"date_iso": "2024-01-01"},  # Old activity
        ]

        from src.services.account_service import AccountService
        service = AccountService()

        # Use a short threshold for testing
        result = service.is_account_dormant("ACC001", threshold_days=30)

        assert result is True


# ============================================================
# Test: Institution Operations
# ============================================================


def test_create_institution() -> None:
    """Verify create_institution delegates to repository."""
    with patch("src.services.account_service.AccountRepository"), \
         patch("src.services.account_service.AccountBalanceRepository"), \
         patch("src.services.account_service.InstitutionRepository") as MockInstRepo, \
         patch("src.services.account_service.AccountLinkRepository"):
        mock_inst_repo = MockInstRepo.return_value
        mock_inst_repo.create.return_value = "HDFC"

        from src.services.account_service import AccountService
        service = AccountService()

        result = service.create_institution(
            institution_id="HDFC",
            name="HDFC Bank",
            institution_type="BANK",
        )

        mock_inst_repo.create.assert_called_once()
        assert result == "HDFC"


def test_get_institution() -> None:
    """Verify get_institution delegates to repository."""
    with patch("src.services.account_service.AccountRepository"), \
         patch("src.services.account_service.AccountBalanceRepository"), \
         patch("src.services.account_service.InstitutionRepository") as MockInstRepo, \
         patch("src.services.account_service.AccountLinkRepository"):
        mock_inst_repo = MockInstRepo.return_value
        mock_inst_repo.get.return_value = {"institution_id": "HDFC", "name": "HDFC Bank"}

        from src.services.account_service import AccountService
        service = AccountService()

        result = service.get_institution("HDFC")

        mock_inst_repo.get.assert_called_once_with("HDFC")
        assert result is not None
        assert result["name"] == "HDFC Bank"


# ============================================================
# Test: Account Linking
# ============================================================


def test_link_accounts_validates_exists() -> None:
    """Verify link_accounts validates both accounts exist."""
    with patch("src.services.account_service.AccountRepository") as MockAccountRepo, \
         patch("src.services.account_service.AccountBalanceRepository"), \
         patch("src.services.account_service.InstitutionRepository"), \
         patch("src.services.account_service.AccountLinkRepository") as MockLinkRepo:
        mock_account_repo = MockAccountRepo.return_value
        mock_account_repo.get_account_by_id.return_value = None  # Account not found

        from src.services.account_service import AccountService
        service = AccountService()

        with pytest.raises(ValueError, match="not found"):
            service.link_accounts("ACC001", "ACC002", "TRANSFER")

        mock_link_repo = MockLinkRepo.return_value
        mock_link_repo.link_accounts.assert_not_called()


def test_get_linked_accounts() -> None:
    """Verify get_linked_accounts delegates to repository."""
    with patch("src.services.account_service.AccountRepository"), \
         patch("src.services.account_service.AccountBalanceRepository"), \
         patch("src.services.account_service.InstitutionRepository"), \
         patch("src.services.account_service.AccountLinkRepository") as MockLinkRepo:
        mock_link_repo = MockLinkRepo.return_value
        mock_link_repo.get_linked_accounts.return_value = [
            {"primary_account_id": "ACC001", "linked_account_id": "ACC002", "relationship_type": "TRANSFER"}
        ]

        from src.services.account_service import AccountService
        service = AccountService()

        result = service.get_linked_accounts("ACC001")

        mock_link_repo.get_linked_accounts.assert_called_once_with("ACC001")
        assert len(result) == 1


def test_unlink_accounts() -> None:
    """Verify unlink_accounts delegates to repository."""
    with patch("src.services.account_service.AccountRepository"), \
         patch("src.services.account_service.AccountBalanceRepository"), \
         patch("src.services.account_service.InstitutionRepository"), \
         patch("src.services.account_service.AccountLinkRepository") as MockLinkRepo:
        mock_link_repo = MockLinkRepo.return_value
        mock_link_repo.unlink_accounts.return_value = True

        from src.services.account_service import AccountService
        service = AccountService()

        result = service.unlink_accounts("ACC001", "ACC002")

        mock_link_repo.unlink_accounts.assert_called_once_with("ACC001", "ACC002")
        assert result is True


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
