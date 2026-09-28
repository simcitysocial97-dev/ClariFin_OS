# backend/tests/unit/engines/recommendation/test_recommendation_payload.py
#
# M9-C71 — Contract tests for the Recommendation PAYLOAD invariant.
#
# WHY THIS FILE EXISTS
# --------------------
# Every function in the recommendation engine returns the same object: a
# `Recommendation` with five fields, all of which the user reads on a
# recommendation card —
#
#     title             the headline
#     reason            why this was raised
#     metric            the number that triggered it
#     severity          LOW | MEDIUM | HIGH | CRITICAL
#     suggested_action  what to do about it
#
# A card with `reason=None` or `suggested_action=""` is not a degraded card, it
# is a broken one: the user is told something is wrong and given no explanation
# and no next step.
#
# The pre-existing tests assert that a recommendation IS returned and check its
# title. None of them assert that the other four fields are populated, so every
# one of those fields could be emptied without a single test failing. That is
# the class of defect mutation testing surfaced here as 80+ surviving
# control-flow mutants concentrated in the recommendation builders.
#
# These tests assert the payload invariant ACROSS every producer, so a new
# recommendation cannot ship with a blank field, and pin the specific
# threshold behaviour each rule documents.

from __future__ import annotations

from decimal import Decimal

import pytest
from src.engines.recommendation_engine.recommendations import (
    Recommendation,
    check_debt_dependency,
    check_foir,
    check_liquidity,
    compute_recommendations,
    detect_subscription_growth,
)

VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

#: The five fields a card renders. All of them are user-visible.
PAYLOAD_FIELDS = ("title", "reason", "metric", "severity", "suggested_action")


def _assert_complete(card: Recommendation) -> None:
    """A recommendation must be fully presentable, or it is not shippable."""
    for field in PAYLOAD_FIELDS:
        value = getattr(card, field, None)
        assert value is not None, f"{field} is None"
        assert isinstance(value, str), f"{field} is {type(value).__name__}, not str"
        assert value.strip(), f"{field} is blank"


# ── the payload invariant, per producer ──────────────────────────────────────


class TestRecommendationPayloadIsComplete:
    def test_debt_dependency_card_is_complete(self):
        card = check_debt_dependency(Decimal("0.30"))
        assert card is not None
        _assert_complete(card)
        assert card.severity in VALID_SEVERITIES

    def test_foir_card_is_complete(self):
        card = check_foir(Decimal("0.55"))
        assert card is not None
        _assert_complete(card)

    def test_liquidity_card_is_complete(self):
        card = check_liquidity(1)
        assert card is not None
        _assert_complete(card)

    def test_subscription_cards_are_complete(self):
        """Every branch of the subscription rule must render a full card."""
        cards = [
            # 3+ services with no history: "Multiple subscription services"
            detect_subscription_growth(
                [
                    {"name": "Netflix", "avg_amount_paise": 64900},
                    {"name": "Spotify", "avg_amount_paise": 11900},
                    {"name": "Gym", "avg_amount_paise": 30000},
                ]
            ),
            # previously empty: "New subscriptions detected"
            detect_subscription_growth(
                [
                    {"name": "Netflix", "avg_amount_paise": 64900},
                    {"name": "Spotify", "avg_amount_paise": 11900},
                ],
                [],
            ),
            # growth against a prior period
            detect_subscription_growth(
                [
                    {"name": "Netflix", "avg_amount_paise": 64900},
                    {"name": "Spotify", "avg_amount_paise": 11900},
                ],
                [
                    {"name": "Netflix", "avg_amount_paise": 64900},
                    {"name": "Spotify", "avg_amount_paise": 11900},
                ],
            ),
        ]
        produced = [c for c in cards if c is not None]
        assert produced, "no subscription branch produced a card"
        for card in produced:
            _assert_complete(card)

    def test_every_card_from_compute_recommendations_is_complete(self):
        """The aggregate entry point is what the API actually calls, so its
        output is what must be guaranteed shippable."""
        cards = compute_recommendations(
            borrowed_lifestyle_ratio=Decimal("0.30"),
            foir=Decimal("0.65"),
            liquidity_months=1,
            current_subscriptions=[
                {"name": "Netflix", "avg_amount_paise": 64900},
                {"name": "Spotify", "avg_amount_paise": 11900},
            ],
        )
        assert cards, "expected several cards from an unhealthy profile"
        for card in cards:
            _assert_complete(card)

    def test_a_healthy_profile_produces_no_cards_at_all(self):
        """The other half of the contract: nothing fires when nothing is wrong.

        Without this, a rule that fired unconditionally would still satisfy the
        completeness invariant above.
        """
        cards = compute_recommendations(
            borrowed_lifestyle_ratio=Decimal("0.05"),
            foir=Decimal("0.20"),
            liquidity_months=12,
            current_subscriptions=[{"name": "Netflix", "avg_amount_paise": 64900}],
        )
        assert cards == []

    def test_severity_is_ordered_critical_first(self):
        """Cards are sorted by severity, so a user sees the worst problem first.

        CRITICAL must outrank HIGH, which must outrank MEDIUM.
        """
        cards = compute_recommendations(
            borrowed_lifestyle_ratio=Decimal("0.30"),
            foir=Decimal("0.65"),
            liquidity_months=1,
            current_subscriptions=[
                {"name": "Netflix", "avg_amount_paise": 64900},
                {"name": "Spotify", "avg_amount_paise": 11900},
            ],
        )
        rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        ranks = [rank[c.severity] for c in cards]
        assert ranks == sorted(ranks), [c.severity for c in cards]


# ── the thresholds each rule documents ───────────────────────────────────────


class TestRecommendationThresholds:
    @pytest.mark.parametrize("ratio", ["0.00", "0.10", "0.20"])
    def test_debt_dependency_silent_at_or_below_20_percent(self, ratio):
        """The rule is 'exceeds 20%', so exactly 20% must NOT fire."""
        assert check_debt_dependency(Decimal(ratio)) is None

    def test_debt_dependency_fires_just_above_20_percent(self):
        assert check_debt_dependency(Decimal("0.2001")) is not None

    @pytest.mark.parametrize("ratio", ["0.00", "0.30", "0.50"])
    def test_foir_silent_at_or_below_50_percent(self, ratio):
        assert check_foir(Decimal(ratio)) is None

    def test_foir_fires_just_above_50_percent(self):
        assert check_foir(Decimal("0.5001")) is not None

    def test_foir_escalates_to_critical_at_60_percent(self):
        """≥60% FOIR is a different class of problem and must say so."""
        assert check_foir(Decimal("0.60")).severity == "CRITICAL"
        assert check_foir(Decimal("0.59")).severity == "HIGH"

    @pytest.mark.parametrize("months", [3, 6, 12])
    def test_liquidity_silent_at_or_above_three_months(self, months):
        assert check_liquidity(months) is None

    def test_liquidity_severity_escalates_only_with_no_cover_at_all(self):
        """Only ZERO months of cover is HIGH; thin cover is MEDIUM.

        The distinction matters because HIGH cards are sorted above MEDIUM ones,
        so widening it to "1 month" would push every under-funded household to
        the top of the list.
        """
        assert check_liquidity(0).severity == "HIGH"
        assert check_liquidity(1).severity == "MEDIUM"
        assert check_liquidity(2).severity == "MEDIUM"

    def test_metrics_quote_the_number_that_triggered_them(self):
        """A card that says 'high' without saying how high is not actionable."""
        debt = check_debt_dependency(Decimal("0.30"))
        assert "30" in debt.metric

        foir = check_foir(Decimal("0.55"))
        assert "55" in foir.metric

        liquidity = check_liquidity(2)
        assert "2" in liquidity.metric

    def test_subscription_metric_quotes_a_rupee_amount(self):
        """Subscription spend is reported in whole rupees, not paise.

        `avg_amount_paise` is paise; a card showing "₹64900" for a ₹649
        subscription is off by 100x and the user cannot act on it.
        """
        card = detect_subscription_growth(
            [
                {"name": "Netflix", "avg_amount_paise": 64900},
                {"name": "Spotify", "avg_amount_paise": 11900},
                {"name": "Gym", "avg_amount_paise": 30000},
            ]
        )
        assert card is not None
        assert "₹" in card.metric
        assert "64900" not in card.metric, "paise leaked into a rupee metric"
        # 64900 + 11900 + 30000 = 106800 paise = ₹1068
        assert "1068" in card.metric

    def test_two_subscriptions_need_history_to_trigger(self):
        """Without history the rule needs 3+ services; with history, 2 is enough.

        A single subscription is normal and must never trigger on its own.
        """
        two = [
            {"name": "Netflix", "avg_amount_paise": 64900},
            {"name": "Spotify", "avg_amount_paise": 11900},
        ]
        assert detect_subscription_growth(two) is None
        assert detect_subscription_growth(two, []) is not None
        assert (
            detect_subscription_growth([{"name": "Netflix", "avg_amount_paise": 64900}])
            is None
        )
