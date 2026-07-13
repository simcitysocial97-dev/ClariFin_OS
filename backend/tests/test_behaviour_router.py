"""Tests for Behaviour Router.

Verifies:
- Endpoint routing to correct service methods
- Request parameter handling
- Response serialization
- Error handling for missing snapshots
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.models.behaviour import (
    CashflowHealthResponse,
    DebtHealthResponse,
    FinancialPattern,
    FinancialProfileResponse,
    MonthlySummaryResponse,
    RecommendationResponse,
    RecommendationsResponse,
    WellnessScoreResponse,
)

# ============================================================
# Test Fixtures
# ============================================================


@pytest.fixture
def mock_service() -> MagicMock:
    """Create a mock BehaviourService."""
    return MagicMock()


@pytest.fixture
def client(mock_service: MagicMock) -> TestClient:
    """Create TestClient with mocked BehaviourService."""
    from fastapi import FastAPI

    from src.errors import register_error_handlers
    from src.routers.behaviour import router as behaviour_router

    # Patch BehaviourService in the router module
    with patch("src.routers.behaviour.BehaviourService", return_value=mock_service):
        test_app = FastAPI(title="Test API")
        register_error_handlers(test_app)
        test_app.include_router(behaviour_router)

        yield TestClient(test_app)


# ============================================================
# Tests: Profile Endpoint
# ============================================================


class TestGetFinancialProfile:
    """Tests for GET /api/v1/behaviour/profile endpoint."""

    def test_get_profile_success(
        self,
        client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test successful profile retrieval."""
        mock_service.compute_financial_profile.return_value = FinancialProfileResponse(
            profile_type="SAVER",
            confidence=Decimal("0.85"),
            explanation="High savings rate detected",
            snapshot_date="2023-01-15",
        )

        response = client.get("/api/v1/behaviour/profile")

        assert response.status_code == 200
        data = response.json()
        assert data["profile_type"] == "SAVER"
        assert data["confidence"] == "0.85"
        assert "snapshot_date" in data

        mock_service.compute_financial_profile.assert_called_once_with(household_id="default")

    def test_get_profile_with_household_id(
        self,
        client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test profile retrieval with custom household_id."""
        mock_service.compute_financial_profile.return_value = FinancialProfileResponse(
            profile_type="BALANCED",
            confidence=Decimal("0.75"),
            explanation="Balanced profile",
            snapshot_date="2023-01-15",
        )

        response = client.get("/api/v1/behaviour/profile?household_id=test-household")

        assert response.status_code == 200
        mock_service.compute_financial_profile.assert_called_once_with(household_id="test-household")

    def test_get_profile_insufficient_data(
        self,
        client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test profile retrieval with insufficient data."""
        mock_service.compute_financial_profile.return_value = FinancialProfileResponse(
            profile_type="INSUFFICIENT_DATA",
            confidence=Decimal("0"),
            explanation="Insufficient transaction data for profile classification",
            snapshot_date="2023-01-15",
        )

        response = client.get("/api/v1/behaviour/profile")

        assert response.status_code == 200
        data = response.json()
        assert data["profile_type"] == "INSUFFICIENT_DATA"


# ============================================================
# Tests: Wellness Score Endpoint
# ============================================================


class TestGetWellnessScore:
    """Tests for GET /api/v1/behaviour/wellness-score endpoint."""

    def test_get_wellness_score_success(
        self,
        client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test successful wellness score retrieval."""
        mock_service.get_wellness_score.return_value = WellnessScoreResponse(
            score=Decimal("80.00"),
            band="Healthy",
            components={
                "cashflow_health": Decimal("80.00"),
                "debt_health": Decimal("0.60"),
                "savings_behaviour": Decimal("0.72"),
                "resilience": Decimal("0.65"),
                "lifestyle_control": Decimal("0.95"),
                "credit_behaviour": Decimal("0.80"),
            },
            snapshot_date="2023-01-15",
            version=1,
        )

        response = client.get("/api/v1/behaviour/wellness-score")

        assert response.status_code == 200
        data = response.json()
        assert data["score"] == "80.00"
        assert data["band"] == "Healthy"
        assert "components" in data

        mock_service.get_wellness_score.assert_called_once_with(household_id="default")


# ============================================================
# Tests: Debt Health Endpoint
# ============================================================


class TestGetDebtHealth:
    """Tests for GET /api/v1/behaviour/debt-health endpoint."""

    def test_get_debt_health_success(
        self,
        client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test successful debt health retrieval."""
        mock_service.get_debt_health.return_value = DebtHealthResponse(
            foir=Decimal("0.35"),
            credit_dependency_ratio=Decimal("0.20"),
            debt_cycle_score=40,
            credit_revolver_ratio=Decimal("0.15"),
            band="MODERATE",
            snapshot_date="2023-01-15",
        )

        response = client.get("/api/v1/behaviour/debt-health")

        assert response.status_code == 200
        data = response.json()
        assert data["foir"] == "0.35"
        assert data["band"] == "MODERATE"

        mock_service.get_debt_health.assert_called_once_with(household_id="default")


# ============================================================
# Tests: Cashflow Health Endpoint
# ============================================================


class TestGetCashflowHealth:
    """Tests for GET /api/v1/behaviour/cashflow-health endpoint."""

    def test_get_cashflow_health_success(
        self,
        client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test successful cashflow health retrieval."""
        mock_service.get_cashflow_health.return_value = CashflowHealthResponse(
            cashflow_stability_index=Decimal("80.00"),
            income_stability=Decimal("85.00"),
            expense_stability=Decimal("75.00"),
            monthly_surplus_paise=3000000,
            snapshot_date="2023-01-15",
        )

        response = client.get("/api/v1/behaviour/cashflow-health")

        assert response.status_code == 200
        data = response.json()
        assert data["cashflow_stability_index"] == "80.00"
        assert data["monthly_surplus_paise"] == 3000000

        mock_service.get_cashflow_health.assert_called_once_with(household_id="default")


# ============================================================
# Tests: Patterns Endpoint
# ============================================================


class TestGetPatterns:
    """Tests for GET /api/v1/behaviour/patterns endpoint."""

    def test_get_patterns_success(
        self,
        client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test successful patterns retrieval."""
        mock_service.get_patterns.return_value = [
            FinancialPattern(
                pattern_type="IMPULSE",
                pattern_key="Amazon",
                strength=Decimal("0.80"),
                transaction_count=5,
                total_amount_paise=250000,
                first_observed="2023-01-01",
                last_observed="2023-01-15",
            ),
        ]

        response = client.get("/api/v1/behaviour/patterns")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["pattern_type"] == "IMPULSE"
        assert data[0]["pattern_key"] == "Amazon"

        mock_service.get_patterns.assert_called_once_with(household_id="default", limit=30)

    def test_get_patterns_with_days_parameter(
        self,
        client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test patterns retrieval with custom days parameter."""
        mock_service.get_patterns.return_value = []

        response = client.get("/api/v1/behaviour/patterns?days=60")

        assert response.status_code == 200
        mock_service.get_patterns.assert_called_once_with(household_id="default", limit=60)

    def test_get_patterns_with_type_filter(
        self,
        client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test patterns retrieval with pattern_type filter."""
        mock_service.get_patterns.return_value = [
            FinancialPattern(
                pattern_type="IMPULSE",
                pattern_key="Amazon",
                strength=Decimal("0.80"),
                transaction_count=5,
                total_amount_paise=250000,
                first_observed="2023-01-01",
                last_observed="2023-01-15",
            ),
            FinancialPattern(
                pattern_type="SUBSCRIPTION",
                pattern_key="Netflix",
                strength=Decimal("0.90"),
                transaction_count=12,
                total_amount_paise=60000,
                first_observed="2023-01-01",
                last_observed="2023-01-15",
            ),
        ]

        response = client.get("/api/v1/behaviour/patterns?pattern_type=IMPULSE")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["pattern_type"] == "IMPULSE"


# ============================================================
# Tests: Recommendations Endpoint
# ============================================================


class TestGetRecommendations:
    """Tests for GET /api/v1/behaviour/recommendations endpoint."""

    def test_get_recommendations_success(
        self,
        client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test successful recommendations retrieval."""
        mock_service.get_recommendations.return_value = RecommendationsResponse(
            recommendations=[
                RecommendationResponse(
                    title="Emergency Fund Needed",
                    reason="Emergency fund required",
                    metric="2 months of expenses covered",
                    severity="HIGH",
                    suggested_action="Build an emergency fund covering 3-6 months of essential expenses",
                ),
            ],
            total_count=1,
            snapshot_date="2023-01-15",
        )

        response = client.get("/api/v1/behaviour/recommendations")

        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert data["total_count"] == 1

        mock_service.get_recommendations.assert_called_once_with(
            household_id="default", limit=10, severity_filter=None
        )

    def test_get_recommendations_with_severity_filter(
        self,
        client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test recommendations retrieval with severity filter."""
        mock_service.get_recommendations.return_value = RecommendationsResponse(
            recommendations=[],
            total_count=0,
            snapshot_date="2023-01-15",
        )

        response = client.get("/api/v1/behaviour/recommendations?severity=HIGH")

        assert response.status_code == 200
        mock_service.get_recommendations.assert_called_once_with(
            household_id="default", limit=10, severity_filter="HIGH"
        )

    def test_get_recommendations_with_limit(
        self,
        client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test recommendations retrieval with custom limit."""
        mock_service.get_recommendations.return_value = RecommendationsResponse(
            recommendations=[],
            total_count=0,
            snapshot_date="2023-01-15",
        )

        response = client.get("/api/v1/behaviour/recommendations?limit=5")

        assert response.status_code == 200
        mock_service.get_recommendations.assert_called_once_with(
            household_id="default", limit=5, severity_filter=None
        )


# ============================================================
# Tests: Monthly Report Endpoint
# ============================================================


class TestGetMonthlyReport:
    """Tests for GET /api/v1/behaviour/monthly-report endpoint."""

    def test_get_monthly_report_success(
        self,
        client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test successful monthly report retrieval."""
        mock_service.generate_monthly_summary.return_value = MonthlySummaryResponse(
            period="2023-01",
            wellness_score=WellnessScoreResponse(
                score=Decimal("75.00"),
                band="Healthy",
                components={},
                snapshot_date="2023-01-15",
                version=1,
            ),
            debt_health=DebtHealthResponse(
                foir=Decimal("0.40"),
                credit_dependency_ratio=Decimal("0.20"),
                debt_cycle_score=40,
                credit_revolver_ratio=Decimal("0.15"),
                band="MODERATE",
                snapshot_date="2023-01-15",
            ),
            cashflow_health=CashflowHealthResponse(
                cashflow_stability_index=Decimal("80.00"),
                income_stability=Decimal("85.00"),
                expense_stability=Decimal("75.00"),
                monthly_surplus_paise=3000000,
                snapshot_date="2023-01-15",
            ),
            top_patterns=[],
            savings_rate=Decimal("0.15"),
            total_income_paise=5000000,
            total_expenses_paise=4000000,
            alerts=[],
        )

        response = client.get("/api/v1/behaviour/monthly-report?period=2023-01")

        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "2023-01"

        mock_service.generate_monthly_summary.assert_called_once_with(
            period="2023-01", household_id="default"
        )

    def test_get_monthly_report_without_period(
        self,
        client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test monthly report retrieval without period parameter (uses current month)."""
        mock_service.generate_monthly_summary.return_value = MonthlySummaryResponse(
            period="2023-07",
            wellness_score=WellnessScoreResponse(
                score=Decimal("75.00"),
                band="Healthy",
                components={},
                snapshot_date="2023-07-15",
                version=1,
            ),
            debt_health=DebtHealthResponse(
                foir=Decimal("0.40"),
                credit_dependency_ratio=Decimal("0.20"),
                debt_cycle_score=40,
                credit_revolver_ratio=Decimal("0.15"),
                band="MODERATE",
                snapshot_date="2023-07-15",
            ),
            cashflow_health=CashflowHealthResponse(
                cashflow_stability_index=Decimal("80.00"),
                income_stability=Decimal("85.00"),
                expense_stability=Decimal("75.00"),
                monthly_surplus_paise=3000000,
                snapshot_date="2023-07-15",
            ),
            top_patterns=[],
            savings_rate=Decimal("0.15"),
            total_income_paise=5000000,
            total_expenses_paise=4000000,
            alerts=[],
        )

        response = client.get("/api/v1/behaviour/monthly-report")

        assert response.status_code == 200
        mock_service.generate_monthly_summary.assert_called_once()


# ============================================================
# Tests: Query Parameter Validation
# ============================================================


class TestQueryParameterValidation:
    """Tests for query parameter validation."""

    def test_invalid_days_parameter(
        self,
        client: TestClient,
    ) -> None:
        """Test that days parameter with invalid value returns validation error."""
        response = client.get("/api/v1/behaviour/patterns?days=0")

        assert response.status_code == 422

    def test_days_parameter_out_of_range(
        self,
        client: TestClient,
    ) -> None:
        """Test that days parameter outside valid range returns validation error."""
        response = client.get("/api/v1/behaviour/patterns?days=400")

        assert response.status_code == 422

    def test_invalid_limit_parameter(
        self,
        client: TestClient,
    ) -> None:
        """Test that limit parameter with invalid value returns validation error."""
        response = client.get("/api/v1/behaviour/recommendations?limit=0")

        assert response.status_code == 422
