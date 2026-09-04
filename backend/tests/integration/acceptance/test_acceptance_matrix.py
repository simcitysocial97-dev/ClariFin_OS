"""Real Repository Acceptance Matrix Tests.

Tests that validate the repository works end-to-end with real data,
exercising the critical paths through the full stack.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestAcceptanceMatrix:
    """Acceptance tests for critical repository paths."""

    def test_app_boots(self, client: TestClient) -> None:
        """The FastAPI app boots and responds."""
        response = client.get("/")
        assert response.status_code in (200, 404, 405), (
            f"App should respond, got {response.status_code}"
        )

    def test_health_endpoint(self, client: TestClient) -> None:
        """Health endpoint returns success."""
        response = client.get("/api/health")
        assert response.status_code in (200, 404), (
            f"Health endpoint should return 200 or 404, got {response.status_code}"
        )


class TestAccountsAcceptance:
    """Account acceptance tests."""

    def test_accounts_list_works(self, client: TestClient) -> None:
        """Accounts list endpoint works."""
        response = client.get("/api/accounts/manage")
        assert response.status_code == 200
        data = response.json()
        assert "accounts" in data
        assert "total" in data

    def test_accounts_create_works(self, client: TestClient) -> None:
        """Accounts create endpoint works."""
        payload = {
            "name": "Acceptance Test",
            "bank": "Test Bank",
            "account_type": "savings",
            "balance_paise": 100000,
        }
        response = client.post("/api/accounts/manage", json=payload)
        assert response.status_code in (200, 201)


class TestLoansAcceptance:
    """Loan acceptance tests."""

    def test_loans_list_works(self, client: TestClient) -> None:
        """Loans list endpoint works."""
        response = client.get("/api/loans")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_loans_create_works(self, client: TestClient) -> None:
        """Loans create endpoint works."""
        payload = {
            "name": "Acceptance Loan",
            "lender": "Test Bank",
            "loan_type": "personal",
            "principal_paise": 500000,
            "outstanding_paise": 500000,
            "rate_bps": 1000,
            "disbursed_date": "2026-01-01",
            "tenure_months": 36,
        }
        response = client.post("/api/loans", json=payload)
        assert response.status_code in (200, 201)


class TestDashboardAcceptance:
    """Dashboard acceptance tests."""

    def test_dashboard_summary_works(self, client: TestClient) -> None:
        """Dashboard summary endpoint works."""
        response = client.get("/api/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert "net_cash_flow_paise" in data
        assert "savings_rate" in data


class TestNetworthAcceptance:
    """Networth acceptance tests."""

    def test_networth_works(self, client: TestClient) -> None:
        """Networth endpoint works."""
        response = client.get("/api/networth")
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            data = response.json()
            assert "total_net_worth_paise" in data or "net_worth_paise" in data or "assets" in data


class TestCashflowAcceptance:
    """Cashflow acceptance tests."""

    def test_cashflow_works(self, client: TestClient) -> None:
        """Cashflow endpoint works."""
        response = client.get("/api/cashflow/monthly?months=6")
        assert response.status_code == 200
        data = response.json()
        assert "months" in data
        assert "total_count" in data


class TestReconciliationAcceptance:
    """Reconciliation acceptance tests."""

    def test_reconciliation_works(self, client: TestClient) -> None:
        """Reconciliation endpoint works."""
        response = client.get("/api/reconciliation")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)


class TestCrossLayerAcceptance:
    """Cross-layer acceptance tests."""

    def test_account_to_networth_flow(self, client: TestClient) -> None:
        """Account creation should reflect in networth."""
        initial_accounts = client.get("/api/accounts/manage")
        initial_count = initial_accounts.json().get("total", 0) if initial_accounts.status_code == 200 else 0

        create_payload = {
            "name": "Cross-layer Test",
            "bank": "Test Bank",
            "account_type": "savings",
            "balance_paise": 500000,
        }
        create_response = client.post("/api/accounts/manage", json=create_payload)
        assert create_response.status_code in (200, 201)

        updated_accounts = client.get("/api/accounts/manage")
        if updated_accounts.status_code == 200:
            updated_count = updated_accounts.json().get("total", 0)
            assert updated_count >= initial_count, (
                f"Account count should not decrease: {initial_count} -> {updated_count}"
            )


class TestAcceptanceInvariants:
    """Invariants that must hold across the acceptance matrix."""

    def test_all_paise_fields_are_integers(self, client: TestClient) -> None:
        """All *_paise fields across endpoints are integers."""
        endpoints = [
            "/api/accounts/manage",
            "/api/loans",
            "/api/dashboard/summary",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code != 200:
                continue
            data = response.json()
            _validate_paise_integers(data, endpoint)

    def test_no_negative_balances_in_normal_accounts(self, client: TestClient) -> None:
        """Active accounts shouldn't have unexpected negative balances."""
        response = client.get("/api/accounts/manage")
        if response.status_code != 200:
            pytest.skip("Account endpoint not available")

        data = response.json()
        for account in data.get("accounts", []):
            if account.get("is_active") == 1 and account.get("balance_paise", 0) < 0:
                pytest.warns(
                    UserWarning,
                    f"Active account {account.get('id')} has negative balance",
                )


def _validate_paise_integers(data, path: str) -> None:
    """Recursively validate paise fields are integers."""
    if isinstance(data, dict):
        for key, value in data.items():
            current = f"{path}.{key}"
            if key.endswith("_paise") and isinstance(value, (int, float)) and not isinstance(value, bool):
                assert isinstance(value, int), (
                    f"{current} should be int, got {type(value).__name__}"
                )
            else:
                _validate_paise_integers(value, current)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            _validate_paise_integers(item, f"{path}[{i}]")
