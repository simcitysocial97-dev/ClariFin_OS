"""
Insight Generator
=================

Generates deterministic, evidence-based behavioral insights.
No motivational fluff. No randomness.

Phase 3: Part of the Advanced Behavioral Intelligence Layer.
"""

from typing import Dict, List, Any


def generate_behavioral_insights(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate structured behavioral insights from behavior profile.
    
    Insights must:
    - Include quantitative evidence
    - Avoid generic motivational text
    - Reference computed metrics
    - Be deterministic
    
    Returns list of insight dicts with:
    - type: "warning" | "positive" | "info"
    - title: Short title
    - message: Detailed insight with numbers
    - metric: The key metric referenced
    """
    insights = []
    
    if not profile:
        return insights
    
    indices = profile.get("behavioral_indices", {})
    risk_signals = profile.get("risk_signals", {})
    temporal = profile.get("temporal_patterns", {})
    
    # Extract individual indices
    loss_aversion = indices.get("loss_aversion", {})
    impulsivity = indices.get("impulsivity", {})
    habit_stability = indices.get("habit_stability", {})
    financial_stress = indices.get("financial_stress", {})
    savings_discipline = indices.get("savings_discipline", {})
    
    # ============================================================
    # Loss Aversion Insights
    # ============================================================
    
    velocity = loss_aversion.get("post_income_velocity", 0)
    if velocity > 0.5:
        pct = int(velocity * 100)
        insights.append({
            "type": "warning",
            "title": "Post-Income Spending Spike",
            "message": f"{pct}% of income is spent within 72 hours of credit. This indicates loss aversion behavior—spending gains quickly.",
            "metric": "post_income_velocity",
            "value": velocity,
        })
    
    large_expenses = loss_aversion.get("large_expense_count", 0)
    if large_expenses > 3:
        insights.append({
            "type": "info",
            "title": "Large Expense Frequency",
            "message": f"{large_expenses} expenses exceeded 2x your median spend. Consider building a buffer for these events.",
            "metric": "large_expense_count",
            "value": large_expenses,
        })
    
    # ============================================================
    # Impulsivity Insights
    # ============================================================
    
    micro_ratio = impulsivity.get("micro_txn_ratio", 0)
    if micro_ratio > 0.4:
        pct = int(micro_ratio * 100)
        insights.append({
            "type": "warning",
            "title": "High Micro-Transaction Rate",
            "message": f"{pct}% of transactions are under ₹500. Small frequent spends often accumulate to significant amounts.",
            "metric": "micro_txn_ratio",
            "value": micro_ratio,
        })
    
    weekend_ratio = impulsivity.get("weekend_ratio", 1.0)
    if weekend_ratio > 1.3:
        pct = int((weekend_ratio - 1) * 100)
        insights.append({
            "type": "info",
            "title": "Weekend Spending Premium",
            "message": f"Weekend spending is {pct}% higher than weekday average. This may indicate discretionary impulse patterns.",
            "metric": "weekend_ratio",
            "value": weekend_ratio,
        })
    
    disc_ratio = impulsivity.get("discretionary_ratio", 0)
    if disc_ratio > 0.4:
        pct = int(disc_ratio * 100)
        insights.append({
            "type": "warning",
            "title": "High Discretionary Spending",
            "message": f"{pct}% of spending is in discretionary categories (dining, entertainment, shopping). Consider setting category limits.",
            "metric": "discretionary_ratio",
            "value": disc_ratio,
        })
    
    # ============================================================
    # Habit Stability Insights
    # ============================================================
    
    category_cv = habit_stability.get("category_cv", 0)
    if category_cv > 0.5:
        insights.append({
            "type": "warning",
            "title": "Unstable Spending Patterns",
            "message": f"Category spending varies {int(category_cv * 100)}% month-to-month. Higher consistency enables better planning.",
            "metric": "category_cv",
            "value": category_cv,
        })
    elif category_cv < 0.2:
        insights.append({
            "type": "positive",
            "title": "Consistent Spending Habits",
            "message": f"Category spending is highly stable (CV: {int(category_cv * 100)}%). This indicates strong financial discipline.",
            "metric": "category_cv",
            "value": category_cv,
        })
    
    recurring = habit_stability.get("recurring_count", 0)
    if recurring >= 5:
        insights.append({
            "type": "positive",
            "title": "Strong Recurring Pattern",
            "message": f"{recurring} recurring expense patterns detected. Predictable expenses reduce financial stress.",
            "metric": "recurring_count",
            "value": recurring,
        })
    
    # ============================================================
    # Financial Stress Insights
    # ============================================================
    
    buffer_days = financial_stress.get("buffer_days", 0)
    if buffer_days < 7:
        insights.append({
            "type": "warning",
            "title": "Low Financial Buffer",
            "message": f"Current buffer covers only {buffer_days:.1f} days of expenses. Target: 30 days minimum for financial security.",
            "metric": "buffer_days",
            "value": buffer_days,
        })
    elif buffer_days > 30:
        insights.append({
            "type": "positive",
            "title": "Healthy Financial Buffer",
            "message": f"Buffer covers {buffer_days:.0f} days of expenses. This provides strong financial resilience.",
            "metric": "buffer_days",
            "value": buffer_days,
        })
    
    credit_dep = financial_stress.get("credit_dependency", 0)
    if credit_dep > 1.2:
        insights.append({
            "type": "warning",
            "title": "High Credit Dependency",
            "message": f"Credit inflows are {int(credit_dep * 100)}% of debit outflows. This may indicate reliance on borrowed funds.",
            "metric": "credit_dependency",
            "value": credit_dep,
        })
    
    eom_ratio = financial_stress.get("eom_depletion_ratio", 0)
    if eom_ratio > 0.25:
        pct = int(eom_ratio * 100)
        insights.append({
            "type": "warning",
            "title": "End-of-Month Depletion",
            "message": f"{pct}% of monthly spending occurs in the last 5 days. This pattern often indicates cash flow stress.",
            "metric": "eom_depletion_ratio",
            "value": eom_ratio,
        })
    
    # ============================================================
    # Savings Discipline Insights
    # ============================================================
    
    savings_rate = savings_discipline.get("savings_rate", 0)
    if savings_rate < 0:
        insights.append({
            "type": "warning",
            "title": "Negative Savings Rate",
            "message": f"Monthly expenses exceed income by {int(abs(savings_rate) * 100)}%. This is unsustainable long-term.",
            "metric": "savings_rate",
            "value": savings_rate,
        })
    elif savings_rate > 0.2:
        insights.append({
            "type": "positive",
            "title": "Strong Savings Rate",
            "message": f"Saving {int(savings_rate * 100)}% of income monthly. This exceeds the recommended 20% target.",
            "metric": "savings_rate",
            "value": savings_rate,
        })
    
    momentum = savings_discipline.get("momentum", 0)
    if momentum < -0.1:
        insights.append({
            "type": "warning",
            "title": "Declining Savings Trend",
            "message": f"Savings rate dropped {int(abs(momentum) * 100)}% compared to previous period. Review recent expense increases.",
            "metric": "momentum",
            "value": momentum,
        })
    elif momentum > 0.1:
        insights.append({
            "type": "positive",
            "title": "Improving Savings Trend",
            "message": f"Savings rate improved {int(momentum * 100)}% compared to previous period. Maintain this trajectory.",
            "metric": "momentum",
            "value": momentum,
        })
    
    consistency = savings_discipline.get("consistency", 0)
    if consistency < 0.5:
        insights.append({
            "type": "info",
            "title": "Inconsistent Savings",
            "message": f"Only {int(consistency * 100)}% of months had positive savings. Aim for consistency over intensity.",
            "metric": "consistency",
            "value": consistency,
        })
    
    # ============================================================
    # India-Specific Risk Insights
    # ============================================================
    
    india_risks = risk_signals.get("india_specific", {})
    
    if india_risks.get("upi_micro_spend_flag"):
        insights.append({
            "type": "warning",
            "title": "UPI Micro-Spend Clustering",
            "message": "High frequency of small UPI transactions detected. These often accumulate unnoticed. Consider weekly spend reviews.",
            "metric": "upi_micro_spend_flag",
            "value": True,
        })
    
    if india_risks.get("gambling_flag"):
        count = india_risks.get("gambling_transaction_count", 0)
        insights.append({
            "type": "warning",
            "title": "Gaming/Gambling Transactions",
            "message": f"{count} transactions linked to gaming/gambling platforms detected. Monitor for addictive patterns.",
            "metric": "gambling_flag",
            "value": True,
        })
    
    if india_risks.get("loan_app_pattern_flag"):
        insights.append({
            "type": "warning",
            "title": "Loan App Activity",
            "message": "Multiple loan app credits detected. High-frequency borrowing may indicate financial stress.",
            "metric": "loan_app_pattern_flag",
            "value": True,
        })
    
    emi_ratio = india_risks.get("emi_ratio", 0)
    if emi_ratio > 0.4:
        pct = int(emi_ratio * 100)
        insights.append({
            "type": "warning",
            "title": "High EMI Burden",
            "message": f"EMI payments consume {pct}% of income. Recommended maximum is 40% for financial stability.",
            "metric": "emi_ratio",
            "value": emi_ratio,
        })
    
    # ============================================================
    # Temporal Pattern Insights
    # ============================================================
    
    trend = temporal.get("trend", 0)
    if trend > 0.1:
        insights.append({
            "type": "warning",
            "title": "Upward Spending Trend",
            "message": f"Spending trend is up {int(trend * 100)}% over the past week. Monitor for sustained increases.",
            "metric": "trend",
            "value": trend,
        })
    elif trend < -0.1:
        insights.append({
            "type": "positive",
            "title": "Downward Spending Trend",
            "message": f"Spending trend is down {int(abs(trend) * 100)}% over the past week. Keep this momentum.",
            "metric": "trend",
            "value": trend,
        })
    
    volatility = temporal.get("volatility", 0)
    if volatility > 0.8:
        insights.append({
            "type": "info",
            "title": "High Spending Volatility",
            "message": f"Daily spending varies significantly (CV: {int(volatility * 100)}%). Smoothing expenses can reduce stress.",
            "metric": "volatility",
            "value": volatility,
        })
    
    # ============================================================
    # Overall Health Score Insight
    # ============================================================
    
    health_score = profile.get("financial_health_score", 50)
    confidence = profile.get("confidence", 0)
    
    if health_score >= 70:
        insights.append({
            "type": "positive",
            "title": "Strong Financial Health",
            "message": f"Financial Health Score: {health_score:.0f}/100. Your financial behavior shows discipline and stability.",
            "metric": "financial_health_score",
            "value": health_score,
        })
    elif health_score < 40:
        insights.append({
            "type": "warning",
            "title": "Financial Health Needs Attention",
            "message": f"Financial Health Score: {health_score:.0f}/100. Multiple behavioral indicators suggest room for improvement.",
            "metric": "financial_health_score",
            "value": health_score,
        })
    
    if confidence < 0.5:
        insights.append({
            "type": "info",
            "title": "Limited Data for Analysis",
            "message": f"Confidence level: {int(confidence * 100)}%. More transaction history improves insight accuracy.",
            "metric": "confidence",
            "value": confidence,
        })
    
    return insights


def generate_summary_text(profile: Dict[str, Any]) -> str:
    """
    Generate a brief text summary of the behavioral profile.
    
    Returns a single paragraph summary.
    """
    if not profile:
        return "Insufficient data for behavioral analysis."
    
    health_score = profile.get("financial_health_score", 50)
    confidence = profile.get("confidence", 0)
    
    indices = profile.get("behavioral_indices", {})
    
    savings = indices.get("savings_discipline", {}).get("score", 0.5)
    impulse = indices.get("impulsivity", {}).get("score", 0.5)
    stress = indices.get("financial_stress", {}).get("score", 0.5)
    
    parts = []
    
    # Health score
    if health_score >= 70:
        parts.append("Your financial behavior shows strong discipline")
    elif health_score >= 50:
        parts.append("Your financial behavior is moderate with room for improvement")
    else:
        parts.append("Your financial behavior needs attention")
    
    # Savings
    if savings > 0.6:
        parts.append("savings discipline is strong")
    elif savings < 0.3:
        parts.append("savings discipline needs work")
    
    # Impulsivity
    if impulse > 0.7:
        parts.append("impulse spending is high")
    elif impulse < 0.3:
        parts.append("spending is well-controlled")
    
    # Stress
    if stress > 0.6:
        parts.append("financial stress indicators are elevated")
    
    # Confidence
    if confidence < 0.5:
        parts.append(f"(analysis based on limited data: {int(confidence * 100)}% confidence)")
    
    return ". ".join(parts) + "."