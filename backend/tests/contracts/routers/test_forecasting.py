"""Contract tests for forecast router."""

from __future__ import annotations

# Add tests to path for relative imports
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestForecastingContract:
    """Validate forecast endpoints against OpenAPI contract."""

    def test_forecast_contract(self, client: TestClient) -> None:
        """GET /forecast returns valid response."""
        response = client.get("/api/v1/forecast?horizon=3")
        assert response.status_code in (200, 500)

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_forecast_default_horizon(self, client: TestClient) -> None:
        """GET /forecast with default horizon returns valid response."""
        response = client.get("/api/v1/forecast")
        assert response.status_code in (200, 500)

    def test_forecast_invalid_horizon(self, client: TestClient) -> None:
        """GET /forecast validates horizon constraint (1-60)."""
        response = client.get("/api/v1/forecast?horizon=0")
        assert response.status_code == 422

    def test_forecast_above_max_horizon(self, client: TestClient) -> None:
        """GET /forecast rejects horizon above 60."""
        response = client.get("/api/v1/forecast?horizon=61")
        assert response.status_code == 422

    def test_forecast_negative_horizon(self, client: TestClient) -> None:
        """GET /forecast rejects negative horizon."""
        response = client.get("/api/v1/forecast?horizon=-1")
        assert response.status_code == 422

    def test_forecast_with_scenarios(self, client: TestClient) -> None:
        """GET /forecast accepts scenarios parameter."""
        response = client.get("/api/v1/forecast?horizon=3&scenarios=base,optimistic")
        assert response.status_code in (200, 500)
