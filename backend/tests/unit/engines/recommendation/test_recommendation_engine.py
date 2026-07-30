"""Tests for Recommendation Engine - Deterministic recommendation rules.

All tests verify:
- Correct rule implementation
- Edge cases (zero values, boundary values)
- Determinism (same input -> same output)
- Recommendation structure (title, reason, metric, severity, suggested_action)
"""

from decimal import Decimal

from src.engines.recommendation_engine import (
    check_debt_dependency,
    check_foir,
    check_liquidity,
    compute_recommendations,
    detect_subscription_growth,
)

# ============================================================
# Tests: Debt Dependency Rule
# ============================================================


class TestDebtDependency:
    """Tests for check_debt_dependency rule."""

    def test_no_recommendation_below_threshold(self):
        """Ratio at or below 20% should not trigger recommendation."""
        result = check_debt_dependency(Decimal("0.20"))
        assert result is None

    def test_no_recommendation_zero(self):
        """Zero ratio should not trigger recommendation."""
        result = check_debt_dependency(Decimal("0.0"))
        assert result is None

    def test_recommendation_above_threshold(self):
        """Ratio above 20% should trigger recommendation."""
        result = check_debt_dependency(Decimal("0.25"))
        assert result is not None
        assert result.title == "Lifestyle Debt Alert"
        assert result.reason == "Your lifestyle is partly funded by borrowed money"
        assert result.severity == "HIGH"
        assert result.metric == "25% of expenses are credit-funded"

    def test_recommendation_contains_required_fields(self):
        """Recommendation should have all required fields."""
        result = check_debt_dependency(Decimal("0.30"))
        assert result is not None
        assert hasattr(result, "title")
        assert hasattr(result, "reason")
        assert hasattr(result, "metric")
        assert hasattr(result, "severity")
        assert hasattr(result, "suggested_action")

    def test_recommendation_to_dict(self):
        """Recommendation should convert to dictionary correctly."""
        result = check_debt_dependency(Decimal("0.25"))
        assert result is not None
        d = result.to_dict()
        assert d["title"] == "Lifestyle Debt Alert"
        assert d["reason"] == "Your lifestyle is partly funded by borrowed money"
        assert d["metric"] == "25% of expenses are credit-funded"
        assert d["severity"] == "HIGH"
        assert "suggested_action" in d


# ============================================================
# Tests: FOIR Rule
# ============================================================


class TestFOIRRule:
    """Tests for check_foir rule."""

    def test_no_recommendation_below_threshold(self):
        """FOIR at or below 50% should not trigger recommendation."""
        result = check_foir(Decimal("0.50"))
        assert result is None

    def test_no_recommendation_zero(self):
        """Zero FOIR should not trigger recommendation."""
        result = check_foir(Decimal("0.0"))
        assert result is None

    def test_recommendation_above_threshold(self):
        """FOIR above 50% should trigger recommendation."""
        result = check_foir(Decimal("0.55"))
        assert result is not None
        assert result.title == "High Fixed Obligations"
        assert result.reason == "Fixed obligations are high"
        assert result.severity == "HIGH"
        assert result.metric == "55% of income goes to fixed obligations"

    def test_recommendation_critical_severity(self):
        """FOIR >= 60% should have CRITICAL severity."""
        result = check_foir(Decimal("0.70"))
        assert result is not None
        assert result.severity == "CRITICAL"

    def test_recommendation_contains_required_fields(self):
        """Recommendation should have all required fields."""
        result = check_foir(Decimal("0.60"))
        assert result is not None
        assert hasattr(result, "title")
        assert hasattr(result, "reason")
        assert hasattr(result, "metric")
        assert hasattr(result, "severity")
        assert hasattr(result, "suggested_action")


# ============================================================
# Tests: Liquidity Rule
# ============================================================


class TestLiquidityRule:
    """Tests for check_liquidity rule."""

    def test_no_recommendation_sufficient_months(self):
        """3+ months should not trigger recommendation."""
        result = check_liquidity(3)
        assert result is None

    def test_no_recommendation_many_months(self):
        """6+ months should not trigger recommendation."""
        result = check_liquidity(6)
        assert result is None

    def test_recommendation_below_threshold(self):
        """Less than 3 months should trigger recommendation."""
        result = check_liquidity(2)
        assert result is not None
        assert result.title == "Emergency Fund Needed"
        assert result.reason == "Emergency fund required"
        assert result.severity == "MEDIUM"

    def test_recommendation_zero_months(self):
        """Zero months should trigger HIGH severity recommendation."""
        result = check_liquidity(0)
        assert result is not None
        assert result.severity == "HIGH"
        assert result.metric == "Only 0 months of expenses covered"

    def test_recommendation_one_month(self):
        """1 month should trigger MEDIUM severity recommendation (HIGH only for < 1 month)."""
        result = check_liquidity(1)
        assert result is not None
        assert result.severity == "MEDIUM"

    def test_recommendation_two_months(self):
        """2 months should trigger MEDIUM severity recommendation."""
        result = check_liquidity(2)
        assert result is not None
        assert result.severity == "MEDIUM"

    def test_recommendation_contains_required_fields(self):
        """Recommendation should have all required fields."""
        result = check_liquidity(1)
        assert result is not None
        assert hasattr(result, "title")
        assert hasattr(result, "reason")
        assert hasattr(result, "metric")
        assert hasattr(result, "severity")
        assert hasattr(result, "suggested_action")


# ============================================================
# Tests: Subscription Growth Rule
# ============================================================


class TestSubscriptionGrowth:
    """Tests for detect_subscription_growth rule."""

    def test_no_recommendation_empty_subscriptions(self):
        """Empty subscriptions list should not trigger recommendation."""
        result = detect_subscription_growth([])
        assert result is None

    def test_no_recommendation_few_subscriptions(self):
        """1-2 subscriptions without previous data should not trigger recommendation."""
        subscriptions = [{"merchant": "NETFLIX", "avg_amount_paise": 79000}]
        result = detect_subscription_growth(subscriptions)
        assert result is None

    def test_recommendation_multiple_subscriptions(self):
        """3+ subscriptions without previous data should trigger recommendation."""
        subscriptions = [
            {"merchant": "NETFLIX", "avg_amount_paise": 79000},
            {"merchant": "SPOTIFY", "avg_amount_paise": 119000},
            {"merchant": "AMAZON", "avg_amount_paise": 149000},
        ]
        result = detect_subscription_growth(subscriptions)
        assert result is not None
        assert result.title == "Review Subscriptions"

    def test_recommendation_no_growth(self):
        """No growth between periods should not trigger recommendation."""
        current = [{"merchant": "NETFLIX", "avg_amount_paise": 79000}]
        previous = [{"merchant": "NETFLIX", "avg_amount_paise": 79000}]
        result = detect_subscription_growth(current, previous)
        assert result is None

    def test_recommendation_growth_detected(self):
        """25%+ subscription growth should trigger recommendation."""
        current = [{"merchant": "NETFLIX", "avg_amount_paise": 100000}]
        previous = [{"merchant": "NETFLIX", "avg_amount_paise": 70000}]
        result = detect_subscription_growth(current, previous)
        assert result is not None
        assert (
            "increasing" in result.reason.lower()
            or "increased" in result.reason.lower()
        )

    def test_recommendation_new_subscription(self):
        """New subscription not in previous period should trigger recommendation."""
        current = [{"merchant": "NETFLIX", "avg_amount_paise": 79000}]
        previous = [{"merchant": "SPOTIFY", "avg_amount_paise": 119000}]
        result = detect_subscription_growth(current, previous)
        assert result is not None
        assert "new" in result.reason.lower()

    def test_recommendation_contains_required_fields(self):
        """Recommendation should have all required fields."""
        subscriptions = [
            {"merchant": "NETFLIX", "avg_amount_paise": 79000},
            {"merchant": "SPOTIFY", "avg_amount_paise": 119000},
            {"merchant": "AMAZON", "avg_amount_paise": 149000},
        ]
        result = detect_subscription_growth(subscriptions)
        assert result is not None
        assert hasattr(result, "title")
        assert hasattr(result, "reason")
        assert hasattr(result, "metric")
        assert hasattr(result, "severity")
        assert hasattr(result, "suggested_action")


# ============================================================
# Tests: Compute All Recommendations
# ============================================================


class TestComputeRecommendations:
    """Tests for compute_recommendations function."""

    def test_no_recommendations_all_healthy(self):
        """All healthy metrics should not trigger recommendations."""
        recommendations = compute_recommendations(
            borrowed_lifestyle_ratio=Decimal("0.10"),
            foir=Decimal("0.30"),
            liquidity_months=6,
            current_subscriptions=[],
        )
        assert len(recommendations) == 0

    def test_single_recommendation(self):
        """One unhealthy metric should trigger one recommendation."""
        recommendations = compute_recommendations(
            borrowed_lifestyle_ratio=Decimal("0.25"),
            foir=Decimal("0.30"),
            liquidity_months=6,
            current_subscriptions=[],
        )
        assert len(recommendations) == 1
        assert recommendations[0].title == "Lifestyle Debt Alert"

    def test_multiple_recommendations(self):
        """Multiple unhealthy metrics should trigger multiple recommendations."""
        recommendations = compute_recommendations(
            borrowed_lifestyle_ratio=Decimal("0.25"),
            foir=Decimal("0.55"),
            liquidity_months=1,
            current_subscriptions=[
                {"merchant": "NETFLIX", "avg_amount_paise": 79000},
                {"merchant": "SPOTIFY", "avg_amount_paise": 119000},
                {"merchant": "AMAZON", "avg_amount_paise": 149000},
            ],
        )
        assert len(recommendations) == 4  # debt + foir + liquidity + subscription

    def test_recommendations_sorted_by_severity(self):
        """Recommendations should be sorted by severity (CRITICAL first)."""
        recommendations = compute_recommendations(
            borrowed_lifestyle_ratio=Decimal("0.25"),  # HIGH
            foir=Decimal("0.70"),  # CRITICAL
            liquidity_months=0,  # HIGH
            current_subscriptions=[],
        )
        assert len(recommendations) == 3
        # First should be CRITICAL
        assert recommendations[0].severity == "CRITICAL"
        assert recommendations[0].title == "High Fixed Obligations"

    def test_recommendations_to_dict(self):
        """All recommendations should convert to dictionaries."""
        recommendations = compute_recommendations(
            borrowed_lifestyle_ratio=Decimal("0.30"),
            foir=Decimal("0.55"),
            liquidity_months=2,
            current_subscriptions=[],
        )
        for rec in recommendations:
            d = rec.to_dict()
            assert isinstance(d, dict)
            assert "title" in d
            assert "reason" in d
            assert "metric" in d
            assert "severity" in d
            assert "suggested_action" in d


# ============================================================
# Tests: Determinism
# ============================================================


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_debt_dependency_deterministic(self):
        """check_debt_dependency should be deterministic."""
        for _ in range(5):
            result = check_debt_dependency(Decimal("0.25"))
            assert result is not None
            assert result.title == "Lifestyle Debt Alert"

    def test_foir_deterministic(self):
        """check_foir should be deterministic."""
        for _ in range(5):
            result = check_foir(Decimal("0.55"))
            assert result is not None
            assert result.severity == "HIGH"

    def test_liquidity_deterministic(self):
        """check_liquidity should be deterministic."""
        for _ in range(5):
            result = check_liquidity(2)
            assert result is not None
            assert result.severity == "MEDIUM"

    def test_subscription_growth_deterministic(self):
        """detect_subscription_growth should be deterministic."""
        subscriptions = [
            {"merchant": "NETFLIX", "avg_amount_paise": 79000},
            {"merchant": "SPOTIFY", "avg_amount_paise": 119000},
            {"merchant": "AMAZON", "avg_amount_paise": 149000},
        ]
        for _ in range(5):
            result = detect_subscription_growth(subscriptions)
            assert result is not None
            assert result.title == "Review Subscriptions"

    def test_compute_all_recommendations_deterministic(self):
        """compute_recommendations should be deterministic."""
        for _ in range(5):
            recommendations = compute_recommendations(
                borrowed_lifestyle_ratio=Decimal("0.25"),
                foir=Decimal("0.55"),
                liquidity_months=1,
                current_subscriptions=[
                    {"merchant": "NETFLIX", "avg_amount_paise": 79000}
                ],
            )
            assert (
                len(recommendations) == 3
            )  # debt + foir + liquidity (no subscription without prev)
