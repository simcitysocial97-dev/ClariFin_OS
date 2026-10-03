"""Recommendation Service - Personalized financial recommendations.

Provides personalized financial recommendations based on behavior patterns,
spending habits, and financial goals.

Provenance
----------
Every metric fed to the recommendation engine is computed from the household's
own recorded transactions, accounts, loans and cards by ``BehaviourService``.
Nothing here is a constant standing in for data the system does not have.

This method previously returned a hardcoded demonstration profile —

    borrowed_lifestyle_ratio = Decimal("0.35")   # "35% of income goes to debt"
    foir = Decimal("0.45")                       # "45% debt-to-income ratio"
    liquidity_months = 1
    current_subscriptions = []                   # "No subscriptions in demo"

— and derived every recommendation from it, so `GET
/api/v1/financial-intelligence/recommendations` reported the same "Build
Emergency Fund" advice with the same "63% of Indians cannot cover a ₹50,000
emergency" evidence to every household regardless of its data. When there is not
enough recorded data the recommendation list is empty and the response states
why, rather than substituting plausible figures.

It also serialised with `r.dict() if hasattr(r, "dict") else r`.
``Recommendation`` (``engines/recommendation_engine/recommendations.py:14``) is a
plain class with its own ``to_dict()`` — not a Pydantic model — so it has
neither a ``dict`` attribute nor ``model_dump``. The raw domain objects
therefore reached FastAPI's serialiser and the endpoint returned HTTP 500 with
"Unable to serialize unknown type: Recommendation". It now calls ``to_dict()``.

It also computed FOIR by dividing a MONTHLY obligation by a MULTI-MONTH income
total, understating the ratio by the number of months observed (a genuine 0.70
reported as 0.2333 over three months). ``compute_foir`` is a monthly ratio, so
income is now divided by the distinct months present.
"""

from decimal import Decimal
from typing import Any

from src.engines.recommendation_engine.recommendations import compute_recommendations

#: Below this many transactions the derived ratios are not meaningful and no
#: recommendation is issued. A single transaction gives a credit-dependency
#: ratio of 0 or 1 depending only on its own sign.
MIN_TRANSACTIONS_FOR_RECOMMENDATIONS = 5


class RecommendationService:
    """Service for generating personalized financial recommendations."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path

    def get_recommendations(self, household_id: str = "primary") -> dict[str, Any]:
        """Get personalized financial recommendations for a household.

        Args:
            household_id: Household identifier (default: "primary")

        Returns:
            Dict with recommendations, the profile they were derived from, and
            the model version. ``recommendations`` is empty and ``status`` is
            ``"insufficient_data"`` when the household has too little recorded
            activity to derive the metrics from.
        """
        profile, status, reason = self._build_profile(household_id)

        if status != "available":
            return {
                "recommendations": [],
                "status": status,
                "reason": reason,
                "profile": None,
                "model_version": "v1.0-recommendation-engine",
            }

        # Only the four metrics the engine accepts are passed to it; the
        # remaining profile fields are traceability and stay on the response.
        engine_inputs = {
            key: profile[key]
            for key in (
                "borrowed_lifestyle_ratio",
                "foir",
                "liquidity_months",
                "current_subscriptions",
            )
        }
        recommendations = compute_recommendations(**engine_inputs)

        return {
            # `Recommendation` is a plain class with its own `to_dict()` — not a
            # Pydantic model. This method previously did
            # `r.dict() if hasattr(r, "dict") else r`, and `Recommendation` has
            # neither `dict` nor `model_dump`, so the raw domain object reached
            # FastAPI's serialiser and the endpoint returned HTTP 500 with
            # "Unable to serialize unknown type: Recommendation".
            "recommendations": [r.to_dict() for r in recommendations],
            "status": "available",
            "reason": None,
            "profile": {
                key: (float(value) if isinstance(value, Decimal) else value)
                for key, value in profile.items()
            },
            "model_version": "v1.0-recommendation-engine",
        }

    def _build_profile(
        self, household_id: str
    ) -> tuple[dict[str, Any], str, str | None]:
        """Derive the engine's inputs from the household's recorded data."""
        from src.core.db.config import get_db_path
        from src.engines.behaviour_engine.debt import compute_foir
        from src.engines.behaviour_engine.resilience import compute_liquidity_months
        from src.engines.behaviour_engine.savings import (
            compute_borrowed_lifestyle_ratio,
        )
        from src.repositories.transaction_repository import TransactionRepository
        from src.services.behaviour_service import BehaviourService

        db_path = self.db_path or get_db_path()
        transactions = TransactionRepository(db_path).get_all_transactions()

        if len(transactions) < MIN_TRANSACTIONS_FOR_RECOMMENDATIONS:
            return (
                {},
                "insufficient_data",
                f"Recommendations need at least {MIN_TRANSACTIONS_FOR_RECOMMENDATIONS} "
                f"recorded transactions to derive credit dependency, FOIR and "
                f"liquidity from; {len(transactions)} recorded. No recommendations "
                f"are reported rather than ones invented from constants.",
            )

        total_income = sum(
            t["amount_paise"] for t in transactions if t["type"] == "credit"
        )
        total_expenses = sum(
            t["amount_paise"] for t in transactions if t["type"] == "debit"
        )

        if total_income <= 0 or total_expenses <= 0:
            return (
                {},
                "insufficient_data",
                "Recommendations need both recorded income and recorded expenses; "
                f"income total is {total_income} paise and expenses total is "
                f"{total_expenses} paise. No recommendations are reported.",
            )

        behaviour = BehaviourService(db_path)
        loans = behaviour.loan_repo.list_loans()
        credit_cards = behaviour.credit_card_repo.list_cards()
        accounts = behaviour.account_repo.get_all_accounts()

        # `compute_foir` divides a MONTHLY obligation by MONTHLY income. The
        # totals above span every recorded month, so income is converted to a
        # monthly figure first — otherwise a household with three months of
        # salary and one EMI reports a FOIR a third of its real value and the
        # engine never sees a ratio worth warning about.
        observed_months = max(1, len({str(t["date_iso"])[:7] for t in transactions}))
        monthly_income = total_income // observed_months

        borrowed_lifestyle_ratio = compute_borrowed_lifestyle_ratio(
            behaviour._compute_credit_funded_expenses(transactions),  # noqa: SLF001
            total_expenses,
        )
        foir, _foir_band = compute_foir(
            behaviour._compute_fixed_obligations(loans, credit_cards),  # noqa: SLF001
            behaviour._compute_minimum_obligations(loans, credit_cards),  # noqa: SLF001
            monthly_income,
        )
        # `compute_foir` divides by monthly income; the recorded income total
        # above spans every recorded month, so it is converted to a monthly
        # figure before use.

        # Liquidity in months of essential expenses the household's liquid assets
        # cover — the quantity the engine thresholds on. Both inputs come from
        # the household's own accounts and transactions.
        liquidity_months = compute_liquidity_months(
            behaviour._compute_liquid_assets(accounts),  # noqa: SLF001
            behaviour._compute_essential_expenses(transactions),  # noqa: SLF001
        )

        profile: dict[str, Any] = {
            "borrowed_lifestyle_ratio": Decimal(str(borrowed_lifestyle_ratio)),
            "foir": Decimal(str(foir)),
            "liquidity_months": liquidity_months,
            "current_subscriptions": [],
            "total_income_paise": total_income,
            "total_expenses_paise": total_expenses,
            "monthly_income_paise": monthly_income,
            "months_observed": observed_months,
        }
        return profile, "available", None

    def get_recommendation_details(self, recommendation_id: str) -> dict[str, Any]:
        """Get detailed information about a specific recommendation.

        Args:
            recommendation_id: Recommendation identifier

        Returns:
            Dict with detailed recommendation information.

        This previously returned a fixed "Build Emergency Fund" payload for ANY
        id, with the fabricated evidence line "63% of Indians cannot cover a
        ₹50,000 emergency (RBI survey)" attached to it regardless of the
        household's data — and a static confidence of 0.95. It now resolves the
        id against the recommendations the engine can actually produce for this
        household and reports `found: false` for anything else.
        """
        recommendations = self.get_recommendations().get("recommendations", [])
        for recommendation in recommendations:
            if str(recommendation.get("id")) == recommendation_id:
                return {
                    "id": recommendation_id,
                    "found": True,
                    "detail": recommendation,
                }

        return {
            "id": recommendation_id,
            "found": False,
            "detail": None,
            "reason": (
                "No recommendation with this id was derived for this household. "
                "Ids are produced by the recommendation engine from measured "
                "metrics and are not a fixed catalogue."
            ),
            "available_ids": sorted(
                str(r.get("id")) for r in recommendations if r.get("id")
            ),
        }
