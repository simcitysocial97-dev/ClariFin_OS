# backend/tests/unit/engines/financial_intelligence/test_goal_health_contract.py
#
# M9-C71 — Contract tests for the goal HEALTH-BAND contract.
#
# WHY THIS FILE EXISTS
# --------------------
# `calculate_goal_health` reduces a savings goal to one of three statuses —
# `on_track`, `at_risk`, `behind` — each with a score and a human explanation.
# Those statuses drive what the product tells someone about money they are
# relying on, so the band boundaries are contractual:
#
#     invalid target (≤ 0)          -> behind,  score 0
#     already achieved (0 months)   -> on_track, score 1
#     completes on/before target    -> on_track
#     1-3 months late               -> at_risk
#     more than 3 months late       -> behind
#
# and, when no timeline is available, a progress-based banding instead:
#
#     >= 75% complete  -> on_track
#     >= 50% complete  -> at_risk
#     below 50%        -> behind
#
# The pre-existing tests never asserted WHICH band a given input produces, nor
# that the explanation matches the status. A goal reported as `on_track` with
# the explanation "Significantly behind" would satisfy nothing that was written.
# That is what mutation testing surfaced here: every band boundary, and the
# `explanation` value, survived untouched.
#
# These tests pin the bands and the status/explanation agreement.

from __future__ import annotations

from decimal import Decimal

import pytest
from src.engines.financial_intelligence.goal_planner import calculate_goal_health

VALID_STATUSES = {"on_track", "at_risk", "behind"}

# 1,000,000 paise = ₹10,000 target.
TARGET = 1_000_000


def _health(current: int, months: int | None, projected: str | None, target_date):
    return calculate_goal_health(TARGET, current, months, projected, target_date)


def _assert_wellformed(health: dict) -> None:
    assert {"score", "status", "explanation"} <= set(health)
    assert health["status"] in VALID_STATUSES
    assert isinstance(health["score"], Decimal)
    assert isinstance(health["explanation"], str)
    assert health["explanation"].strip(), "an explanation the user can read"
    assert Decimal("0") <= health["score"] <= Decimal("1")


# ── the invalid-input and achieved bands ─────────────────────────────────────


class TestGoalHealthEdges:
    @pytest.mark.parametrize("target", [0, -1, -100_000])
    def test_a_non_positive_target_is_behind_with_zero_score(self, target):
        """A goal of nothing is not a goal, and must not score as achievable."""
        health = calculate_goal_health(target, 0, 12, "2025-12", "2025-06-01")

        _assert_wellformed(health)
        assert health["status"] == "behind"
        assert health["score"] == Decimal("0")

    def test_a_single_paise_target_is_still_a_valid_goal(self):
        """The guard is `<= 0`, so a ₹0.01 goal is a real target, not invalid.

        Widening the guard to `<= 1` would classify it as invalid and tell the
        user their goal is broken. (The status itself is legitimately `behind`
        here — 0% funded, six months past its target date — so the meaningful
        assertion is that the goal is not rejected as invalid.)
        """
        health = calculate_goal_health(1, 0, 12, "2025-12", "2025-06-01")

        _assert_wellformed(health)
        assert health["explanation"] != "Invalid target amount"
        assert "invalid" not in health["explanation"].lower()

    def test_a_single_paise_target_can_still_be_on_track_when_funded(self):
        """The same goal, funded, is a normal goal."""
        health = calculate_goal_health(1, 1, 0, "2025-01", "2025-12-01")

        assert health["status"] == "on_track"
        assert health["explanation"] == "Goal already achieved"

    def test_zero_months_remaining_is_already_achieved(self):
        health = _health(TARGET, 0, "2025-01", "2025-12-01")

        _assert_wellformed(health)
        assert health["status"] == "on_track"
        assert health["score"] == Decimal("1")
        assert health["explanation"] == "Goal already achieved"

    def test_achieved_takes_precedence_over_a_late_projection(self):
        """A goal already banked is on track even if the forecast says otherwise.

        The achieved check runs before the date comparison, so an inflated
        projection must not downgrade it.
        """
        health = _health(TARGET, 0, "2030-01", "2025-12-01")

        assert health["status"] == "on_track"
        assert health["explanation"] == "Goal already achieved"

    def test_progress_is_capped_at_one(self):
        """Over-saving must not produce a score above 1, which callers may
        treat as invalid."""
        health = _health(TARGET * 3, 5, "2025-06", "2025-12-01")

        assert health["score"] <= Decimal("1")
        assert Decimal("0") <= health["score"]


# ── the timeline bands ───────────────────────────────────────────────────────


class TestGoalHealthTimelineBands:
    def test_completing_before_the_target_is_on_track(self):
        health = _health(0, 6, "2025-06", "2025-12-01")

        assert health["status"] == "on_track"
        assert "on track" in health["explanation"].lower()

    def test_completing_exactly_on_the_target_is_on_track(self):
        health = _health(0, 6, "2025-12", "2025-12-01")

        assert health["status"] == "on_track"

    def test_three_months_late_is_at_risk_not_behind(self):
        """3 months late is the top of the at_risk band, so widening it to
        `<= 4` would wrongly reassure someone who is a quarter behind."""
        health = _health(0, 6, "2026-03", "2025-12-01")

        assert health["status"] == "at_risk"
        assert "3" in health["explanation"]

    def test_one_month_late_is_at_risk(self):
        health = _health(0, 6, "2026-01", "2025-12-01")

        assert health["status"] == "at_risk"

    def test_four_months_late_is_behind(self):
        """One month past the at_risk band."""
        health = _health(0, 6, "2026-04", "2025-12-01")

        assert health["status"] == "behind"
        assert "behind" in health["explanation"].lower()

    def test_a_far_off_projection_is_behind(self):
        health = _health(0, 6, "2030-01", "2025-12-01")

        assert health["status"] == "behind"

    def test_late_years_are_compared_not_by_string_order(self):
        """2026-01 is one month after 2025-12 despite sorting earlier as a
        number; the comparison is year*12 + month, so this must hold."""
        assert _health(0, 6, "2026-01", "2025-12-01")["status"] == "at_risk"
        assert _health(0, 6, "2025-12", "2026-01")["status"] == "on_track"


# ── the progress bands used when no timeline exists ──────────────────────────


class TestGoalHealthProgressBands:
    @pytest.mark.parametrize(
        ("ratio_pct", "expected"),
        [
            (80, "on_track"),
            (75, "on_track"),
            (60, "at_risk"),
            (50, "at_risk"),
            (20, "behind"),
        ],
    )
    def test_progress_bands_without_a_timeline(self, ratio_pct, expected):
        health = _health(TARGET * ratio_pct // 100, None, None, None)

        assert health["status"] == expected

    def test_exactly_seventy_five_percent_is_on_track(self):
        """The band is `>= 0.75`, so exactly three quarters is on track.

        This is the boundary that survived as `> Decimal("0.75")` before this
        test existed — an exactly-75% goal was being reported as merely at risk.
        """
        health = _health(750_000, None, None, None)

        assert health["status"] == "on_track"
        assert "75%" in health["explanation"]

    def test_just_under_seventy_five_percent_is_at_risk(self):
        health = _health(749_000, None, None, None)

        assert health["status"] == "at_risk"

    def test_exactly_half_is_at_risk(self):
        health = _health(500_000, None, None, None)

        assert health["status"] == "at_risk"
        assert "50%" in health["explanation"]

    def test_explanation_always_agrees_with_status(self):
        """A card saying "Significantly behind" on an on_track goal is a
        contradiction a user would notice immediately."""
        cases = [
            (0, None, None, None),
            (300_000, None, None, None),
            (750_000, None, None, None),
            (999_000, None, None, None),
            (0, 6, "2025-12", "2025-12-01"),
            (0, 6, "2026-03", "2025-12-01"),
            (0, 6, "2027-06", "2025-12-01"),
        ]
        for current, months, projected, target_date in cases:
            health = _health(current, months, projected, target_date)
            explanation = health["explanation"].lower()
            if health["status"] == "behind":
                assert (
                    "behind" in explanation
                    or "unknown" in explanation
                    or "attention" in explanation
                ), (health["status"], explanation)
            elif health["status"] == "on_track":
                assert not explanation.startswith("significantly"), explanation


# ── malformed input must degrade, not crash ──────────────────────────────────


class TestGoalHealthDegradation:
    def test_unparseable_dates_fall_back_to_progress_banding(self):
        """A malformed date must not raise; it falls back to progress."""
        health = _health(800_000, 6, "not-a-month", "also-not-a-date")

        _assert_wellformed(health)
        assert health["status"] == "on_track"

    def test_a_missing_target_date_uses_progress_banding(self):
        health = _health(800_000, 6, "2025-12", None)

        _assert_wellformed(health)
        assert health["status"] == "on_track"

    def test_a_missing_projection_uses_progress_banding(self):
        health = _health(100_000, 6, None, "2025-12-01")

        _assert_wellformed(health)
        assert health["status"] in VALID_STATUSES
