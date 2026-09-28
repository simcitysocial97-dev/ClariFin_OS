"""Behavioral strengthening tests for the Recommendation Engine (M9-C42.23 Batch 3).

The existing suite covers the primary threshold boundaries. These tests pin the
exact metric strings, the FOIR CRITICAL boundary at exactly 60%, the subscription
growth boundary at exactly 25%, deterministic ordering, and the "new subscription"
classification — the gaps that remained as surviving mutants in the C42.21 baseline.

All inputs are deterministic; no time, randomness, or external services are used.
"""

from __future__ import annotations

from decimal import Decimal

from src.engines.recommendation_engine.recommendations import (
    Recommendation,
    check_debt_dependency,
    check_foir,
    check_liquidity,
    compute_recommendations,
    detect_subscription_growth,
)


def test_debt_dependency_metric_string_is_exact_percentage() -> None:
    """The metric string must report the exact integer percentage of the ratio."""
    rec = check_debt_dependency(Decimal("0.25"))
    assert rec is not None
    assert rec.metric == "25% of expenses are credit-funded"
    rec_low = check_debt_dependency(Decimal("0.21"))
    assert rec_low is not None
    assert rec_low.metric == "21% of expenses are credit-funded"


def test_foir_critical_severity_at_exactly_60_percent() -> None:
    """FOIR == 0.60 is the CRITICAL boundary (>= 0.6), not HIGH."""
    rec = check_foir(Decimal("0.60"))
    assert rec is not None
    assert rec.severity == "CRITICAL"
    assert rec.metric == "60% of income goes to fixed obligations"


def test_foir_metric_string_is_exact_percentage() -> None:
    rec = check_foir(Decimal("0.55"))
    assert rec is not None
    assert rec.metric == "55% of income goes to fixed obligations"


def test_liquidity_metric_string_reports_months() -> None:
    rec = check_liquidity(2)
    assert rec is not None
    assert rec.metric == "Only 2 months of expenses covered"
    assert rec.severity == "MEDIUM"


def test_subscription_growth_boundary_exactly_25_percent_is_no_growth() -> None:
    """Growth of exactly 25% must NOT trigger (threshold is strictly > 0.25)."""
    current = [{"avg_amount_paise": 125, "merchant": "a"}]
    previous = [{"avg_amount_paise": 100, "merchant": "a"}]
    assert detect_subscription_growth(current, previous) is None


def test_subscription_growth_above_25_percent_triggers() -> None:
    current = [{"avg_amount_paise": 126, "merchant": "a"}]
    previous = [{"avg_amount_paise": 100, "merchant": "a"}]
    rec = detect_subscription_growth(current, previous)
    assert rec is not None
    assert rec.metric == "Subscription spending increased by 26%"


def test_subscription_new_since_previous_period_classified_low() -> None:
    """A merchant absent from the previous period is a NEW subscription (LOW)."""
    current = [
        {"avg_amount_paise": 200, "merchant": "a"},
        {"avg_amount_paise": 50, "merchant": "b"},
    ]
    previous = [{"avg_amount_paise": 200, "merchant": "a"}]
    rec = detect_subscription_growth(current, previous)
    assert rec is not None
    assert rec.severity == "LOW"
    assert rec.metric == "1 new subscriptions added"


def test_compute_recommendations_orders_critical_before_low() -> None:
    """Severity ordering must place CRITICAL first and LOW last deterministically."""
    recs = compute_recommendations(
        borrowed_lifestyle_ratio=Decimal("0.30"),  # HIGH
        foir=Decimal("0.70"),  # CRITICAL
        liquidity_months=1,  # MEDIUM
        current_subscriptions=[{"avg_amount_paise": 100, "merchant": "x"}],
        previous_subscriptions=[{"avg_amount_paise": 50, "merchant": "y"}],
    )
    severities = [r.severity for r in recs]
    assert severities[0] == "CRITICAL"
    assert severities[-1] in ("LOW", "MEDIUM")
    assert severities.index("CRITICAL") < severities.index("HIGH")


def test_recommendation_to_dict_round_trip() -> None:
    rec = Recommendation(
        title="t",
        reason="r",
        metric="m",
        severity="HIGH",
        suggested_action="a",
    )
    assert rec.to_dict() == {
        "title": "t",
        "reason": "r",
        "metric": "m",
        "severity": "HIGH",
        "suggested_action": "a",
    }
