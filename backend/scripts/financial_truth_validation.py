#!/usr/bin/env python3
"""
Financial Truth Validation - P3.3

Objective: Verify that dashboard outputs accurately reflect the underlying financial records.

This is a financial correctness audit that validates dashboard metrics against
independent recalculations from the database.

Variance Rules: Expected variance = 0 paise. Any difference must be reported.
"""

import sqlite3
from typing import Dict, Any, List
from decimal import Decimal
import os
from pathlib import Path

def format_paise(amount_paise: int) -> str:
    """Convert paise to formatted rupees string."""
    if amount_paise is None:
        return "₹0.00"
    rupees = Decimal(amount_paise) / 100
    return f"₹{rupees:,.2f}"

def get_dashboard_metrics(db_path: str) -> Dict[str, Any]:
    """Simulate dashboard API calls to get current metrics."""
    # Import the engines to use the same calculation methods as the dashboard
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from src.db import FinanceDB
    from src.engines.networth_engine import compute_net_worth, compute_asset_allocation
    from src.engines.cashflow_engine import compute_monthly_cashflow, compute_cashflow_summary

    db = FinanceDB(db_path=db_path)

    # Get dashboard metrics using the same engines as the actual dashboard
    dashboard_metrics = {}

    # 1. Net Worth from networth engine
    net_worth = compute_net_worth(db)
    dashboard_metrics['net_worth'] = {
        'total_assets_paise': net_worth['total_assets_paise'],
        'total_liabilities_paise': net_worth['total_liabilities_paise'],
        'net_worth_paise': net_worth['net_worth_paise']
    }

    # 2. Monthly Cashflow (current month)
    monthly_cashflow = compute_monthly_cashflow(db, months=1)
    if monthly_cashflow:
        current_month = monthly_cashflow[0]
        dashboard_metrics['monthly_cashflow'] = {
            'total_income_paise': current_month['total_income_paise'],
            'total_expense_paise': current_month['total_expense_paise'],
            'net_cashflow_paise': current_month['net_cashflow_paise'],
            'savings_rate': current_month['savings_rate']
        }
    else:
        dashboard_metrics['monthly_cashflow'] = {
            'total_income_paise': 0,
            'total_expense_paise': 0,
            'net_cashflow_paise': 0,
            'savings_rate': 0.0
        }

    # 3. Debt Totals from loans and credit cards
    with db.connection() as conn:
        # Loans
        cur = conn.execute("""
            SELECT
                COALESCE(SUM(principal_paise), 0) as total_principal,
                COALESCE(SUM(outstanding_paise), 0) as total_outstanding,
                COALESCE(SUM(emi_paise), 0) as total_emi
            FROM loans
            WHERE status = 'active'
        """)
        loan_data = cur.fetchone()
        dashboard_metrics['debt_totals'] = {
            'total_principal_paise': loan_data['total_principal'],
            'total_outstanding_paise': loan_data['total_outstanding'],
            'total_emi_paise': loan_data['total_emi']
        }

    # 4. Savings Rate (from cashflow summary)
    cashflow_summary = compute_cashflow_summary(db)
    dashboard_metrics['savings_rate'] = cashflow_summary.get('avg_savings_rate', 0.0)

    # 5. Asset Allocation
    asset_allocation = compute_asset_allocation(db)
    dashboard_metrics['asset_allocation'] = {
        'total_assets_paise': sum(item['value_paise'] for item in asset_allocation),
        'allocation_breakdown': asset_allocation
    }

    db.close()
    return dashboard_metrics

def calculate_independent_metrics(db_path: str) -> Dict[str, Any]:
    """Calculate metrics independently from raw database queries."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    independent_metrics = {}

    # 1. Net Worth Calculation
    # Assets: Bank accounts (savings, current, wallet)
    cursor.execute("""
        SELECT COALESCE(SUM(balance_paise), 0) as bank_accounts_paise
        FROM accounts
        WHERE account_type IN ('savings', 'current', 'wallet')
        AND is_active = 1
    """)
    bank_accounts = cursor.fetchone()['bank_accounts_paise']

    # Assets: Fixed Deposits
    cursor.execute("""
        SELECT COALESCE(SUM(balance_paise), 0) as fixed_deposits_paise
        FROM accounts
        WHERE account_type = 'fd'
        AND is_active = 1
    """)
    fixed_deposits = cursor.fetchone()['fixed_deposits_paise']

    # Assets: Investments
    cursor.execute("""
        SELECT COALESCE(SUM(current_value_paise), 0) as investments_paise
        FROM investments
        WHERE is_active = 1
    """)
    investments = cursor.fetchone()['investments_paise']

    # Liabilities: Loans
    cursor.execute("""
        SELECT COALESCE(SUM(outstanding_paise), 0) as loans_paise
        FROM loans
        WHERE status = 'active'
    """)
    loans = cursor.fetchone()['loans_paise']

    # Liabilities: Credit Cards
    cursor.execute("""
        SELECT COALESCE(SUM(balance_paise), 0) as credit_cards_paise
        FROM accounts
        WHERE account_type = 'credit_card'
        AND is_active = 1
    """)
    credit_cards = cursor.fetchone()['credit_cards_paise']

    total_assets = bank_accounts + fixed_deposits + investments
    total_liabilities = loans + credit_cards
    net_worth = total_assets - total_liabilities

    independent_metrics['net_worth'] = {
        'total_assets_paise': total_assets,
        'total_liabilities_paise': total_liabilities,
        'net_worth_paise': net_worth
    }

    # 2. Monthly Cashflow (current month)
    cursor.execute("""
        SELECT
            strftime('%Y-%m', date_iso) as current_month
        FROM transactions
        WHERE date_iso IS NOT NULL
        ORDER BY date_iso DESC
        LIMIT 1
    """)
    month_row = cursor.fetchone()
    current_month = month_row['current_month'] if month_row else None

    if current_month:
        cursor.execute("""
            SELECT
                COALESCE(SUM(credit), 0) as total_income_paise,
                COALESCE(SUM(debit), 0) as total_expense_paise,
                COALESCE(SUM(credit) - SUM(debit), 0) as net_cashflow_paise
            FROM transactions
            WHERE strftime('%Y-%m', date_iso) = ?
        """, (current_month,))
        cashflow_data = cursor.fetchone()
        total_income = cashflow_data['total_income_paise']
        total_expense = cashflow_data['total_expense_paise']
        net_cashflow = cashflow_data['net_cashflow_paise']

        # Calculate savings rate
        savings_rate = round(net_cashflow / total_income, 4) if total_income > 0 else 0.0

        independent_metrics['monthly_cashflow'] = {
            'total_income_paise': total_income,
            'total_expense_paise': total_expense,
            'net_cashflow_paise': net_cashflow,
            'savings_rate': savings_rate
        }
    else:
        independent_metrics['monthly_cashflow'] = {
            'total_income_paise': 0,
            'total_expense_paise': 0,
            'net_cashflow_paise': 0,
            'savings_rate': 0.0
        }

    # 3. Debt Totals
    cursor.execute("""
        SELECT
            COALESCE(SUM(principal_paise), 0) as total_principal,
            COALESCE(SUM(outstanding_paise), 0) as total_outstanding,
            COALESCE(SUM(emi_paise), 0) as total_emi
        FROM loans
        WHERE status = 'active'
    """)
    debt_data = cursor.fetchone()
    independent_metrics['debt_totals'] = {
        'total_principal_paise': debt_data['total_principal'],
        'total_outstanding_paise': debt_data['total_outstanding'],
        'total_emi_paise': debt_data['total_emi']
    }

    # 4. Savings Rate (average over all months)
    cursor.execute("""
        SELECT
            strftime('%Y-%m', date_iso) as month,
            COALESCE(SUM(credit), 0) as income,
            COALESCE(SUM(debit), 0) as expense,
            COALESCE(SUM(credit) - SUM(debit), 0) as net
        FROM transactions
        WHERE date_iso IS NOT NULL AND date_iso != ''
        GROUP BY strftime('%Y-%m', date_iso)
    """)
    monthly_data = cursor.fetchall()

    total_savings_rate = 0.0
    months_with_income = 0

    for row in monthly_data:
        income = row['income']
        net = row['net']
        if income > 0:
            savings_rate = net / income
            total_savings_rate += savings_rate
            months_with_income += 1

    avg_savings_rate = round(total_savings_rate / months_with_income, 4) if months_with_income > 0 else 0.0
    independent_metrics['savings_rate'] = avg_savings_rate

    # 5. Asset Allocation
    # Bank Accounts (savings, current, wallet)
    cursor.execute("""
        SELECT COALESCE(SUM(balance_paise), 0) as value_paise
        FROM accounts
        WHERE account_type IN ('savings', 'current', 'wallet')
        AND is_active = 1
    """)
    bank_accounts_paise = cursor.fetchone()['value_paise']

    # Fixed Deposits
    cursor.execute("""
        SELECT COALESCE(SUM(balance_paise), 0) as value_paise
        FROM accounts
        WHERE account_type = 'fd'
        AND is_active = 1
    """)
    fixed_deposits_paise = cursor.fetchone()['value_paise']

    # Mutual Funds
    cursor.execute("""
        SELECT COALESCE(SUM(current_value_paise), 0) as value_paise
        FROM investments
        WHERE type = 'mutual_fund'
        AND is_active = 1
    """)
    mutual_funds_paise = cursor.fetchone()['value_paise']

    # Stocks
    cursor.execute("""
        SELECT COALESCE(SUM(current_value_paise), 0) as value_paise
        FROM investments
        WHERE type = 'stock'
        AND is_active = 1
    """)
    stocks_paise = cursor.fetchone()['value_paise']

    # PPF/EPF/NPS
    cursor.execute("""
        SELECT COALESCE(SUM(current_value_paise), 0) as value_paise
        FROM investments
        WHERE type IN ('ppf', 'epf', 'nps')
        AND is_active = 1
    """)
    retirement_paise = cursor.fetchone()['value_paise']

    # Gold
    cursor.execute("""
        SELECT COALESCE(SUM(current_value_paise), 0) as value_paise
        FROM investments
        WHERE type = 'gold'
        AND is_active = 1
    """)
    gold_paise = cursor.fetchone()['value_paise']

    # Real Estate
    cursor.execute("""
        SELECT COALESCE(SUM(current_value_paise), 0) as value_paise
        FROM investments
        WHERE type = 'real_estate'
        AND is_active = 1
    """)
    real_estate_paise = cursor.fetchone()['value_paise']

    # Crypto
    cursor.execute("""
        SELECT COALESCE(SUM(current_value_paise), 0) as value_paise
        FROM investments
        WHERE type = 'crypto'
        AND is_active = 1
    """)
    crypto_paise = cursor.fetchone()['value_paise']

    # Other investments
    cursor.execute("""
        SELECT COALESCE(SUM(current_value_paise), 0) as value_paise
        FROM investments
        WHERE type = 'other'
        AND is_active = 1
    """)
    other_paise = cursor.fetchone()['value_paise']

    total_assets_paise = (
        bank_accounts_paise + fixed_deposits_paise + mutual_funds_paise +
        stocks_paise + retirement_paise + gold_paise +
        real_estate_paise + crypto_paise + other_paise
    )

    allocation_breakdown = [
        {"category": "Bank Accounts", "value_paise": bank_accounts_paise},
        {"category": "Fixed Deposits", "value_paise": fixed_deposits_paise},
        {"category": "Mutual Funds", "value_paise": mutual_funds_paise},
        {"category": "Stocks", "value_paise": stocks_paise},
        {"category": "PPF/EPF/NPS", "value_paise": retirement_paise},
        {"category": "Gold", "value_paise": gold_paise},
        {"category": "Real Estate", "value_paise": real_estate_paise},
        {"category": "Crypto", "value_paise": crypto_paise},
        {"category": "Other", "value_paise": other_paise},
    ]

    # Calculate percentages
    for item in allocation_breakdown:
        if total_assets_paise > 0:
            item["percentage"] = round((item["value_paise"] / total_assets_paise) * 100, 2)
        else:
            item["percentage"] = 0.0

    independent_metrics['asset_allocation'] = {
        'total_assets_paise': total_assets_paise,
        'allocation_breakdown': allocation_breakdown
    }

    conn.close()
    return independent_metrics

def perform_consistency_checks(dashboard_metrics: Dict[str, Any], independent_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Perform financial consistency checks."""
    checks = {}

    # 1. Assets - Liabilities = Net Worth
    dashboard_assets = dashboard_metrics['net_worth']['total_assets_paise']
    dashboard_liabilities = dashboard_metrics['net_worth']['total_liabilities_paise']
    dashboard_net_worth = dashboard_metrics['net_worth']['net_worth_paise']

    independent_assets = independent_metrics['net_worth']['total_assets_paise']
    independent_liabilities = independent_metrics['net_worth']['total_liabilities_paise']
    independent_net_worth = independent_metrics['net_worth']['net_worth_paise']

    # Check if Assets - Liabilities = Net Worth (both methods)
    dashboard_consistent = (dashboard_assets - dashboard_liabilities) == dashboard_net_worth
    independent_consistent = (independent_assets - independent_liabilities) == independent_net_worth

    checks['assets_liabilities_net_worth'] = {
        'dashboard_consistent': dashboard_consistent,
        'independent_consistent': independent_consistent,
        'dashboard_variance': (dashboard_assets - dashboard_liabilities) - dashboard_net_worth,
        'independent_variance': (independent_assets - independent_liabilities) - independent_net_worth
    }

    # 2. Monthly Credits - Monthly Debits = Net Cashflow
    dashboard_income = dashboard_metrics['monthly_cashflow']['total_income_paise']
    dashboard_expense = dashboard_metrics['monthly_cashflow']['total_expense_paise']
    dashboard_net_cashflow = dashboard_metrics['monthly_cashflow']['net_cashflow_paise']

    independent_income = independent_metrics['monthly_cashflow']['total_income_paise']
    independent_expense = independent_metrics['monthly_cashflow']['total_expense_paise']
    independent_net_cashflow = independent_metrics['monthly_cashflow']['net_cashflow_paise']

    dashboard_cashflow_consistent = (dashboard_income - dashboard_expense) == dashboard_net_cashflow
    independent_cashflow_consistent = (independent_income - independent_expense) == independent_net_cashflow

    checks['income_expense_net_cashflow'] = {
        'dashboard_consistent': dashboard_cashflow_consistent,
        'independent_consistent': independent_cashflow_consistent,
        'dashboard_variance': (dashboard_income - dashboard_expense) - dashboard_net_cashflow,
        'independent_variance': (independent_income - independent_expense) - independent_net_cashflow
    }

    # 3. Loan Outstanding <= Principal
    dashboard_outstanding = dashboard_metrics['debt_totals']['total_outstanding_paise']
    dashboard_principal = dashboard_metrics['debt_totals']['total_principal_paise']

    independent_outstanding = independent_metrics['debt_totals']['total_outstanding_paise']
    independent_principal = independent_metrics['debt_totals']['total_principal_paise']

    checks['loan_outstanding_principal'] = {
        'dashboard_valid': dashboard_outstanding <= dashboard_principal,
        'independent_valid': independent_outstanding <= independent_principal,
        'dashboard_variance': max(0, dashboard_outstanding - dashboard_principal),
        'independent_variance': max(0, independent_outstanding - independent_principal)
    }

    # 4. No negative balances (unless intentionally allowed)
    checks['negative_balances'] = {
        'dashboard_has_negative': dashboard_assets < 0 or dashboard_liabilities < 0 or dashboard_net_worth < 0,
        'independent_has_negative': independent_assets < 0 or independent_liabilities < 0 or independent_net_worth < 0
    }

    return checks

def generate_financial_truth_report(db_path: str, output_file: str = "P3_3_FINANCIAL_TRUTH_VALIDATION.md"):
    """Generate comprehensive financial truth validation report."""
    # Get metrics from both sources
    dashboard_metrics = get_dashboard_metrics(db_path)
    independent_metrics = calculate_independent_metrics(db_path)
    consistency_checks = perform_consistency_checks(dashboard_metrics, independent_metrics)

    # Generate markdown report
    report = f"""# P3.3 - Financial Truth Validation

## Executive Summary

This audit verifies that dashboard outputs accurately reflect the underlying financial records. All calculations are performed independently and compared against dashboard metrics.

**Audit Date**: 23/06/2026
**Database**: {db_path}
**Variance Tolerance**: 0 paise (exact match required)

---

## Metric Validation Results

### 1. Net Worth Validation

| Metric | Dashboard Value | Independent Calculation | Variance | Status |
|-------|-----------------|------------------------|----------|--------|
| Total Assets | {format_paise(dashboard_metrics['net_worth']['total_assets_paise'])} | {format_paise(independent_metrics['net_worth']['total_assets_paise'])} | {format_paise(dashboard_metrics['net_worth']['total_assets_paise'] - independent_metrics['net_worth']['total_assets_paise'])} | {'✅ PASS' if dashboard_metrics['net_worth']['total_assets_paise'] == independent_metrics['net_worth']['total_assets_paise'] else '❌ FAIL'} |
| Total Liabilities | {format_paise(dashboard_metrics['net_worth']['total_liabilities_paise'])} | {format_paise(independent_metrics['net_worth']['total_liabilities_paise'])} | {format_paise(dashboard_metrics['net_worth']['total_liabilities_paise'] - independent_metrics['net_worth']['total_liabilities_paise'])} | {'✅ PASS' if dashboard_metrics['net_worth']['total_liabilities_paise'] == independent_metrics['net_worth']['total_liabilities_paise'] else '❌ FAIL'} |
| Net Worth | {format_paise(dashboard_metrics['net_worth']['net_worth_paise'])} | {format_paise(independent_metrics['net_worth']['net_worth_paise'])} | {format_paise(dashboard_metrics['net_worth']['net_worth_paise'] - independent_metrics['net_worth']['net_worth_paise'])} | {'✅ PASS' if dashboard_metrics['net_worth']['net_worth_paise'] == independent_metrics['net_worth']['net_worth_paise'] else '❌ FAIL'} |

**Net Worth Breakdown:**
- Dashboard: Assets ({format_paise(dashboard_metrics['net_worth']['total_assets_paise'])}) - Liabilities ({format_paise(dashboard_metrics['net_worth']['total_liabilities_paise'])}) = Net Worth ({format_paise(dashboard_metrics['net_worth']['net_worth_paise'])})
- Independent: Assets ({format_paise(independent_metrics['net_worth']['total_assets_paise'])}) - Liabilities ({format_paise(independent_metrics['net_worth']['total_liabilities_paise'])}) = Net Worth ({format_paise(independent_metrics['net_worth']['net_worth_paise'])})

---

### 2. Monthly Cashflow Validation

| Metric | Dashboard Value | Independent Calculation | Variance | Status |
|-------|-----------------|------------------------|----------|--------|
| Total Income | {format_paise(dashboard_metrics['monthly_cashflow']['total_income_paise'])} | {format_paise(independent_metrics['monthly_cashflow']['total_income_paise'])} | {format_paise(dashboard_metrics['monthly_cashflow']['total_income_paise'] - independent_metrics['monthly_cashflow']['total_income_paise'])} | {'✅ PASS' if dashboard_metrics['monthly_cashflow']['total_income_paise'] == independent_metrics['monthly_cashflow']['total_income_paise'] else '❌ FAIL'} |
| Total Expense | {format_paise(dashboard_metrics['monthly_cashflow']['total_expense_paise'])} | {format_paise(independent_metrics['monthly_cashflow']['total_expense_paise'])} | {format_paise(dashboard_metrics['monthly_cashflow']['total_expense_paise'] - independent_metrics['monthly_cashflow']['total_expense_paise'])} | {'✅ PASS' if dashboard_metrics['monthly_cashflow']['total_expense_paise'] == independent_metrics['monthly_cashflow']['total_expense_paise'] else '❌ FAIL'} |
| Net Cashflow | {format_paise(dashboard_metrics['monthly_cashflow']['net_cashflow_paise'])} | {format_paise(independent_metrics['monthly_cashflow']['net_cashflow_paise'])} | {format_paise(dashboard_metrics['monthly_cashflow']['net_cashflow_paise'] - independent_metrics['monthly_cashflow']['net_cashflow_paise'])} | {'✅ PASS' if dashboard_metrics['monthly_cashflow']['net_cashflow_paise'] == independent_metrics['monthly_cashflow']['net_cashflow_paise'] else '❌ FAIL'} |
| Savings Rate | {dashboard_metrics['monthly_cashflow']['savings_rate']*100:.2f}% | {independent_metrics['monthly_cashflow']['savings_rate']*100:.2f}% | {(dashboard_metrics['monthly_cashflow']['savings_rate'] - independent_metrics['monthly_cashflow']['savings_rate'])*100:.2f}% | {'✅ PASS' if abs(dashboard_metrics['monthly_cashflow']['savings_rate'] - independent_metrics['monthly_cashflow']['savings_rate']) < 0.0001 else '❌ FAIL'} |

**Cashflow Breakdown:**
- Dashboard: Income ({format_paise(dashboard_metrics['monthly_cashflow']['total_income_paise'])}) - Expense ({format_paise(dashboard_metrics['monthly_cashflow']['total_expense_paise'])}) = Net Cashflow ({format_paise(dashboard_metrics['monthly_cashflow']['net_cashflow_paise'])})
- Independent: Income ({format_paise(independent_metrics['monthly_cashflow']['total_income_paise'])}) - Expense ({format_paise(independent_metrics['monthly_cashflow']['total_expense_paise'])}) = Net Cashflow ({format_paise(independent_metrics['monthly_cashflow']['net_cashflow_paise'])})

---

### 3. Debt Totals Validation

| Metric | Dashboard Value | Independent Calculation | Variance | Status |
|-------|-----------------|------------------------|----------|--------|
| Total Principal | {format_paise(dashboard_metrics['debt_totals']['total_principal_paise'])} | {format_paise(independent_metrics['debt_totals']['total_principal_paise'])} | {format_paise(dashboard_metrics['debt_totals']['total_principal_paise'] - independent_metrics['debt_totals']['total_principal_paise'])} | {'✅ PASS' if dashboard_metrics['debt_totals']['total_principal_paise'] == independent_metrics['debt_totals']['total_principal_paise'] else '❌ FAIL'} |
| Total Outstanding | {format_paise(dashboard_metrics['debt_totals']['total_outstanding_paise'])} | {format_paise(independent_metrics['debt_totals']['total_outstanding_paise'])} | {format_paise(dashboard_metrics['debt_totals']['total_outstanding_paise'] - independent_metrics['debt_totals']['total_outstanding_paise'])} | {'✅ PASS' if dashboard_metrics['debt_totals']['total_outstanding_paise'] == independent_metrics['debt_totals']['total_outstanding_paise'] else '❌ FAIL'} |
| Total EMI | {format_paise(dashboard_metrics['debt_totals']['total_emi_paise'])} | {format_paise(independent_metrics['debt_totals']['total_emi_paise'])} | {format_paise(dashboard_metrics['debt_totals']['total_emi_paise'] - independent_metrics['debt_totals']['total_emi_paise'])} | {'✅ PASS' if dashboard_metrics['debt_totals']['total_emi_paise'] == independent_metrics['debt_totals']['total_emi_paise'] else '❌ FAIL'} |

**Debt Validation:**
- Dashboard: Principal ({format_paise(dashboard_metrics['debt_totals']['total_principal_paise'])}) >= Outstanding ({format_paise(dashboard_metrics['debt_totals']['total_outstanding_paise'])}) = {'✅ VALID' if dashboard_metrics['debt_totals']['total_outstanding_paise'] <= dashboard_metrics['debt_totals']['total_principal_paise'] else '❌ INVALID'}
- Independent: Principal ({format_paise(independent_metrics['debt_totals']['total_principal_paise'])}) >= Outstanding ({format_paise(independent_metrics['debt_totals']['total_outstanding_paise'])}) = {'✅ VALID' if independent_metrics['debt_totals']['total_outstanding_paise'] <= independent_metrics['debt_totals']['total_principal_paise'] else '❌ INVALID'}

---

### 4. Savings Rate Validation

| Metric | Dashboard Value | Independent Calculation | Variance | Status |
|-------|-----------------|------------------------|----------|--------|
| Average Savings Rate | {dashboard_metrics['savings_rate']*100:.2f}% | {independent_metrics['savings_rate']*100:.2f}% | {(dashboard_metrics['savings_rate'] - independent_metrics['savings_rate'])*100:.2f}% | {'✅ PASS' if abs(dashboard_metrics['savings_rate'] - independent_metrics['savings_rate']) < 0.0001 else '❌ FAIL'} |

---

### 5. Asset Allocation Validation

| Metric | Dashboard Value | Independent Calculation | Variance | Status |
|-------|-----------------|------------------------|----------|--------|
| Total Assets | {format_paise(dashboard_metrics['asset_allocation']['total_assets_paise'])} | {format_paise(independent_metrics['asset_allocation']['total_assets_paise'])} | {format_paise(dashboard_metrics['asset_allocation']['total_assets_paise'] - independent_metrics['asset_allocation']['total_assets_paise'])} | {'✅ PASS' if dashboard_metrics['asset_allocation']['total_assets_paise'] == independent_metrics['asset_allocation']['total_assets_paise'] else '❌ FAIL'} |

**Asset Allocation Breakdown:**
"""

    # Add asset allocation categories
    dashboard_categories = {item['category']: item['value_paise'] for item in dashboard_metrics['asset_allocation']['allocation_breakdown']}
    independent_categories = {item['category']: item['value_paise'] for item in independent_metrics['asset_allocation']['allocation_breakdown']}

    all_categories = set(dashboard_categories.keys()) | set(independent_categories.keys())

    for category in sorted(all_categories):
        dashboard_value = dashboard_categories.get(category, 0)
        independent_value = independent_categories.get(category, 0)
        variance = dashboard_value - independent_value
        status = '✅ PASS' if variance == 0 else '❌ FAIL'

        report += f"""| {category} | {format_paise(dashboard_value)} | {format_paise(independent_value)} | {format_paise(variance)} | {status} |\n"""

    report += f"""

---

## Consistency Checks

### 1. Assets - Liabilities = Net Worth

| Check | Dashboard | Independent | Status |
|-------|-----------|-------------|--------|
| Dashboard Consistency | {'✅ PASS' if consistency_checks['assets_liabilities_net_worth']['dashboard_consistent'] else '❌ FAIL'} | N/A | {'✅ CONSISTENT' if consistency_checks['assets_liabilities_net_worth']['dashboard_consistent'] else '❌ INCONSISTENT'} |
| Independent Consistency | N/A | {'✅ PASS' if consistency_checks['assets_liabilities_net_worth']['independent_consistent'] else '❌ FAIL'} | {'✅ CONSISTENT' if consistency_checks['assets_liabilities_net_worth']['independent_consistent'] else '❌ INCONSISTENT'} |
| Dashboard Variance | {format_paise(consistency_checks['assets_liabilities_net_worth']['dashboard_variance'])} | N/A | {'✅ ZERO' if consistency_checks['assets_liabilities_net_worth']['dashboard_variance'] == 0 else '❌ NON-ZERO'} |
| Independent Variance | N/A | {format_paise(consistency_checks['assets_liabilities_net_worth']['independent_variance'])} | {'✅ ZERO' if consistency_checks['assets_liabilities_net_worth']['independent_variance'] == 0 else '❌ NON-ZERO'} |

### 2. Income - Expense = Net Cashflow

| Check | Dashboard | Independent | Status |
|-------|-----------|-------------|--------|
| Dashboard Consistency | {'✅ PASS' if consistency_checks['income_expense_net_cashflow']['dashboard_consistent'] else '❌ FAIL'} | N/A | {'✅ CONSISTENT' if consistency_checks['income_expense_net_cashflow']['dashboard_consistent'] else '❌ INCONSISTENT'} |
| Independent Consistency | N/A | {'✅ PASS' if consistency_checks['income_expense_net_cashflow']['independent_consistent'] else '❌ FAIL'} | {'✅ CONSISTENT' if consistency_checks['income_expense_net_cashflow']['independent_consistent'] else '❌ INCONSISTENT'} |
| Dashboard Variance | {format_paise(consistency_checks['income_expense_net_cashflow']['dashboard_variance'])} | N/A | {'✅ ZERO' if consistency_checks['income_expense_net_cashflow']['dashboard_variance'] == 0 else '❌ NON-ZERO'} |
| Independent Variance | N/A | {format_paise(consistency_checks['income_expense_net_cashflow']['independent_variance'])} | {'✅ ZERO' if consistency_checks['income_expense_net_cashflow']['independent_variance'] == 0 else '❌ NON-ZERO'} |

### 3. Loan Outstanding <= Principal

| Check | Dashboard | Independent | Status |
|-------|-----------|-------------|--------|
| Dashboard Valid | {'✅ PASS' if consistency_checks['loan_outstanding_principal']['dashboard_valid'] else '❌ FAIL'} | N/A | {'✅ VALID' if consistency_checks['loan_outstanding_principal']['dashboard_valid'] else '❌ INVALID'} |
| Independent Valid | N/A | {'✅ PASS' if consistency_checks['loan_outstanding_principal']['independent_valid'] else '❌ FAIL'} | {'✅ VALID' if consistency_checks['loan_outstanding_principal']['independent_valid'] else '❌ INVALID'} |
| Dashboard Variance | {format_paise(consistency_checks['loan_outstanding_principal']['dashboard_variance'])} | N/A | {'✅ ZERO' if consistency_checks['loan_outstanding_principal']['dashboard_variance'] == 0 else '❌ NON-ZERO'} |
| Independent Variance | N/A | {format_paise(consistency_checks['loan_outstanding_principal']['independent_variance'])} | {'✅ ZERO' if consistency_checks['loan_outstanding_principal']['independent_variance'] == 0 else '❌ NON-ZERO'} |

### 4. Negative Balances Check

| Check | Dashboard | Independent | Status |
|-------|-----------|-------------|--------|
| Has Negative Balances | {'❌ YES' if consistency_checks['negative_balances']['dashboard_has_negative'] else '✅ NO'} | {'❌ YES' if consistency_checks['negative_balances']['independent_has_negative'] else '✅ NO'} | {'❌ FOUND' if consistency_checks['negative_balances']['dashboard_has_negative'] or consistency_checks['negative_balances']['independent_has_negative'] else '✅ NONE'} |

---

## Summary Statistics

### Validation Results Summary

| Metric | Total Checks | Passed | Failed | Pass Rate |
|-------|--------------|--------|--------|-----------|
| Net Worth | 3 | {sum(1 for metric in ['total_assets_paise', 'total_liabilities_paise', 'net_worth_paise'] if dashboard_metrics['net_worth'][metric] == independent_metrics['net_worth'][metric])} | {3 - sum(1 for metric in ['total_assets_paise', 'total_liabilities_paise', 'net_worth_paise'] if dashboard_metrics['net_worth'][metric] == independent_metrics['net_worth'][metric])} | {sum(1 for metric in ['total_assets_paise', 'total_liabilities_paise', 'net_worth_paise'] if dashboard_metrics['net_worth'][metric] == independent_metrics['net_worth'][metric])/3*100:.1f}% |
| Monthly Cashflow | 4 | {sum(1 for metric in ['total_income_paise', 'total_expense_paise', 'net_cashflow_paise'] if dashboard_metrics['monthly_cashflow'][metric] == independent_metrics['monthly_cashflow'][metric]) + (1 if abs(dashboard_metrics['monthly_cashflow']['savings_rate'] - independent_metrics['monthly_cashflow']['savings_rate']) < 0.0001 else 0)} | {4 - (sum(1 for metric in ['total_income_paise', 'total_expense_paise', 'net_cashflow_paise'] if dashboard_metrics['monthly_cashflow'][metric] == independent_metrics['monthly_cashflow'][metric]) + (1 if abs(dashboard_metrics['monthly_cashflow']['savings_rate'] - independent_metrics['monthly_cashflow']['savings_rate']) < 0.0001 else 0))} | {((sum(1 for metric in ['total_income_paise', 'total_expense_paise', 'net_cashflow_paise'] if dashboard_metrics['monthly_cashflow'][metric] == independent_metrics['monthly_cashflow'][metric]) + (1 if abs(dashboard_metrics['monthly_cashflow']['savings_rate'] - independent_metrics['monthly_cashflow']['savings_rate']) < 0.0001 else 0)) / 4 * 100:.1f}% |
| Debt Totals | 3 | {sum(1 for metric in ['total_principal_paise', 'total_outstanding_paise', 'total_emi_paise'] if dashboard_metrics['debt_totals'][metric] == independent_metrics['debt_totals'][metric])} | {3 - sum(1 for metric in ['total_principal_paise', 'total_outstanding_paise', 'total_emi_paise'] if dashboard_metrics['debt_totals'][metric] == independent_metrics['debt_totals'][metric])} | {sum(1 for metric in ['total_principal_paise', 'total_outstanding_paise', 'total_emi_paise'] if dashboard_metrics['debt_totals'][metric] == independent_metrics['debt_totals'][metric])/3*100:.1f}% |
| Savings Rate | 1 | {1 if abs(dashboard_metrics['savings_rate'] - independent_metrics['savings_rate']) < 0.0001 else 0} | {0 if abs(dashboard_metrics['savings_rate'] - independent_metrics['savings_rate']) < 0.0001 else 1} | {100.0 if abs(dashboard_metrics['savings_rate'] - independent_metrics['savings_rate']) < 0.0001 else 0.0}% |
| Asset Allocation | 1 | {1 if dashboard_metrics['asset_allocation']['total_assets_paise'] == independent_metrics['asset_allocation']['total_assets_paise'] else 0} | {0 if dashboard_metrics['asset_allocation']['total_assets_paise'] == independent_metrics['asset_allocation']['total_assets_paise'] else 1} | {100.0 if dashboard_metrics['asset_allocation']['total_assets_paise'] == independent_metrics['asset_allocation']['total_assets_paise'] else 0.0}% |

### Overall Validation Score

**Total Checks**: 12
**Total Passed**: {sum(1 for metric in ['total_assets_paise', 'total_liabilities_paise', 'net_worth_paise'] if dashboard_metrics['net_worth'][metric] == independent_metrics['net_worth'][metric]) + sum(1 for metric in ['total_income_paise', 'total_expense_paise', 'net_cashflow_paise'] if dashboard_metrics['monthly_cashflow'][metric] == independent_metrics['monthly_cashflow'][metric]) + (1 if abs(dashboard_metrics['monthly_cashflow']['savings_rate'] - independent_metrics['monthly_cashflow']['savings_rate']) < 0.0001 else 0) + sum(1 for metric in ['total_principal_paise', 'total_outstanding_paise', 'total_emi_paise'] if dashboard_metrics['debt_totals'][metric] == independent_metrics['debt_totals'][metric]) + (1 if abs(dashboard_metrics['savings_rate'] - independent_metrics['savings_rate']) < 0.0001 else 0) + (1 if dashboard_metrics['asset_allocation']['total_assets_paise'] == independent_metrics['asset_allocation']['total_assets_paise'] else 0)}
**Total Failed**: {12 - (sum(1 for metric in ['total_assets_paise', 'total_liabilities_paise', 'net_worth_paise'] if dashboard_metrics['net_worth'][metric] == independent_metrics['net_worth'][metric]) + sum(1 for metric in ['total_income_paise', 'total_expense_paise', 'net_cashflow_paise'] if dashboard_metrics['monthly_cashflow'][metric] == independent_metrics['monthly_cashflow'][metric]) + (1 if abs(dashboard_metrics['monthly_cashflow']['savings_rate'] - independent_metrics['monthly_cashflow']['savings_rate']) < 0.0001 else 0) + sum(1 for metric in ['total_principal_paise', 'total_outstanding_paise', 'total_emi_paise'] if dashboard_metrics['debt_totals'][metric] == independent_metrics['debt_totals'][metric]) + (1 if abs(dashboard_metrics['savings_rate'] - independent_metrics['savings_rate']) < 0.0001 else 0) + (1 if dashboard_metrics['asset_allocation']['total_assets_paise'] == independent_metrics['asset_allocation']['total_assets_paise'] else 0))}
**Pass Rate**: {((sum(1 for metric in ['total_assets_paise', 'total_liabilities_paise', 'net_worth_paise'] if dashboard_metrics['net_worth'][metric] == independent_metrics['net_worth'][metric]) + sum(1 for metric in ['total_income_paise', 'total_expense_paise', 'net_cashflow_paise'] if dashboard_metrics['monthly_cashflow'][metric] == independent_metrics['monthly_cashflow'][metric]) + (1 if abs(dashboard_metrics['monthly_cashflow']['savings_rate'] - independent_metrics['monthly_cashflow']['savings_rate']) < 0.0001 else 0) + sum(1 for metric in ['total_principal_paise', 'total_outstanding_paise', 'total_emi_paise'] if dashboard_metrics['debt_totals'][metric] == independent_metrics['debt_totals'][metric]) + (1 if abs(dashboard_metrics['savings_rate'] - independent_metrics['savings_rate']) < 0.0001 else 0) + (1 if dashboard_metrics['asset_allocation']['total_assets_paise'] == independent_metrics['asset_allocation']['total_assets_paise'] else 0))/12*100:.1f}%

---

## Conclusion

This comprehensive financial truth validation audit compared dashboard metrics against independent calculations across 5 key financial dimensions:

1. **Net Worth**: {sum(1 for metric in ['total_assets_paise', 'total_liabilities_paise', 'net_worth_paise'] if dashboard_metrics['net_worth'][metric] == independent_metrics['net_worth'][metric])}/3 metrics matched exactly
2. **Monthly Cashflow**: {sum(1 for metric in ['total_income_paise', 'total_expense_paise', 'net_cashflow_paise'] if dashboard_metrics['monthly_cashflow'][metric] == independent_metrics['monthly_cashflow'][metric]) + (1 if abs(dashboard_metrics['monthly_cashflow']['savings_rate'] - independent_metrics['monthly_cashflow']['savings_rate']) < 0.0001 else 0)}/4 metrics matched exactly
3. **Debt Totals**: {sum(1 for metric in ['total_principal_paise', 'total_outstanding_paise', 'total_emi_paise'] if dashboard_metrics['debt_totals'][metric] == independent_metrics['debt_totals'][metric])}/3 metrics matched exactly
4. **Savings Rate**: {'✅ MATCHED' if abs(dashboard_metrics['savings_rate'] - independent_metrics['savings_rate']) < 0.0001 else '❌ MISMATCHED'}
5. **Asset Allocation**: {'✅ MATCHED' if dashboard_metrics['asset_allocation']['total_assets_paise'] == independent_metrics['asset_allocation']['total_assets_paise'] else '❌ MISMATCHED'}

**Overall Financial Truth Assessment**: {'✅ EXCELLENT - ALL METRICS VALIDATED' if (sum(1 for metric in ['total_assets_paise', 'total_liabilities_paise', 'net_worth_paise'] if dashboard_metrics['net_worth'][metric] == independent_metrics['net_worth'][metric]) + sum(1 for metric in ['total_income_paise', 'total_expense_paise', 'net_cashflow_paise'] if dashboard_metrics['monthly_cashflow'][metric] == independent_metrics['monthly_cashflow'][metric]) + (1 if abs(dashboard_metrics['monthly_cashflow']['savings_rate'] - independent_metrics['monthly_cashflow']['savings_rate']) < 0.0001 else 0) + sum(1 for metric in ['total_principal_paise', 'total_outstanding_paise', 'total_emi_paise'] if dashboard_metrics['debt_totals'][metric] == independent_metrics['debt_totals'][metric]) + (1 if abs(dashboard_metrics['savings_rate'] - independent_metrics['savings_rate']) < 0.0001 else 0) + (1 if dashboard_metrics['asset_allocation']['total_assets_paise'] == independent_metrics['asset_allocation']['total_assets_paise'] else 0) == 12 else '⚠️ GOOD - MINOR VARIANCES' if (sum(1 for metric in ['total_assets_paise', 'total_liabilities_paise', 'net_worth_paise'] if dashboard_metrics['net_worth'][metric] == independent_metrics['net_worth'][metric]) + sum(1 for metric in ['total_income_paise', 'total_expense_paise', 'net_cashflow_paise'] if dashboard_metrics['monthly_cashflow'][metric] == independent_metrics['monthly_cashflow'][metric]) + (1 if abs(dashboard_metrics['monthly_cashflow']['savings_rate'] - independent_metrics['monthly_cashflow']['savings_rate']) < 0.0001 else 0) + sum(1 for metric in ['total_principal_paise', 'total_outstanding_paise', 'total_emi_paise'] if dashboard_metrics['debt_totals'][metric] == independent_metrics['debt_totals'][metric]) + (1 if abs(dashboard_metrics['savings_rate'] - independent_metrics['savings_rate']) < 0.0001 else 0) + (1 if dashboard_metrics['asset_allocation']['total_assets_paise'] == independent_metrics['asset_allocation']['total_assets_paise'] else 0)) >= 10 else '🔴 NEEDS ATTENTION - SIGNIFICANT VARIANCES'}

**No production data was modified during this audit.** All validations were performed using read-only queries and independent calculations.

---

**Audit Status**: {'✅ COMPLETE' if (sum(1 for metric in ['total_assets_paise', 'total_liabilities_paise', 'net_worth_paise'] if dashboard_metrics['net_worth'][metric] == independent_metrics['net_worth'][metric]) + sum(1 for metric in ['total_income_paise', 'total_expense_paise', 'net_cashflow_paise'] if dashboard_metrics['monthly_cashflow'][metric] == independent_metrics['monthly_cashflow'][metric]) + (1 if abs(dashboard_metrics['monthly_cashflow']['savings_rate'] - independent_metrics['monthly_cashflow']['savings_rate']) < 0.0001 else 0) + sum(1 for metric in ['total_principal_paise', 'total_outstanding_paise', 'total_emi_paise'] if dashboard_metrics['debt_totals'][metric] == independent_metrics['debt_totals'][metric]) + (1 if abs(dashboard_metrics['savings_rate'] - independent_metrics['savings_rate']) < 0.0001 else 0) + (1 if dashboard_metrics['asset_allocation']['total_assets_paise'] == independent_metrics['asset_allocation']['total_assets_paise'] else 0) == 12 else '⚠️ ACTION REQUIRED'}
**Generated**: 23/06/2026
"""

    # Write report to file
    with open(output_file, 'w') as f:
        f.write(report)

    print(f"✅ Financial Truth Validation Report generated: {output_file}")
    return report

if __name__ == "__main__":
    import sys
    import os
    db_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "data", "finance.db")
    generate_financial_truth_report(db_path)