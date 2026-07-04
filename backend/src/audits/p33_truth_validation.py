"""P3.3 - Financial Truth Validation

Objective: Verify that dashboard outputs accurately reflect the underlying financial records.

This is a financial correctness audit that validates dashboard metrics against
independent recalculations from the database.

Variance Rules: Expected variance = 0 paise. Any difference must be reported.
"""

from datetime import datetime
from typing import Dict, Any
from audits.base_audit import BaseAudit
from core.models import AuditResult, AuditStatus, Finding
from core.db.connection import DatabaseConnection
from engines.networth_engine import compute_net_worth, compute_asset_allocation
from engines.cashflow_engine import compute_monthly_cashflow, compute_cashflow_summary

class P33TruthValidationAudit(BaseAudit):
    """Financial Truth Validation Audit."""

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def run(self) -> AuditResult:
        """Run the financial truth validation audit."""
        # Get metrics from both sources
        dashboard_metrics = self._get_dashboard_metrics()
        independent_metrics = self._calculate_independent_metrics()
        consistency_checks = self._perform_consistency_checks(dashboard_metrics, independent_metrics)

        # Determine status
        status = self._determine_status(dashboard_metrics, independent_metrics, consistency_checks)

        # Create audit result
        result = AuditResult(
            audit_name="P3.3 - Financial Truth Validation",
            timestamp=datetime.now(),
            metrics={
                'total_checks': 12,
                'passed_checks': self._count_passed_checks(dashboard_metrics, independent_metrics),
                'validation_score': self._calculate_validation_score(dashboard_metrics, independent_metrics)
            },
            summary={
                'dashboard_metrics': dashboard_metrics,
                'independent_metrics': independent_metrics,
                'consistency_checks': consistency_checks
            },
            findings=self._create_findings(dashboard_metrics, independent_metrics, consistency_checks),
            status=status
        )

        return result

    def _get_dashboard_metrics(self) -> Dict[str, Any]:
        """Simulate dashboard API calls to get current metrics using existing engines."""
        from db import FinanceDB

        db = FinanceDB(db_path=self.db.db_path)

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

    def _calculate_independent_metrics(self) -> Dict[str, Any]:
        """Calculate metrics independently from raw database queries."""
        independent_metrics = {}

        with self.db.connection() as conn:
            # 1. Net Worth Calculation
            # Assets: Bank accounts (savings, current, wallet)
            cursor = conn.execute("""
                SELECT COALESCE(SUM(balance_paise), 0) as bank_accounts_paise
                FROM accounts
                WHERE account_type IN ('savings', 'current', 'wallet')
                AND is_active = 1
            """)
            bank_accounts = cursor.fetchone()['bank_accounts_paise']

            # Assets: Fixed Deposits
            cursor = conn.execute("""
                SELECT COALESCE(SUM(balance_paise), 0) as fixed_deposits_paise
                FROM accounts
                WHERE account_type = 'fd'
                AND is_active = 1
            """)
            fixed_deposits = cursor.fetchone()['fixed_deposits_paise']

            # Assets: Investments
            cursor = conn.execute("""
                SELECT COALESCE(SUM(current_value_paise), 0) as investments_paise
                FROM investments
                WHERE is_active = 1
            """)
            investments = cursor.fetchone()['investments_paise']

            # Liabilities: Loans
            cursor = conn.execute("""
                SELECT COALESCE(SUM(outstanding_paise), 0) as loans_paise
                FROM loans
                WHERE status = 'active'
            """)
            loans = cursor.fetchone()['loans_paise']

            # Liabilities: Credit Cards
            cursor = conn.execute("""
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

        return independent_metrics

    def _perform_consistency_checks(self, dashboard_metrics: Dict[str, Any], independent_metrics: Dict[str, Any]) -> Dict[str, Any]:
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

    def _count_passed_checks(self, dashboard_metrics: Dict[str, Any], independent_metrics: Dict[str, Any]) -> int:
        """Count the number of passed validation checks."""
        passed = 0

        # Net Worth checks
        for metric in ['total_assets_paise', 'total_liabilities_paise', 'net_worth_paise']:
            if dashboard_metrics['net_worth'][metric] == independent_metrics['net_worth'][metric]:
                passed += 1

        # Monthly Cashflow checks
        for metric in ['total_income_paise', 'total_expense_paise', 'net_cashflow_paise']:
            if dashboard_metrics['monthly_cashflow'][metric] == independent_metrics['monthly_cashflow'][metric]:
                passed += 1
        if abs(dashboard_metrics['monthly_cashflow']['savings_rate'] - independent_metrics['monthly_cashflow']['savings_rate']) < 0.0001:
            passed += 1

        # Debt Totals checks
        for metric in ['total_principal_paise', 'total_outstanding_paise', 'total_emi_paise']:
            if dashboard_metrics['debt_totals'][metric] == independent_metrics['debt_totals'][metric]:
                passed += 1

        # Savings Rate check
        if abs(dashboard_metrics['savings_rate'] - independent_metrics['savings_rate']) < 0.0001:
            passed += 1

        # Asset Allocation check
        if dashboard_metrics['asset_allocation']['total_assets_paise'] == independent_metrics['asset_allocation']['total_assets_paise']:
            passed += 1

        return passed

    def _calculate_validation_score(self, dashboard_metrics: Dict[str, Any], independent_metrics: Dict[str, Any]) -> float:
        """Calculate overall validation score (0-100)."""
        passed = self._count_passed_checks(dashboard_metrics, independent_metrics)
        return round((passed / 12) * 100, 1)

    def _determine_status(self, dashboard_metrics: Dict[str, Any], independent_metrics: Dict[str, Any],
                         consistency_checks: Dict[str, Any]) -> AuditStatus:
        """Determine overall audit status."""
        validation_score = self._calculate_validation_score(dashboard_metrics, independent_metrics)

        if validation_score == 100:
            return AuditStatus.PASS
        elif validation_score >= 80:
            return AuditStatus.WARNING
        else:
            return AuditStatus.FAIL

    def _create_findings(self, dashboard_metrics: Dict[str, Any], independent_metrics: Dict[str, Any],
                         consistency_checks: Dict[str, Any]) -> List[Finding]:
        """Create findings from validation results."""
        findings = []

        # Net Worth findings
        for metric in ['total_assets_paise', 'total_liabilities_paise', 'net_worth_paise']:
            dashboard_val = dashboard_metrics['net_worth'][metric]
            independent_val = independent_metrics['net_worth'][metric]
            variance = dashboard_val - independent_val

            if variance != 0:
                findings.append(Finding(
                    description=f"Net Worth {metric} variance: Dashboard={dashboard_val} vs Independent={independent_val} (Δ={variance})",
                    severity="HIGH" if abs(variance) > 100 else "MEDIUM",
                    details={
                        "type": "net_worth_variance",
                        "metric": metric,
                        "dashboard_value": dashboard_val,
                        "independent_value": independent_val,
                        "variance": variance
                    }
                ))

        # Monthly Cashflow findings
        for metric in ['total_income_paise', 'total_expense_paise', 'net_cashflow_paise']:
            dashboard_val = dashboard_metrics['monthly_cashflow'][metric]
            independent_val = independent_metrics['monthly_cashflow'][metric]
            variance = dashboard_val - independent_val

            if variance != 0:
                findings.append(Finding(
                    description=f"Cashflow {metric} variance: Dashboard={dashboard_val} vs Independent={independent_val} (Δ={variance})",
                    severity="HIGH" if abs(variance) > 100 else "MEDIUM",
                    details={
                        "type": "cashflow_variance",
                        "metric": metric,
                        "dashboard_value": dashboard_val,
                        "independent_value": independent_val,
                        "variance": variance
                    }
                ))

        # Savings Rate finding
        dashboard_rate = dashboard_metrics['monthly_cashflow']['savings_rate']
        independent_rate = independent_metrics['monthly_cashflow']['savings_rate']
        variance = abs(dashboard_rate - independent_rate)

        if variance >= 0.0001:
            findings.append(Finding(
                description=f"Savings rate variance: Dashboard={dashboard_rate*100:.2f}% vs Independent={independent_rate*100:.2f}% (Δ={variance*100:.2f}%)",
                severity="MEDIUM",
                details={
                    "type": "savings_rate_variance",
                    "dashboard_rate": dashboard_rate,
                    "independent_rate": independent_rate,
                    "variance": variance
                }
            ))

        # Debt Totals findings
        for metric in ['total_principal_paise', 'total_outstanding_paise', 'total_emi_paise']:
            dashboard_val = dashboard_metrics['debt_totals'][metric]
            independent_val = independent_metrics['debt_totals'][metric]
            variance = dashboard_val - independent_val

            if variance != 0:
                findings.append(Finding(
                    description=f"Debt {metric} variance: Dashboard={dashboard_val} vs Independent={independent_val} (Δ={variance})",
                    severity="HIGH" if abs(variance) > 100 else "MEDIUM",
                    details={
                        "type": "debt_variance",
                        "metric": metric,
                        "dashboard_value": dashboard_val,
                        "independent_value": independent_val,
                        "variance": variance
                    }
                ))

        # Overall savings rate finding
        dashboard_rate = dashboard_metrics['savings_rate']
        independent_rate = independent_metrics['savings_rate']
        variance = abs(dashboard_rate - independent_rate)

        if variance >= 0.0001:
            findings.append(Finding(
                description=f"Overall savings rate variance: Dashboard={dashboard_rate*100:.2f}% vs Independent={independent_rate*100:.2f}% (Δ={variance*100:.2f}%)",
                severity="MEDIUM",
                details={
                    "type": "overall_savings_rate_variance",
                    "dashboard_rate": dashboard_rate,
                    "independent_rate": independent_rate,
                    "variance": variance
                }
            ))

        # Asset Allocation finding
        dashboard_assets = dashboard_metrics['asset_allocation']['total_assets_paise']
        independent_assets = independent_metrics['asset_allocation']['total_assets_paise']
        variance = dashboard_assets - independent_assets

        if variance != 0:
            findings.append(Finding(
                description=f"Total assets variance: Dashboard={dashboard_assets} vs Independent={independent_assets} (Δ={variance})",
                severity="HIGH" if abs(variance) > 100 else "MEDIUM",
                details={
                    "type": "asset_allocation_variance",
                    "dashboard_assets": dashboard_assets,
                    "independent_assets": independent_assets,
                    "variance": variance
                }
            ))

        # Consistency check findings
        if not consistency_checks['assets_liabilities_net_worth']['dashboard_consistent']:
            findings.append(Finding(
                description="Dashboard net worth calculation inconsistent: Assets - Liabilities ≠ Net Worth",
                severity="CRITICAL",
                details={
                    "type": "consistency_error",
                    "check": "dashboard_net_worth_consistency",
                    "variance": consistency_checks['assets_liabilities_net_worth']['dashboard_variance']
                }
            ))

        if not consistency_checks['assets_liabilities_net_worth']['independent_consistent']:
            findings.append(Finding(
                description="Independent net worth calculation inconsistent: Assets - Liabilities ≠ Net Worth",
                severity="CRITICAL",
                details={
                    "type": "consistency_error",
                    "check": "independent_net_worth_consistency",
                    "variance": consistency_checks['assets_liabilities_net_worth']['independent_variance']
                }
            ))

        if not consistency_checks['income_expense_net_cashflow']['dashboard_consistent']:
            findings.append(Finding(
                description="Dashboard cashflow calculation inconsistent: Income - Expense ≠ Net Cashflow",
                severity="CRITICAL",
                details={
                    "type": "consistency_error",
                    "check": "dashboard_cashflow_consistency",
                    "variance": consistency_checks['income_expense_net_cashflow']['dashboard_variance']
                }
            ))

        if not consistency_checks['income_expense_net_cashflow']['independent_consistent']:
            findings.append(Finding(
                description="Independent cashflow calculation inconsistent: Income - Expense ≠ Net Cashflow",
                severity="CRITICAL",
                details={
                    "type": "consistency_error",
                    "check": "independent_cashflow_consistency",
                    "variance": consistency_checks['income_expense_net_cashflow']['independent_variance']
                }
            ))

        if not consistency_checks['loan_outstanding_principal']['dashboard_valid']:
            findings.append(Finding(
                description="Dashboard debt validation failed: Outstanding > Principal",
                severity="CRITICAL",
                details={
                    "type": "validation_error",
                    "check": "dashboard_loan_validation",
                    "variance": consistency_checks['loan_outstanding_principal']['dashboard_variance']
                }
            ))

        if not consistency_checks['loan_outstanding_principal']['independent_valid']:
            findings.append(Finding(
                description="Independent debt validation failed: Outstanding > Principal",
                severity="CRITICAL",
                details={
                    "type": "validation_error",
                    "check": "independent_loan_validation",
                    "variance": consistency_checks['loan_outstanding_principal']['independent_variance']
                }
            ))

        if consistency_checks['negative_balances']['dashboard_has_negative']:
            findings.append(Finding(
                description="Dashboard metrics contain negative balance values",
                severity="CRITICAL",
                details={
                    "type": "negative_balance",
                    "source": "dashboard"
                }
            ))

        if consistency_checks['negative_balances']['independent_has_negative']:
            findings.append(Finding(
                description="Independent metrics contain negative balance values",
                severity="CRITICAL",
                details={
                    "type": "negative_balance",
                    "source": "independent"
                }
            ))

        return findings