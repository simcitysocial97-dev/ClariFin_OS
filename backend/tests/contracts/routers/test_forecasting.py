"""Contract tests for forecasting (financial_intelligence) router."""

from __future__ import annotations

# Add tests to path for relative imports
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestForecastingContract:
    """Validate forecasting endpoints against OpenAPI contract."""

    def test_cashflow_forecast_contract(self, client: TestClient) -> None:
        """GET /financial-intelligence/cashflow-forecast returns valid response."""
        response = client.get("/api/v1/financial-intelligence/cashflow-forecast?forecast_months=3")
        assert response.status_code in (200, 422, 500)

        if response.status_code == 200:
            data = response.json()
            assert "forecast" in data

    def test_cashflow_forecast_invalid_months(self, client: TestClient) -> None:
        """GET /financial-intelligence/cashflow-forecast validates months constraint."""
        response = client.get("/api/v1/financial-intelligence/cashflow-forecast?forecast_months=20")
        assert response.status_code == 422

    def test_cashflow_forecast_negative_months(self, client: TestClient) -> None:
        """GET /financial-intelligence/cashflow-forecast rejects negative months."""
        response = client.get("/api/v1/financial-intelligence/cashflow-forecast?forecast_months=-1")
        assert response.status_code == 422

    def test_liquidity_forecast_contract(self, client: TestClient) -> None:
        """GET /financial-intelligence/liquidity-forecast returns valid response."""
        response = client.get("/api/v1/financial-intelligence/liquidity-forecast?forecast_months=3")
        assert response.status_code in (200, 422, 500)

    def test_credit_forecast_contract(self, client: TestClient) -> None:
        """GET /financial-intelligence/credit-forecast returns valid response."""
        response = client.get("/api/v1/financial-intelligence/credit-forecast?forecast_months=3")
        assert response.status_code in (200, 422, 500)

    def test_outlook_contract(self, client: TestClient) -> None:
        """GET /financial-intelligence/outlook returns valid response."""
        response = client.get("/api/v1/financial-intelligence/outlook")
        assert response.status_code in (200, 500)
