"""
Health Scorer
=============
Computes loan health scores and related metrics.

Formula:
Health_Score = 0.25 × DTI_Score + 0.25 × Utilization_Score + 0.25 × Stress_Score + 0.25 × Payment_Score

INVARIANT 1-6 enforced throughout.
"""

from src.engines.loan_engine.types import HealthScoreResult

MAX_DTI: int = 40  # 40%


def compute_dti_score(
    monthly_emi_paise: int,
    monthly_income_paise: int,
    other_debt_paise: int = 0,
) -> float:
    """
    Compute DTI (Debt-to-Income) score component.

    DTI = (Total_monthly_EMI + other_debt_payments) / Monthly_income × 100

    Score = min(1, (Max_DTI - Current_DTI) / Max_DTI) × 100
    """
    if monthly_income_paise <= 0:
        return 0.0

    dti = ((monthly_emi_paise + other_debt_paise) / monthly_income_paise) * 100
    score = min(1.0, (MAX_DTI - dti) / MAX_DTI) * 100
    return round(score, 2)


def compute_utilization_score(
    sanction_amount_paise: int,
    outstanding_paise: int,
) -> float:
    """
    Compute utilization score component.

    Utilization = Sanction_Amount / Outstanding
    Score = min(1, Sanction_Amount / Outstanding) × 100

    Lower utilization = better score.
    """
    if sanction_amount_paise <= 0:
        return 100.0

    outstanding_paise / sanction_amount_paise
    score = min(1.0, (sanction_amount_paise / max(outstanding_paise, 1))) * 100
    return round(score, 2)


def compute_stress_score(
    missed_payments: int,
    total_payments: int,
    days_overdue_avg: int = 0,
) -> float:
    """
    Compute stress score component.

    Stress_Score = 100 - Missed_payment_rate × 50
    Lower missed payment rate = better score.
    """
    if total_payments <= 0:
        return 100.0

    missed_rate = missed_payments / total_payments
    score = max(0.0, 100 - missed_rate * 50)
    return round(score, 2)


def compute_payment_score(
    months_since_start: int,
) -> float:
    """
    Compute payment score component.

    Payment_Score = Months_since_start / 12 (capped at 100)
    Longer repayment history = better score.
    """
    score = min(100.0, months_since_start * 100 / 12)
    return round(score, 2)


def compute_health_score(
    monthly_emi_paise: int,
    monthly_income_paise: int,
    sanction_amount_paise: int,
    outstanding_paise: int,
    missed_payments: int,
    total_payments: int,
    months_since_start: int,
    other_debt_paise: int = 0,
) -> HealthScoreResult:
    """
    Compute complete loan health score.

    INVARIANT 1: All money values in paise (integer)
    """
    dti_score = compute_dti_score(monthly_emi_paise, monthly_income_paise, other_debt_paise)
    utilization_score = compute_utilization_score(sanction_amount_paise, outstanding_paise)
    stress_score = compute_stress_score(missed_payments, total_payments)
    payment_score = compute_payment_score(months_since_start)

    overall = (dti_score + utilization_score + stress_score + payment_score) / 4

    return HealthScoreResult(
        dti_score=dti_score,
        utilization_score=utilization_score,
        stress_score=stress_score,
        payment_score=payment_score,
        overall_score=round(overall, 2),
    )


def get_health_recommendations(
    health_result: HealthScoreResult,
) -> list[str]:
    """Generate actionable recommendations based on health score."""
    recommendations = []

    if health_result.dti_score < 50:
        recommendations.append("Consider prepayment to reduce EMI burden")

    if health_result.utilization_score < 50:
        recommendations.append("Loan nearly fully utilized - consider refinancing")

    if health_result.stress_score < 70:
        recommendations.append("Make consistent payments to improve credit health")

    if health_result.overall_score >= 80:
        recommendations.append("Excellent loan health - keep up the good work!")

    return recommendations
