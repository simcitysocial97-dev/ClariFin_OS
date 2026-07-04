"""
Cash Flow Engine
================

Deterministic cash flow computation engine for monthly income, expenses,
savings, and cash flow metrics from transaction data.

Key Principles:
1. All amounts are stored as INTEGER paise (1 rupee = 100 paise)
2. No floating-point arithmetic - all calculations use integers
3. All computations via SQL aggregation, NOT Python loops
4. Deterministic: same data → same output, every time
"""

from datetime import datetime, timedelta
from calendar import monthrange
from typing import Dict, List, Optional, Any, TYPE_CHECKING

from src.logger import log

if TYPE_CHECKING:
    from src.db import FinanceDB


# ============================================================
# Function 1: Monthly Cash Flow
# ============================================================

def compute_monthly_cashflow(db: "FinanceDB", months: int = 12) -> list[dict]:
    """
    Query transactions from the last N months and compute monthly cash flow metrics.

    Args:
        db: FinanceDB instance
        months: Number of months to look back (default 12)

    Returns:
        List of dicts with keys:
            - month: "YYYY-MM"
            - total_income_paise: SUM of credit column
            - total_expense_paise: SUM of debit column
            - net_cashflow_paise: income - expenses
            - savings_rate: net_cashflow / income (0 if no income)
            - transaction_count: COUNT
        Sorted by month ascending (oldest first)
    """
    log.info("Computing monthly cashflow for last %d months", months)

    # Calculate cutoff date (first day of month N months ago)
    today = datetime.now()
    cutoff_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    for _ in range(months - 1):
        cutoff_date = (cutoff_date - timedelta(days=1)).replace(day=1)
    cutoff_str = cutoff_date.strftime("%Y-%m-%d")

    with db.connection() as conn:
        # Check if we have any data
        cur = conn.execute("SELECT 1 FROM transactions LIMIT 1")
        if not cur.fetchone():
            log.warning("No transactions found for cashflow computation")
            return []

        # SQL aggregation for monthly cashflow
        # Uses amount_paise as the authoritative column (positive = credit, negative = debit)
        # NOT the credit/debit columns which may have incomplete data
        sql = """
            SELECT
                strftime('%Y-%m', date_iso) as month,
                COALESCE(SUM(CASE WHEN amount_paise > 0 THEN amount_paise ELSE 0 END), 0) as total_income_paise,
                COALESCE(SUM(CASE WHEN amount_paise < 0 THEN ABS(amount_paise) ELSE 0 END), 0) as total_expense_paise,
                COALESCE(SUM(amount_paise), 0) as net_cashflow_paise,
                COUNT(*) as transaction_count
            FROM transactions
            WHERE date_iso >= ?
            GROUP BY strftime('%Y-%m', date_iso)
            ORDER BY month ASC
        """
        cur = conn.execute(sql, (cutoff_str,))
        rows = cur.fetchall()

    results = []
    for row in rows:
        month = row["month"]
        income = row["total_income_paise"]
        expense = row["total_expense_paise"]
        net = row["net_cashflow_paise"]
        count = row["transaction_count"]

        # Calculate savings rate (0 if no income)
        savings_rate = 0.0
        if income > 0:
            savings_rate = round(net / income, 4)

        results.append({
            "month": month,
            "total_income_paise": income,
            "total_expense_paise": expense,
            "net_cashflow_paise": net,
            "savings_rate": savings_rate,
            "transaction_count": count,
        })

    log.info("Computed cashflow for %d months", len(results))
    return results


# ============================================================
# Function 2: Cash Flow Breakdown
# ============================================================

def compute_cashflow_breakdown(db: "FinanceDB", month: str | None = None) -> dict:
    """
    Compute detailed cash flow breakdown for a specific month.

    Args:
        db: FinanceDB instance
        month: Month in YYYY-MM format, or None for current month

    Returns:
        Dict with:
            - fixed_expenses_paise: SUM of debits for fixed categories or linked to recurring
            - variable_expenses_paise: total_expense - fixed_expenses
            - income_by_source: list of {category, amount_paise} for credits
            - expense_by_category: list of {category, amount_paise} for debits
            - daily_burn_rate_paise: total_expense / days_in_month
            - runway_months: liquid_assets / monthly_expenses
    """
    log.info("Computing cashflow breakdown for month: %s", month or "current")

    # Determine target month
    if month is None:
        month = datetime.now().strftime("%Y-%m")

    # Fixed expense categories
    fixed_categories = ['EMI', 'Rent', 'Insurance', 'Subscription', 'Utilities']

    with db.connection() as conn:
        # Get total income and expenses for the month
        cur = conn.execute("""
            SELECT
                COALESCE(SUM(credit), 0) as total_income,
                COALESCE(SUM(debit), 0) as total_expense,
                COUNT(*) as transaction_count
            FROM transactions
            WHERE strftime('%Y-%m', date_iso) = ?
        """, (month,))
        row = cur.fetchone()
        total_income = row["total_income"] if row else 0
        total_expense = row["total_expense"] if row else 0

        # Fixed expenses: categories in fixed list OR linked to recurring_id (if column exists)
        placeholders = ','.join('?' * len(fixed_categories))
        # Check if recurring_id column exists
        columns = [row[1] for row in conn.execute("PRAGMA table_info(transactions)").fetchall()]
        has_recurring_id = "recurring_id" in columns
        
        if has_recurring_id:
            cur = conn.execute(f"""
                SELECT COALESCE(SUM(debit), 0) as fixed_expenses
                FROM transactions
                WHERE strftime('%Y-%m', date_iso) = ?
                AND (category IN ({placeholders}) OR recurring_id IS NOT NULL)
            """, (month, *fixed_categories))
        else:
            cur = conn.execute(f"""
                SELECT COALESCE(SUM(debit), 0) as fixed_expenses
                FROM transactions
                WHERE strftime('%Y-%m', date_iso) = ?
                AND category IN ({placeholders})
            """, (month, *fixed_categories))
        row = cur.fetchone()
        fixed_expenses = row["fixed_expenses"] if row else 0

        # Income by source (category for credits)
        cur = conn.execute("""
            SELECT
                COALESCE(category, 'Uncategorized') as category,
                COALESCE(SUM(credit), 0) as amount_paise
            FROM transactions
            WHERE strftime('%Y-%m', date_iso) = ?
            AND credit > 0
            GROUP BY category
            ORDER BY amount_paise DESC
        """, (month,))
        income_by_source = [
            {"category": row["category"], "amount_paise": row["amount_paise"]}
            for row in cur.fetchall()
        ]

        # Expense by category (debits)
        cur = conn.execute("""
            SELECT
                COALESCE(category, 'Uncategorized') as category,
                COALESCE(SUM(debit), 0) as amount_paise
            FROM transactions
            WHERE strftime('%Y-%m', date_iso) = ?
            AND debit > 0
            GROUP BY category
            ORDER BY amount_paise DESC
        """, (month,))
        expense_by_category = [
            {"category": row["category"], "amount_paise": row["amount_paise"]}
            for row in cur.fetchall()
        ]

        # Liquid assets from accounts (savings, current, wallet)
        cur = conn.execute("""
            SELECT COALESCE(SUM(balance_paise), 0) as liquid_assets
            FROM accounts
            WHERE account_type IN ('savings', 'current', 'wallet')
            AND is_active = 1
        """)
        row = cur.fetchone()
        liquid_assets = row["liquid_assets"] if row else 0

    # Calculate derived metrics
    variable_expenses = total_expense - fixed_expenses

    # Daily burn rate
    year, mon = int(month[:4]), int(month[5:7])
    days_in_month = monthrange(year, mon)[1]
    daily_burn_rate = total_expense // days_in_month if days_in_month > 0 else 0

    # Runway months (liquid assets / monthly expenses)
    runway_months = None
    if total_expense > 0:
        runway_months = round(liquid_assets / total_expense, 2)
    elif liquid_assets > 0:
        runway_months = None  # Cannot calculate when no expenses

    result = {
        "month": month,
        "total_income_paise": total_income,
        "total_expense_paise": total_expense,
        "fixed_expenses_paise": fixed_expenses,
        "variable_expenses_paise": variable_expenses,
        "income_by_source": income_by_source,
        "expense_by_category": expense_by_category,
        "daily_burn_rate_paise": daily_burn_rate,
        "liquid_assets_paise": liquid_assets,
        "runway_months": runway_months,
        "days_in_month": days_in_month,
    }

    log.info("Cashflow breakdown computed for %s", month)
    return result


# ============================================================
# Function 3: Cash Flow Summary
# ============================================================

def compute_cashflow_summary(db: "FinanceDB") -> dict:
    """
    Compute comprehensive cash flow summary over all available data.

    Args:
        db: FinanceDB instance

    Returns:
        Dict with:
            - avg_monthly_income_paise
            - avg_monthly_expense_paise
            - avg_savings_rate
            - best_month: month with highest net cashflow
            - worst_month: month with lowest net cashflow
            - months_positive: count of months with positive net cashflow
            - months_negative: count of months with negative net cashflow
            - trend: "improving" | "declining" | "stable"
    """
    log.info("Computing cashflow summary")

    with db.connection() as conn:
        # Check if we have any data
        cur = conn.execute("SELECT 1 FROM transactions LIMIT 1")
        if not cur.fetchone():
            log.warning("No transactions found for summary")
            return {
                "avg_monthly_income_paise": 0,
                "avg_monthly_expense_paise": 0,
                "avg_savings_rate": 0.0,
                "best_month": None,
                "worst_month": None,
                "months_positive": 0,
                "months_negative": 0,
                "trend": "stable",
            }

        # Get monthly aggregates for all months using amount_paise (authoritative column)
        cur = conn.execute("""
            SELECT
                strftime('%Y-%m', date_iso) as month,
                COALESCE(SUM(CASE WHEN amount_paise > 0 THEN amount_paise ELSE 0 END), 0) as income,
                COALESCE(SUM(CASE WHEN amount_paise < 0 THEN ABS(amount_paise) ELSE 0 END), 0) as expense,
                COALESCE(SUM(amount_paise), 0) as net
            FROM transactions
            WHERE date_iso IS NOT NULL AND date_iso != ''
            GROUP BY strftime('%Y-%m', date_iso)
            ORDER BY month ASC
        """)
        monthly_data = cur.fetchall()

    if not monthly_data:
        log.warning("No monthly data available for summary")
        return {
            "avg_monthly_income_paise": 0,
            "avg_monthly_expense_paise": 0,
            "avg_savings_rate": 0.0,
            "best_month": None,
            "worst_month": None,
            "months_positive": 0,
            "months_negative": 0,
            "trend": "stable",
        }

    # Calculate averages and find best/worst months
    total_income = 0
    total_expense = 0
    total_savings_rate = 0.0
    months_with_income = 0

    best_month = None
    worst_month = None
    best_net = float('-inf')
    worst_net = float('inf')

    months_positive = 0
    months_negative = 0

    monthly_nets = []

    for row in monthly_data:
        month = row["month"]
        income = row["income"]
        expense = row["expense"]
        net = row["net"]

        total_income += income
        total_expense += expense

        if income > 0:
            savings_rate = net / income
            total_savings_rate += savings_rate
            months_with_income += 1

        # Track best/worst
        if net > best_net:
            best_net = net
            best_month = month
        if net < worst_net:
            worst_net = net
            worst_month = month

        # Track positive/negative
        if net > 0:
            months_positive += 1
        elif net < 0:
            months_negative += 1

        monthly_nets.append((month, net))

    num_months = len(monthly_data)
    avg_income = total_income // num_months if num_months > 0 else 0
    avg_expense = total_expense // num_months if num_months > 0 else 0
    avg_savings = round(total_savings_rate / months_with_income, 4) if months_with_income > 0 else 0.0

    # Calculate trend: compare last 3 months avg to prior 3 months avg
    trend = "stable"
    if len(monthly_nets) >= 6:
        last_3 = monthly_nets[-3:]
        prior_3 = monthly_nets[-6:-3]

        last_3_avg = sum(n for _, n in last_3) / 3
        prior_3_avg = sum(n for _, n in prior_3) / 3

        if prior_3_avg != 0:
            change_pct = (last_3_avg - prior_3_avg) / abs(prior_3_avg)
            if change_pct > 0.1:
                trend = "improving"
            elif change_pct < -0.1:
                trend = "declining"
            else:
                trend = "stable"
        elif last_3_avg > 0:
            trend = "improving"
        elif last_3_avg < 0:
            trend = "declining"

    result = {
        "avg_monthly_income_paise": avg_income,
        "avg_monthly_expense_paise": avg_expense,
        "avg_savings_rate": avg_savings,
        "best_month": {"month": best_month, "net_cashflow_paise": best_net} if best_month else None,
        "worst_month": {"month": worst_month, "net_cashflow_paise": worst_net} if worst_month else None,
        "months_positive": months_positive,
        "months_negative": months_negative,
        "total_months": num_months,
        "trend": trend,
    }

    log.info("Cashflow summary computed: %d months, trend=%s", num_months, trend)
    return result


# ============================================================
# CLI Test
# ============================================================

if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from src.db import FinanceDB

    # Default db path
    db_path = str(Path(__file__).parent.parent / "data" / "finance.db")

    log.info("=" * 60)
    log.info("Cash Flow Engine Test")
    log.info("=" * 60)
    log.info("Database: %s", db_path)

    db = FinanceDB(db_path=db_path)

    # Test monthly cashflow
    log.info("\n--- Monthly Cashflow (last 6 months) ---")
    monthly = compute_monthly_cashflow(db, months=6)
    for m in monthly:
        log.info("  %s: Income=₹%.2f, Expense=₹%.2f, Net=₹%.2f, Rate=%.1f%%",
            m['month'],
            m['total_income_paise']/100,
            m['total_expense_paise']/100,
            m['net_cashflow_paise']/100,
            m['savings_rate']*100
        )

    # Test breakdown
    if monthly:
        latest_month = monthly[-1]['month']
        log.info("\n--- Cashflow Breakdown for %s ---", latest_month)
        breakdown = compute_cashflow_breakdown(db, latest_month)
        log.info("  Total Income: ₹%.2f", breakdown['total_income_paise']/100)
        log.info("  Total Expense: ₹%.2f", breakdown['total_expense_paise']/100)
        log.info("  Fixed Expenses: ₹%.2f", breakdown['fixed_expenses_paise']/100)
        log.info("  Variable Expenses: ₹%.2f", breakdown['variable_expenses_paise']/100)
        log.info("  Daily Burn Rate: ₹%.2f", breakdown['daily_burn_rate_paise']/100)
        log.info("  Runway: %.1f months", breakdown['runway_months'])

    # Test summary
    log.info("\n--- Cashflow Summary ---")
    summary = compute_cashflow_summary(db)
    log.info("  Avg Monthly Income: ₹%.2f", summary['avg_monthly_income_paise']/100)
    log.info("  Avg Monthly Expense: ₹%.2f", summary['avg_monthly_expense_paise']/100)
    log.info("  Avg Savings Rate: %.1f%%", summary['avg_savings_rate']*100)
    log.info("  Best Month: %s", summary['best_month']['month'] if summary['best_month'] else 'N/A')
    log.info("  Worst Month: %s", summary['worst_month']['month'] if summary['worst_month'] else 'N/A')
    log.info("  Positive Months: %d", summary['months_positive'])
    log.info("  Negative Months: %d", summary['months_negative'])
    log.info("  Trend: %s", summary['trend'])

    db.close()
