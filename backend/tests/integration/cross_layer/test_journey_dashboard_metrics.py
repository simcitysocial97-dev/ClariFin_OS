"""Cross-layer test for Dashboard metrics aggregation journey.

Validates end-to-end data flow:
- Frontend hook (useDashboardMetrics) → API route → DashboardService →
  CashflowService → AccountRepository → DB
- Aggregation calculations
- Rate calculations (savings_rate, emi_ratio)
- Financial health score
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestDashboardMetricsJourney:
    """Full-stack dashboard metrics journey tests."""

    def test_dashboard_summary_via_api(self, client: TestClient) -> None:
        """GET /api/dashboard/summary returns valid metrics."""
        response = client.get("/api/dashboard/summary")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert isinstance(data, dict), "Response should be a dict"

    def test_dashboard_schema_validation(self, client: TestClient) -> None:
        """Dashboard metrics match frontend Zod schema."""
        response = client.get("/api/dashboard/summary")
        assert response.status_code == 200

        data = response.json()
        required_fields = [
            "net_cash_flow_paise",
            "total_income_paise",
            "total_expenses_paise",
            "emi_paise",
            "savings_rate",
            "emi_ratio",
            "buffer_days",
            "financial_health_score",
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        assert isinstance(data["net_cash_flow_paise"], int), "net_cash_flow_paise should be int"
        assert isinstance(data["total_income_paise"], int), "total_income_paise should be int"
        assert isinstance(data["total_expenses_paise"], int), "total_expenses_paise should be int"
        assert isinstance(data["emi_paise"], int), "emi_paise should be int"

    def test_dashboard_rates_in_range(self, client: TestClient) -> None:
        """savings_rate and emi_ratio are ratios (0-1) per backend DTO spec."""
        response = client.get("/api/dashboard/summary")
        assert response.status_code == 200

        data = response.json()
        assert 0 <= data["savings_rate"] <= 1, (
            f"savings_rate should be 0-1, got {data['savings_rate']}"
        )
        assert 0 <= data["emi_ratio"] <= 1, (
            f"emi_ratio should be 0-1, got {data['emi_ratio']}"
        )

    def test_health_score_in_range(self, client: TestClient) -> None:
        """financial_health_score is 0-100 or null per DTO spec."""
        response = client.get("/api/dashboard/summary")
        assert response.status_code == 200

        data = response.json()
        score = data["financial_health_score"]
        if score is not None:
            assert 0 <= score <= 100, f"financial_health_score should be 0-100, got {score}"

    def test_buffer_days_is_non_negative(self, client: TestClient) -> None:
        """buffer_days is a non-negative integer."""
        response = client.get("/api/dashboard/summary")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data["buffer_days"], int), "buffer_days should be int"
        assert data["buffer_days"] >= 0, f"buffer_days should be non-negative, got {data['buffer_days']}"


class TestDashboardServiceLayer:
    """Test dashboard service business logic independently."""

    def test_dashboard_service_initializes(self) -> None:
        """DashboardService can be instantiated."""
        from src.services.dashboard_service import DashboardService

        service = DashboardService()
        assert service is not None

    def test_dashboard_service_get_summary(self) -> None:
        """DashboardService can compute summary metrics."""
        from src.services.dashboard_service import DashboardService

        service = DashboardService()
        summary = service.get_summary()
        assert summary is not None
        assert hasattr(summary, "net_cash_flow_paise")
        assert hasattr(summary, "savings_rate")
        assert hasattr(summary, "emi_paise")


class TestCashflowAggregation:
    """Test cashflow aggregation across layers."""

    def test_cashflow_service_initializes(self) -> None:
        """CashflowService can be instantiated."""
        from src.services.cashflow_service import CashflowService

        service = CashflowService()
        assert service is not None

    def test_cashflow_calculate_summary(self) -> None:
        """CashflowService can calculate summary."""
        from src.services.cashflow_service import CashflowService

        service = CashflowService()
        summary = service.calculate_summary()
        assert summary is not None
