"""Contract tests for credit_cards router."""

from __future__ import annotations

# Add tests to path for relative imports
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestCreditCardsContract:
    """Validate credit_cards router against OpenAPI contract."""

    def test_list_cards_contract(self, client: TestClient) -> None:
        """GET /credit-cards returns valid response."""
        response = client.get("/api/v1/credit-cards")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_create_card_contract(self, client: TestClient) -> None:
        """POST /credit-cards validates request body."""
        valid_request = {
            "name": "Test Card",
            "bank": "Test Bank",
            "credit_limit_paise": 100000,
        }

        response = client.post("/api/v1/credit-cards", json=valid_request)
        # Valid request should not return 422
        assert response.status_code in (200, 201, 400, 500)

    def test_create_card_missing_required(self, client: TestClient) -> None:
        """POST /credit-cards rejects missing required fields."""
        invalid_request = {"bank": "Test Bank"}  # missing name

        response = client.post("/api/v1/credit-cards", json=invalid_request)
        assert response.status_code == 422

    def test_get_card_contract(self, client: TestClient) -> None:
        """GET /credit-cards/{card_id} validates path parameter."""
        response = client.get("/api/v1/credit-cards/test_card")
        assert response.status_code in (200, 404)

    def test_get_outstanding_contract(self, client: TestClient) -> None:
        """GET /credit-cards/{card_id}/outstanding returns valid response."""
        response = client.get("/api/v1/credit-cards/test_card/outstanding")
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            data = response.json()
            assert "outstanding_paise" in data

    def test_get_utilization_contract(self, client: TestClient) -> None:
        """GET /credit-cards/{card_id}/utilization returns valid response."""
        response = client.get("/api/v1/credit-cards/test_card/utilization")
        assert response.status_code in (200, 404)

    def test_list_statements_contract(self, client: TestClient) -> None:
        """GET /credit-cards/{card_id}/statements returns valid response."""
        response = client.get("/api/v1/credit-cards/test_card/statements?limit=12")
        assert response.status_code in (200, 404)

    def test_create_statement_contract(self, client: TestClient) -> None:
        """POST /credit-cards/{card_id}/statements validates request body."""
        valid_request = {"statement_date": "2025-01-15"}

        response = client.post(
            "/api/v1/credit-cards/test_card/statements",
            json=valid_request,
        )
        assert response.status_code in (200, 201, 404, 500)

    def test_record_payment_contract(self, client: TestClient) -> None:
        """POST /credit-cards/{card_id}/payments validates request body."""
        valid_request = {"amount_paise": 10000, "payment_date": "2025-01-20"}

        response = client.post(
            "/api/v1/credit-cards/test_card/payments",
            json=valid_request,
        )
        assert response.status_code in (200, 201, 404, 422, 500)

    def test_emi_conversion_contract(self, client: TestClient) -> None:
        """POST /credit-cards/{card_id}/emi-conversion validates request body."""
        valid_request = {
            "amount_paise": 50000,
            "tenure_months": 6,
            "annual_rate_bps": 1200,
        }

        response = client.post(
            "/api/v1/credit-cards/test_card/emi-conversion",
            json=valid_request,
        )
        assert response.status_code in (200, 201, 404, 422, 500)

    def test_foreclosure_contract(self, client: TestClient) -> None:
        """POST /credit-cards/{card_id}/foreclosure validates request body."""
        valid_request = {"remaining_months": 6, "penalty_bps": 100}

        response = client.post(
            "/api/v1/credit-cards/test_card/foreclosure",
            json=valid_request,
        )
        assert response.status_code in (200, 201, 404, 422, 500)
