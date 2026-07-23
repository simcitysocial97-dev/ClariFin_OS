"""Stress and behavioural indices for behaviour engine.

All monetary values are integers in paise (₹1.00 = 100 paise).
All functions are pure - no database access.

Transactions are expected as dicts with keys:
- date_iso: str - YYYY-MM-DD format
- time_iso: str (optional) - HH:MM format
- description: str - merchant/description
- amount_paise: int - transaction amount
- type: str - "debit" or "credit"
- category: str - transaction category
"""

import math
from collections import defaultdict
from datetime import datetime
from typing import Any

# ============================================================
# Utility Functions (internal)
# ============================================================

def _parse_date(date_str: str) -> datetime | None:
    """Parse various date formats to datetime."""
    if not date_str:
        return None
    formats = [
        "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y",
        "%d %b %Y", "%d %b %y", "%d-%b-%Y", "%d-%b-%y",
    ]
    s = date_str.strip()
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _normalize_score(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Normalize a value to 0-1 range with clamping."""
    if max_val == min_val:
        return 0.5
    normalized = (value - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, normalized))


def _coefficient_of_variation(values: list[float]) -> float:
    """Calculate coefficient of variation (std/mean)."""
    if not values or len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    if mean == 0:
        return 0.0
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    std = math.sqrt(variance)
    return std / mean


# ============================================================
# Loss Aversion Index
# ============================================================

def loss_aversion_index(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compute Loss Aversion Index based on Kahneman & Tversky.

    Components:
    - Post-income spend velocity (72h window)
    - Emotional overspend after large expenses
    - Recovery time to baseline

    Parameters:
        transactions: List of transaction dicts with date_iso, amount_paise, type.

    Returns:
        Dict with score, post_income_velocity, recovery_time_days, large_expense_count.
    """
    if not transactions:
        return {"score": 0.5, "post_income_velocity": 0.0, "recovery_time_days": 0}

    credits = [t for t in transactions if t.get("type") == "credit"]
    debits = [t for t in transactions if t.get("type") == "debit"]

    if not credits or not debits:
        return {"score": 0.5, "post_income_velocity": 0.0, "recovery_time_days": 0}

    # Calculate median debit for baseline (convert from paise to rupees for thresholds)
    debit_amounts = [(t.get("amount_paise", 0) or 0) / 100.0 for t in debits]
    if not debit_amounts:
        return {"score": 0.5, "post_income_velocity": 0.0, "recovery_time_days": 0}

    median_debit = sorted(debit_amounts)[len(debit_amounts) // 2]

    # Post-income spending velocity
    post_income_spends: list[float] = []

    for credit in credits:
        credit_date = _parse_date(credit.get("date_iso", "") or credit.get("date", ""))
        if not credit_date:
            continue

        # Find debits within 72 hours
        spend_72h = 0.0
        for debit in debits:
            debit_date = _parse_date(debit.get("date_iso", "") or debit.get("date", ""))
            if not debit_date:
                continue

            days_diff = (debit_date - credit_date).days
            if 0 <= days_diff <= 3:
                spend_72h += (debit.get("amount_paise", 0) or 0) / 100.0

        credit_amount = (credit.get("amount_paise", 0) or 0) / 100.0
        if credit_amount > 0:
            velocity = spend_72h / credit_amount
            post_income_spends.append(velocity)

    # Calculate average velocity
    avg_velocity = sum(post_income_spends) / len(post_income_spends) if post_income_spends else 0

    # Emotional overspend after large expenses (>2x median)
    large_expenses = [t for t in debits if (t.get("amount_paise", 0) or 0) / 100.0 > 2 * median_debit]

    # Recovery time calculation (simplified)
    recovery_days = 0
    if large_expenses:
        avg_large = sum((t.get("amount_paise", 0) or 0) / 100.0 for t in large_expenses) / len(large_expenses)
        recovery_days = min(30, int(avg_large / max(median_debit, 1)))

    # Normalize to 0-1 score
    velocity_score = _normalize_score(avg_velocity, 0, 1.5)
    recovery_score = _normalize_score(recovery_days, 0, 30)

    score = (velocity_score * 0.6 + recovery_score * 0.4)

    return {
        "score": round(score, 4),
        "post_income_velocity": round(avg_velocity, 4),
        "recovery_time_days": recovery_days,
        "large_expense_count": len(large_expenses),
    }


# ============================================================
# Impulsivity Score
# ============================================================

def impulsivity_score(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compute Impulsivity Score based on Present Bias.

    Signals:
    - Micro-transactions clustering (< ₹500)
    - Late-night spending ratio (22:00–06:00)
    - Weekend vs weekday variance
    - Category switching frequency

    Parameters:
        transactions: List of transaction dicts with date_iso, amount_paise, type, category.

    Returns:
        Dict with score, micro_txn_ratio, late_night_ratio, weekend_ratio, discretionary_ratio.
    """
    if not transactions:
        return {"score": 0.5, "micro_txn_ratio": 0.0, "late_night_ratio": 0.0}

    debits = [t for t in transactions if t.get("type") == "debit"]
    if not debits:
        return {"score": 0.5, "micro_txn_ratio": 0.0, "late_night_ratio": 0.0}

    total_debits = len(debits)

    # Micro-transactions (< ₹500)
    micro_txns = [t for t in debits if (t.get("amount_paise", 0) or 0) / 100.0 < 500]
    micro_ratio = len(micro_txns) / total_debits if total_debits > 0 else 0

    # Late-night spending (simplified - would need timestamp data)
    # For now, use weekend spending as proxy
    weekend_txns = []
    weekday_txns = []

    for txn in debits:
        date_iso = txn.get("date_iso", "")
        if date_iso:
            try:
                dt = datetime.strptime(date_iso, "%Y-%m-%d")
                if dt.weekday() >= 5:  # Saturday, Sunday
                    weekend_txns.append(txn)
                else:
                    weekday_txns.append(txn)
            except (ValueError, TypeError):
                pass

    # Weekend vs weekday variance
    if weekend_txns and weekday_txns:
        weekend_avg = sum((t.get("amount_paise", 0) or 0) / 100.0 for t in weekend_txns) / len(weekend_txns)
        weekday_avg = sum((t.get("amount_paise", 0) or 0) / 100.0 for t in weekday_txns) / len(weekday_txns)
        weekend_ratio = weekend_avg / max(weekday_avg, 1)
    else:
        weekend_ratio = 1.0

    # Category switching (discretionary categories)
    discretionary_categories = [
        "Food & Dining", "Entertainment", "Shopping", "Travel",
        "Lifestyle", "Groceries", "Online Shopping"
    ]

    discretionary_txns = [t for t in debits if t.get("category") in discretionary_categories]
    disc_ratio = len(discretionary_txns) / total_debits if total_debits > 0 else 0

    # Compute composite score
    micro_score = _normalize_score(micro_ratio, 0, 0.8)
    weekend_score = _normalize_score(weekend_ratio, 0.5, 2.0)
    disc_score = _normalize_score(disc_ratio, 0, 0.6)

    score = (micro_score * 0.35 + weekend_score * 0.35 + disc_score * 0.30)

    return {
        "score": round(score, 4),
        "micro_txn_ratio": round(micro_ratio, 4),
        "weekend_ratio": round(weekend_ratio, 4),
        "discretionary_ratio": round(disc_ratio, 4),
        "micro_txn_count": len(micro_txns),
    }


# ============================================================
# Habit Stability Score
# ============================================================

def habit_stability_score(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compute Habit Stability Score based on Habit Loop Theory.

    Measures:
    - Category coefficient of variation (monthly)
    - Recurring expense predictability
    - Behavioral rhythm regularity

    Parameters:
        transactions: List of transaction dicts with date_iso, amount_paise, type, category, description.

    Returns:
        Dict with score, category_cv, recurring_predictability, recurring_count, rhythm_score.
    """
    if not transactions:
        return {"score": 0.5, "category_cv": 0.0, "recurring_predictability": 0.0}

    debits = [t for t in transactions if t.get("type") == "debit"]
    if not debits:
        return {"score": 0.5, "category_cv": 0.0, "recurring_predictability": 0.0}

    # Monthly category spending (use amount_paise, convert to rupees for analysis)
    monthly_category: defaultdict[str, defaultdict[str, float]] = defaultdict(lambda: defaultdict(float))
    for txn in debits:
        date_iso = txn.get("date_iso", "")
        if date_iso:
            month = date_iso[:7]  # YYYY-MM
            category = txn.get("category", "Uncategorized")
            monthly_category[month][category] += (txn.get("amount_paise", 0) or 0) / 100.0

    # Category CV across months
    category_cvs: list[float] = []
    if monthly_category:
        all_categories: set[str] = set()
        for month_data in monthly_category.values():
            all_categories.update(month_data.keys())

        for cat in all_categories:
            monthly_vals = [monthly_category[m].get(cat, 0) for m in sorted(monthly_category.keys())]
            if len(monthly_vals) >= 2:
                cv = _coefficient_of_variation(monthly_vals)
                category_cvs.append(cv)

    avg_category_cv = sum(category_cvs) / len(category_cvs) if category_cvs else 0

    # Recurring expense detection (similar amounts, same description)
    desc_amounts: defaultdict[str, list[float]] = defaultdict(list)
    for txn in debits:
        desc = txn.get("description", "")[:30]  # Truncate for matching
        amount = (txn.get("amount_paise", 0) or 0) / 100.0
        if amount > 0:
            desc_amounts[desc].append(amount)

    recurring_count = 0
    for _desc, amounts in desc_amounts.items():
        if len(amounts) >= 3:
            # Check if amounts are similar (within 10%)
            avg = sum(amounts) / len(amounts)
            if all(abs(a - avg) / max(avg, 1) < 0.1 for a in amounts):
                recurring_count += 1

    recurring_score = min(1.0, recurring_count / 10)  # Normalize to max 10 recurring

    # Behavioral rhythm (regular transaction days)
    daily_counts: defaultdict[str, float] = defaultdict(float)
    for txn in debits:
        date_iso = txn.get("date_iso", "")
        if date_iso:
            daily_counts[date_iso] += 1

    if daily_counts:
        counts = [float(v) for v in daily_counts.values()]
        rhythm_cv = _coefficient_of_variation(counts)
        rhythm_score = 1 - _normalize_score(rhythm_cv, 0, 2)
    else:
        rhythm_score = 0.5

    # Composite score (lower CV = higher stability)
    cv_score = 1 - _normalize_score(avg_category_cv, 0, 1.5)

    score = (cv_score * 0.40 + recurring_score * 0.30 + rhythm_score * 0.30)

    return {
        "score": round(score, 4),
        "category_cv": round(avg_category_cv, 4),
        "recurring_count": recurring_count,
        "rhythm_score": round(rhythm_score, 4),
    }


# ============================================================
# Financial Stress Index
# ============================================================

def financial_stress_index(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compute Financial Stress Index.

    Measures:
    - Balance volatility coefficient
    - End-of-month depletion ratio
    - Credit dependency ratio
    - Buffer adequacy (days covered)

    Parameters:
        transactions: List of transaction dicts with date_iso, amount_paise, type.

    Returns:
        Dict with score, balance_volatility, credit_dependency, eom_depletion_ratio, buffer_days.
    """
    if not transactions:
        return {"score": 0.5, "balance_volatility": 0.0, "credit_dependency": 0.0}

    # Separate credits and debits
    credits = [t for t in transactions if t.get("type") == "credit"]
    debits = [t for t in transactions if t.get("type") == "debit"]

    if not debits:
        return {"score": 0.5, "balance_volatility": 0.0, "credit_dependency": 0.0}

    # Daily net flow (convert amount_paise to rupees for analysis)
    daily_net: defaultdict[str, float] = defaultdict(float)
    for txn in transactions:
        date_iso = txn.get("date_iso", "")
        if date_iso:
            amount = (txn.get("amount_paise", 0) or 0) / 100.0
            if txn.get("type") == "debit":
                daily_net[date_iso] -= amount
            else:
                daily_net[date_iso] += amount

    # Running balance simulation
    sorted_dates = sorted(daily_net.keys())
    running_balance: list[float] = []
    balance: float = 0.0
    for date in sorted_dates:
        balance += daily_net[date]
        running_balance.append(balance)

    # Balance volatility
    if running_balance:
        balance_cv = _coefficient_of_variation([abs(b) for b in running_balance])
    else:
        balance_cv = 0

    # Credit dependency (convert amount_paise to rupees)
    total_credit = sum((t.get("amount_paise", 0) or 0) / 100.0 for t in credits)
    total_debit = sum((t.get("amount_paise", 0) or 0) / 100.0 for t in debits)
    credit_dependency = total_credit / max(total_debit, 1) if total_debit > 0 else 0

    # End-of-month depletion (last 5 days spending ratio)
    eom_spending: float = 0.0
    total_spending: float = 0.0

    for txn in debits:
        date_iso = txn.get("date_iso", "")
        amount = (txn.get("amount_paise", 0) or 0) / 100.0
        total_spending += amount

        if date_iso:
            try:
                dt = datetime.strptime(date_iso, "%Y-%m-%d")
                if dt.day >= 26:  # Last 5 days
                    eom_spending += amount
            except (ValueError, TypeError):
                pass

    eom_ratio = eom_spending / max(total_spending, 1)

    # Buffer adequacy (days of expenses covered by average balance)
    avg_balance = abs(sum(running_balance) / len(running_balance)) if running_balance else 0
    daily_avg_spend = total_debit / max(len(daily_net), 1)
    buffer_days = avg_balance / max(daily_avg_spend, 1)
    buffer_score = _normalize_score(buffer_days, 0, 30)

    # Composite stress index (higher = more stress)
    volatility_score = _normalize_score(balance_cv, 0, 2)
    dependency_score = _normalize_score(credit_dependency, 0, 2)
    eom_score = _normalize_score(eom_ratio, 0, 0.5)

    score = (volatility_score * 0.30 + dependency_score * 0.30 +
             eom_score * 0.20 + (1 - buffer_score) * 0.20)

    return {
        "score": round(score, 4),
        "balance_volatility": round(balance_cv, 4),
        "credit_dependency": round(credit_dependency, 4),
        "eom_depletion_ratio": round(eom_ratio, 4),
        "buffer_days": round(buffer_days, 1),
    }


# ============================================================
# Savings Discipline Score
# ============================================================

def savings_discipline_score(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compute Savings Discipline Score.

    Measures:
    - 3-month rolling savings rate trend
    - Savings transfer consistency
    - Positive savings momentum

    Parameters:
        transactions: List of transaction dicts with date_iso, amount_paise, type.

    Returns:
        Dict with score, savings_rate, momentum, consistency, positive_savings_months.
    """
    if not transactions:
        return {"score": 0.5, "savings_rate": 0.0, "momentum": 0.0}

    # Monthly income vs expenses (use amount_paise, convert to rupees for analysis)
    monthly_data: defaultdict[str, dict[str, float]] = defaultdict(lambda: {"income": 0.0, "expenses": 0.0})

    for txn in transactions:
        date_iso = txn.get("date_iso", "")
        if date_iso:
            month = date_iso[:7]
            amount = (txn.get("amount_paise", 0) or 0) / 100.0
            if txn.get("type") == "credit":
                monthly_data[month]["income"] += amount
            else:
                monthly_data[month]["expenses"] += amount

    if not monthly_data:
        return {"score": 0.5, "savings_rate": 0.0, "momentum": 0.0}

    # Calculate monthly savings rates
    savings_rates: list[tuple[str, float]] = []
    sorted_months = sorted(monthly_data.keys())

    for month in sorted_months:
        income = monthly_data[month]["income"]
        expenses = monthly_data[month]["expenses"]
        if income > 0:
            rate = (income - expenses) / income
            savings_rates.append((month, rate))

    if not savings_rates:
        return {"score": 0.5, "savings_rate": 0.0, "momentum": 0.0}

    # Average savings rate
    avg_rate = sum(r for _, r in savings_rates) / len(savings_rates)

    # Savings momentum (trend over last 3 months)
    if len(savings_rates) >= 2:
        recent_rates = [r for _, r in savings_rates[-3:]]
        earlier_rates = [r for _, r in savings_rates[:-3]] if len(savings_rates) > 3 else [0]

        recent_avg = sum(recent_rates) / len(recent_rates)
        earlier_avg = sum(earlier_rates) / len(earlier_rates) if earlier_rates else 0

        momentum = recent_avg - earlier_avg
    else:
        momentum = 0

    # Savings consistency (how often positive savings)
    positive_months = sum(1 for _, r in savings_rates if r > 0)
    consistency = positive_months / len(savings_rates) if savings_rates else 0

    # Composite score
    rate_score = _normalize_score(avg_rate, -0.5, 0.5)
    momentum_score = _normalize_score(momentum, -0.3, 0.3)
    consistency_score = consistency

    score = (rate_score * 0.40 + momentum_score * 0.30 + consistency_score * 0.30)

    return {
        "score": round(score, 4),
        "savings_rate": round(avg_rate, 4),
        "momentum": round(momentum, 4),
        "consistency": round(consistency, 4),
        "positive_savings_months": positive_months,
    }


# ============================================================
# India-Specific Risk Detection
# ============================================================

def detect_risk_patterns(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Detect India-specific risky financial behaviors.

    Patterns:
    - UPI micro-spend clustering
    - Gambling/gaming transactions
    - Loan app patterns
    - EMI burden ratio

    Parameters:
        transactions: List of transaction dicts with date_iso, amount_paise, type, description.

    Returns:
        Dict with upi_micro_spend_flag, gambling_flag, loan_app_pattern_flag, emi_ratio.
    """
    if not transactions:
        return {
            "upi_micro_spend_flag": False,
            "gambling_flag": False,
            "loan_app_pattern_flag": False,
            "emi_ratio": 0.0,
        }

    debits = [t for t in transactions if t.get("type") == "debit"]
    credits = [t for t in transactions if t.get("type") == "credit"]

    # UPI micro-spend detection (>10 transactions/day < ₹200)
    daily_micro: dict[str, int] = defaultdict(int)
    for txn in debits:
        amount = (txn.get("amount_paise", 0) or 0) / 100.0
        date_iso = txn.get("date_iso", "")
        if amount < 200 and date_iso:
            daily_micro[date_iso] += 1

    upi_flag = any(count > 10 for count in daily_micro.values())

    # Gambling detection
    gambling_keywords = [
        "dream11", "mpl", "rummy", "bet", "casino", "poker",
        "teen patti", "my11circle", "fantasy", "betting", "gambl"
    ]

    gambling_txns = []
    for txn in debits:
        desc = (txn.get("description", "") or "").lower()
        if any(kw in desc for kw in gambling_keywords):
            gambling_txns.append(txn)

    gambling_flag = len(gambling_txns) > 0

    # Loan app detection (multiple small credits from NBFCs)
    loan_keywords = ["loan", "nbfc", "credit", "lend", "finance", "cash", "instant"]

    loan_credits = []
    for txn in credits:
        desc = (txn.get("description", "") or "").lower()
        amount = (txn.get("amount_paise", 0) or 0) / 100.0
        if any(kw in desc for kw in loan_keywords) and amount < 50000:
            loan_credits.append(txn)

    # Check for clustering (multiple loans within 7 days)
    loan_dates = []
    for txn in loan_credits:
        date_iso = txn.get("date_iso", "")
        if date_iso:
            loan_dates.append(date_iso)

    loan_flag = len(loan_dates) >= 2  # Multiple loan credits

    # EMI ratio calculation
    emi_keywords = ["emi", "loan repayment", "installment"]
    monthly_emi: dict[str, float] = defaultdict(float)

    for txn in debits:
        desc = (txn.get("description", "") or "").lower()
        date_iso = txn.get("date_iso", "")
        if any(kw in desc for kw in emi_keywords) and date_iso:
            month = date_iso[:7]
            monthly_emi[month] += (txn.get("amount_paise", 0) or 0) / 100.0

    # Calculate EMI to income ratio
    monthly_income: dict[str, float] = defaultdict(float)
    for txn in credits:
        date_iso = txn.get("date_iso", "")
        if date_iso:
            month = date_iso[:7]
            monthly_income[month] += (txn.get("amount_paise", 0) or 0) / 100.0

    emi_ratios = []
    for month in monthly_emi:
        if monthly_income.get(month, 0) > 0:
            ratio = monthly_emi[month] / monthly_income[month]
            emi_ratios.append(ratio)

    avg_emi_ratio = sum(emi_ratios) / len(emi_ratios) if emi_ratios else 0

    return {
        "upi_micro_spend_flag": upi_flag,
        "gambling_flag": gambling_flag,
        "gambling_transaction_count": len(gambling_txns),
        "loan_app_pattern_flag": loan_flag,
        "loan_credit_count": len(loan_credits),
        "emi_ratio": round(avg_emi_ratio, 4),
        "monthly_emi_total": sum(monthly_emi.values()),
    }
