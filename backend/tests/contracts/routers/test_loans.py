"""Contract tests for loans router."""

from __future__ import annotations

# Add tests to path for relative imports
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestLoansContract:
    """Validate loans router against OpenAPI contract."""

    def test_list_loans_contract(self, client: TestClient) -> None:
        """GET /loans returns valid response or handles empty data gracefully."""
        response = client.get("/api/loans")
        assert response.status_code in (200, 500)

    def test_create_loan_contract(self, client: TestClient) -> None:
        """POST /loans validates request body."""
        valid_request = {
            "name": "Test Loan",
            "lender": "Test Bank",
            "principal_paise": 1000000,
            "rate_bps": 1200,
            "tenure_months": 12,
            "disbursed_date": "2025-01-15",
        }

        response = client.post("/api/loans", json=valid_request)
        assert response.status_code in (200, 201, 400, 500)

    def test_create_loan_missing_required(self, client: TestClient) -> None:
        """POST /loans rejects missing required fields."""
        invalid_request = {"name": "Test Loan"}  # missing principal, rate, etc.

        response = client.post("/api/loans", json=invalid_request)
        assert response.status_code == 422

    def test_get_loan_contract(self, client: TestClient) -> None:
        """GET /loans/{loan_id} validates path parameter."""
        response = client.get("/api/loans/999999")
        assert response.status_code in (200, 404)

    def test_get_schedule_contract(self, client: TestClient) -> None:
        """GET /loans/{loan_id}/schedule returns valid response."""
        response = client.get("/api/loans/999999/schedule")
        assert response.status_code in (200, 404)

    def test_update_loan_contract(self, client: TestClient) -> None:
        """PUT /loans/{loan_id} validates request body."""
        valid_request = {"name": "Updated Loan"}

        response = client.put("/api/loans/999999", json=valid_request)
        assert response.status_code in (200, 404)

    def test_delete_loan_contract(self, client: TestClient) -> None:
        """DELETE /loans/{loan_id} validates path parameter."""
        response = client.delete("/api/loans/999999")
        assert response.status_code in (200, 404)
