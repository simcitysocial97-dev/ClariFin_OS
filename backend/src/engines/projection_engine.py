"""
Projection Engine
=================

Deterministic financial forecasting engine for net worth projections,
loan payoff calculations, goal planning, and what-if scenario analysis.

Key Principles:
1. All amounts are INTEGER paise (1 rupee = 100 paise)
2. Deterministic: same inputs → same output, every time
3. No side effects - SQL only for reading current state
4. No duplication of loan amortization logic (uses loan_engine)
5. Monthly compounding for investments
6. Never double count EMI (included in savings calculation)
7. Conservative modeling (no future salary growth)

Assumptions (logged in output):
- Equity annual return: 10% (configurable)
- Debt annual return: 7% (configurable)
- 365-day loan interest handled by loan_engine
- Savings basis: MEDIAN of last 6 months
- Monthly compounding
"""

from datetime import date, timedelta
from typing import List, Dict, Optional, Any, TYPE_CHECKING
from statistics import median
from decimal import Decimal, ROUND_HALF_UP

from src.logger import log
from src.utils import add_months, MAX_PROJECTION_MONTHS, GOAL_MAX_MONTHS, DEFAULT_EQUITY_RETURN, DEFAULT_DEBT_RETURN
from src.engines.loan_engine import (
    replay_payments,
    forecast_from_state,
    simulate_prepayment,
    compute_emi,
)

if TYPE_CHECKING:
    from src.db import FinanceDB


# ============================================================
# Function 1: Project Net Worth
# ============================================================

def project_net_worth(
    db: "FinanceDB",
    months_ahead: int = 60,
    equity_annual_return: float = DEFAULT_EQUITY_RETURN,
    debt_annual_return: float = DEFAULT_DEBT_RETURN
) -> dict:
    """
    Project net worth over time based on current assets, liabilities,
    historical cashflow, and loan projections.

    Args:
        db: FinanceDB instance
        months_ahead: Number of months to project (default 60 = 5 years)
        equity_annual_return: Expected annual return for equity investments (%)
        debt_annual_return: Expected annual return for debt investments (%)

    Returns:
        Dict with:
            - projections: List of monthly projections
            - assumptions: Dict of assumptions used
            - summary: Dict with starting and ending values
    """
    log.info("Projecting net worth for %d months", months_ahead)

    # Fetch current state from database
    assets = _fetch_current_assets(db)
    loans = _fetch_active_loans(db)
    sips = _fetch_active_sips(db)
    monthly_savings = _compute_stabilized_monthly_savings(db)

    log.info("Starting projection: assets=₹%.2f, loans=%d, sips=%d, monthly_savings=₹%.2f",
             (assets['cash'] + assets['equity'] + assets['debt']) / 100,
             len(loans), len(sips), monthly_savings / 100)

    # Prepare loan states for forecasting
    loan_states = _prepare_loan_states(db, loans)

    # Calculate monthly rates
    equity_monthly_rate = equity_annual_return / 12 / 100
    debt_monthly_rate = debt_annual_return / 12 / 100

    # Initialize projections
    projections = []
    current_assets = assets.copy()
    current_date = date.today()

    for month in range(1, min(months_ahead + 1, MAX_PROJECTION_MONTHS)):
        # a) Assets growth and contributions
        # Add monthly savings to cash first
        current_assets['cash'] += monthly_savings

        # Apply investment growth (monthly compounding)
        current_assets['equity'] = int(current_assets['equity'] * (1 + equity_monthly_rate))
        current_assets['debt'] = int(current_assets['debt'] * (1 + debt_monthly_rate))

        # Add SIP contributions (split between equity and debt based on type)
        for sip in sips:
            if sip['type'] == 'equity':
                current_assets['equity'] += sip['monthly_amount_paise']
            elif sip['type'] == 'debt':
                current_assets['debt'] += sip['monthly_amount_paise']
            else:
                # Default: add to cash
                current_assets['cash'] += sip['monthly_amount_paise']

        # b) Liabilities reduction (call loan_engine for each loan)
        total_liabilities = 0
        for loan_state in loan_states:
            if loan_state['remaining_principal'] <= 0:
                continue

            # Forecast one month ahead from current state
            forecast = forecast_from_state(
                remaining_principal_paise=loan_state['remaining_principal'],
                annual_rate_percent=loan_state['interest_rate'],
                emi_paise=loan_state['emi'],
                from_date=loan_state['current_date']
            )

            if forecast['schedule']:
                # Update loan state with first month's result
                first_period = forecast['schedule'][0]
                loan_state['remaining_principal'] = first_period['remaining_principal_paise']
                loan_state['current_date'] = add_months(loan_state['current_date'], 1)

            total_liabilities += loan_state['remaining_principal']

        # c) Compute totals
        total_assets = current_assets['cash'] + current_assets['equity'] + current_assets['debt']
        net_worth = total_assets - total_liabilities

        # Projected month key (YYYY-MM)
        projection_month = add_months(current_date, month)
        month_key = projection_month.strftime("%Y-%m")

        projections.append({
            "month": month_key,
            "projected_net_worth_paise": net_worth,
            "projected_assets_paise": total_assets,
            "projected_liabilities_paise": total_liabilities,
            "asset_breakdown": {
                "cash_paise": current_assets['cash'],
                "equity_paise": current_assets['equity'],
                "debt_paise": current_assets['debt'],
            }
        })

    # Build assumptions
    assumptions = {
        "equity_return_percent": equity_annual_return,
        "debt_return_percent": debt_annual_return,
        "savings_basis": "median_last_6_months" if monthly_savings > 0 else "no_savings_data",
        "monthly_compounding": True,
        "loan_interest_calculation": "daily_reducing_365_day",
        "months_projected": len(projections),
    }

    # Summary
    summary = {
        "starting_net_worth_paise": projections[0]["projected_net_worth_paise"] if projections else 0,
        "ending_net_worth_paise": projections[-1]["projected_net_worth_paise"] if projections else 0,
        "net_worth_change_paise": (projections[-1]["projected_net_worth_paise"] - projections[0]["projected_net_worth_paise"]) if projections else 0,
    }

    log.info("Net worth projection complete: %d months", len(projections))

    return {
        "projections": projections,
        "assumptions": assumptions,
        "summary": summary,
    }


# ============================================================
# Function 2: Project Loan Payoff
# ============================================================

def project_loan_payoff(
    db: "FinanceDB",
    loan_id: int
) -> dict:
    """
    Project when a specific loan will be fully paid off.

    Uses loan_engine.replay_payments() for current state,
    then loan_engine.forecast_from_state() for future projections.

    Args:
        db: FinanceDB instance
        loan_id: ID of the loan to project

    Returns:
        Dict with:
            - payoff_date: date when loan will be fully paid
            - remaining_months: int
            - total_remaining_interest_paise: int
            - remaining_principal_paise: int
            - is_closed: bool (if already paid off)
    """
    log.info("Projecting loan payoff for loan_id=%d", loan_id)

    with db.connection() as conn:
        # Fetch loan details
        cur = conn.execute("SELECT * FROM loans WHERE id = ?", (loan_id,))
        loan = cur.fetchone()

        if not loan:
            log.warning("Loan %d not found", loan_id)
            return {
                "payoff_date": None,
                "remaining_months": 0,
                "total_remaining_interest_paise": 0,
                "remaining_principal_paise": 0,
                "is_closed": True,
                "error": "Loan not found"
            }

        loan = dict(loan)

        # Check if already closed
        if loan.get('status') == 'closed' or loan.get('outstanding_paise', 0) <= 0:
            log.info("Loan %d is already closed", loan_id)
            return {
                "payoff_date": date.today(),
                "remaining_months": 0,
                "total_remaining_interest_paise": 0,
                "remaining_principal_paise": 0,
                "is_closed": True,
            }

        # Parse start date
        start_date = _parse_date(loan.get('start_date'))
        if not start_date:
            log.warning("Loan %d has invalid start_date", loan_id)
            return {
                "payoff_date": None,
                "remaining_months": 0,
                "total_remaining_interest_paise": 0,
                "remaining_principal_paise": loan.get('outstanding_paise', 0),
                "is_closed": False,
                "error": "Invalid start date"
            }

        # Fetch payment history
        cur = conn.execute(
            "SELECT * FROM loan_payments WHERE loan_id = ? ORDER BY payment_date ASC",
            (loan_id,)
        )
        payments = []
        for row in cur.fetchall():
            p = dict(row)
            payment_date = _parse_date(p.get('payment_date'))
            if payment_date:
                # Total payment amount
                total_amount = (p.get('principal_component_paise', 0) +
                               p.get('interest_component_paise', 0))
                payments.append({
                    "date": payment_date,
                    "amount_paise": total_amount,
                    "type": "EMI"
                })

    # Replay payments to get current state
    principal = loan.get('principal_paise', 0)
    rate = loan.get('interest_rate', 0)

    state = replay_payments(
        principal_paise=principal,
        annual_rate_percent=rate,
        start_date=start_date,
        payments=payments
    )

    remaining_principal = state['remaining_principal_paise']

    # If already paid off
    if remaining_principal <= 0:
        return {
            "payoff_date": state['last_date'],
            "remaining_months": 0,
            "total_remaining_interest_paise": 0,
            "remaining_principal_paise": 0,
            "is_closed": True,
        }

    # Forecast from current state
    emi = loan.get('emi_paise', 0)
    if emi <= 0:
        # Compute EMI if not set
        tenure = loan.get('tenure_months', 0)
        emi = compute_emi(principal, rate, tenure) if tenure > 0 else 0

    forecast = forecast_from_state(
        remaining_principal_paise=remaining_principal,
        annual_rate_percent=rate,
        emi_paise=emi,
        from_date=state['last_date']
    )

    result = {
        "payoff_date": forecast['projected_closure_date'],
        "remaining_months": forecast['months_remaining'],
        "total_remaining_interest_paise": forecast['future_interest_paise'],
        "remaining_principal_paise": remaining_principal,
        "is_closed": False,
    }

    log.info("Loan %d payoff projection: %d months remaining, payoff on %s",
             loan_id, result['remaining_months'], result['payoff_date'])

    return result


# ============================================================
# Function 3: Project Goal (Pure Math)
# ============================================================

def project_goal(
    monthly_savings_paise: int,
    target_paise: int,
    current_paise: int = 0,
    annual_return: float = 0.0
) -> dict:
    """
    Calculate months needed to reach a financial goal.

    Pure math function - no database access.

    Args:
        monthly_savings_paise: Monthly contribution amount in paise
        target_paise: Target amount to reach in paise
        current_paise: Starting balance in paise (default 0)
        annual_return: Expected annual return percentage (default 0)

    Returns:
        Dict with:
            - months_needed: int
            - projected_date: date
            - total_contributed_paise: int
            - total_returns_paise: int
    """
    log.info("Projecting goal: target=₹%.2f, monthly=₹%.2f, current=₹%.2f, return=%.1f%%",
             target_paise / 100, monthly_savings_paise / 100,
             current_paise / 100, annual_return)

    # Edge case: target already achieved
    if current_paise >= target_paise:
        return {
            "months_needed": 0,
            "projected_date": date.today(),
            "total_contributed_paise": 0,
            "total_returns_paise": 0,
            "target_already_achieved": True,
        }

    # Edge case: zero savings and zero return - impossible to reach target
    if monthly_savings_paise <= 0 and annual_return <= 0:
        return {
            "months_needed": None,
            "projected_date": None,
            "total_contributed_paise": 0,
            "total_returns_paise": 0,
            "target_achievable": False,
            "reason": "Zero savings and zero return - target cannot be reached"
        }

    # Calculate monthly rate
    monthly_rate = annual_return / 12 / 100

    # Simulate month by month
    balance = current_paise
    months = 0
    total_contributed = 0

    while balance < target_paise and months < GOAL_MAX_MONTHS:
        # Apply growth
        balance = int(balance * (1 + monthly_rate))
        # Add monthly savings
        balance += monthly_savings_paise
        total_contributed += monthly_savings_paise
        months += 1

    # Check if we hit the cap
    if months >= GOAL_MAX_MONTHS and balance < target_paise:
        return {
            "months_needed": None,
            "projected_date": None,
            "total_contributed_paise": total_contributed,
            "total_returns_paise": balance - current_paise - total_contributed,
            "target_achievable": False,
            "reason": f"Target not reached within {GOAL_MAX_MONTHS} months"
        }

    total_returns = balance - current_paise - total_contributed
    projected_date = add_months(date.today(), months)

    result = {
        "months_needed": months,
        "projected_date": projected_date,
        "total_contributed_paise": total_contributed,
        "total_returns_paise": total_returns,
        "target_achievable": True,
        "final_projected_amount_paise": balance,
    }

    log.info("Goal projection: %d months needed, projected date: %s",
             months, projected_date)

    return result


# ============================================================
# Function 4: What-If Analysis
# ============================================================

def what_if_analysis(
    db: "FinanceDB",
    scenario: dict
) -> dict:
    """
    Compare baseline projection with a modified scenario.

    Args:
        db: FinanceDB instance
        scenario: Dict with modifications:
            - increase_savings_by_paise: int (default 0)
            - extra_loan_payment_paise: int (default 0) - one-time prepayment
            - extra_loan_payment_loan_id: int (default None) - which loan
            - new_sip_paise: int (default 0)
            - new_sip_type: str (default 'equity') - 'equity' or 'debt'
            - equity_return_override_percent: float (default None)

    Returns:
        Dict with:
            - baseline: baseline projections
            - modified: modified projections
            - difference_at_1y_paise: int
            - difference_at_3y_paise: int
            - difference_at_5y_paise: int
            - percentage_improvement_5y: float
    """
    log.info("Running what-if analysis")

    # Extract scenario parameters with defaults
    increase_savings = scenario.get('increase_savings_by_paise', 0)
    extra_payment = scenario.get('extra_loan_payment_paise', 0)
    extra_payment_loan_id = scenario.get('extra_loan_payment_loan_id')
    new_sip = scenario.get('new_sip_paise', 0)
    new_sip_type = scenario.get('new_sip_type', 'equity')
    equity_override = scenario.get('equity_return_override_percent')

    # Compute baseline (60 months)
    equity_return = equity_override if equity_override is not None else DEFAULT_EQUITY_RETURN
    baseline = project_net_worth(db, months_ahead=60, equity_annual_return=equity_return)

    # Compute modified scenario
    # For this, we'll need to manually run the projection with modifications
    modified_projections = _compute_modified_projection(
        db=db,
        months_ahead=60,
        equity_annual_return=equity_return,
        increase_savings=increase_savings,
        extra_payment=extra_payment,
        extra_payment_loan_id=extra_payment_loan_id,
        new_sip=new_sip,
        new_sip_type=new_sip_type
    )

    # Calculate differences at specific intervals
    def get_net_worth_at_month(projections, month):
        if month <= len(projections):
            return projections[month - 1]['projected_net_worth_paise']
        return projections[-1]['projected_net_worth_paise'] if projections else 0

    baseline_projections = baseline['projections']

    diff_1y = get_net_worth_at_month(modified_projections, 12) - get_net_worth_at_month(baseline_projections, 12)
    diff_3y = get_net_worth_at_month(modified_projections, 36) - get_net_worth_at_month(baseline_projections, 36)
    diff_5y = get_net_worth_at_month(modified_projections, 60) - get_net_worth_at_month(baseline_projections, 60)

    # Calculate percentage improvement at 5 years
    baseline_5y = get_net_worth_at_month(baseline_projections, 60)
    pct_improvement = None
    if baseline_5y > 0:
        pct_improvement = round((diff_5y / baseline_5y) * 100, 2)
    elif diff_5y > 0:
        pct_improvement = None  # Cannot calculate percentage when baseline is zero

    # Build modified result structure matching baseline format
    modified = {
        "projections": modified_projections,
        "assumptions": baseline['assumptions'].copy(),
        "summary": {
            "starting_net_worth_paise": modified_projections[0]['projected_net_worth_paise'] if modified_projections else 0,
            "ending_net_worth_paise": modified_projections[-1]['projected_net_worth_paise'] if modified_projections else 0,
            "net_worth_change_paise": (modified_projections[-1]['projected_net_worth_paise'] - modified_projections[0]['projected_net_worth_paise']) if modified_projections else 0,
        }
    }

    # Add scenario modifications to assumptions
    modified['assumptions']['scenario_modifications'] = {
        "increased_savings_by_paise": increase_savings,
        "extra_loan_payment_paise": extra_payment,
        "extra_loan_payment_loan_id": extra_payment_loan_id,
        "new_sip_paise": new_sip,
        "new_sip_type": new_sip_type,
    }

    result = {
        "baseline": baseline['projections'],
        "modified": modified['projections'],
        "difference_at_1y_paise": diff_1y,
        "difference_at_3y_paise": diff_3y,
        "difference_at_5y_paise": diff_5y,
        "percentage_improvement_5y": pct_improvement,
        "baseline_summary": baseline['summary'],
        "modified_summary": modified['summary'],
        "assumptions": baseline['assumptions'],
    }

    log.info("What-if analysis complete: 5y improvement = %.2f%%", pct_improvement)

    return result


def _compute_modified_projection(
    db: "FinanceDB",
    months_ahead: int,
    equity_annual_return: float,
    increase_savings: int,
    extra_payment: int,
    extra_payment_loan_id: Optional[int],
    new_sip: int,
    new_sip_type: str
) -> List[dict]:
    """
    Compute modified projection with scenario changes.
    Internal helper for what_if_analysis.
    """
    # Fetch current state
    assets = _fetch_current_assets(db)
    loans = _fetch_active_loans(db)
    sips = _fetch_active_sips(db)
    base_savings = _compute_stabilized_monthly_savings(db)

    # Add new SIP
    if new_sip > 0:
        sips.append({
            'type': new_sip_type,
            'monthly_amount_paise': new_sip
        })

    # Adjust savings
    monthly_savings = base_savings + increase_savings

    # Prepare loan states with potential extra payment
    loan_states = _prepare_loan_states(db, loans)

    # Apply one-time extra payment if specified
    if extra_payment > 0 and extra_payment_loan_id:
        for loan_state in loan_states:
            if loan_state['id'] == extra_payment_loan_id:
                # Apply prepayment immediately
                loan_state['remaining_principal'] = max(0, loan_state['remaining_principal'] - extra_payment)
                log.info("Applied extra payment of ₹%.2f to loan %d",
                         extra_payment / 100, extra_payment_loan_id)
                break

    # Calculate monthly rates
    equity_monthly_rate = equity_annual_return / 12 / 100
    debt_monthly_rate = DEFAULT_DEBT_RETURN / 12 / 100

    # Run projection
    projections = []
    current_assets = assets.copy()
    current_date = date.today()

    for month in range(1, min(months_ahead + 1, MAX_PROJECTION_MONTHS)):
        # Assets
        current_assets['cash'] += monthly_savings
        current_assets['equity'] = int(current_assets['equity'] * (1 + equity_monthly_rate))
        current_assets['debt'] = int(current_assets['debt'] * (1 + debt_monthly_rate))

        for sip in sips:
            if sip['type'] == 'equity':
                current_assets['equity'] += sip['monthly_amount_paise']
            elif sip['type'] == 'debt':
                current_assets['debt'] += sip['monthly_amount_paise']
            else:
                current_assets['cash'] += sip['monthly_amount_paise']

        # Liabilities
        total_liabilities = 0
        for loan_state in loan_states:
            if loan_state['remaining_principal'] <= 0:
                continue

            forecast = forecast_from_state(
                remaining_principal_paise=loan_state['remaining_principal'],
                annual_rate_percent=loan_state['interest_rate'],
                emi_paise=loan_state['emi'],
                from_date=loan_state['current_date']
            )

            if forecast['schedule']:
                first_period = forecast['schedule'][0]
                loan_state['remaining_principal'] = first_period['remaining_principal_paise']
                loan_state['current_date'] = add_months(loan_state['current_date'], 1)

            total_liabilities += loan_state['remaining_principal']

        # Totals
        total_assets = current_assets['cash'] + current_assets['equity'] + current_assets['debt']
        net_worth = total_assets - total_liabilities

        projection_month = add_months(current_date, month)
        month_key = projection_month.strftime("%Y-%m")

        projections.append({
            "month": month_key,
            "projected_net_worth_paise": net_worth,
            "projected_assets_paise": total_assets,
            "projected_liabilities_paise": total_liabilities,
        })

    return projections


# ============================================================
# Helper Functions
# ============================================================

def _fetch_current_assets(db: "FinanceDB") -> dict:
    """Fetch current asset balances from database."""
    with db.connection() as conn:
        # Cash: savings, current, wallet accounts
        cur = conn.execute("""
            SELECT COALESCE(SUM(balance_paise), 0) as cash_paise
            FROM accounts
            WHERE account_type IN ('savings', 'current', 'wallet')
            AND is_active = 1
        """)
        cash = cur.fetchone()[0] or 0

        # Fixed deposits (treated as debt-like investments)
        cur = conn.execute("""
            SELECT COALESCE(SUM(balance_paise), 0) as fd_paise
            FROM accounts
            WHERE account_type = 'fd'
            AND is_active = 1
        """)
        fd = cur.fetchone()[0] or 0

        # Investments: Split by type
        # Equity investments: stocks, mutual_funds, crypto
        cur = conn.execute("""
            SELECT COALESCE(SUM(current_value_paise), 0) as equity_paise
            FROM investments
            WHERE type IN ('stock', 'mutual_fund', 'crypto')
            AND is_active = 1
        """)
        equity = cur.fetchone()[0] or 0

        # Debt investments: ppf, epf, nps, gold, real_estate, fd
        cur = conn.execute("""
            SELECT COALESCE(SUM(current_value_paise), 0) as debt_paise
            FROM investments
            WHERE type IN ('ppf', 'epf', 'nps', 'gold', 'real_estate', 'fd')
            AND is_active = 1
        """)
        debt = cur.fetchone()[0] or 0

        # Other investments treated as cash
        cur = conn.execute("""
            SELECT COALESCE(SUM(current_value_paise), 0) as other_paise
            FROM investments
            WHERE type = 'other'
            AND is_active = 1
        """)
        other = cur.fetchone()[0] or 0

    # Add FD to debt, other to cash
    return {
        'cash': cash + other,
        'equity': equity,
        'debt': debt + fd,
    }


def _fetch_active_loans(db: "FinanceDB") -> List[dict]:
    """Fetch active loans from database."""
    with db.connection() as conn:
        cur = conn.execute("""
            SELECT id, principal_paise, outstanding_paise, interest_rate,
                   emi_paise, tenure_months, start_date
            FROM loans
            WHERE status = 'active'
        """)
        return [dict(row) for row in cur.fetchall()]


def _fetch_active_sips(db: "FinanceDB") -> List[dict]:
    """Fetch active SIPs (recurring investment transactions)."""
    with db.connection() as conn:
        # Look for recurring transactions that might be SIPs
        # Heuristic: monthly debits with 'SIP' or investment-related descriptions
        cur = conn.execute("""
            SELECT amount_paise, description, category
            FROM recurring_transactions
            WHERE is_active = 1
            AND frequency = 'monthly'
            AND type = 'debit'
            AND (
                description LIKE '%SIP%'
                OR description LIKE '%mutual fund%'
                OR category IN ('Investment', 'SIP', 'Mutual Fund')
            )
        """)

        sips = []
        for row in cur.fetchall():
            desc = (row[1] or '').lower()
            category = (row[2] or '').lower()

            # Classify as equity or debt based on description/category
            sip_type = 'equity'  # default
            if any(kw in desc or kw in category for kw in ['debt', 'liquid', 'ppf', 'epf', 'fd']):
                sip_type = 'debt'
            elif any(kw in desc or kw in category for kw in ['equity', 'stock', 'growth']):
                sip_type = 'equity'

            sips.append({
                'type': sip_type,
                'monthly_amount_paise': row[0]
            })

        return sips


def _compute_stabilized_monthly_savings(db: "FinanceDB") -> int:
    """
    Compute stabilized monthly savings using median of last 6 months.
    Savings = income - expenses (EMI is already included in expenses)
    """
    with db.connection() as conn:
        # Get last 6 months of cashflow data
        cur = conn.execute("""
            SELECT
                strftime('%Y-%m', date_iso) as month,
                COALESCE(SUM(credit), 0) as income,
                COALESCE(SUM(debit), 0) as expenses
            FROM transactions
            WHERE date_iso >= date('now', '-6 months')
            AND date_iso IS NOT NULL
            GROUP BY strftime('%Y-%m', date_iso)
            ORDER BY month DESC
            LIMIT 6
        """)

        monthly_savings = []
        for row in cur.fetchall():
            savings = row[1] - row[2]  # income - expenses
            monthly_savings.append(savings)

    if not monthly_savings:
        log.warning("No cashflow history found for savings computation")
        return 0

    # Use median for stability
    stabilized = int(median(monthly_savings))
    log.info("Computed stabilized monthly savings: ₹%.2f (median of %d months)",
             stabilized / 100, len(monthly_savings))

    return stabilized


def _prepare_loan_states(db: "FinanceDB", loans: List[dict]) -> List[dict]:
    """
    Prepare loan states for forecasting by replaying payments.
    Returns list of loan state dicts ready for forecast_from_state().
    
    Optimized: N+1 queries → 2 queries total (regardless of loan count)
    - Was: N loans × 1 query per loan = N queries
    - Now: 1 query for all payments + Python grouping
    """
    states = []
    
    # Optimized: Fetch ALL payments for active loans in ONE query
    # This replaces N individual loan payment queries
    all_payments_grouped = db.get_all_loan_payments_grouped()
    
    log.debug("Preparing loan states for %d loans using batched payments", len(loans))

    for loan in loans:
        loan_id = loan['id']

        # Parse start date
        start_date = _parse_date(loan.get('start_date'))
        if not start_date:
            log.warning("Loan %d has invalid start_date, skipping", loan_id)
            continue

        # Use pre-fetched payments for this loan (already grouped by loan_id)
        loan_payments = all_payments_grouped.get(loan_id, [])
        payments = []
        for p in loan_payments:
            payment_date = _parse_date(p.get('payment_date'))
            if payment_date:
                total_amount = (p.get('principal_component_paise', 0) +
                               p.get('interest_component_paise', 0))
                payments.append({
                    "date": payment_date,
                    "amount_paise": total_amount,
                    "type": "EMI"
                })

        # Replay to get current state
        state = replay_payments(
            principal_paise=loan.get('principal_paise', 0),
            annual_rate_percent=loan.get('interest_rate', 0),
            start_date=start_date,
            payments=payments
        )

        # Compute EMI if not set
        emi = loan.get('emi_paise', 0)
        if emi <= 0:
            tenure = loan.get('tenure_months', 0)
            if tenure > 0:
                emi = compute_emi(loan.get('principal_paise', 0),
                                  loan.get('interest_rate', 0), tenure)

        states.append({
            'id': loan_id,
            'remaining_principal': state['remaining_principal_paise'],
            'interest_rate': loan.get('interest_rate', 0),
            'emi': emi,
            'current_date': state['last_date'],
        })

    return states


def _parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse date string to date object."""
    if not date_str:
        return None

    try:
        return date.fromisoformat(date_str)
    except (ValueError, TypeError):
        pass

    # Try DD/MM/YYYY format
    try:
        from datetime import datetime
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    except (ValueError, TypeError):
        pass

    return None
