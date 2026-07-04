#!/usr/bin/env python3
"""
Transaction Classification Quality Audit - P3.2

Objective: Measure transaction classification quality across all imported financial history.

Scope: Audit approximately 465 transactions for category accuracy, merchant normalization,
and duplicate detection without modifying any data.
"""

import sqlite3
from typing import List, Dict, Any, Tuple
from decimal import Decimal
import re
from collections import defaultdict

def format_paise(amount_paise: int) -> str:
    """Convert paise to formatted rupees string."""
    if amount_paise is None:
        return "₹0.00"
    rupees = Decimal(amount_paise) / 100
    return f"₹{rupees:,.2f}"

def get_category_distribution(db_path: str) -> List[Dict[str, Any]]:
    """Extract category distribution with counts and amounts."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
    SELECT
        category,
        COUNT(*) as transaction_count,
        SUM(debit) as total_debit_paise,
        SUM(credit) as total_credit_paise
    FROM transactions
    GROUP BY category
    ORDER BY transaction_count DESC
    """

    cursor.execute(query)
    categories = []
    for row in cursor.fetchall():
        categories.append({
            'category': row['category'],
            'transaction_count': row['transaction_count'],
            'total_debit_paise': row['total_debit_paise'],
            'total_debit_formatted': format_paise(row['total_debit_paise']),
            'total_credit_paise': row['total_credit_paise'],
            'total_credit_formatted': format_paise(row['total_credit_paise'])
        })

    conn.close()
    return categories

def analyze_uncategorized_transactions(db_path: str, total_transactions: int) -> Dict[str, Any]:
    """Analyze uncategorized transactions and calculate metrics."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get uncategorized transactions
    cursor.execute("""
    SELECT
        COUNT(*) as count,
        SUM(debit) as debit_paise,
        SUM(credit) as credit_paise
    FROM transactions
    WHERE category = 'Uncategorized'
    """)

    uncategorized = cursor.fetchone()
    uncategorized_count = uncategorized['count'] if uncategorized['count'] else 0
    uncategorized_debit = uncategorized['debit_paise'] if uncategorized['debit_paise'] else 0
    uncategorized_credit = uncategorized['credit_paise'] if uncategorized['credit_paise'] else 0

    # Get sample uncategorized transactions
    cursor.execute("""
    SELECT id, description, amount_paise, type
    FROM transactions
    WHERE category = 'Uncategorized'
    LIMIT 10
    """)

    samples = []
    for row in cursor.fetchall():
        samples.append({
            'id': row['id'],
            'description': row['description'],
            'amount_paise': row['amount_paise'],
            'amount_formatted': format_paise(row['amount_paise']),
            'type': row['type']
        })

    conn.close()

    return {
        'uncategorized_count': uncategorized_count,
        'uncategorized_percentage': (uncategorized_count / total_transactions * 100) if total_transactions > 0 else 0,
        'uncategorized_debit_paise': uncategorized_debit,
        'uncategorized_debit_formatted': format_paise(uncategorized_debit),
        'uncategorized_credit_paise': uncategorized_credit,
        'uncategorized_credit_formatted': format_paise(uncategorized_credit),
        'samples': samples,
        'target_met': uncategorized_count / total_transactions * 100 < 5 if total_transactions > 0 else True
    }

def normalize_merchant_name(name: str) -> str:
    """Normalize merchant name for duplicate detection."""
    if not name:
        return ""

    # Convert to uppercase and remove common prefixes/suffixes
    name = name.upper().strip()
    name = re.sub(r'^[^A-Z0-9]*', '', name)  # Remove leading non-alphanumeric
    name = re.sub(r'[^A-Z0-9]*$', '', name)  # Remove trailing non-alphanumeric
    name = re.sub(r'[^A-Z0-9]+', ' ', name)   # Replace non-alphanumeric with space
    name = re.sub(r'\s+', ' ', name).strip() # Normalize spaces

    # Remove common payment indicators
    name = re.sub(r'\b(PAY|PAYMENT|TRANSFER|TO|FROM|INR|RS|₹)\b', '', name)
    name = re.sub(r'\s+', ' ', name).strip()

    return name

def find_merchant_normalization_candidates(db_path: str) -> List[Dict[str, Any]]:
    """Identify merchant names that likely represent the same entity."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all unique merchant names
    cursor.execute("SELECT DISTINCT description FROM transactions WHERE description IS NOT NULL AND description != ''")
    merchants = [row['description'] for row in cursor.fetchall()]

    # Group by normalized name
    merchant_groups = defaultdict(list)
    for merchant in merchants:
        normalized = normalize_merchant_name(merchant)
        if normalized:
            merchant_groups[normalized].append(merchant)

    # Find groups with multiple variants
    candidates = []
    for normalized, variants in merchant_groups.items():
        if len(variants) > 1:
            # Get transaction count for each variant
            variant_stats = []
            for variant in variants:
                cursor.execute("""
                SELECT COUNT(*), SUM(debit), SUM(credit)
                FROM transactions
                WHERE description = ?
                """, (variant,))
                stats = cursor.fetchone()
                variant_stats.append({
                    'variant': variant,
                    'count': stats[0],
                    'debit_paise': stats[1],
                    'credit_paise': stats[2]
                })

            candidates.append({
                'normalized_name': normalized,
                'variants': variant_stats,
                'total_transactions': sum(v['count'] for v in variant_stats)
            })

    conn.close()

    # Sort by total transactions descending
    candidates.sort(key=lambda x: x['total_transactions'], reverse=True)
    return candidates

def find_suspicious_classifications(db_path: str) -> List[Dict[str, Any]]:
    """Identify potentially incorrect transaction classifications."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    suspicious = []

    # 1. Look for large transactions in unexpected categories
    cursor.execute("""
    SELECT id, description, category, amount_paise, type
    FROM transactions
    WHERE amount_paise > 50000  -- Large transactions (> ₹5,000)
    AND category NOT IN ('Transfer_SA', 'CC_Payment', 'Debt_Injection', 'EMI_Payment')
    ORDER BY amount_paise DESC
    LIMIT 5
    """)

    for row in cursor.fetchall():
        suspicious.append({
            'id': row['id'],
            'description': row['description'],
            'category': row['category'],
            'amount_paise': row['amount_paise'],
            'amount_formatted': format_paise(row['amount_paise']),
            'type': row['type'],
            'issue': 'Large transaction in unexpected category',
            'severity': 'HIGH'
        })

    # 2. Look for EMI payments not categorized as EMI
    cursor.execute("""
    SELECT id, description, category, amount_paise
    FROM transactions
    WHERE (description LIKE '%EMI%' OR description LIKE '%LOAN%')
    AND category != 'EMI_Payment'
    AND category != 'Transfer_SA'
    LIMIT 5
    """)

    for row in cursor.fetchall():
        suspicious.append({
            'id': row['id'],
            'description': row['description'],
            'category': row['category'],
            'amount_paise': row['amount_paise'],
            'amount_formatted': format_paise(row['amount_paise']),
            'type': 'debit',
            'issue': 'Potential EMI misclassified',
            'severity': 'MEDIUM'
        })

    # 3. Look for salary/income not categorized properly
    cursor.execute("""
    SELECT id, description, category, amount_paise
    FROM transactions
    WHERE (description LIKE '%SALARY%' OR description LIKE '%INCOME%')
    AND category NOT IN ('Salary', 'Income', 'Transfer_SA', 'Debt_Injection')
    LIMIT 5
    """)

    for row in cursor.fetchall():
        suspicious.append({
            'id': row['id'],
            'description': row['description'],
            'category': row['category'],
            'amount_paise': row['amount_paise'],
            'amount_formatted': format_paise(row['amount_paise']),
            'type': 'credit',
            'issue': 'Potential salary/income misclassified',
            'severity': 'HIGH'
        })

    conn.close()
    return suspicious

def find_duplicate_transactions(db_path: str) -> Dict[str, Any]:
    """Identify exact and near duplicate transactions."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    duplicates = {
        'exact_duplicates': [],
        'near_duplicates': []
    }

    # 1. Find exact duplicates (same description, amount, date)
    cursor.execute("""
    SELECT description, amount_paise, date_iso, COUNT(*) as count
    FROM transactions
    GROUP BY description, amount_paise, date_iso
    HAVING COUNT(*) > 1
    ORDER BY COUNT(*) DESC
    LIMIT 5
    """)

    for row in cursor.fetchall():
        cursor.execute("""
        SELECT id, date, amount_paise
        FROM transactions
        WHERE description = ? AND amount_paise = ? AND date_iso = ?
        ORDER BY id
        """, (row['description'], row['amount_paise'], row['date_iso']))

        duplicate_ids = [f"{r['id']} (₹{r['amount_paise']/100:.2f})" for r in cursor.fetchall()]

        duplicates['exact_duplicates'].append({
            'description': row['description'],
            'amount_paise': row['amount_paise'],
            'amount_formatted': format_paise(row['amount_paise']),
            'date': row['date_iso'],
            'count': row['count'],
            'transaction_ids': ', '.join(duplicate_ids),
            'severity': 'CRITICAL'
        })

    # 2. Find near duplicates (same description and amount, different dates)
    cursor.execute("""
    SELECT description, amount_paise, COUNT(*) as count, MIN(date_iso) as first_date, MAX(date_iso) as last_date
    FROM transactions
    GROUP BY description, amount_paise
    HAVING COUNT(*) > 1
    ORDER BY COUNT(*) DESC
    LIMIT 5
    """)

    for row in cursor.fetchall():
        if row['first_date'] != row['last_date']:  # Different dates
            duplicates['near_duplicates'].append({
                'description': row['description'],
                'amount_paise': row['amount_paise'],
                'amount_formatted': format_paise(row['amount_paise']),
                'count': row['count'],
                'first_date': row['first_date'],
                'last_date': row['last_date'],
                'severity': 'MEDIUM'
            })

    conn.close()
    return duplicates

def generate_classification_audit_report(db_path: str, output_file: str = "P3_2_TRANSACTION_CLASSIFICATION_AUDIT.md"):
    """Generate comprehensive transaction classification quality audit report."""
    # Get total transaction count
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM transactions")
    total_transactions = cursor.fetchone()[0]
    conn.close()

    # Perform all analyses
    category_distribution = get_category_distribution(db_path)
    uncategorized_analysis = analyze_uncategorized_transactions(db_path, total_transactions)
    merchant_candidates = find_merchant_normalization_candidates(db_path)
    suspicious_classifications = find_suspicious_classifications(db_path)
    duplicate_transactions = find_duplicate_transactions(db_path)

    # Generate markdown report
    report = f"""# P3.2 - Transaction Classification Quality Audit

## Executive Summary

This audit measures transaction classification quality across all {total_transactions} imported financial transactions. The goal is to identify classification issues, merchant normalization opportunities, and duplicate transactions without modifying any data.

**Audit Date**: 23/06/2026
**Total Transactions**: {total_transactions}
**Database**: {db_path}

---

## Step 1 - Category Distribution

### Category Breakdown (Sorted by Count)

| Category | Transaction Count | Total Debit | Total Credit |
|----------|-------------------|-------------|--------------|
"""

    for category in category_distribution:
        report += f"""| {category['category']} | {category['transaction_count']} | {category['total_debit_formatted']} | {category['total_credit_formatted']} |\n"""

    report += f"""

### Top Categories Analysis
- **Most Frequent**: {category_distribution[0]['category']} ({category_distribution[0]['transaction_count']} transactions, {category_distribution[0]['transaction_count']/total_transactions*100:.1f}%)
- **Highest Debit Volume**: {max(category_distribution, key=lambda x: x['total_debit_paise'])['category']} ({max(category_distribution, key=lambda x: x['total_debit_paise'])['total_debit_formatted']})
- **Highest Credit Volume**: {max(category_distribution, key=lambda x: x['total_credit_paise'])['category']} ({max(category_distribution, key=lambda x: x['total_credit_paise'])['total_credit_formatted']})

---

## Step 2 - Uncategorized Analysis

### Uncategorized Metrics
- **Uncategorized Count**: {uncategorized_analysis['uncategorized_count']} transactions
- **Uncategorized Percentage**: {uncategorized_analysis['uncategorized_percentage']:.2f}%
- **Debit Volume Affected**: {uncategorized_analysis['uncategorized_debit_formatted']}
- **Credit Volume Affected**: {uncategorized_analysis['uncategorized_credit_formatted']}
- **Target Met (< 5%)**: {'✅ YES' if uncategorized_analysis['target_met'] else '❌ NO'}

### Status Assessment
"""

    if uncategorized_analysis['target_met']:
        report += "- ✅ **EXCELLENT**: Uncategorized rate is below 5% target\n"
    elif uncategorized_analysis['uncategorized_percentage'] < 10:
        report += "- ⚠️  **GOOD**: Uncategorized rate is acceptable but could be improved\n"
    else:
        report += "- 🔴 **CRITICAL**: Uncategorized rate exceeds acceptable threshold\n"

    if uncategorized_analysis['samples']:
        report += f"""

### Sample Uncategorized Transactions ({len(uncategorized_analysis['samples'])} shown)
| ID | Description | Amount | Type |
|----|-------------|--------|------|
"""
        for sample in uncategorized_analysis['samples']:
            report += f"""| {sample['id']} | {sample['description']} | {sample['amount_formatted']} | {sample['type']} |\n"""
    else:
        report += f"""

- ✅ **PERFECT**: No uncategorized transactions found\n"""

    # Step 3 - Merchant Normalization
    report += f"""

---

## Step 3 - Merchant Normalization Audit

### Merchant Variants Requiring Normalization ({len(merchant_candidates)} groups found)
"""

    if merchant_candidates:
        for i, candidate in enumerate(merchant_candidates, 1):
            report += f"""

#### Group {i}: {candidate['normalized_name']} ({candidate['total_transactions']} total transactions)
| Variant | Count | Debit | Credit |
|---------|-------|-------|--------|
"""
            for variant in candidate['variants']:
                report += f"""| {variant['variant']} | {variant['count']} | {format_paise(variant['debit_paise'])} | {format_paise(variant['credit_paise'])} |\n"""

            report += f"""

**Recommendation**: Standardize to '{candidate['normalized_name']}' for consistent reporting\n"""
    else:
        report += "- ✅ **EXCELLENT**: No merchant normalization candidates identified\n"

    # Step 4 - Category Quality Review
    report += f"""

---

## Step 4 - Category Quality Review

### Suspicious Classifications Found ({len(suspicious_classifications)} issues)
"""

    if suspicious_classifications:
        report += f"""

| ID | Description | Category | Amount | Type | Issue | Severity |
|----|-------------|----------|--------|------|-------|----------|
"""
        for issue in suspicious_classifications:
            report += f"""| {issue['id']} | {issue['description']} | {issue['category']} | {issue['amount_formatted']} | {issue['type']} | {issue['issue']} | {issue['severity']} |\n"""

        # Summary statistics
        high_severity = sum(1 for issue in suspicious_classifications if issue['severity'] == 'HIGH')
        medium_severity = sum(1 for issue in suspicious_classifications if issue['severity'] == 'MEDIUM')

        report += f"""

### Severity Summary
- **High Severity**: {high_severity} issues (require immediate review)
- **Medium Severity**: {medium_severity} issues (should be reviewed)
- **Total Impact**: {len(suspicious_classifications)} transactions potentially misclassified
"""
    else:
        report += "- ✅ **EXCELLENT**: No suspicious classifications detected\n"

    # Step 5 - Duplicate Detection
    report += f"""

---

## Step 5 - Duplicate Detection

### Exact Duplicates ({len(duplicate_transactions['exact_duplicates'])} groups found)
"""

    if duplicate_transactions['exact_duplicates']:
        for dup in duplicate_transactions['exact_duplicates']:
            report += f"""

- **{dup['description']}** (₹{dup['amount_formatted']}, {dup['date']})
  - **Count**: {dup['count']} identical transactions
  - **IDs**: {dup['transaction_ids']}
  - **Severity**: {dup['severity']} - Likely import duplicates
"""
    else:
        report += "- ✅ **EXCELLENT**: No exact duplicates found\n"

    report += f"""

### Near Duplicates ({len(duplicate_transactions['near_duplicates'])} groups found)
"""

    if duplicate_transactions['near_duplicates']:
        for dup in duplicate_transactions['near_duplicates']:
            report += f"""

- **{dup['description']}** (₹{dup['amount_formatted']})
  - **Count**: {dup['count']} similar transactions
  - **Date Range**: {dup['first_date']} to {dup['last_date']}
  - **Severity**: {dup['severity']} - Potential recurring transactions
"""
    else:
        report += "- ✅ **EXCELLENT**: No near duplicates found\n"

    # Recommendations
    report += f"""

---

## Recommendations

### Immediate Actions
"""

    actions = []
    if not uncategorized_analysis['target_met']:
        actions.append(f"- 🔴 **CRITICAL**: Reduce uncategorized rate from {uncategorized_analysis['uncategorized_percentage']:.1f}% to < 5%")
    if merchant_candidates:
        actions.append(f"- ⚠️  **RECOMMENDED**: Normalize {len(merchant_candidates)} merchant name groups for consistent reporting")
    if suspicious_classifications:
        actions.append(f"- ⚠️  **RECOMMENDED**: Review {len(suspicious_classifications)} suspicious classifications")
    if duplicate_transactions['exact_duplicates']:
        actions.append(f"- 🔴 **CRITICAL**: Investigate {len(duplicate_transactions['exact_duplicates'])} exact duplicate groups")

    if actions:
        for action in actions:
            report += f"{action}\n"
    else:
        report += "- ✅ **EXCELLENT**: No immediate actions required\n"

    report += f"""

### Data Quality Improvements
- Implement automated merchant normalization rules
- Add pattern matching for common misclassifications (EMI, salary, etc.)
- Enhance categorization rules for uncategorized transactions
- Review duplicate detection logic in import pipeline
- Consider adding transaction deduplication features

---

## Quality Metrics Summary

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Total Transactions | {total_transactions} | N/A | ✅ |
| Uncategorized Rate | {uncategorized_analysis['uncategorized_percentage']:.2f}% | < 5% | {'✅ PASS' if uncategorized_analysis['target_met'] else '❌ FAIL'} |
| Merchant Variants | {len(merchant_candidates)} groups | 0 | {'✅ PASS' if not merchant_candidates else '⚠️ REVIEW'} |
| Suspicious Classifications | {len(suspicious_classifications)} | 0 | {'✅ PASS' if not suspicious_classifications else '⚠️ REVIEW'} |
| Exact Duplicates | {len(duplicate_transactions['exact_duplicates'])} groups | 0 | {'✅ PASS' if not duplicate_transactions['exact_duplicates'] else '🔴 FAIL'} |

---

## Conclusion

This comprehensive audit analyzed {total_transactions} transactions across multiple dimensions:

- **Category Distribution**: {len(category_distribution)} unique categories identified
- **Uncategorized Rate**: {uncategorized_analysis['uncategorized_percentage']:.2f}% {'(✅ Below target)' if uncategorized_analysis['target_met'] else '(❌ Above target)'}
- **Merchant Normalization**: {len(merchant_candidates)} merchant groups needing standardization
- **Classification Quality**: {len(suspicious_classifications)} potential misclassifications detected
- **Duplicate Detection**: {len(duplicate_transactions['exact_duplicates'])} exact duplicate groups found

**Overall Quality Assessment**: {'✅ EXCELLENT' if (uncategorized_analysis['target_met'] and not merchant_candidates and not suspicious_classifications and not duplicate_transactions['exact_duplicates']) else '⚠️ GOOD WITH IMPROVEMENT OPPORTUNITIES' if uncategorized_analysis['target_met'] else '🔴 NEEDS ATTENTION'}

**No production data was modified during this audit.** All findings are based on read-only analysis of the existing database state.

---

**Audit Status**: {'✅ COMPLETE' if uncategorized_analysis['target_met'] else '⚠️ ACTION REQUIRED'}
**Generated**: 23/06/2026
"""

    # Write report to file
    with open(output_file, 'w') as f:
        f.write(report)

    print(f"✅ Transaction Classification Audit Report generated: {output_file}")
    return report

if __name__ == "__main__":
    import sys
    import os
    db_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "data", "finance.db")
    generate_classification_audit_report(db_path)