"""
Nudge Engine
============

Rules-based behavioral suggestion engine.
Non-intrusive, deterministic nudges based on behavioral profile.

Phase 3: Part of the Advanced Behavioral Intelligence Layer.

Based on behavioral economics principles:
- Default bias
- Friction mechanisms
- Goal framing
- Loss aversion messaging
"""

from typing import Any


def generate_nudges(profile: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Generate behavioral nudges based on profile.

    Rules-based deterministic suggestions.
    No push notifications - return JSON only.

    Returns list of nudge dicts with:
    - type: "habit" | "friction" | "goal" | "awareness"
    - priority: 1 (high) | 2 (medium) | 3 (low)
    - title: Short title
    - message: Actionable suggestion
    - trigger: The condition that triggered this nudge
    """
    nudges: list[dict[str, Any]] = []

    if not profile:
        return nudges

    indices = profile.get("behavioral_indices", {})
    risk_signals = profile.get("risk_signals", {})

    # Extract indices
    loss_aversion = indices.get("loss_aversion", {})
    impulsivity = indices.get("impulsivity", {})
    habit_stability = indices.get("habit_stability", {})
    financial_stress = indices.get("financial_stress", {})
    savings_discipline = indices.get("savings_discipline", {})

    # ============================================================
    # High Impulsivity Nudges
    # ============================================================

    impulse_score = impulsivity.get("score", 0)
    if impulse_score > 0.7:
        nudges.append(
            {
                "type": "friction",
                "priority": 1,
                "title": "Implement 24-Hour Rule",
                "message": "Your impulse score is high. Before any discretionary purchase over ₹500, wait 24 hours. This simple friction reduces impulse spending by 30%.",
                "trigger": f"impulse_score > 0.7 (current: {impulse_score:.2f})",
                "actionable": True,
            }
        )

    micro_ratio = impulsivity.get("micro_txn_ratio", 0)
    if micro_ratio > 0.5:
        nudges.append(
            {
                "type": "awareness",
                "priority": 2,
                "title": "Track Micro-Transactions",
                "message": f"{int(micro_ratio * 100)}% of your transactions are under ₹500. Set a daily micro-spend limit (e.g., ₹200/day) and track weekly totals.",
                "trigger": f"micro_txn_ratio > 0.5 (current: {micro_ratio:.2f})",
                "actionable": True,
            }
        )

    # ============================================================
    # Low Savings Nudges
    # ============================================================

    savings_score = savings_discipline.get("score", 0)
    if savings_score < 0.3:
        nudges.append(
            {
                "type": "habit",
                "priority": 1,
                "title": "Automate Savings Transfer",
                "message": "Set up an automatic transfer of 10% of income to a separate savings account on payday. Automation removes the decision friction.",
                "trigger": f"savings_score < 0.3 (current: {savings_score:.2f})",
                "actionable": True,
            }
        )

    savings_rate = savings_discipline.get("savings_rate", 0)
    if savings_rate < 0.1:
        nudges.append(
            {
                "type": "goal",
                "priority": 2,
                "title": "Start with 10% Target",
                "message": "Your current savings rate is below 10%. Start with a modest 10% target and increase by 1% each month. Small wins build momentum.",
                "trigger": f"savings_rate < 0.1 (current: {savings_rate:.2f})",
                "actionable": True,
            }
        )

    # ============================================================
    # High Stress Nudges
    # ============================================================

    stress_score = financial_stress.get("score", 0)
    buffer_days = financial_stress.get("buffer_days", 0)

    if stress_score > 0.6:
        nudges.append(
            {
                "type": "goal",
                "priority": 1,
                "title": "Build Emergency Buffer",
                "message": f"Your financial stress indicators are elevated. Target a 30-day expense buffer. Current: {buffer_days:.0f} days. Start with a 7-day goal.",
                "trigger": f"stress_score > 0.6 (current: {stress_score:.2f})",
                "actionable": True,
            }
        )

    if buffer_days < 7:
        nudges.append(
            {
                "type": "friction",
                "priority": 1,
                "title": "Pause Non-Essential Spending",
                "message": f"Your buffer covers only {buffer_days:.0f} days. Consider a 2-week pause on discretionary spending to build a safety cushion.",
                "trigger": f"buffer_days < 7 (current: {buffer_days:.0f})",
                "actionable": True,
            }
        )

    # ============================================================
    # Loss Aversion Nudges
    # ============================================================

    velocity = loss_aversion.get("post_income_velocity", 0)
    if velocity > 0.6:
        nudges.append(
            {
                "type": "friction",
                "priority": 2,
                "title": "Delay Post-Income Spending",
                "message": f"You spend {int(velocity * 100)}% of income within 72 hours. Implement a 48-hour waiting period after salary credit before any discretionary purchase.",
                "trigger": f"post_income_velocity > 0.6 (current: {velocity:.2f})",
                "actionable": True,
            }
        )

    # ============================================================
    # Habit Stability Nudges
    # ============================================================

    category_cv = habit_stability.get("category_cv", 0)
    if category_cv > 0.6:
        nudges.append(
            {
                "type": "habit",
                "priority": 2,
                "title": "Set Category Budgets",
                "message": f"Your spending varies {int(category_cv * 100)}% month-to-month. Set fixed monthly budgets for top 3 categories to build predictability.",
                "trigger": f"category_cv > 0.6 (current: {category_cv:.2f})",
                "actionable": True,
            }
        )

    recurring = habit_stability.get("recurring_count", 0)
    if recurring < 3:
        nudges.append(
            {
                "type": "awareness",
                "priority": 3,
                "title": "Identify Recurring Expenses",
                "message": "Few recurring expense patterns detected. Review your subscriptions and fixed costs. Predictable expenses reduce decision fatigue.",
                "trigger": f"recurring_count < 3 (current: {recurring})",
                "actionable": True,
            }
        )

    # ============================================================
    # India-Specific Risk Nudges
    # ============================================================

    india_risks = risk_signals.get("india_specific", {})

    if india_risks.get("upi_micro_spend_flag"):
        nudges.append(
            {
                "type": "friction",
                "priority": 2,
                "title": "Set UPI Daily Limit",
                "message": "High UPI micro-spend activity detected. Consider setting a daily UPI spend limit in your banking app. Many banks offer this feature.",
                "trigger": "upi_micro_spend_flag = True",
                "actionable": True,
            }
        )

    if india_risks.get("gambling_flag"):
        nudges.append(
            {
                "type": "awareness",
                "priority": 1,
                "title": "Review Gaming Spending",
                "message": "Gaming/gambling transactions detected. These platforms are designed for engagement. Set strict monthly limits or consider self-exclusion options.",
                "trigger": "gambling_flag = True",
                "actionable": True,
            }
        )

    if india_risks.get("loan_app_pattern_flag"):
        nudges.append(
            {
                "type": "awareness",
                "priority": 1,
                "title": "Review Loan App Usage",
                "message": "Multiple loan app credits detected. These often carry high interest rates. Consider consolidating or building an alternative credit buffer.",
                "trigger": "loan_app_pattern_flag = True",
                "actionable": True,
            }
        )

    emi_ratio = india_risks.get("emi_ratio", 0)
    if emi_ratio > 0.5:
        nudges.append(
            {
                "type": "goal",
                "priority": 1,
                "title": "Reduce EMI Burden",
                "message": f"EMI payments are {int(emi_ratio * 100)}% of income. Target: under 40%. Consider prepaying high-interest loans or refinancing.",
                "trigger": f"emi_ratio > 0.5 (current: {emi_ratio:.2f})",
                "actionable": True,
            }
        )

    # ============================================================
    # Positive Reinforcement Nudges
    # ============================================================

    health_score = profile.get("financial_health_score", 50)

    if health_score >= 70:
        nudges.append(
            {
                "type": "goal",
                "priority": 3,
                "title": "Set Stretch Goals",
                "message": f"Your financial health score is {health_score:.0f}/100. You're ready for stretch goals: increase savings rate by 5% or build a 6-month emergency fund.",
                "trigger": f"health_score >= 70 (current: {health_score:.0f})",
                "actionable": True,
            }
        )

    if savings_score > 0.7:
        nudges.append(
            {
                "type": "goal",
                "priority": 3,
                "title": "Consider Investment",
                "message": "Your savings discipline is strong. Consider moving excess savings to investment vehicles (FD, mutual funds) for better returns.",
                "trigger": f"savings_score > 0.7 (current: {savings_score:.2f})",
                "actionable": True,
            }
        )

    # Sort by priority
    nudges.sort(key=lambda x: x["priority"])

    return nudges


def get_top_nudge(profile: dict[str, Any]) -> dict[str, Any]:
    """
    Get the single highest priority nudge.

    Returns the most important actionable suggestion.
    """
    nudges = generate_nudges(profile)

    if not nudges:
        return {
            "type": "info",
            "priority": 3,
            "title": "Keep Tracking",
            "message": "Continue tracking your transactions. More data enables better insights.",
            "trigger": "insufficient_data",
            "actionable": False,
        }

    return nudges[0]


def get_nudge_summary(profile: dict[str, Any]) -> str:
    """
    Get a brief text summary of recommended actions.

    Returns a single paragraph with top 3 suggestions.
    """
    nudges = generate_nudges(profile)[:3]

    if not nudges:
        return "Continue tracking your financial transactions for better insights."

    actions = [n["title"] for n in nudges]

    if len(actions) == 1:
        return f"Recommended action: {actions[0]}."
    elif len(actions) == 2:
        return f"Recommended actions: {actions[0]} and {actions[1]}."
    else:
        return f"Top 3 actions: {', '.join(actions[:-1])}, and {actions[-1]}."
