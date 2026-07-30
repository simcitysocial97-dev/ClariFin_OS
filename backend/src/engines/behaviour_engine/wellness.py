"""Financial Wellness Scoring for Behaviour Engine.

All monetary values are integers in paise (₹1.00 = 100 paise).
All functions are pure - no database access.

Computes composite financial wellness score based on multiple behavioral dimensions.
"""

from decimal import Decimal


def compute_wellness_score(
    cashflow_stability: Decimal,
    debt_cycle_score: int,
    savings_rate: Decimal,
    resilience_index: Decimal,
    lifestyle_inflation: Decimal,
    credit_revolver_ratio: Decimal,
    foir: Decimal,
) -> Decimal:
    """
    Compute composite financial wellness score (0-100).

    Formula: Weighted sum of normalized component scores.

    Weights:
    - 30% Cashflow Health: cashflow_stability (0-1)
    - 20% Debt Health: (1 - (debt_cycle_score / 100))
    - 15% Savings Behaviour: max(0, savings_rate)
    - 20% Resilience: resilience_index (0-1)
    - 10% Lifestyle Control: 1 - min(max(lifestyle_inflation, 0), 1)
    - 5% Credit Behaviour: 0.5*(1-revolver_ratio) + 0.5*(1 - min(foir,1))

    Parameters:
        cashflow_stability: Decimal from compute_cashflow_stability_index (0-1)
        debt_cycle_score: Integer from compute_debt_cycle_score (0-100)
        savings_rate: Decimal from compute_true_savings_rate (-1 to 1)
        resilience_index: Decimal from compute_resilience_index (0-1)
        lifestyle_inflation: Decimal from compute_lifestyle_inflation (-1 to ∞)
        credit_revolver_ratio: Decimal from compute_credit_revolver_ratio (0-1)
        foir: Decimal from compute_foir (Fixed Obligation to Income Ratio) (0-∞)

    Returns:
        Decimal wellness score between 0 and 100

    Note:
        - Negative savings rates are clamped to 0 (no negative contribution)
        - Lifestyle inflation > 1 is capped at 1 (maximum penalty)
        - FOIR > 1 is capped at 1 (maximum penalty)
        - Debt cycle score is inverted (lower score = better health)
    """
    # Normalize each component
    cashflow_component = cashflow_stability * Decimal("0.30")

    # Debt health: lower debt cycle score = better health
    debt_component = (
        Decimal("1") - (Decimal(str(debt_cycle_score)) / Decimal("100"))
    ) * Decimal("0.20")

    # Savings behaviour: clamp negative values to 0
    savings_component = max(Decimal("0"), savings_rate) * Decimal("0.15")

    # Resilience: already 0-1
    resilience_component = resilience_index * Decimal("0.20")

    # Lifestyle control: negative inflation = perfect (1), positive inflation capped at 1
    lifestyle_component = (
        Decimal("1") - min(max(lifestyle_inflation, Decimal("0")), Decimal("1"))
    ) * Decimal("0.10")

    # Credit behaviour: combines revolver ratio and FOIR
    credit_component = (
        Decimal("0.5") * (Decimal("1") - credit_revolver_ratio)
        + Decimal("0.5") * (Decimal("1") - min(foir, Decimal("1")))
    ) * Decimal("0.05")

    # Sum all components
    wellness_score = (
        cashflow_component
        + debt_component
        + savings_component
        + resilience_component
        + lifestyle_component
        + credit_component
    )

    # Convert to 0-100 scale and clamp
    wellness_score_100 = wellness_score * Decimal("100")
    return max(Decimal("0"), min(wellness_score_100, Decimal("100")))


def classify_wellness_band(score: Decimal) -> str:
    """
    Classify wellness score into bands.

    Bands:
    - 90-100: Excellent
    - 75-89: Healthy
    - 50-74: Developing
    - 25-49: Risk
    - <25: Critical

    Parameters:
        score: Decimal wellness score (0-100)

    Returns:
        String classification band
    """
    if score >= Decimal("90"):
        return "Excellent"
    elif score >= Decimal("75"):
        return "Healthy"
    elif score >= Decimal("50"):
        return "Developing"
    elif score >= Decimal("25"):
        return "Risk"
    else:
        return "Critical"
