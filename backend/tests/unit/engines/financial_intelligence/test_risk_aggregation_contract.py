# backend/tests/unit/engines/financial_intelligence/test_risk_aggregation_contract.py
#
# M9-C71 — Contract tests for the RISK AGGREGATION contract.
#
# WHY THIS FILE EXISTS
# --------------------
# `_aggregate_risks` merges four independent sources into the risk list a user
# is shown. Each source has a documented trigger and a documented severity:
#
#     liquidity risk_level "high"        -> liquidity_stress / critical
#     liquidity risk_level "medium"      -> liquidity_stress / warning
#     credit trend "worsening"           -> credit_dependency / warning
#     credit dependency_ratio > 0.3      -> credit_dependency / warning
#     behaviour debt_cycle_score > 70    -> debt_cycle / warning
#     each optimisation warning          -> optimization_warning / warning
#
# The pre-existing tests did not assert the trigger thresholds or the
# type-to-severity mapping, so a threshold could be moved, a severity swapped
# for another, or a risk silently dropped without a failure. Those are exactly
# the fields that decide whether someone is warned about their finances.
#
# These tests pin the triggers and the severity mapping, and assert that a
# healthy profile produces no risks at all.

from __future__ import annotations

from decimal import Decimal

from src.engines.financial_intelligence.intelligence import _aggregate_risks

VALID_SEVERITIES = {"critical", "warning"}
VALID_SOURCES = {"forecasting_engine", "behaviour_engine", "optimization_engine"}

#: A profile with nothing wrong.
HEALTHY = (
    {"risk_level": "low"},
    {"trend": "stable", "current_dependency_ratio": Decimal("0.10")},
    {"warnings": []},
    {"debt_cycle_score": 10},
)


def _risks(liquidity=None, credit=None, optimisation=None, behaviour=None) -> list:
    return _aggregate_risks(
        liquidity if liquidity is not None else HEALTHY[0],
        credit if credit is not None else HEALTHY[1],
        optimisation if optimisation is not None else HEALTHY[2],
        behaviour if behaviour is not None else HEALTHY[3],
    )


def _types(risks: list) -> set[str]:
    return {r["type"] for r in risks}


def _assert_wellformed(risks: list) -> None:
    for risk in risks:
        assert {"type", "severity", "source", "details"} <= set(risk), risk
        assert risk["severity"] in VALID_SEVERITIES, risk["severity"]
        assert risk["source"] in VALID_SOURCES, risk["source"]
        assert isinstance(risk["details"], dict)


# ── the healthy baseline ─────────────────────────────────────────────────────


class TestHealthyProfileIsQuiet:
    def test_a_healthy_profile_produces_no_risks(self):
        """The other half of the contract: no warning when nothing is wrong.

        Without this, an aggregation that flagged everything would satisfy every
        structural assertion below.
        """
        assert _risks() == []

    def test_a_missing_risk_level_is_treated_as_low(self):
        """Absent data is not a crisis; defaulting to `high` would warn every
        user whose forecast has not run yet."""
        risks = _risks(liquidity={})

        assert "liquidity_stress" not in _types(risks)


# ── liquidity ────────────────────────────────────────────────────────────────


class TestLiquidityRisk:
    def test_high_liquidity_risk_is_critical(self):
        risks = _risks(liquidity={"risk_level": "high", "months_until_stress": 1})

        assert "liquidity_stress" in _types(risks)
        risk = next(r for r in risks if r["type"] == "liquidity_stress")
        assert risk["severity"] == "critical"
        assert risk["source"] == "forecasting_engine"

    def test_medium_liquidity_risk_is_only_a_warning(self):
        """Medium must not be escalated to critical, or every user with a
        soft month is told they are in serious trouble."""
        risks = _risks(liquidity={"risk_level": "medium"})

        risk = next(r for r in risks if r["type"] == "liquidity_stress")
        assert risk["severity"] == "warning"

    def test_critical_liquidity_carries_the_projection_detail(self):
        """An operator acting on the warning needs the numbers behind it."""
        risks = _risks(
            liquidity={
                "risk_level": "high",
                "months_until_stress": 2,
                "projected_min_balance_paise": -50_000,
            }
        )

        risk = next(r for r in risks if r["type"] == "liquidity_stress")
        assert risk["details"]["months_until_stress"] == 2
        assert risk["details"]["projected_min_balance_paise"] == -50_000

    def test_low_liquidity_risk_produces_nothing(self):
        assert "liquidity_stress" not in _types(_risks(liquidity={"risk_level": "low"}))


# ── credit dependency ────────────────────────────────────────────────────────


class TestCreditDependencyRisk:
    def test_a_worsening_trend_raises_the_risk(self):
        risks = _risks(
            credit={"trend": "worsening", "current_dependency_ratio": Decimal("0")}
        )

        risk = next(r for r in risks if r["type"] == "credit_dependency")
        assert risk["severity"] == "warning"
        assert risk["details"]["trend"] == "worsening"

    def test_a_dependency_ratio_above_thirty_percent_raises_the_risk(self):
        """A stable trend with high dependency is still a risk."""
        risks = _risks(
            credit={"trend": "stable", "current_dependency_ratio": Decimal("0.31")}
        )

        assert "credit_dependency" in _types(risks)

    def test_exactly_thirty_percent_does_not_raise_the_risk(self):
        """The threshold is `> 0.3`, so exactly 30% is not yet a risk."""
        risks = _risks(
            credit={"trend": "stable", "current_dependency_ratio": Decimal("0.30")}
        )

        assert "credit_dependency" not in _types(risks)

    def test_a_stable_low_dependency_profile_is_quiet(self):
        risks = _risks(
            credit={"trend": "stable", "current_dependency_ratio": Decimal("0.20")}
        )

        assert "credit_dependency" not in _types(risks)

    def test_the_dependency_ratio_is_reported_as_a_readable_string(self):
        """`Decimal` is stored for arithmetic, but a JSON payload must serialise."""
        risks = _risks(
            credit={"trend": "worsening", "current_dependency_ratio": Decimal("0.42")}
        )

        risk = next(r for r in risks if r["type"] == "credit_dependency")
        assert isinstance(risk["details"]["dependency_ratio"], str)
        assert "0.42" in risk["details"]["dependency_ratio"]

    def test_a_non_decimal_ratio_does_not_crash_the_comparison(self):
        """The ratio arrives from JSON, where it may be a float or string."""
        risks = _risks(credit={"trend": "stable", "current_dependency_ratio": 0.9})

        assert isinstance(risks, list)


# ── behaviour ────────────────────────────────────────────────────────────────


class TestDebtCycleRisk:
    def test_a_debt_cycle_score_above_seventy_raises_the_risk(self):
        risks = _risks(behaviour={"debt_cycle_score": 71})

        risk = next(r for r in risks if r["type"] == "debt_cycle")
        assert risk["severity"] == "warning"
        assert risk["source"] == "behaviour_engine"
        assert risk["details"]["debt_cycle_score"] == 71

    def test_exactly_seventy_does_not_raise_the_risk(self):
        """The threshold is `> 70`, so exactly 70 is not yet a risk."""
        assert "debt_cycle" not in _types(_risks(behaviour={"debt_cycle_score": 70}))

    def test_a_missing_debt_cycle_score_is_quiet(self):
        assert "debt_cycle" not in _types(_risks(behaviour={}))

    def test_a_zero_debt_cycle_score_is_quiet(self):
        assert "debt_cycle" not in _types(_risks(behaviour={"debt_cycle_score": 0}))


# ── optimisation warnings ────────────────────────────────────────────────────


class TestOptimisationWarnings:
    def test_each_warning_becomes_its_own_risk(self):
        """Warnings are not merged: two problems need two entries, or one is
        silently dropped from the user's list."""
        risks = _risks(optimisation={"warnings": ["High interest debt", "No buffer"]})

        warnings = [r for r in risks if r["type"] == "optimization_warning"]
        assert len(warnings) == 2
        messages = {w["details"]["message"] for w in warnings}
        assert messages == {"High interest debt", "No buffer"}

    def test_no_warnings_produces_no_risks(self):
        assert "optimization_warning" not in _types(
            _risks(optimisation={"warnings": []})
        )

    def test_a_missing_warnings_key_is_quiet(self):
        """Absent data must not be read as an empty list of problems AND must
        not raise."""
        assert isinstance(_risks(optimisation={}), list)


# ── the combined profile ─────────────────────────────────────────────────────


class TestCombinedProfile:
    def test_every_source_can_contribute_at_once(self):
        """Risks from independent sources must all survive the merge."""
        risks = _risks(
            liquidity={"risk_level": "high"},
            credit={"trend": "worsening"},
            behaviour={"debt_cycle_score": 90},
            optimisation={"warnings": ["buffer thin"]},
        )

        assert _types(risks) == {
            "liquidity_stress",
            "credit_dependency",
            "debt_cycle",
            "optimization_warning",
        }
        _assert_wellformed(risks)

    def test_only_liquidity_can_be_critical(self):
        """Critical is reserved for immediate solvency risk. If any other source
        could raise it, the severity scale stops meaning anything."""
        risks = _risks(
            credit={"trend": "worsening"},
            behaviour={"debt_cycle_score": 100},
            optimisation={"warnings": ["anything"]},
        )

        assert {r["severity"] for r in risks} == {"warning"}

    def test_liquidity_is_reported_once_not_once_per_level(self):
        """A high level is critical, not both critical and warning."""
        risks = _risks(liquidity={"risk_level": "high"})

        assert len([r for r in risks if r["type"] == "liquidity_stress"]) == 1

    def test_credit_dependency_is_reported_once(self):
        """Both triggers firing must still produce one credit_dependency entry,
        so the user's list does not double-count one problem."""
        risks = _risks(
            credit={"trend": "worsening", "current_dependency_ratio": Decimal("0.9")}
        )

        assert len([r for r in risks if r["type"] == "credit_dependency"]) == 1

    def test_every_risk_names_the_engine_that_raised_it(self):
        """A risk with no source cannot be acted on or triaged."""
        risks = _risks(
            liquidity={"risk_level": "high"},
            behaviour={"debt_cycle_score": 90},
            optimisation={"warnings": ["x"]},
        )

        for risk in risks:
            assert risk["source"] in VALID_SOURCES
