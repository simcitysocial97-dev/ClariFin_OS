#!/usr/bin/env python3
"""
Financial Inventory Reconciliation Audit - P3.1

Objective: Determine whether the system contains a complete representation
of the user's real financial world.

Scope: Audit Accounts, Credit Cards, Loans, Investments, Recurring Obligations
"""

import sqlite3
from typing import List, Dict, Any, Optional
from decimal import Decimal

def format_paise(amount_paise: int) -> str:
    """Convert paise to formatted rupees string."""
    if amount_paise is None:
        return "₹0.00"
    rupees = Decimal(amount_paise) / 100
    return f"₹{rupees:,.2f}"

def get_accounts_inventory(db_path: str) -> List[Dict[str, Any]]:
    """Extract complete accounts inventory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
    SELECT
        id, name, bank_name as institution, account_type,
        balance_paise, credit_limit_paise, is_active
    FROM accounts
    ORDER BY name
    """

    cursor.execute(query)
    accounts = []
    for row in cursor.fetchall():
        accounts.append({
            'id': row['id'],
            'name': row['name'],
            'institution': row['institution'],
            'account_type': row['account_type'],
            'balance_paise': row['balance_paise'],
            'balance_formatted': format_paise(row['balance_paise']),
            'credit_limit_paise': row['credit_limit_paise'],
            'credit_limit_formatted': format_paise(row['credit_limit_paise']),
            'active': 'Active' if row['is_active'] else 'Inactive'
        })

    conn.close()
    return accounts

def get_credit_cards_inventory(db_path: str) -> List[Dict[str, Any]]:
    """Extract complete credit cards inventory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
    SELECT
        c.id, c.card_name, c.issuer, c.card_type as network,
        c.credit_limit_paise, c.is_active,
        a.name as account_name
    FROM cards c
    LEFT JOIN accounts a ON c.account_id = a.id
    ORDER BY c.card_name
    """

    cursor.execute(query)
    cards = []
    for row in cursor.fetchall():
        cards.append({
            'id': row['id'],
            'issuer': row['issuer'],
            'card_name': row['card_name'],
            'network': row['network'],
            'credit_limit_paise': row['credit_limit_paise'],
            'credit_limit_formatted': format_paise(row['credit_limit_paise']),
            'account_name': row['account_name'],
            'active': 'Active' if row['is_active'] else 'Inactive'
        })

    conn.close()
    return cards

def get_loans_inventory(db_path: str) -> List[Dict[str, Any]]:
    """Extract complete loans inventory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
    SELECT
        l.id, l.lender, l.loan_type, l.principal_paise,
        l.outstanding_paise, l.emi_paise, l.status,
        a.name as account_name
    FROM loans l
    LEFT JOIN accounts a ON l.linked_account_id = a.id
    ORDER BY lender
    """

    cursor.execute(query)
    loans = []
    for row in cursor.fetchall():
        loans.append({
            'id': row['id'],
            'lender': row['lender'],
            'loan_type': row['loan_type'],
            'principal_paise': row['principal_paise'],
            'principal_formatted': format_paise(row['principal_paise']),
            'outstanding_paise': row['outstanding_paise'],
            'outstanding_formatted': format_paise(row['outstanding_paise']),
            'emi_paise': row['emi_paise'],
            'emi_formatted': format_paise(row['emi_paise']),
            'status': row['status'],
            'account_name': row['account_name']
        })

    conn.close()
    return loans

def get_investments_inventory(db_path: str) -> List[Dict[str, Any]]:
    """Extract complete investments inventory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
    SELECT
        id, type as investment_type, platform as institution,
        current_value_paise, is_active
    FROM investments
    ORDER BY platform, type
    """

    cursor.execute(query)
    investments = []
    for row in cursor.fetchall():
        investments.append({
            'id': row['id'],
            'investment_type': row['investment_type'],
            'institution': row['institution'],
            'current_value_paise': row['current_value_paise'],
            'current_value_formatted': format_paise(row['current_value_paise']),
            'active': 'Active' if row['is_active'] else 'Inactive'
        })

    conn.close()
    return investments

def get_recurring_transactions_inventory(db_path: str) -> List[Dict[str, Any]]:
    """Extract complete recurring transactions inventory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
    SELECT
        description, category, amount_paise, frequency,
        account_id, is_active
    FROM recurring_transactions
    ORDER BY description
    """

    cursor.execute(query)
    recurring = []
    for row in cursor.fetchall():
        recurring.append({
            'description': row['description'],
            'category': row['category'],
            'amount_paise': row['amount_paise'],
            'amount_formatted': format_paise(row['amount_paise']),
            'frequency': row['frequency'],
            'account_id': row['account_id'],
            'active': 'Active' if row['is_active'] else 'Inactive'
        })

    conn.close()
    return recurring

def analyze_completeness(accounts: List[Dict], cards: List[Dict],
                        loans: List[Dict], investments: List[Dict],
                        recurring: List[Dict]) -> Dict[str, Any]:
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
    loans_without_accounts = [loan for loan in loans if not loan['account_name']]
    if loans_without_accounts:
        analysis['potential_gaps'].append(
            f"Loans without linked accounts: {len(loans_without_accounts)}"
        )

    # Check for recurring transactions without account links
    recurring_without_accounts = [r for r in recurring if not r['account_id']]
    if recurring_without_accounts:
        analysis['potential_gaps'].append(
            f"Recurring transactions without account links: {len(recurring_without_accounts)}"
        )

    return analysis

def validate_relationships(db_path: str) -> Dict[str, Any]:
    """Validate relationships between financial entities."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    validation = {
        'orphaned_transactions': [],
        'orphaned_loans': [],
        'orphaned_recurring': []
    }

    # Check transactions reference valid accounts
    cursor.execute("""
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
    cursor.execute("""
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
    cursor.execute("""
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

    conn.close()
    return validation

def generate_audit_report(db_path: str, output_file: str = "P3_1_FINANCIAL_INVENTORY_AUDIT.md"):
    """Generate comprehensive financial inventory audit report."""
    # Extract inventories
    accounts = get_accounts_inventory(db_path)
    cards = get_credit_cards_inventory(db_path)
    loans = get_loans_inventory(db_path)
    investments = get_investments_inventory(db_path)
    recurring = get_recurring_transactions_inventory(db_path)

    # Perform analysis
    completeness = analyze_completeness(accounts, cards, loans, investments, recurring)
    relationships = validate_relationships(db_path)

    # Generate markdown report
    report = f"""# P3.1 - Financial Inventory Reconciliation Audit

## Executive Summary

This audit determines whether ClariFin_OS contains a complete representation of the user's real financial world. The goal is to identify missing or incomplete financial entities without modifying any data.

**Audit Date**: 23/06/2026
**Database**: {db_path}

---

## Step 1 - Inventory Extraction

### Accounts Inventory ({len(accounts)} total)

| ID | Name | Institution | Type | Balance | Credit Limit | Status |
|----|------|-------------|------|---------|--------------|--------|
"""

    for account in accounts:
        report += f"""| {account['id']} | {account['name']} | {account['institution']} | {account['account_type']} | {account['balance_formatted']} | {account['credit_limit_formatted']} | {account['active']} |\n"""

    report += f"""

### Credit Cards Inventory ({len(cards)} total)

| ID | Issuer | Card Name | Network | Credit Limit | Account | Status |
|----|--------|-----------|---------|--------------|---------|--------|
"""

    for card in cards:
        report += f"""| {card['id']} | {card['issuer']} | {card['card_name']} | {card['network']} | {card['credit_limit_formatted']} | {card['account_name'] or 'N/A'} | {card['active']} |\n"""

    report += f"""

### Loans Inventory ({len(loans)} total)

| ID | Lender | Type | Principal | Outstanding | EMI | Account | Status |
|----|--------|------|-----------|------------|-----|---------|--------|
"""

    for loan in loans:
        report += f"""| {loan['id']} | {loan['lender']} | {loan['loan_type']} | {loan['principal_formatted']} | {loan['outstanding_formatted']} | {loan['emi_formatted']} | {loan['account_name'] or 'N/A'} | {loan['status']} |\n"""

    report += f"""

### Investments Inventory ({len(investments)} total)

| ID | Type | Institution | Current Value | Status |
|----|------|-------------|---------------|--------|
"""

    if investments:
        for investment in investments:
            report += f"""| {investment['id']} | {investment['investment_type']} | {investment['institution']} | {investment['current_value_formatted']} | {investment['active']} |\n"""
    else:
        report += """| N/A | N/A | N/A | N/A | N/A |\n"""

    report += f"""

### Recurring Transactions Inventory ({len(recurring)} total)

| Description | Category | Amount | Frequency | Account | Status |
|-------------|----------|--------|-----------|---------|--------|
"""

    for rec in recurring:
        report += f"""| {rec['description']} | {rec['category']} | {rec['amount_formatted']} | {rec['frequency']} | {rec['account_id'] or 'N/A'} | {rec['active']} |\n"""

    # Step 2 - Completeness Analysis
    report += f"""

---

## Step 2 - Completeness Analysis

### Statistics Summary
- **Total Accounts**: {completeness['statistics']['total_accounts']}
- **Total Credit Cards**: {completeness['statistics']['total_cards']}
- **Total Loans**: {completeness['statistics']['total_loans']}
- **Total Investments**: {completeness['statistics']['total_investments']}
- **Total Recurring Transactions**: {completeness['statistics']['total_recurring']}

### Missing Entities
"""

    if completeness['missing_entities']:
        for entity in completeness['missing_entities']:
            report += f"- ❌ {entity}\n"
    else:
        report += "- ✅ No major missing entity categories detected\n"

    report += f"""

### Potential Gaps
"""

    if completeness['potential_gaps']:
        for gap in completeness['potential_gaps']:
            report += f"- ⚠️  {gap}\n"
    else:
        report += "- ✅ No potential gaps identified\n"

    # Step 3 - Relationship Validation
    report += f"""

---

## Step 3 - Relationship Validation

### Orphaned Transaction References
"""

    if relationships['orphaned_transactions']:
        report += f"Found {len(relationships['orphaned_transactions'])} orphaned transactions:\n"
        for orphan in relationships['orphaned_transactions']:
            report += f"- Transaction {orphan['transaction_id']} references invalid account: {orphan['invalid_account_id']}\n"
    else:
        report += "- ✅ All transactions reference valid accounts\n"

    report += f"""

### Orphaned Loan References
"""

    if relationships['orphaned_loans']:
        report += f"Found {len(relationships['orphaned_loans'])} loans with invalid account references:\n"
        for orphan in relationships['orphaned_loans']:
            report += f"- Loan {orphan['loan_id']} ({orphan['lender']}) references invalid account\n"
    else:
        report += "- ✅ All loans reference valid accounts\n"

    report += f"""

### Orphaned Recurring Transaction References
"""

    if relationships['orphaned_recurring']:
        report += f"Found {len(relationships['orphaned_recurring'])} recurring transactions with invalid account references:\n"
        for orphan in relationships['orphaned_recurring']:
            report += f"- '{orphan['description']}' references invalid account: {orphan['invalid_account_id']}\n"
    else:
        report += "- ✅ All recurring transactions reference valid accounts\n"

    # Recommendations
    report += f"""

---

## Recommendations

### Immediate Actions
"""

    if completeness['missing_entities'] or completeness['potential_gaps'] or any(relationships['orphaned_transactions']) or any(relationships['orphaned_loans']) or any(relationships['orphaned_recurring']):
        if len(accounts) == 0:
            report += "- 🔴 **CRITICAL**: Add primary bank accounts to enable financial tracking\n"
        if len(cards) == 0:
            report += "- 🔴 **CRITICAL**: Add credit cards to track spending patterns\n"
        if len(investments) == 0:
            report += "- ⚠️  **RECOMMENDED**: Add investment accounts for complete net worth tracking\n"
        if relationships['orphaned_transactions']:
            report += f"- 🔧 **TECHNICAL**: Fix {len(relationships['orphaned_transactions'])} orphaned transaction references\n"
    else:
        report += "- ✅ **EXCELLENT**: Financial inventory appears complete and consistent\n"

    report += f"""

### Data Quality Improvements
- Consider adding institution names to all accounts for better organization
- Review credit card account linkages to ensure proper spending tracking
- Validate loan account associations for accurate EMI tracking
- Add investment accounts to complete the financial picture

---

## Conclusion

This audit provides a comprehensive snapshot of the financial data completeness within ClariFin_OS. The system currently tracks:

- **{len(accounts)} accounts** across various financial institutions
- **{len(cards)} credit cards** for spending analysis
- **{len(loans)} loans** for debt management
- **{len(investments)} investments** for wealth tracking
- **{len(recurring)} recurring transactions** for cash flow forecasting

**No production data was modified during this audit.** All findings are based on read-only analysis of the existing database state.

---

**Audit Status**: {'✅ COMPLETE' if not (completeness['missing_entities'] or completeness['potential_gaps'] or any(relationships.values())) else '⚠️ ACTION REQUIRED'}
**Generated**: 23/06/2026
"""

    # Write report to file
    with open(output_file, 'w') as f:
        f.write(report)

    print(f"✅ Financial Inventory Audit Report generated: {output_file}")
    return report

if __name__ == "__main__":
    import sys
    import os
    db_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "data", "finance.db")
    generate_audit_report(db_path)
