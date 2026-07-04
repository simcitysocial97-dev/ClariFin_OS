"""P3.1 - Financial Inventory Reconciliation Audit

Objective: Determine whether the system contains a complete representation
of the user's real financial world.

Scope: Audit Accounts, Credit Cards, Loans, Investments, Recurring Obligations
"""

from datetime import datetime
from typing import List
from audits.base_audit import BaseAudit
from core.models import AuditResult, AuditStatus, Finding, Account, Card, Loan, Investment, RecurringTransaction
from core.repositories.account_repo import AccountRepository
from core.repositories.card_repo import CardRepository
from core.repositories.loan_repo import LoanRepository
from core.repositories.investment_repo import InvestmentRepository
from core.repositories.recurring_transaction_repo import RecurringTransactionRepository
from core.db.connection import DatabaseConnection

class P31InventoryAudit(BaseAudit):
    """Financial Inventory Reconciliation Audit."""

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
        self.account_repo = AccountRepository(db_connection)
        self.card_repo = CardRepository(db_connection)
        self.loan_repo = LoanRepository(db_connection)
        self.investment_repo = InvestmentRepository(db_connection)
        self.recurring_repo = RecurringTransactionRepository(db_connection)

    def run(self) -> AuditResult:
        """Run the financial inventory audit."""
        # Extract inventories
        accounts = self.account_repo.get_all_accounts()
        cards = self.card_repo.get_all_cards()
        loans = self.loan_repo.get_all_loans()
        investments = self.investment_repo.get_all_investments()
        recurring = self.recurring_repo.get_all_recurring_transactions()

        # Perform analysis
        completeness = self._analyze_completeness(accounts, cards, loans, investments, recurring)
        relationships = self._validate_relationships()

        # Determine status
        status = self._determine_status(completeness, relationships)

        # Create audit result
        result = AuditResult(
            audit_name="P3.1 - Financial Inventory Reconciliation Audit",
            timestamp=datetime.now(),
            metrics={
                'total_accounts': len(accounts),
                'total_cards': len(cards),
                'total_loans': len(loans),
                'total_investments': len(investments),
                'total_recurring': len(recurring),
                'orphaned_transactions': len(relationships['orphaned_transactions']),
                'orphaned_loans': len(relationships['orphaned_loans']),
                'orphaned_recurring': len(relationships['orphaned_recurring'])
            },
            summary={
                'completeness': completeness,
                'relationships': relationships
            },
            findings=self._create_findings(completeness, relationships),
            status=status
        )

        return result

    def _analyze_completeness(self, accounts: List[Account], cards: List[Card],
                            loans: List[Loan], investments: List[Investment],
                            recurring: List[RecurringTransaction]) -> dict:
        """Analyze completeness of financial entities."""
        analysis = {
            'missing_entities': [],
            'potential_gaps': [],
            'statistics': {
                'total_accounts': len(accounts),
                'total_cards': len(cards),
                'total_loans': len(loans),
                'total_investments': len(investments),
                'total_recurring': len(recurring)
            }
        }

        # Check for common missing entities
        if len(accounts) == 0:
            analysis['missing_entities'].append("No accounts found - primary financial tracking missing")

        if len(cards) == 0:
            analysis['missing_entities'].append("No credit cards found - spending tracking incomplete")

        # Check for loans without linked accounts
        loans_without_accounts = [loan for loan in loans if not loan.linked_account_id]
        if loans_without_accounts:
            analysis['potential_gaps'].append(
                f"Loans without linked accounts: {len(loans_without_accounts)}"
            )

        # Check for recurring transactions without account links
        recurring_without_accounts = [r for r in recurring if not r.account_id]
        if recurring_without_accounts:
            analysis['potential_gaps'].append(
                f"Recurring transactions without account links: {len(recurring_without_accounts)}"
            )

        return analysis

    def _validate_relationships(self) -> dict:
        """Validate relationships between financial entities."""
        validation = {
            'orphaned_transactions': [],
            'orphaned_loans': [],
            'orphaned_recurring': []
        }

        # Check transactions reference valid accounts
        with self.db.connection() as conn:
            cursor = conn.execute("""
            SELECT t.id, t.account_id
            FROM transactions t
            WHERE t.account_id IS NOT NULL AND t.account_id != ''
            AND NOT EXISTS (SELECT 1 FROM accounts a WHERE a.name = t.account_id)
            LIMIT 10
            """)

            for row in cursor.fetchall():
                validation['orphaned_transactions'].append({
                    'transaction_id': row['id'],
                    'invalid_account_id': row['account_id']
                })

            # Check loans reference valid accounts
            cursor = conn.execute("""
            SELECT l.id, l.lender
            FROM loans l
            WHERE l.linked_account_id IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM accounts a WHERE a.id = l.linked_account_id)
            """)

            for row in cursor.fetchall():
                validation['orphaned_loans'].append({
                    'loan_id': row['id'],
                    'lender': row['lender']
                })

            # Check recurring transactions reference valid accounts
            cursor = conn.execute("""
            SELECT r.description, r.account_id
            FROM recurring_transactions r
            WHERE r.account_id IS NOT NULL AND r.account_id != ''
            AND NOT EXISTS (SELECT 1 FROM accounts a WHERE a.name = r.account_id)
            """)

            for row in cursor.fetchall():
                validation['orphaned_recurring'].append({
                    'description': row['description'],
                    'invalid_account_id': row['account_id']
                })

        return validation

    def _determine_status(self, completeness: dict, relationships: dict) -> AuditStatus:
        """Determine overall audit status."""
        has_missing_entities = len(completeness['missing_entities']) > 0
        has_potential_gaps = len(completeness['potential_gaps']) > 0
        has_orphaned_relationships = any(len(items) > 0 for items in relationships.values())

        if has_missing_entities:
            return AuditStatus.FAIL
        elif has_potential_gaps or has_orphaned_relationships:
            return AuditStatus.WARNING
        else:
            return AuditStatus.PASS

    def _create_findings(self, completeness: dict, relationships: dict) -> List[Finding]:
        """Create findings from analysis results."""
        findings = []

        # Missing entities findings
        for entity in completeness['missing_entities']:
            findings.append(Finding(
                description=entity,
                severity="HIGH",
                details={"type": "missing_entity"}
            ))

        # Potential gaps findings
        for gap in completeness['potential_gaps']:
            findings.append(Finding(
                description=gap,
                severity="MEDIUM",
                details={"type": "potential_gap"}
            ))

        # Orphaned transaction findings
        for orphan in relationships['orphaned_transactions']:
            findings.append(Finding(
                description=f"Transaction {orphan['transaction_id']} references invalid account: {orphan['invalid_account_id']}",
                severity="HIGH",
                details={"type": "orphaned_transaction", "data": orphan}
            ))

        # Orphaned loan findings
        for orphan in relationships['orphaned_loans']:
            findings.append(Finding(
                description=f"Loan {orphan['loan_id']} ({orphan['lender']}) references invalid account",
                severity="HIGH",
                details={"type": "orphaned_loan", "data": orphan}
            ))

        # Orphaned recurring findings
        for orphan in relationships['orphaned_recurring']:
            findings.append(Finding(
                description=f"Recurring transaction '{orphan['description']}' references invalid account: {orphan['invalid_account_id']}",
                severity="MEDIUM",
                details={"type": "orphaned_recurring", "data": orphan}
            ))

        return findings