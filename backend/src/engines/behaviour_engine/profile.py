"""Financial personality classification for behaviour engine.

All monetary values are integers in paise (₹1.00 = 100 paise).
All functions are pure - no database access.

Classifies users into one of five financial personality profiles based on
their spending and saving behaviors.

Profiles:
- SAVER: High savings rate, low credit dependency
- BALANCED: Moderate savings, balanced spending
- SPENDER: High discretionary spending, impulse purchases
- DEBT_OPTIMIZER: Uses credit responsibly with positive savings
- DEBT_DEPENDENT: High credit lifestyle, recurring debt
"""

from decimal import Decimal

# ============================================================
# Thresholds (Configurable Constants)
# ============================================================

# SAVER: Savings rate threshold
SAVER_MIN_SAVINGS_RATE = Decimal("0.20")  # 20%

# SAVER confidence bonus thresholds
SAVER_STRONG_SAVINGS_THRESHOLD = Decimal("0.25")  # Strong if > 25%

# DEBT_DEPENDENT: Borrowed lifestyle ratio threshold
DEBT_DEPENDENT_MIN_BORROWED_RATIO = Decimal("0.20")  # 20%

# DEBT_DEPENDENT revolver threshold (indicates recurring debt extraction)
DEBT_DEPENDENT_MAX_REVOLVER_FOR_POSITIVE = Decimal("0.5")  # High revolver = dependent
DEBT_DEPENDENT_SAVINGS_THRESHOLD = Decimal("0.10")  # Low savings + high revolver

# SPENDER: Discretionary spending thresholds
SPENDER_MIN_DISCRETIONARY_RATIO = Decimal("0.40")  # 40% of expenses
SPENDER_MIN_IMPULSE_RATIO = Decimal("0.30")  # 30% impulse transactions
SPENDER_MIN_LIFESTYLE_CREEP = Decimal("0.50")  # Significant creep

# DEBT_OPTIMIZER: Responsible debt usage
DEBT_OPTIMIZER_MIN_REVOLVER_RATIO = Decimal("0.01")  # Some credit usage
DEBT_OPTIMIZER_MAX_REVOLVER_RATIO = Decimal("0.20")  # Low revolver = pays in full
DEBT_OPTIMIZER_MIN_SAVINGS_RATE = Decimal("0.05")  # Positive savings

# Confidence calculation constants
CONFIDENCE_BASE = Decimal("0.5")
CONFIDENCE_STRONG_CONDITION_BONUS = Decimal("0.10")
CONFIDENCE_SECONDARY_CONDITION_BONUS = Decimal("0.05")
CONFIDENCE_TRANSACTION_VOLUME_BONUS = Decimal(
    "0.05"
)  # Per 100 transactions, capped at 0.2


# ============================================================
# Classification Function
# ============================================================


def classify_financial_personality(
    savings_rate: Decimal,
    borrowed_lifestyle_ratio: Decimal,
    credit_revolver_ratio: Decimal,
    discretionary_spending_ratio: Decimal,
    impulse_transaction_ratio: Decimal,
    lifestyle_creep_index: Decimal,
    transaction_count: int,
) -> tuple[str, Decimal, str]:
    """
    Classify financial personality based on behavioral metrics.

    Classification priority (checked in order):
    1. DEBT_DEPENDENT - High credit lifestyle or recurring debt extraction
    2. SAVER - High savings rate with no debt dependency
    3. DEBT_OPTIMIZER - Uses debt responsibly with positive savings
    4. SPENDER - High discretionary spending and impulse purchases
    5. BALANCED - Default when no clear pattern emerges

    Parameters:
        savings_rate: Decimal from compute_true_savings_rate (0.20 = 20% savings)
        borrowed_lifestyle_ratio: Decimal from compute_borrowed_lifestyle_ratio
        credit_revolver_ratio: Decimal from compute_credit_revolver_ratio
        discretionary_spending_ratio: Proportion of expenses on non-essential categories
        impulse_transaction_ratio: Ratio of impulse transactions to total transactions
        lifestyle_creep_index: Decimal from compute_lifestyle_creep_index
        transaction_count: Number of transactions analyzed (for confidence)

    Returns:
        Tuple of (profile: str, confidence: Decimal, explanation: str)
        Profile is one of: "SAVER", "BALANCED", "SPENDER", "DEBT_OPTIMIZER", "DEBT_DEPENDENT"
    """
    # Check DEBT_DEPENDENT first (highest priority)
    if _is_debt_dependent(
        borrowed_lifestyle_ratio, credit_revolver_ratio, savings_rate
    ):
        return _build_result(
            "DEBT_DEPENDENT",
            savings_rate,
            borrowed_lifestyle_ratio,
            credit_revolver_ratio,
            transaction_count,
        )

    # Check SAVER
    if _is_saver(savings_rate, borrowed_lifestyle_ratio, credit_revolver_ratio):
        return _build_result(
            "SAVER",
            savings_rate,
            borrowed_lifestyle_ratio,
            credit_revolver_ratio,
            transaction_count,
        )

    # Check DEBT_OPTIMIZER
    if _is_debt_optimizer(savings_rate, credit_revolver_ratio):
        return _build_result(
            "DEBT_OPTIMIZER",
            savings_rate,
            borrowed_lifestyle_ratio,
            credit_revolver_ratio,
            transaction_count,
        )

    # Check SPENDER
    if _is_spender(
        discretionary_spending_ratio, impulse_transaction_ratio, lifestyle_creep_index
    ):
        return _build_result(
            "SPENDER",
            savings_rate,
            borrowed_lifestyle_ratio,
            credit_revolver_ratio,
            transaction_count,
            discretionary_spending_ratio,
            impulse_transaction_ratio,
        )

    # Default to BALANCED
    return _build_result(
        "BALANCED",
        savings_rate,
        borrowed_lifestyle_ratio,
        credit_revolver_ratio,
        transaction_count,
    )


# ============================================================
# Profile Detection Helpers
# ============================================================


def _is_debt_dependent(
    borrowed_lifestyle_ratio: Decimal,
    credit_revolver_ratio: Decimal,
    savings_rate: Decimal,
) -> bool:
    """
    Check if user is DEBT_DEPENDENT.

    Conditions:
    - Borrowed lifestyle ratio > 20% (significant credit-funded lifestyle)
    - OR high revolver ratio + low savings (recurring debt extraction pattern)
    """
    # High credit lifestyle
    if borrowed_lifestyle_ratio > DEBT_DEPENDENT_MIN_BORROWED_RATIO:
        return True

    # Recurring debt extraction: high revolver + low savings
    return bool(
        credit_revolver_ratio >= DEBT_DEPENDENT_MAX_REVOLVER_FOR_POSITIVE
        and savings_rate < DEBT_DEPENDENT_SAVINGS_THRESHOLD
    )


def _is_saver(
    savings_rate: Decimal,
    borrowed_lifestyle_ratio: Decimal,
    credit_revolver_ratio: Decimal,
) -> bool:
    """
    Check if user is SAVER.

    Conditions:
    - Savings rate > 20%
    - AND no significant debt creation (low borrowed lifestyle ratio)
    - AND pays credit in full (low revolver ratio)
    """
    if savings_rate <= SAVER_MIN_SAVINGS_RATE:
        return False

    # Must not be debt-dependent
    if borrowed_lifestyle_ratio >= DEBT_DEPENDENT_MIN_BORROWED_RATIO:
        return False

    # Should pay credit in full (low revolver)
    return not credit_revolver_ratio >= DEBT_OPTIMIZER_MAX_REVOLVER_RATIO


def _is_debt_optimizer(
    savings_rate: Decimal,
    credit_revolver_ratio: Decimal,
) -> bool:
    """
    Check if user is DEBT_OPTIMIZER.

    Conditions:
    - Uses some credit (revolver > 0)
    - But pays responsibly (revolver < 20%)
    - AND has positive savings
    """
    # Some credit usage but pays in full
    if credit_revolver_ratio < DEBT_OPTIMIZER_MIN_REVOLVER_RATIO:
        return False  # Not using credit at all

    if credit_revolver_ratio >= DEBT_OPTIMIZER_MAX_REVOLVER_RATIO:
        return False  # Revolver too high - not paying in full

    # Must have positive savings
    return not savings_rate <= Decimal("0")


def _is_spender(
    discretionary_spending_ratio: Decimal,
    impulse_transaction_ratio: Decimal,
    lifestyle_creep_index: Decimal,
) -> bool:
    """
    Check if user is SPENDER.

    Conditions:
    - High discretionary spending (> 40% of expenses)
    - OR high impulse transaction ratio (> 30%)
    - OR high lifestyle creep (> 50%)
    """
    # High discretionary spending
    if discretionary_spending_ratio >= SPENDER_MIN_DISCRETIONARY_RATIO:
        return True

    # High impulse purchases
    if impulse_transaction_ratio >= SPENDER_MIN_IMPULSE_RATIO:
        return True

    # Significant lifestyle creep
    return lifestyle_creep_index >= SPENDER_MIN_LIFESTYLE_CREEP


# ============================================================
# Result Builder
# ============================================================


def _build_result(
    profile: str,
    savings_rate: Decimal,
    borrowed_lifestyle_ratio: Decimal,
    credit_revolver_ratio: Decimal,
    transaction_count: int,
    discretionary_spending_ratio: Decimal | None = None,
    impulse_transaction_ratio: Decimal | None = None,
) -> tuple[str, Decimal, str]:
    """Build the result tuple with confidence and explanation."""
    confidence = _calculate_confidence(
        profile,
        savings_rate,
        borrowed_lifestyle_ratio,
        credit_revolver_ratio,
        transaction_count,
    )
    explanation = _build_explanation(
        profile,
        savings_rate,
        borrowed_lifestyle_ratio,
        credit_revolver_ratio,
        discretionary_spending_ratio,
        impulse_transaction_ratio,
    )
    return (profile, confidence, explanation)


def _calculate_confidence(
    profile: str,
    savings_rate: Decimal,
    borrowed_lifestyle_ratio: Decimal,
    credit_revolver_ratio: Decimal,
    transaction_count: int,
) -> Decimal:
    """
    Calculate confidence score for the classification.

    Formula:
    - Base: 0.5
    - +0.10 if primary condition strongly met
    - +0.05 if secondary conditions also met
    - +0.05 per 100 transactions (capped at +0.20)
    - Clamped between 0.0 and 1.0
    """
    score = CONFIDENCE_BASE

    # Strong condition bonus
    if profile == "SAVER" and savings_rate >= SAVER_STRONG_SAVINGS_THRESHOLD:
        score += CONFIDENCE_STRONG_CONDITION_BONUS
    elif profile == "DEBT_DEPENDENT":
        if borrowed_lifestyle_ratio >= Decimal(
            "0.30"
        ) or credit_revolver_ratio >= Decimal("0.60"):
            score += CONFIDENCE_STRONG_CONDITION_BONUS
    elif profile == "SPENDER":
        if borrowed_lifestyle_ratio > Decimal("0.30"):
            score += CONFIDENCE_STRONG_CONDITION_BONUS  # Combined stressor
    elif profile == "DEBT_OPTIMIZER":
        # Moderate confidence for this profile
        score += CONFIDENCE_SECONDARY_CONDITION_BONUS
    # BALANCED: base confidence is appropriate

    # Secondary condition bonus
    if profile in ("SAVER", "DEBT_OPTIMIZER") and credit_revolver_ratio > Decimal("0"):
        score += CONFIDENCE_SECONDARY_CONDITION_BONUS
    elif profile == "DEBT_DEPENDENT" and savings_rate < Decimal("0"):
        score += CONFIDENCE_SECONDARY_CONDITION_BONUS  # Combined negative pattern

    # Transaction volume bonus (more data = higher confidence)
    volume_bonus = min(
        CONFIDENCE_TRANSACTION_VOLUME_BONUS * (transaction_count // 100),
        Decimal("0.20"),
    )
    score += volume_bonus

    # Clamp between 0 and 1
    return max(Decimal("0"), min(Decimal("1"), score))


def _build_explanation(
    profile: str,
    savings_rate: Decimal,
    borrowed_lifestyle_ratio: Decimal,
    credit_revolver_ratio: Decimal,
    discretionary_spending_ratio: Decimal | None = None,
    impulse_transaction_ratio: Decimal | None = None,
) -> str:
    """Build human-readable explanation for the classification."""
    savings_pct = round(savings_rate * 100, 1)
    borrowed_pct = round(borrowed_lifestyle_ratio * 100, 1)
    revolver_pct = round(credit_revolver_ratio * 100, 1)

    if profile == "SAVER":
        return (
            f"You are classified as SAVER because your savings rate is {savings_pct}% "
            f"(above {int(SAVER_MIN_SAVINGS_RATE * 100)}% threshold) and you do not rely "
            f"on credit for lifestyle expenses (borrowed lifestyle ratio {borrowed_pct}%)."
        )

    elif profile == "DEBT_DEPENDENT":
        if borrowed_lifestyle_ratio >= DEBT_DEPENDENT_MIN_BORROWED_RATIO:
            return (
                f"You are classified as DEBT_DEPENDENT because your borrowed lifestyle ratio "
                f"is {borrowed_pct}% (above {int(DEBT_DEPENDENT_MIN_BORROWED_RATIO * 100)}% threshold), "
                f"indicating significant reliance on credit for daily expenses."
            )
        else:
            return (
                f"You are classified as DEBT_DEPENDENT due to recurring debt extraction "
                f"(revolver ratio {revolver_pct}% with savings rate {savings_pct}%), "
                f"suggesting reliance on revolving credit."
            )

    elif profile == "DEBT_OPTIMIZER":
        return (
            f"You are classified as DEBT_OPTIMIZER because you use credit responsibly "
            f"(revolver ratio {revolver_pct}%, indicating primarily on-time payments) "
            f"while maintaining positive savings ({savings_pct}%)."
        )

    elif profile == "SPENDER":
        reasons = []
        if (
            discretionary_spending_ratio
            and discretionary_spending_ratio >= SPENDER_MIN_DISCRETIONARY_RATIO
        ):
            disc_pct = round(discretionary_spending_ratio * 100, 1)
            reasons.append(f"discretionary spending ratio {disc_pct}%")
        if (
            impulse_transaction_ratio
            and impulse_transaction_ratio >= SPENDER_MIN_IMPULSE_RATIO
        ):
            impulse_pct = round(impulse_transaction_ratio * 100, 1)
            reasons.append(f"impulse transaction ratio {impulse_pct}%")

        if reasons:
            return (
                f"You are classified as SPENDER due to high {(' and '.join(reasons))}, "
                f"indicating elevated discretionary spending patterns."
            )
        else:
            return (
                "You are classified as SPENDER due to elevated discretionary spending "
                "and lifestyle creep patterns."
            )

    else:  # BALANCED
        return (
            f"You are classified as BALANCED with savings rate {savings_pct}%, "
            f"borrowed lifestyle ratio {borrowed_pct}%, and revolver ratio {revolver_pct}%, "
            f"indicating balanced financial behavior without extreme patterns."
        )
