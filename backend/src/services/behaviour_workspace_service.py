"""Behaviour Intelligence Workspace Service.

Returns aggregated behaviour data matching BehaviourViewModel format.

Provenance
----------
Every figure this service reports is read from ``BehaviourService``, which is
the authority for behaviour metrics and derives them from the household's own
recorded transactions, accounts, loans and cards.

This service previously invented most of its own output:

* ``wellness_score`` started at 100 and subtracted ``min(30, outstanding //
  100000)`` — labelled "(placeholder)" in the source. It bore no relation to
  ``BehaviourService.get_wellness_score`` and none to the documented 0-100
  wellness semantics.
* ``spending_patterns`` were three fixed rows: housing ₹30,000 / 30% / 1
  transaction, food ₹15,000 / 15% / 50 transactions, transport ₹10,000 / 10% /
  20 transactions.
* ``savings_rate`` was four constants: ``current_rate`` 15.0, ``trend`` "up",
  ``monthly_savings_paise`` 100000, ``income_paise`` 1000000.
* ``debt_health.score`` was 75 and ``debt_to_income_ratio`` was 0.25.
* ``wellness_radar`` was five constants: 80 / 70 / 75 / 65 / 60.
* ``evidence_chain.confidence_score`` was 85.

So ``GET /api/v1/workspaces/behaviour`` — which the ``/behaviour`` page renders —
showed the same numbers to every household, and showed them alongside the real
``/api/v1/behaviour/*`` endpoints that told a different story. Where the
household has too little recorded data to derive a metric, it is now reported as
unavailable rather than filled in.
"""

from datetime import date, timedelta
from typing import Any

from src.repositories.credit_card_repository import CreditCardRepository
from src.repositories.loan_repository import LoanRepository
from src.services.base import BaseService
from src.services.behaviour_service import BehaviourService

#: Below this many transactions no behaviour metric is derivable. One
#: transaction cannot express a spending pattern or a savings rate.
MIN_TRANSACTIONS_FOR_BEHAVIOUR = 3

#: How many months of transactions to aggregate the spending breakdown over.
SPENDING_PATTERN_MONTHS = 3

#: Components of the authoritative wellness score, mapped to the radar axes the
#: workspace renders. Each is a measured component; none is invented here.
WELLNESS_COMPONENT_TO_RADAR_AXIS = {
    "savings_behaviour": "saving_rate",
    "cashflow_health": "spending_discipline",
    "debt_health": "debt_health",
    "resilience": "investment_growth",
    "credit_behaviour": "credit_utilization",
}


class BehaviourWorkspaceService(BaseService):
    """Service for behaviour workspace aggregation."""

    def __init__(self, db_path: str | None = None) -> None:
        super().__init__(db_path)
        self.loan_repo = LoanRepository(self.db_path)
        self.card_repo = CreditCardRepository(self.db_path)
        self.behaviour_service = BehaviourService(self.db_path)

    def get_behaviour_summary(
        self,
        period: str = "monthly",
    ) -> dict[str, Any]:
        """Get behaviour summary for the workspace.

        Returns aggregated data matching BehaviourViewModel format.
        """
        from src.repositories.transaction_repository import TransactionRepository

        loans = self.loan_repo.list_loans()
        cards = self.card_repo.list_cards()
        total_outstanding = sum(loan.get("outstanding_paise", 0) for loan in loans)

        transactions = TransactionRepository(self.db_path).get_all_transactions()
        has_data = len(transactions) >= MIN_TRANSACTIONS_FOR_BEHAVIOUR

        wellness_score, wellness_band = self._wellness()
        spending_patterns = self._spending_patterns() if has_data else []
        savings_rate = self._savings_rate(period) if has_data else None
        debt_health = self._debt_health(total_outstanding)
        wellness_radar = self._wellness_radar()
        insights = self._insights(wellness_score, has_data)

        return {
            "wellness_score": wellness_score,
            "wellness_band": wellness_band,
            "spending_patterns": spending_patterns,
            "savings_rate": savings_rate,
            "debt_health": debt_health,
            "wellness_radar": wellness_radar,
            "insights": insights,
            "data_status": "available" if has_data else "insufficient_data",
            "evidence_chain": self._evidence_chain(
                loans=loans,
                cards=cards,
                total_outstanding=total_outstanding,
                transaction_count=len(transactions),
                wellness_score=wellness_score,
                wellness_band=wellness_band,
            ),
            "filters": {
                "period": period,
            },
            "navigation": {
                "deep_link": "/behaviour",
                "cross_references": {
                    "loans": "/loans",
                    "cards": "/cards",
                },
            },
        }

    # ===== Individual metrics, each from the authority =====

    def _wellness(self) -> tuple[int, str]:
        """The documented 0-100 wellness score and its band."""
        response = self.behaviour_service.get_wellness_score()
        return int(round(float(response.score))), response.band

    def _spending_patterns(self) -> list[dict[str, Any]]:
        """Category breakdown of real debits, with a measured month-over-month trend."""
        from src.repositories.transaction_repository import TransactionRepository

        transactions = TransactionRepository(self.db_path).get_all_transactions()
        this_month = _current_month_key()
        previous_month = _shifted_month_key(this_month, -1)

        def totals_for(month_key: str) -> dict[str, int]:
            per_category: dict[str, int] = {}
            for transaction in transactions:
                if transaction["type"] != "debit":
                    continue
                if str(transaction["date_iso"])[:7] != month_key:
                    continue
                category = (transaction.get("category") or "uncategorised").lower()
                per_category[category] = per_category.get(category, 0) + int(
                    transaction["amount_paise"]
                )
            return per_category

        current = totals_for(this_month)
        previous = totals_for(previous_month)

        total = sum(current.values())
        if total <= 0:
            return []

        patterns = []
        for category, amount in current.items():
            prior = previous.get(category, 0)
            change = round((amount - prior) / prior * 100, 2) if prior > 0 else 0.0
            patterns.append(
                {
                    "category": category,
                    "amount_paise": amount,
                    "percentage": round(amount / total * 100, 2),
                    # Direction only: rising, falling or flat. Derived, not assumed.
                    "trend": (
                        "rising"
                        if amount > prior
                        else "falling" if amount < prior else "stable"
                    ),
                    "month_over_month_change": change,
                }
            )

        return sorted(patterns, key=lambda pattern: -pattern["amount_paise"])

    def _savings_rate(self, period: str) -> dict[str, Any] | None:
        """Savings rate in basis points, from measured income and debits."""
        from src.repositories.transaction_repository import TransactionRepository

        in_window = [
            transaction
            for transaction in TransactionRepository(
                self.db_path
            ).get_all_transactions()
            if transaction["date_iso"] in _recent_dates(SPENDING_PATTERN_MONTHS)
        ]
        income = sum(int(t["amount_paise"]) for t in in_window if t["type"] == "credit")
        expenses = sum(
            int(t["amount_paise"]) for t in in_window if t["type"] == "debit"
        )
        if income <= 0:
            return None
        surplus = income - expenses
        return {
            # Basis points, matching the mapper's DTO and the ViewModel. A rate
            # expressed as a bare percentage in one place and bps in another is
            # the same class of unit bug as the wellness score.
            "savings_rate_bps": round(surplus / income * 10000),
            "income_paise": income,
            "savings_paise": surplus,
            "period": f"{SPENDING_PATTERN_MONTHS}M",
        }

    def _debt_health(self, total_outstanding: int) -> dict[str, Any]:
        """Debt health from the authority, in the mapper's declared shape."""
        from src.repositories.transaction_repository import TransactionRepository

        in_window = [
            transaction
            for transaction in TransactionRepository(
                self.db_path
            ).get_all_transactions()
            if transaction["date_iso"] in _recent_dates(SPENDING_PATTERN_MONTHS)
        ]
        total_income = sum(
            int(t["amount_paise"]) for t in in_window if t["type"] == "credit"
        )

        try:
            response = self.behaviour_service.get_debt_health()
            ratio = float(response.foir)
            return {
                "debt_to_income_bps": round(ratio * 10000),
                "total_debt_paise": total_outstanding,
                "total_income_paise": total_income,
                # Health score is the documented inverse of FOIR on 0-100, the
                # same 0-100 convention as the wellness score.
                "health_score": round(max(0.0, min(1.0, 1 - ratio)) * 100, 2),
            }
        except Exception:  # noqa: BLE001 - reported as unavailable, not invented
            return {
                "debt_to_income_bps": None,
                "total_debt_paise": total_outstanding,
                "total_income_paise": total_income,
                "health_score": None,
            }

    def _wellness_radar(self) -> list[dict[str, Any]]:
        """Radar axes mapped from the authority's measured components."""
        try:
            components = self.behaviour_service.get_wellness_score().components
        except Exception:  # noqa: BLE001
            return []

        axes: list[dict[str, Any]] = []
        for component, axis in WELLNESS_COMPONENT_TO_RADAR_AXIS.items():
            value = components.get(component)
            if value is None:
                continue
            axes.append(
                {
                    "dimension": axis,
                    "score": round(float(value), 2),
                    "max_score": 100,
                }
            )
        return axes

    def _insights(
        self, wellness_score: int | None, has_data: bool
    ) -> list[dict[str, Any]]:
        """Insights derived from the score the authority actually returned."""
        if not has_data:
            return [
                {
                    "type": "info",
                    "severity": "low",
                    "message": (
                        "Not enough recorded transactions to derive behaviour "
                        "metrics. Record some activity first."
                    ),
                }
            ]
        if wellness_score is None:
            return [
                {
                    "type": "info",
                    "severity": "low",
                    "message": "The behaviour authority did not produce a wellness score.",
                }
            ]
        if wellness_score < 50:
            return [
                {
                    "type": "alert",
                    "severity": "high",
                    "message": "Financial wellness score is low. Consider reducing debt and increasing savings.",
                }
            ]
        if wellness_score < 80:
            return [
                {
                    "type": "warning",
                    "severity": "medium",
                    "message": "Financial wellness score could be improved.",
                }
            ]
        return [
            {
                "type": "positive",
                "severity": "low",
                "message": "Financial wellness score is good.",
            }
        ]

    def _evidence_chain(
        self,
        *,
        loans: list[dict[str, Any]],
        cards: list[dict[str, Any]],
        total_outstanding: int,
        transaction_count: int,
        wellness_score: int | None,
        wellness_band: str | None,
    ) -> dict[str, Any]:
        """Traceability for what was measured and by which authority."""
        sources = [
            "transactions",
            "accounts",
            "loans",
            "credit_cards",
            "behaviour_service",
        ]
        evidence: list[dict[str, Any]] = [
            {
                "type": "financial_data",
                "summary": f"Total debt: ₹{total_outstanding / 100:,.2f}",
                "source": "loan_repository",
                "confidence": None,
            },
            {
                "type": "transaction_coverage",
                "summary": f"{transaction_count} recorded transaction(s) aggregated",
                "source": "transaction_repository",
                "confidence": None,
            },
        ]
        if wellness_score is not None:
            evidence.append(
                {
                    "type": "behaviour_metric",
                    "summary": (
                        f"Wellness score {wellness_score} (band {wellness_band}), "
                        f"from behaviour_service.get_wellness_score()"
                    ),
                    "source": "behaviour_service.get_wellness_score",
                    "confidence": None,
                }
            )
        return {
            "summary": (
                f"Behaviour analysis from {transaction_count} transactions, "
                f"{len(loans)} loans and {len(cards)} credit cards"
            ),
            "evidence": evidence,
            "calculation_steps": [
                {
                    "name": "Wellness Score",
                    "description": (
                        "Delegated to BehaviourService.get_wellness_score, which "
                        "derives it from measured monthly cashflow, savings, debt, "
                        "lifestyle and resilience components"
                    ),
                    "inputs": {"transaction_count": transaction_count},
                    "outputs": {
                        "wellness_score": wellness_score,
                        "band": wellness_band,
                    },
                }
            ],
            "source_references": sources,
            # Confidence is not a constant. It is null unless something derived
            # it; a hardcoded 85 asserted precision nothing established.
            "confidence_score": None,
        }


def _current_month_key() -> str:
    """The current calendar month as YYYY-MM."""
    return date.today().strftime("%Y-%m")


def _shifted_month_key(month_key: str, months: int) -> str:
    """Shift a YYYY-MM month key by whole calendar months."""
    year, month = (int(part) for part in month_key.split("-"))
    total = year * 12 + (month - 1) + months
    shifted_year, shifted_month = divmod(total, 12)
    return f"{shifted_year:04d}-{shifted_month + 1:02d}"


def _recent_dates(months: int) -> set[str]:
    """ISO dates within the last ``months`` calendar months, inclusive."""
    today = date.today()
    cutoff = date(today.year, today.month, 1)
    for _ in range(months - 1):
        cutoff = (cutoff - timedelta(days=1)).replace(day=1)
    span = (today - cutoff).days + 1
    return {(today - timedelta(days=offset)).isoformat() for offset in range(span)}
