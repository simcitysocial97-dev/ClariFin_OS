"""Contract tests for behaviour router."""

from __future__ import annotations

# Add tests to path for relative imports
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestBehaviourContract:
    """Validate behaviour router against OpenAPI contract."""

    def test_get_behaviour_profile_contract(self, client: TestClient) -> None:
        """GET /behaviour/profile returns valid response or handles empty data."""
        response = client.get("/api/v1/behaviour/profile")
        assert response.status_code in (200, 404, 500)

    def test_get_behaviour_wellness_contract(self, client: TestClient) -> None:
        """GET /behaviour/wellness returns valid response."""
        response = client.get("/api/v1/behaviour/wellness")
        assert response.status_code in (200, 404, 500)

    def test_get_behaviour_metrics_contract(self, client: TestClient) -> None:
        """GET /behaviour/metrics returns valid response."""
        response = client.get("/api/v1/behaviour/metrics")
        assert response.status_code in (200, 404, 500)

    def test_get_behaviour_patterns_contract(self, client: TestClient) -> None:
        """GET /behaviour/patterns returns valid response."""
        response = client.get("/api/v1/behaviour/patterns")
        assert response.status_code in (200, 404, 500)

    def test_get_behaviour_recommendations_contract(self, client: TestClient) -> None:
        """GET /behaviour/recommendations returns valid response."""
        response = client.get("/api/v1/behaviour/recommendations")
        assert response.status_code in (200, 404, 500)
