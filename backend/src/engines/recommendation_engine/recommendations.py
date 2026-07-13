"""Core recommendation logic for financial behaviour engine.

All monetary values are integers in paise (₹1.00 = 100 paise).
All functions are pure - no database access.
"""

from decimal import Decimal
from typing import Any, Literal

# Severity levels for recommendations
RecommendationSeverity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class Recommendation:
    """Recommendation model with title, reason, metric, severity, and suggested action.

    All recommendations are generated based on deterministic rules applied to
    financial behaviour metrics.
    """

    def __init__(
        self,
        title: str,
        reason: str,
        metric: str,
        severity: RecommendationSeverity,
        suggested_action: str,
    ) -> None:
        """Initialize a Recommendation.

        Args:
            title: Short title of the recommendation
            reason: Human-readable explanation of why this recommendation was triggered
            metric: The metric value that triggered this recommendation
            severity: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
            suggested_action: Actionable suggestion for the user to address the issue
        """
        self.title = title
        self.reason = reason
        self.metric = metric
        self.severity = severity
        self.suggested_action = suggested_action

    def to_dict(self) -> dict[str, Any]:
        """Convert recommendation to dictionary format."""
        return {
            "title": self.title,
            "reason": self.reason,
            "metric": self.metric,
            "severity": self.severity,
            "suggested_action": self.suggested_action,
        }


# Thresholds for recommendation triggers
DEBT_DEPENDENCY_THRESHOLD = Decimal("0.20")  # 20%
FOIR_THRESHOLD = Decimal("0.50")  # 50%
LIQUIDITY_MIN_MONTHS = 3
SUBSCRIPTION_GROWTH_THRESHOLD = Decimal("0.25")  # 25% increase


def check_debt_dependency(borrowed_lifestyle_ratio: Decimal) -> Recommendation | None:
    """Generate recommendation if debt dependency ratio exceeds 20%.

    Args:
        borrowed_lifestyle_ratio: Ratio of credit-funded expenses to total expenses (0-1+)

    Returns:
        Recommendation if ratio > 0.20, None otherwise
    """
    if borrowed_lifestyle_ratio > DEBT_DEPENDENCY_THRESHOLD:
        percentage = int(borrowed_lifestyle_ratio * 100)
        return Recommendation(
            title="Lifestyle Debt Alert",
            reason="Your lifestyle is partly funded by borrowed money",
            metric=f"{percentage}% of expenses are credit-funded",
            severity="HIGH",
            suggested_action="Create a debt repayment plan and reduce credit-funded spending to build financial stability",
        )
    return None


def check_foir(foir_ratio: Decimal) -> Recommendation | None:
    """Generate recommendation if FOIR exceeds 50%.

    Args:
        foir_ratio: Fixed Obligation to Income Ratio (0-1+)

    Returns:
        Recommendation if ratio > 0.50, None otherwise
    """
    if foir_ratio > FOIR_THRESHOLD:
        percentage = int(foir_ratio * 100)
        severity: RecommendationSeverity = "CRITICAL" if foir_ratio >= Decimal("0.6") else "HIGH"
        return Recommendation(
            title="High Fixed Obligations",
            reason="Fixed obligations are high",
            metric=f"{percentage}% of income goes to fixed obligations",
            severity=severity,
            suggested_action="Review and renegotiate loan terms, consider prepayment options to reduce monthly obligations",
        )
    return None


def check_liquidity(liquidity_months: int) -> Recommendation | None:
    """Generate recommendation if liquidity months is below 3.

    Args:
        liquidity_months: Number of months of essential expenses covered by liquid assets

    Returns:
        Recommendation if months < 3, None otherwise
    """
    if liquidity_months < LIQUIDITY_MIN_MONTHS:
        return Recommendation(
            title="Emergency Fund Needed",
            reason="Emergency fund required",
            metric=f"Only {liquidity_months} months of expenses covered",
            severity="HIGH" if liquidity_months < 1 else "MEDIUM",
            suggested_action="Build an emergency fund covering 3-6 months of essential expenses before taking on new debt",
        )
    return None


def detect_subscription_growth(
    current_subscriptions: list[dict[str, Any]],
    previous_subscriptions: list[dict[str, Any]] | None = None,
) -> Recommendation | None:
    """Detect subscription growth between periods.

    If there's no previous data, checks if current subscriptions exist and are substantial.

    Args:
        current_subscriptions: List of current subscription patterns with avg_amount_paise
        previous_subscriptions: Optional list of previous subscription patterns for comparison

    Returns:
        Recommendation if subscription growth detected or high subscription count exists
    """
    if not current_subscriptions:
        return None

    total_current = sum(sub.get("avg_amount_paise", 0) for sub in current_subscriptions)

    if previous_subscriptions is None:
        # No historical comparison - just check if subscription count is significant
        if len(current_subscriptions) >= 3:
            # Count is 3+ subscriptions without historical context
            return Recommendation(
                title="Review Subscriptions",
                reason="Multiple subscription services detected",
                metric=f"{len(current_subscriptions)} active subscriptions totaling ₹{total_current // 100}",
                severity="MEDIUM",
                suggested_action="Audit your subscription services and consider canceling unused or redundant ones",
            )
        return None

    total_previous = sum(sub.get("avg_amount_paise", 0) for sub in previous_subscriptions)

    if total_previous == 0:
        # Previous had no subscriptions but current does
        if len(current_subscriptions) >= 2:
            return Recommendation(
                title="Review Subscriptions",
                reason="New subscriptions detected",
                metric=f"{len(current_subscriptions)} new subscriptions adding ₹{total_current // 100}",
                severity="MEDIUM",
                suggested_action="Monitor new subscription services for usage value and consider canceling unused services",
            )
        return None

    # Calculate growth percentage
    if total_previous > 0:
        growth = Decimal(str(total_current - total_previous)) / Decimal(str(total_previous))
        if growth > SUBSCRIPTION_GROWTH_THRESHOLD:
            growth_pct = int(growth * 100)
            return Recommendation(
                title="Review Subscriptions",
                reason="Subscription spending is increasing rapidly",
                metric=f"Subscription spending increased by {growth_pct}%",
                severity="MEDIUM",
                suggested_action="Review and consolidate subscription services to control recurring expenses",
            )

    # Check for new subscriptions (not in previous period)
    previous_merchants = {sub.get("merchant", "") for sub in previous_subscriptions}
    new_subscriptions = [
        sub for sub in current_subscriptions
        if sub.get("merchant", "") not in previous_merchants
    ]

    if len(new_subscriptions) > 0:
        return Recommendation(
            title="Review Subscriptions",
            reason="New subscription services detected",
            metric=f"{len(new_subscriptions)} new subscriptions added",
            severity="LOW",
            suggested_action="Review new subscription services for value and necessity",
        )

    return None


def compute_recommendations(
    borrowed_lifestyle_ratio: Decimal,
    foir: Decimal,
    liquidity_months: int,
    current_subscriptions: list[dict[str, Any]],
    previous_subscriptions: list[dict[str, Any]] | None = None,
) -> list[Recommendation]:
    """Compute all recommendations based on financial behaviour metrics.

    Applies all recommendation rules and returns applicable recommendations.

    Args:
        borrowed_lifestyle_ratio: Ratio of credit-funded expenses (0-1+)
        foir: Fixed Obligation to Income Ratio (0-1+)
        liquidity_months: Number of months of essential expenses covered
        current_subscriptions: Current subscription patterns
        previous_subscriptions: Optional previous subscription patterns for comparison

    Returns:
        List of triggered recommendations sorted by severity (CRITICAL first)
    """
    recommendations: list[Recommendation] = []

    # Check debt dependency rule
    debt_rec = check_debt_dependency(borrowed_lifestyle_ratio)
    if debt_rec:
        recommendations.append(debt_rec)

    # Check FOIR rule
    foir_rec = check_foir(foir)
    if foir_rec:
        recommendations.append(foir_rec)

    # Check liquidity rule
    liquidity_rec = check_liquidity(liquidity_months)
    if liquidity_rec:
        recommendations.append(liquidity_rec)

    # Check subscription growth rule
    sub_rec = detect_subscription_growth(current_subscriptions, previous_subscriptions)
    if sub_rec:
        recommendations.append(sub_rec)

    # Sort by severity
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    recommendations.sort(key=lambda r: severity_order.get(r.severity, 4))

    return recommendations

