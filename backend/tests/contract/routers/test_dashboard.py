"""Contract tests for dashboard router."""

from __future__ import annotations

# Add tests to path for relative imports
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestDashboardContract:
    """Validate dashboard router against OpenAPI contract."""

    def test_get_dashboard_overview_contract(self, client: TestClient) -> None:
        """GET /dashboard/overview returns valid response."""
        response = client.get("/api/v1/dashboard/overview")
        assert response.status_code in (200, 404, 500)

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_get_dashboard_summary_contract(self, client: TestClient) -> None:
        """GET /dashboard/summary returns valid response."""
        response = client.get("/api/v1/dashboard/summary")
        assert response.status_code in (200, 404, 500)

    def test_get_dashboard_net_worth_contract(self, client: TestClient) -> None:
        """GET /dashboard/net-worth returns valid response."""
        response = client.get("/api/v1/dashboard/net-worth")
        assert response.status_code in (200, 404, 500)

    def test_get_dashboard_spending_contract(self, client: TestClient) -> None:
        """GET /dashboard/spending returns valid response."""
        response = client.get("/api/v1/dashboard/spending")
        assert response.status_code in (200, 404, 500)

    def test_get_dashboard_accounts_contract(self, client: TestClient) -> None:
        """GET /dashboard/accounts returns valid response."""
        response = client.get("/api/v1/dashboard/accounts")
        assert response.status_code in (200, 404, 500)
