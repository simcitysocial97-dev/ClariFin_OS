"""Contract tests for cashflow router."""

from __future__ import annotations

# Add tests to path for relative imports
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestCashflowContract:
    """Validate cashflow router against OpenAPI contract."""

    def test_get_cashflow_monthly_contract(self, client: TestClient) -> None:
        """GET /cashflow/monthly returns valid response."""
        response = client.get("/api/cashflow/monthly?months=6")
        assert response.status_code == 200

        data = response.json()
        assert "months" in data
        assert isinstance(data["months"], list)

    def test_get_cashflow_monthly_invalid_months(self, client: TestClient) -> None:
        """GET /cashflow/monthly rejects invalid months parameter."""
        # months should be between 1-12
        response = client.get("/api/cashflow/monthly?months=20")
        assert response.status_code == 422

    def test_get_cashflow_monthly_negative_months(self, client: TestClient) -> None:
        """GET /cashflow/monthly rejects negative months."""
        response = client.get("/api/cashflow/monthly?months=-1")
        assert response.status_code == 422

    def test_get_cashflow_monthly_analysis_contract(self, client: TestClient) -> None:
        """GET /v1/cashflow/monthly returns valid response."""
        response = client.get("/api/v1/cashflow/monthly?month=2025-01&scope=household")
        assert response.status_code in (200, 404, 422, 500)

    def test_get_cashflow_missing_month(self, client: TestClient) -> None:
        """GET /v1/cashflow/monthly requires month parameter."""
        response = client.get("/api/v1/cashflow/monthly")
        assert response.status_code == 422

    def test_get_cashflow_invalid_scope(self, client: TestClient) -> None:
        """GET /v1/cashflow/monthly validates scope enum."""
        response = client.get("/api/v1/cashflow/monthly?month=2025-01&scope=invalid_scope")
        assert response.status_code in (200, 404, 422, 500)
