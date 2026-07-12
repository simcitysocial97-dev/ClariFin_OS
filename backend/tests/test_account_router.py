"""
Account Router API Tests
=========================

Tests for account API contract compliance.
Uses TestClient with mocked AccountService.

Run: cd backend && ./venv/bin/python3 -m pytest tests/test_account_router.py -v
"""

import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.api import app  # noqa: E402


@pytest.fixture
def client() -> Any:
    """Create test client."""
    yield TestClient(app)


# ============================================================
# Account CRUD Tests
# ============================================================


class TestAccountCrud:
    """Tests for Account CRUD endpoints."""

    def test_list_accounts(self, client: TestClient) -> None:
        """Test GET /accounts returns list of accounts."""
        with patch("src.routers.accounts.AccountService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_accounts.return_value = [
                {"id": 1, "name": "Test Account", "bank": "HDFC", "balance_paise": 100000},
                {"id": 2, "name": "Another Account", "bank": "ICICI", "balance_paise": 200000},
            ]

            response = client.get("/api/v1/accounts")
            assert response.status_code == 200
            assert len(response.json()) == 2
            mock_service.list_accounts.assert_called_once()

    def test_create_account(self, client: TestClient) -> None:
        """Test POST /accounts creates account."""
        with patch("src.routers.accounts.AccountService") as MockService:
            mock_service = MockService.return_value
            mock_service.create_account.return_value = {"id": 1}

            response = client.post("/api/v1/accounts", json={
                "name": "Test Account",
                "bank": "HDFC",
                "account_type": "savings",
                "balance_paise": 100000,
            })
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "account_id" in data

    def test_create_account_validation_error(self, client: TestClient) -> None:
        """Test POST /accounts validates request body."""
        response = client.post("/api/v1/accounts", json={
            "name": "",  # Invalid: empty name
            "bank": "HDFC",
        })
        assert response.status_code == 422

    def test_get_account(self, client: TestClient) -> None:
        """Test GET /accounts/{id} returns account."""
        with patch("src.routers.accounts.AccountService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_account.return_value = {
                "id": 1,
                "name": "Test Account",
                "bank": "HDFC",
                "account_type": "savings",
                "balance_paise": 100000,
            }

            response = client.get("/api/v1/accounts/1")
            assert response.status_code == 200
            assert response.json()["name"] == "Test Account"

    def test_get_account_not_found(self, client: TestClient) -> None:
        """Test GET /accounts/{id} returns 404 for missing account."""
        with patch("src.routers.accounts.AccountService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_account.return_value = None

            response = client.get("/api/v1/accounts/999")
            assert response.status_code == 404

    def test_update_account(self, client: TestClient) -> None:
        """Test PUT /accounts/{id} updates account."""
        with patch("src.routers.accounts.AccountService") as MockService:
            mock_service = MockService.return_value
            mock_service.update_account.return_value = {
                "id": 1,
                "name": "Updated Name",
            }

            response = client.put("/api/v1/accounts/1", json={
                "name": "Updated Name",
            })
            assert response.status_code == 200
            assert response.json()["success"] is True

    def test_delete_account(self, client: TestClient) -> None:
        """Test DELETE /accounts/{id} deactivates account."""
        with patch("src.routers.accounts.AccountService") as MockService:
            mock_service = MockService.return_value
            mock_service.deactivate_account.return_value = True

            response = client.delete("/api/v1/accounts/1")
            assert response.status_code == 200
            assert response.json()["success"] is True


# ============================================================
# Balance Snapshot Tests
# ============================================================


class TestBalanceSnapshot:
    """Tests for balance snapshot endpoints."""

    def test_insert_balance_snapshot(self, client: TestClient) -> None:
        """Test POST /accounts/{id}/balance-history."""
        with patch("src.routers.accounts.AccountService") as MockService:
            mock_service = MockService.return_value
            mock_service.insert_balance_snapshot.return_value = 1
            mock_service.get_balance_history.return_value = [{
                "id": 1,
                "account_id": "1",
                "balance_paise": 100000,
                "date_iso": "2026-01-01",
                "source": "actual",
            }]

            response = client.post("/api/v1/accounts/1/balance-history", json={
                "balance_paise": 100000,
                "date_iso": "2026-01-01",
            })
            assert response.status_code == 200
            assert response.json()["success"] is True

    def test_get_balance_history(self, client: TestClient) -> None:
        """Test GET /accounts/{id}/balance-history."""
        with patch("src.routers.accounts.AccountService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_balance_history.return_value = [
                {
                    "id": 1,
                    "account_id": "1",
                    "balance_paise": 100000,
                    "date_iso": "2026-01-01",
                    "source": "actual",
                },
            ]

            response = client.get("/api/v1/accounts/1/balance-history")
            assert response.status_code == 200
            assert len(response.json()) == 1

    def test_get_latest_balance(self, client: TestClient) -> None:
        """Test GET /accounts/{id}/balance-history/latest."""
        with patch("src.routers.accounts.AccountService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_latest_balance.return_value = {
                "id": 1,
                "account_id": "1",
                "balance_paise": 150000,
                "date_iso": "2026-01-15",
                "source": "actual",
            }

            response = client.get("/api/v1/accounts/1/balance-history/latest")
            assert response.status_code == 200
            assert response.json()["balance_paise"] == 150000

    def test_get_latest_balance_not_found(self, client: TestClient) -> None:
        """Test GET /accounts/{id}/balance-history/latest returns 404 when no history."""
        with patch("src.routers.accounts.AccountService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_latest_balance.return_value = None

            response = client.get("/api/v1/accounts/1/balance-history/latest")
            assert response.status_code == 404


# ============================================================
# Analytics Tests
# ============================================================


class TestAnalytics:
    """Tests for analytics endpoints."""

    def test_get_account_analytics(self, client: TestClient) -> None:
        """Test GET /accounts/{id}/analytics."""
        with patch("src.routers.accounts.AccountService") as MockService:
            mock_service = MockService.return_value
            mock_service.calculate_average_balance.return_value = 150000
            mock_service.calculate_balance_change.return_value = 50000
            mock_service.calculate_balance_growth.return_value = 500
            mock_service.calculate_balance_trend.return_value = "IMPROVING"
            mock_service.calculate_balance_velocity.return_value = 1000

            response = client.get("/api/v1/accounts/1/analytics")
            assert response.status_code == 200
            data = response.json()
            assert "average_balance_paise" in data
            assert "balance_change_paise" in data
            assert "balance_growth_bps" in data
            assert "trend" in data
            assert "velocity_paise_per_day" in data

    def test_get_account_metrics(self, client: TestClient) -> None:
        """Test GET /accounts/{id}/metrics."""
        with patch("src.routers.accounts.AccountService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_account_metrics.return_value = {
                "current_balance_paise": 100000,
                "average_balance_paise": 150000,
                "days_since_activity": 30,
            }

            response = client.get("/api/v1/accounts/1/metrics")
            assert response.status_code == 200

    def test_get_account_status(self, client: TestClient) -> None:
        """Test GET /accounts/{id}/status."""
        with patch("src.routers.accounts.AccountService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_account_status.return_value = "ACTIVE"

            response = client.get("/api/v1/accounts/1/status")
            assert response.status_code == 200
            assert response.json()["status"] == "ACTIVE"

    def test_get_account_dormancy(self, client: TestClient) -> None:
        """Test GET /accounts/{id}/dormancy."""
        with patch("src.routers.accounts.AccountService") as MockService:
            mock_service = MockService.return_value
            mock_service.is_account_dormant.return_value = False
            mock_service.get_days_since_activity.return_value = 15

            response = client.get("/api/v1/accounts/1/dormancy")
            assert response.status_code == 200
            data = response.json()
            assert "dormant" in data
            assert "days_since_activity" in data


# ============================================================
# Institution Tests
# ============================================================


class TestInstitution:
    """Tests for institution endpoints."""

    def test_list_institutions(self, client: TestClient) -> None:
        """Test GET /institutions."""
        with patch("src.routers.accounts.AccountService") as MockService:
            mock_service = MockService.return_value
            mock_service.list_institutions.return_value = [
                {"institution_id": "HDFC", "name": "HDFC Bank", "type": "BANK"},
                {"institution_id": "ICICI", "name": "ICICI Bank", "type": "BANK"},
            ]

            response = client.get("/api/v1/institutions")
            assert response.status_code == 200
            assert len(response.json()) == 2

    def test_create_institution(self, client: TestClient) -> None:
        """Test POST /institutions."""
        with patch("src.routers.accounts.AccountService") as MockService:
            mock_service = MockService.return_value
            mock_service.create_institution.return_value = "HDFC"

            response = client.post("/api/v1/institutions", json={
                "institution_id": "HDFC",
                "name": "HDFC Bank",
                "institution_type": "BANK",
            })
            assert response.status_code == 200
            assert response.json()["success"] is True
            assert response.json()["institution_id"] == "HDFC"

    def test_get_institution(self, client: TestClient) -> None:
        """Test GET /institutions/{id}."""
        with patch("src.routers.accounts.AccountService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_institution.return_value = {
                "institution_id": "HDFC",
                "name": "HDFC Bank",
                "type": "BANK",
            }

            response = client.get("/api/v1/institutions/HDFC")
            assert response.status_code == 200
            assert response.json()["name"] == "HDFC Bank"

    def test_update_institution(self, client: TestClient) -> None:
        """Test PUT /institutions/{id}."""
        with patch("src.routers.accounts.AccountService") as MockService:
            mock_service = MockService.return_value
            mock_service.update_institution.return_value = {"institution_id": "HDFC"}

            response = client.put("/api/v1/institutions/HDFC", json={
                "name": "HDFC Bank Ltd",
            })
            assert response.status_code == 200


# ============================================================
# Account Linking Tests
# ============================================================


class TestAccountLinking:
    """Tests for account linking endpoints."""

    def test_link_accounts(self, client: TestClient) -> None:
        """Test POST /accounts/{id}/links."""
        with patch("src.routers.accounts.AccountService") as MockService:
            mock_service = MockService.return_value
            mock_service.link_accounts.return_value = True

            response = client.post("/api/v1/accounts/1/links", json={
                "linked_account_id": "2",
                "relationship_type": "TRANSFER",
            })
            assert response.status_code == 200
            assert response.json()["success"] is True

    def test_link_accounts_validation_error(self, client: TestClient) -> None:
        """Test POST /accounts/{id}/links validates relationship_type."""
        response = client.post("/api/v1/accounts/1/links", json={
            "linked_account_id": "2",
            "relationship_type": "INVALID",  # Invalid enum value
        })
        assert response.status_code == 422

    def test_unlink_accounts(self, client: TestClient) -> None:
        """Test DELETE /accounts/{id}/links/{linked_id}."""
        with patch("src.routers.accounts.AccountService") as MockService:
            mock_service = MockService.return_value
            mock_service.unlink_accounts.return_value = True

            response = client.delete("/api/v1/accounts/1/links/2")
            assert response.status_code == 200
            assert response.json()["success"] is True

    def test_get_linked_accounts(self, client: TestClient) -> None:
        """Test GET /accounts/{id}/links."""
        with patch("src.routers.accounts.AccountService") as MockService:
            mock_service = MockService.return_value
            mock_service.get_linked_accounts.return_value = [
                {
                    "primary_account_id": "1",
                    "linked_account_id": "2",
                    "relationship_type": "TRANSFER",
                },
            ]

            response = client.get("/api/v1/accounts/1/links")
            assert response.status_code == 200
            assert len(response.json()) == 1


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
