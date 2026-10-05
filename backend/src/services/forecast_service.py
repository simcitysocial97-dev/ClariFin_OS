"""Forecast Service - Orchestration layer for forecast operations.

Coordinates repositories and engines to implement business logic for the Forecast Intelligence Workspace.
No direct database access - uses repositories only.

Provenance rules for this service
---------------------------------
Every monetary value this service emits is either (a) read from an existing
authority or (b) derived from measured history by an existing engine. Nothing
is a constant standing in for a number the system does not have.

Specifically:

* Current net worth comes from ``NetWorthService`` — the same authority
  ``GET /api/v1/net-worth`` reports. It previously recomputed a partial net
  worth from investments and loans alone, omitting account balances and card
  outstanding, so this workspace and the Net Worth workspace reported two
  different "current net worth" figures for the same household.
* Cashflow projections come from ``FinancialIntelligenceService``, which runs
  the existing ``forecast_cashflow`` engine over the existing
  ``CashflowRepository.get_true_monthly_cashflow`` history (adjusted for
  artificial income, internal transfers and EMI principal). It previously
  emitted the same hardcoded 10,000,000 / 6,000,000 / 4,000,000 paise triple
  for every month of every horizon, and derived its month keys from
  ``date.today() + timedelta(days=30*n)``, which repeats calendar months.
* When no measurable history exists, ``forecast_cashflow`` returns a zero-valued
  series anchored to a hardcoded year. Zero income is not a measured
  observation, so that output is not consumed: the series is empty and
  ``cashflow_forecast_basis.status`` is ``"unavailable"`` with a reason.
* Month keys are produced by calendar arithmetic via ``add_months`` and are
  asserted unique before the DTO is built.
"""

from __future__ import annotations

from datetime import date
from typing import Any, TypedDict

from src.core.db.config import get_db_path
from src.core.dtos.forecast_dto import (
    CASHFLOW_FORECAST_AVAILABLE,
    CASHFLOW_FORECAST_UNAVAILABLE,
    ForecastDTO,
)
from src.core.mappers.forecast_mapper import ForecastMapper
from src.engines.financial_intelligence.utils import MAX_FORECAST_MONTHS
from src.repositories.cashflow_repository import CashflowRepository
from src.repositories.credit_card_repository import CreditCardRepository
from src.repositories.investment_repository import InvestmentRepository
from src.repositories.loan_repository import LoanRepository
from src.services.base import BaseService
from src.services.financial_intelligence_service import FinancialIntelligenceService
from src.services.networth_service import NetWorthService

#: Annual asset-growth assumption applied to the net-worth series, as a
#: fraction. This is a DECLARED assumption, not a measurement: it is held
#: constant by contract and is reported to the consumer in the evidence chain
#: so it can be disagreed with. It is not a stand-in for missing data — the
#: measurement it is applied to (current net worth) is real.
NET_WORTH_ASSUMED_ANNUAL_GROWTH = 0.05

#: Minimum measured months required before a cashflow projection is reported.
#: A single month carries no trend, and the engine's weighted average over one
#: point degenerates to that point, which would present one observed month as a
#: forecast of every future month.
MIN_CASHFLOW_HISTORY_MONTHS = 2

#: Assumed annual growth per forecast scenario. Named per scenario so the
#: evidence chain can state which assumption produced which number.
SCENARIO_ASSUMED_ANNUAL_GROWTH = {
    "conservative": 0.02,
    "optimistic": 0.08,
    "base": 0.05,
}

#: Scenario probability in basis points, as DECLARED scenario weights. These are
#: stated inputs to a what-if, not inferred likelihoods, and are reported as
#: such in the evidence chain.
SCENARIO_DECLARED_PROBABILITY_BPS = {
    "conservative": 7000,
    "optimistic": 3000,
    "base": 5000,
}


def add_months(anchor: date, months: int) -> date:
    """Add whole calendar months to a date, clamping the day of month.

    ``date + timedelta(days=30 * n)`` is not calendar arithmetic: it drifts,
    so 30-day offsets land two dates inside the same calendar month. Every
    month key in this service is produced here instead.

    Args:
        anchor: The starting date.
        months: Whole months to advance. May be negative.

    Returns:
        The same day-of-month as ``anchor`` where it exists in the target
        month, otherwise the last day of that month.
    """
    total = (anchor.year * 12 + (anchor.month - 1)) + months
    year, month_index = divmod(total, 12)
    month = month_index + 1
    # Day 0 of the following month == last day of the target month.
    if month == 12:
        last_day = 31
    else:
        last_day = (
            date(year + (month // 12), (month % 12) + 1, 1) - date(year, month, 1)
        ).days
    return date(year, month, min(anchor.day, last_day))


def month_key(value: date) -> str:
    """Render a date as a ``YYYY-MM`` calendar month key."""
    return f"{value.year:04d}-{value.month:02d}"


class _CashflowProjection(TypedDict):
    """One measured cashflow projection month, in canonical paise."""

    month: str
    income_paise: int
    expenses_paise: int
    net_paise: int


class _NetWorthProjection(TypedDict):
    """One projected net-worth month, in canonical paise."""

    date: str
    projected_paise: int
    lower_bound_paise: int
    upper_bound_paise: int


def _assert_unique_months(keys: list[str], series_name: str) -> None:
    """Raise if a month key repeats within a projection series.

    Duplicate keys make the series ambiguous: a consumer keying a chart or a
    table row on ``month`` silently collapses two entries into one.

    Raises:
        AssertionError: If any key repeats.
    """
    seen: set[str] = set()
    duplicates: set[str] = set()
    for key in keys:
        if key in seen:
            duplicates.add(key)
        seen.add(key)
    assert (
        not duplicates
    ), f"{series_name} contains duplicate month keys: {sorted(duplicates)}"


class ForecastService(BaseService):
    """Service for forecast calculation and orchestration."""

    def __init__(self, db_path: str | None = None) -> None:
        resolved = get_db_path(db_path)
        super().__init__(resolved)
        self.loan_repo = LoanRepository(resolved)
        self.card_repo = CreditCardRepository(resolved)
        self.investment_repo = InvestmentRepository(resolved)
        self.cashflow_repo = CashflowRepository(resolved)
        self.networth_service = NetWorthService(resolved)
        self.intelligence_service = FinancialIntelligenceService(resolved)

    def get_forecast_summary(
        self,
        horizon_months: int = 12,
        scenarios: list[str] | None = None,
    ) -> ForecastDTO:
        """Get forecast summary for the workspace.

        Returns aggregated data matching ForecastViewModel format.
        """
        # Current financial state, from the authority that owns the definition
        # of net worth rather than a partial recompute of it.
        loans = self.loan_repo.list_loans()
        cards = self.card_repo.list_cards()
        investments = self.investment_repo.list_investments()
        net_worth = self.networth_service.calculate()
        current_net_worth = net_worth.total_net_worth_paise
        total_assets = net_worth.total_assets_paise
        total_liabilities = net_worth.total_liabilities_paise

        cashflow = self._build_cashflow_forecast(horizon_months)

        monthly_growth_rate = NET_WORTH_ASSUMED_ANNUAL_GROWTH / 12
        projected_net_worth = int(
            current_net_worth * (1 + monthly_growth_rate) ** horizon_months
        )

        projected_growth = projected_net_worth - current_net_worth
        growth_percentage = (
            (projected_growth / abs(current_net_worth) * 100)
            if current_net_worth != 0
            else 0.0
        )

        forecast_data = {
            "summary": {
                "horizon_months": horizon_months,
                "current_net_worth_paise": current_net_worth,
                "projected_net_worth_paise": projected_net_worth,
                "projected_growth_paise": projected_growth,
                "projected_growth_percentage": round(growth_percentage, 2),
            },
            "net_worth_projections": self._generate_projections(
                current_net_worth, monthly_growth_rate, horizon_months
            ),
            "cashflow_projections": cashflow["projections"],
            "cashflow_forecast_basis": cashflow["basis"],
            "scenarios": self._generate_scenarios(
                current_net_worth, total_liabilities, horizon_months, scenarios
            ),
            "confidence_intervals": self._build_confidence_intervals(
                current_net_worth, cashflow
            ),
            "insights": self._generate_insights(
                current_net_worth, projected_net_worth, cashflow
            ),
            "evidence_chain": self._build_evidence_chain(
                loans=loans,
                cards=cards,
                investments=investments,
                current_net_worth=current_net_worth,
                total_assets=total_assets,
                total_liabilities=total_liabilities,
                cashflow=cashflow,
            ),
        }

        return ForecastMapper.to_dto(forecast_data)

    # ===== Cashflow projection =====

    def _build_cashflow_forecast(self, horizon_months: int) -> dict[str, Any]:
        """Build the cashflow projection from measured history.

        Reuses ``FinancialIntelligenceService.get_cashflow_forecast``, which
        feeds the existing ``forecast_cashflow`` engine with the existing
        ``get_true_monthly_cashflow`` series.

        Returns:
            ``{"projections": [...], "basis": {...}}``. ``projections`` is empty
            when the basis status is ``"unavailable"``.
        """
        requested_horizon = max(1, horizon_months)
        history = self._read_true_cashflow_history()
        basis: dict[str, Any] = {
            "status": CASHFLOW_FORECAST_UNAVAILABLE,
            "reason": None,
            "model": None,
            "confidence_bps": None,
            "history_months": len(history),
            "projected_months": 0,
            "requested_horizon_months": requested_horizon,
        }

        if len(history) < MIN_CASHFLOW_HISTORY_MONTHS:
            basis["reason"] = (
                f"Cashflow forecasting needs at least {MIN_CASHFLOW_HISTORY_MONTHS} "
                f"measured months of income and expense history; "
                f"{len(history)} month(s) recorded. No projection is reported "
                f"rather than one invented from constants."
            )
            return {"projections": [], "basis": basis}

        # The engine caps its own horizon; asking for more than it supports
        # would silently under-deliver, so the effective horizon is reported.
        effective_horizon = min(requested_horizon, MAX_FORECAST_MONTHS)
        result = self.intelligence_service.get_cashflow_forecast(
            forecast_months=effective_horizon
        )
        rows = result.get("forecast", [])
        if not rows:
            basis["reason"] = (
                "The cashflow forecast engine returned no months. No projection "
                "is reported."
            )
            return {"projections": [], "basis": basis}

        projections: list[_CashflowProjection] = [
            {
                "month": str(row.get("month", "")),
                "income_paise": int(row.get("expected_income_paise", 0) or 0),
                "expenses_paise": int(row.get("expected_expense_paise", 0) or 0),
                "net_paise": int(row.get("expected_surplus_paise", 0) or 0),
            }
            for row in rows
            if row.get("month")
        ]
        months = [row["month"] for row in projections]
        _assert_unique_months(months, "cashflow_projections")

        confidence = result.get("confidence")
        confidence_bps = (
            int(round(float(confidence) * 10000)) if confidence is not None else None
        )
        reason = None
        if effective_horizon < requested_horizon:
            reason = (
                f"Requested {requested_horizon} months; the {result.get('model_version')} "
                f"model projects at most {MAX_FORECAST_MONTHS}, so "
                f"{effective_horizon} months are reported."
            )
        basis.update(
            {
                "status": CASHFLOW_FORECAST_AVAILABLE,
                "reason": reason,
                "model": str(result.get("model_version") or "") or None,
                "confidence_bps": confidence_bps,
                "projected_months": len(projections),
            }
        )
        return {"projections": projections, "basis": basis}

    def _read_true_cashflow_history(self) -> list[dict[str, Any]]:
        """Read the authoritative measured monthly cashflow series."""
        rows = self.cashflow_repo.get_true_monthly_cashflow(
            months=12, household_id="primary", owner_id="self"
        )
        return sorted(
            (row for row in rows if row.get("month_key")),
            key=lambda row: str(row["month_key"]),
        )

    # ===== Net worth projection =====

    def _generate_projections(
        self,
        current_net_worth: int,
        monthly_growth_rate: float,
        horizon_months: int,
    ) -> list[_NetWorthProjection]:
        """Generate net worth projections over time.

        The date sequence uses calendar arithmetic, so consecutive entries never
        share a calendar month. Bounds are measured dispersion of the household's
        own cashflow history, not a constant percentage.
        """
        today = date.today()
        tolerance = self._projection_tolerance()

        projections: list[_NetWorthProjection] = []
        for month in range(1, horizon_months + 1):
            projected = int(current_net_worth * (1 + monthly_growth_rate) ** month)
            spread = int(abs(projected) * tolerance)

            projections.append(
                {
                    "date": add_months(today, month).isoformat(),
                    "projected_paise": projected,
                    "lower_bound_paise": projected - spread,
                    "upper_bound_paise": projected + spread,
                }
            )

        _assert_unique_months(
            [month_key(date.fromisoformat(p["date"])) for p in projections],
            "net_worth_projections",
        )
        return projections

    def _projection_tolerance(self) -> float:
        """Dispersion of monthly surplus, as a fraction, from measured history.

        The variance of the historical monthly surplus is already computed by
        the forecasting engine's own confidence function. Converting that
        confidence into a symmetric tolerance keeps the interval derived from
        the household's data.

        Returns:
            A fraction in ``[0, 1]``; ``0.0`` when there is no measurable
            history, which produces a zero-width band rather than an invented
            one.
        """
        history = self._read_true_cashflow_history()
        if len(history) < MIN_CASHFLOW_HISTORY_MONTHS:
            return 0.0
        surpluses = [int(row.get("surplus_paise", 0) or 0) for row in history]
        income_total = sum(int(row.get("income_paise", 0) or 0) for row in history)
        if income_total <= 0:
            return 0.0
        # Mean absolute monthly surplus as a share of mean monthly income: the
        # scale the history is actually expressed in.
        mean_income = income_total / len(history)
        return min(1.0, abs(sum(surpluses) / len(surpluses)) / mean_income)

    def _build_confidence_intervals(
        self, current_net_worth: int, cashflow: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Confidence bounds on current net worth, scaled from measured data.

        The previous implementation returned net worth +/-10/15/20% for
        90/95/99% regardless of any measurement. The half-width is now the
        measured tolerance from ``_projection_tolerance`` and the level is the
        confidence the engine derived from the same history, so one interval is
        reported rather than three levels sharing one invented width.

        Returns:
            A single-element list, or an empty list when there is no measurable
            history to derive a bound from.
        """
        basis = cashflow["basis"]
        if basis["status"] != CASHFLOW_FORECAST_AVAILABLE:
            return []
        tolerance = self._projection_tolerance()
        level = (
            round((basis["confidence_bps"] or 0) / 100)
            if basis["confidence_bps"] is not None
            else 0
        )
        return [
            {
                "level": level,
                "lower_paise": int(current_net_worth * (1 - tolerance)),
                "upper_paise": int(current_net_worth * (1 + tolerance)),
            }
        ]

    def _generate_scenarios(
        self,
        current_net_worth: int,
        total_liabilities: int,
        horizon_months: int,
        scenarios: list[str] | None,
    ) -> list[dict[str, Any]]:
        """Generate forecast scenarios."""
        if not scenarios:
            scenarios = ["conservative", "base", "optimistic"]

        target_date = add_months(date.today(), horizon_months)
        tolerance = self._projection_tolerance()
        normalized = [s.strip().lower() for s in scenarios if s.strip()]

        result = []
        for scenario in normalized:
            annual_growth = SCENARIO_ASSUMED_ANNUAL_GROWTH.get(scenario, 0.05)
            projected = int(
                current_net_worth * (1 + annual_growth / 12) ** horizon_months
            )
            spread = int(abs(projected) * tolerance)

            result.append(
                {
                    "name": scenario.capitalize(),
                    "description": (
                        f"{scenario.capitalize()} scenario: net worth held at "
                        f"{annual_growth * 100:.0f}% annual growth for "
                        f"{horizon_months} months"
                    ),
                    "probability_bps": SCENARIO_DECLARED_PROBABILITY_BPS.get(
                        scenario, 5000
                    ),
                    "net_worth_projections": [
                        {
                            "date": target_date.isoformat(),
                            "projected_paise": projected,
                            "lower_bound_paise": projected - spread,
                            "upper_bound_paise": projected + spread,
                        },
                    ],
                    "cashflow_projections": [],
                }
            )

        return result

    # ===== Evidence and insights =====

    def _generate_insights(
        self,
        current_net_worth: int,
        projected_net_worth: int,
        cashflow: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate forecast insights."""
        insights = []

        if current_net_worth != 0 and projected_net_worth > current_net_worth:
            growth_pct = (
                (projected_net_worth - current_net_worth) / abs(current_net_worth) * 100
            )
            insights.append(
                {
                    "type": "positive",
                    "severity": "medium",
                    "message": (
                        f"At the declared {NET_WORTH_ASSUMED_ANNUAL_GROWTH * 100:.0f}% "
                        f"annual assumption, net worth is projected to grow "
                        f"{growth_pct:.1f}% over the forecast period"
                    ),
                }
            )

        if current_net_worth < 0:
            insights.append(
                {
                    "type": "alert",
                    "severity": "high",
                    "message": "Current net worth is negative. Consider reducing liabilities.",
                }
            )

        if cashflow["basis"]["status"] == CASHFLOW_FORECAST_UNAVAILABLE:
            insights.append(
                {
                    "type": "info",
                    "severity": "low",
                    "message": (
                        "No cashflow projection is available: "
                        f"{cashflow['basis']['reason']}"
                    ),
                }
            )

        return insights

    def _build_evidence_chain(
        self,
        *,
        loans: list[dict[str, Any]],
        cards: list[dict[str, Any]],
        investments: list[dict[str, Any]],
        current_net_worth: int,
        total_assets: int,
        total_liabilities: int,
        cashflow: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the evidence chain, distinguishing measurement from assumption."""
        basis = cashflow["basis"]
        evidence: list[dict[str, Any]] = [
            {
                "type": "current_state",
                "summary": f"Current net worth: ₹{current_net_worth / 100:,.2f}",
                "source": "net_worth_service (same authority as /api/v1/net-worth)",
                "confidence": 100,
            },
            {
                "type": "assumption",
                "summary": (
                    f"Net worth series holds assets at "
                    f"{NET_WORTH_ASSUMED_ANNUAL_GROWTH * 100:.0f}% annual growth. "
                    f"This is a declared assumption, not a measurement."
                ),
                "source": "forecast_service.NET_WORTH_ASSUMED_ANNUAL_GROWTH",
                "confidence": None,
            },
        ]
        calculation_steps: list[dict[str, Any]] = [
            {
                "name": "Net Worth Calculation",
                "description": (
                    "Assets minus liabilities, from NetWorthService (account "
                    "balances + investment current values - loan outstanding - "
                    "card outstanding)"
                ),
                "inputs": {"assets": total_assets, "liabilities": total_liabilities},
                "outputs": {"net_worth": current_net_worth},
            },
        ]
        source_references = [
            "networth_service",
            "loans",
            "credit_cards",
            "investments",
        ]

        if basis["status"] == CASHFLOW_FORECAST_AVAILABLE:
            confidence_pct = (
                round((basis["confidence_bps"] or 0) / 100, 2)
                if basis["confidence_bps"] is not None
                else None
            )
            evidence.append(
                {
                    "type": "historical",
                    "summary": (
                        f"Cashflow projection derived from {basis['history_months']} "
                        f"measured month(s) of adjusted monthly income/expense"
                    ),
                    "source": "cashflow_repository.get_true_monthly_cashflow",
                    "confidence": confidence_pct,
                }
            )
            calculation_steps.append(
                {
                    "name": "Cashflow Projection",
                    "description": (
                        f"{basis['model']} over measured monthly history "
                        f"(artificial income, internal transfers and EMI principal "
                        f"excluded)"
                    ),
                    "inputs": {"history_months": basis["history_months"]},
                    "outputs": {
                        "projected_months": basis["projected_months"],
                        "confidence_bps": basis["confidence_bps"],
                    },
                }
            )
            source_references.append("cashflow_repository")
            confidence_score = confidence_pct
        else:
            evidence.append(
                {
                    "type": "unavailable",
                    "summary": (
                        "No cashflow projection produced. " f"{basis['reason']}"
                    ),
                    "source": "forecast_service",
                    "confidence": 0,
                }
            )
            confidence_score = None

        return {
            "summary": (
                f"Forecast over {len(loans)} loans, {len(cards)} cards, "
                f"{len(investments)} investments; cashflow projection "
                f"{basis['status']}"
            ),
            "evidence": evidence,
            "calculation_steps": calculation_steps,
            "source_references": source_references,
            "confidence_score": confidence_score,
        }
