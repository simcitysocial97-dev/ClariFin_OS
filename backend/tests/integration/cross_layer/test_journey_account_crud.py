"""Cross-layer test for Account CRUD journey.

Validates end-to-end data flow:
- Frontend hook (useManagedAccounts) → API route → Service → Repository → DB
- Schema validation at each layer
- Financial data consistency
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestAccountCRUDJourney:
    """Full-stack account CRUD journey tests."""

    def test_list_accounts_via_api(self, client: TestClient) -> None:
        """GET /api/accounts/manage returns valid accounts list."""
        response = client.get("/api/accounts/manage")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert isinstance(data, dict), "Response should be a dict"
        assert "accounts" in data, "Response should have 'accounts' key"
        assert isinstance(data["accounts"], list), "'accounts' should be a list"
        assert "total" in data, "Response should have 'total' count"

    def test_account_schema_validation(self, client: TestClient) -> None:
        """Account objects have required fields for frontend Zod schema compatibility."""
        response = client.get("/api/accounts/manage")
        assert response.status_code == 200

        data = response.json()
        required_fields = [
            "name",
            "bank",
            "account_type",
            "balance_paise",
        ]

        for account in data["accounts"]:
            for field in required_fields:
                assert field in account, f"Missing required field: {field}"

            assert isinstance(
                account["balance_paise"], int
            ), "balance_paise should be int"
            assert account["balance_paise"] >= 0, "balance_paise should be non-negative"

    def test_create_account_via_api(self, client: TestClient) -> None:
        """POST /api/accounts/manage creates a new account."""
        new_account = {
            "name": "Test Account",
            "bank": "Test Bank",
            "account_type": "savings",
            "balance_paise": 100000,
            "account_number_last4": "1234",
            "notes": "Test account",
        }

        response = client.post("/api/accounts/manage", json=new_account)
        assert response.status_code in (
            200,
            201,
        ), f"Expected 201 or 200, got {response.status_code}: {response.text}"

        if response.status_code in (200, 201):
            result = response.json()
            assert result.get("success") is True, "Response should indicate success"

    def test_account_total_matches_list(self, client: TestClient) -> None:
        """'total' field in response matches len(accounts)."""
        response = client.get("/api/accounts/manage")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == len(
            data["accounts"]
        ), f"total ({data['total']}) should match len(accounts) ({len(data['accounts'])})"

    def test_balance_precision_in_paise(self, client: TestClient) -> None:
        """All monetary values are in paise (integers), not rupees."""
        response = client.get("/api/accounts/manage")
        assert response.status_code == 200

        data = response.json()
        for account in data["accounts"]:
            assert isinstance(
                account["balance_paise"], int
            ), f"balance_paise should be int, got {type(account['balance_paise'])}"


class TestAccountServiceLayer:
    """Test account service business logic independently."""

    def test_account_service_initializes(self) -> None:
        """AccountService can be instantiated."""
        from src.services.account_service import AccountService

        service = AccountService()
        assert service is not None
        assert hasattr(service, "account_repo")

    def test_account_service_list_accounts(self) -> None:
        """AccountService can list accounts from repository."""
        from src.services.account_service import AccountService

        service = AccountService()
        accounts = service.list_accounts()
        assert isinstance(accounts, list)

    def test_account_repository_accessible(self) -> None:
        """AccountRepository can be accessed via service."""
        from src.services.account_service import AccountService

        service = AccountService()
        assert hasattr(service, "account_repo")
        assert hasattr(service.account_repo, "list_accounts")
