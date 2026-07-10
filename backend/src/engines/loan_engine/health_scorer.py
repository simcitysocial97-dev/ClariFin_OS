"""
Health Scorer
=============
Computes comprehensive loan health scores with actionable insights.

Formula:
Health_Score = 0.2 × DTI_Score + 0.2 × Utilization_Score + 0.2 × Stress_Score
             + 0.2 × Payment_Score + 0.2 × Credit_Score

INVARIANT 1-6 enforced throughout.
"""

from src.engines.loan_engine.types import HealthScoreResult

MAX_DTI: int = 40  # 40%
MIN_CREDIT_SCORE: int = 300
MAX_CREDIT_SCORE: int = 900

def compute_dti_score(
    monthly_emi_paise: int,
    monthly_income_paise: int,
    other_debt_paise: int = 0,
) -> float:
    """
    Compute DTI (Debt-to-Income) score component.

    DTI = (Total_monthly_EMI + other_debt_payments) / Monthly_income × 100

    Score = max(0, (Max_DTI - Current_DTI) / Max_DTI) × 100
    """
    if monthly_income_paise <= 0:
        return 0.0

    dti = ((monthly_emi_paise + other_debt_paise) / monthly_income_paise) * 100
    # Clamp DTI to 0-100 range to prevent negative scores
    score = max(0.0, min(1.0, (MAX_DTI - min(dti, MAX_DTI)) / MAX_DTI)) * 100
    return round(score, 2)

def compute_utilization_score(
    sanction_amount_paise: int,
    outstanding_paise: int,
    ltv_ratio: float = 0.0,  # Loan-to-value ratio (0-1)
) -> float:
    """
    Compute utilization score component.

    Utilization = Outstanding / Sanction_Amount
    Score = (1 - Utilization) × 100

    Includes LTV ratio for secured loans (e.g., home loans)
    """
    if sanction_amount_paise <= 0:
        return 100.0

    utilization = outstanding_paise / sanction_amount_paise
    utilization_score = (1 - min(utilization, 1.0)) * 100

    # Adjust for LTV (higher LTV = higher risk)
    if ltv_ratio > 0:
        ltv_penalty = min(20.0, ltv_ratio * 20)  # Max 20% penalty for high LTV
        utilization_score = max(0.0, utilization_score - ltv_penalty)

    return round(utilization_score, 2)

def compute_stress_score(
    missed_payments: int,
    total_payments: int,
    days_overdue_avg: int = 0,
    recent_missed: int = 0,  # Missed payments in last 6 months
) -> float:
    """
    Compute stress score component.

    Stress_Score = 100 - (Missed_payment_rate × 50 + Recent_missed × 10 + Days_overdue × 0.5)
    """
    if total_payments <= 0:
        return 100.0

    missed_rate = missed_payments / total_payments
    days_penalty = min(20.0, days_overdue_avg * 0.5)  # Max 20% penalty for days overdue
    recent_penalty = min(30.0, recent_missed * 10)  # Max 30% penalty for recent misses

    score = 100 - (missed_rate * 50 + days_penalty + recent_penalty)
    return round(max(0.0, score), 2)

def compute_payment_score(
    months_since_start: int,
    payment_consistency: float = 1.0,  # 0-1, 1 = perfect consistency
    early_payments: int = 0,  # Number of early payments
) -> float:
    """
    Compute payment score component.

    Payment_Score = (Months_since_start / 12 × 0.5 + Payment_consistency × 30 + Early_payments × 2) × 2
    Capped at 100.
    """
    months_score = min(50.0, months_since_start * 0.5)  # Max 50 for 10+ years
    consistency_score = payment_consistency * 30
    early_score = min(20.0, early_payments * 2)  # Max 20 for 10+ early payments

    score = (months_score + consistency_score + early_score) * 2
    return round(min(100.0, score), 2)

def compute_credit_score_component(
    credit_score: int,
) -> float:
    """
    Compute credit score component.

    Score = (Credit_Score - Min_Score) / (Max_Score - Min_Score) × 100
    """
    if credit_score <= 0:
        return 0.0

    score = (credit_score - MIN_CREDIT_SCORE) / (MAX_CREDIT_SCORE - MIN_CREDIT_SCORE) * 100
    return round(max(0.0, min(100.0, score)), 2)

def compute_health_score(
    monthly_emi_paise: int,
    monthly_income_paise: int,
    sanction_amount_paise: int,
    outstanding_paise: int,
    missed_payments: int,
    total_payments: int,
    months_since_start: int,
    other_debt_paise: int = 0,
    credit_score: int = 0,
    ltv_ratio: float = 0.0,
    days_overdue_avg: int = 0,
    recent_missed: int = 0,
    payment_consistency: float = 1.0,
    early_payments: int = 0,
) -> HealthScoreResult:
    """
    Compute comprehensive loan health score.

    INVARIANT 1: All money values in paise (integer)
    """
    dti_score = compute_dti_score(monthly_emi_paise, monthly_income_paise, other_debt_paise)
    utilization_score = compute_utilization_score(sanction_amount_paise, outstanding_paise, ltv_ratio)
    stress_score = compute_stress_score(missed_payments, total_payments, days_overdue_avg, recent_missed)
    payment_score = compute_payment_score(months_since_start, payment_consistency, early_payments)
    credit_score_component = compute_credit_score_component(credit_score)

    # Weighted average (20% each component)
    overall = (dti_score + utilization_score + stress_score + payment_score + credit_score_component) / 5

    return HealthScoreResult(
        dti_score=dti_score,
        utilization_score=utilization_score,
        stress_score=stress_score,
        payment_score=payment_score,
        credit_score=credit_score_component,
        overall_score=round(overall, 2),
        ltv_ratio=ltv_ratio,
        dti=round(((monthly_emi_paise + other_debt_paise) / max(monthly_income_paise, 1)) * 100, 2),
        missed_payment_rate=round((missed_payments / max(total_payments, 1)) * 100, 2) if total_payments > 0 else 0.0,
    )

def get_health_recommendations(
    health_result: HealthScoreResult,
) -> list[str]:
    """Generate actionable recommendations based on health score."""
    recommendations = []

    if health_result.dti > 35:
        recommendations.append(f"High DTI ({health_result.dti}%) - consider prepayment to reduce EMI burden")
    elif health_result.dti > 25:
        recommendations.append(f"Moderate DTI ({health_result.dti}%) - monitor debt levels")

    if health_result.utilization_score < 50:
        recommendations.append("High loan utilization - consider refinancing or prepayment")

    if health_result.stress_score < 70:
        recommendations.append("Payment stress detected - make consistent payments to improve credit health")

    if health_result.credit_score < 50:
        recommendations.append("Low credit score - improve by making timely payments and reducing credit utilization")

    if health_result.ltv_ratio > 0.8:
        recommendations.append(f"High LTV ratio ({int(health_result.ltv_ratio * 100)}%) - consider reducing loan balance")

    if health_result.missed_payment_rate > 5:
        recommendations.append(f"High missed payment rate ({health_result.missed_payment_rate}%) - set up automatic payments")

    if health_result.overall_score >= 80:
        recommendations.append("Excellent loan health - keep up the good work!")
    elif health_result.overall_score >= 60:
        recommendations.append("Good loan health - maintain current payment patterns")
    else:
        recommendations.append("Loan health needs improvement - consider debt management strategies")

    # Add specific prepayment recommendations
    if health_result.dti > 30 and health_result.overall_score < 70:
        recommendations.append("Consider making prepayments to reduce your EMI burden and improve loan health")

    return recommendations

def get_health_insights(
    health_result: HealthScoreResult,
) -> dict[str, str]:
    """Generate detailed insights about loan health."""
    insights = {}

    # DTI insights
    if health_result.dti > 40:
        insights["dti"] = "Very high DTI - you may be overleveraged. Consider reducing debt or increasing income."
    elif health_result.dti > 30:
        insights["dti"] = "High DTI - your debt obligations are significant relative to your income."
    elif health_result.dti > 20:
        insights["dti"] = "Moderate DTI - manageable but monitor debt levels."
    else:
        insights["dti"] = "Good DTI - your debt is well within manageable limits."

    # Utilization insights
    utilization = 100 - health_result.utilization_score
    if utilization > 80:
        insights["utilization"] = "Very high loan utilization - you're close to your sanctioned limit."
    elif utilization > 60:
        insights["utilization"] = "High loan utilization - consider prepayment to reduce interest costs."
    else:
        insights["utilization"] = "Good loan utilization - you have room for additional borrowing if needed."

    # Stress insights
    if health_result.stress_score < 50:
        insights["stress"] = "High payment stress - missed payments are affecting your loan health."
    elif health_result.stress_score < 70:
        insights["stress"] = "Moderate payment stress - recent missed payments are impacting your score."
    else:
        insights["stress"] = "Good payment history - keep making timely payments."

    # Credit score insights
    if health_result.credit_score < 50:
        insights["credit"] = "Low credit score - this may affect your ability to get favorable loan terms."
    elif health_result.credit_score < 70:
        insights["credit"] = "Fair credit score - improve by maintaining good payment history."
    else:
        insights["credit"] = "Good credit score - you're likely to get favorable loan terms."

    return insights