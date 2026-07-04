"""P3.2 - Transaction Classification Quality Audit

Objective: Measure transaction classification quality across all imported financial history.

Scope: Audit transaction categories, merchant normalization, and duplicate detection.
"""

import re
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict
from audits.base_audit import BaseAudit
from core.models import AuditResult, AuditStatus, Finding, Transaction
from core.repositories.transaction_repo import TransactionRepository
from core.db.connection import DatabaseConnection

class P32ClassificationAudit(BaseAudit):
    """Transaction Classification Quality Audit."""

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
        self.transaction_repo = TransactionRepository(db_connection)

    def run(self) -> AuditResult:
        """Run the transaction classification audit."""
        # Get all transactions
        all_transactions = self.transaction_repo.get_all_transactions()
        total_transactions = len(all_transactions)

        # Perform analyses
        category_distribution = self.transaction_repo.get_transactions_by_category()
        uncategorized_analysis = self._analyze_uncategorized_transactions(all_transactions)
        merchant_candidates = self._find_merchant_normalization_candidates()
        suspicious_classifications = self._find_suspicious_classifications()
        duplicate_transactions = self._find_duplicate_transactions()

        # Determine status
        status = self._determine_status(uncategorized_analysis, merchant_candidates,
                                      suspicious_classifications, duplicate_transactions)

        # Create audit result
        result = AuditResult(
            audit_name="P3.2 - Transaction Classification Quality Audit",
            timestamp=datetime.now(),
            metrics={
                'total_transactions': total_transactions,
                'unique_categories': len(category_distribution),
                'uncategorized_count': uncategorized_analysis['uncategorized_count'],
                'uncategorized_percentage': uncategorized_analysis['uncategorized_percentage'],
                'merchant_variant_groups': len(merchant_candidates),
                'suspicious_classifications': len(suspicious_classifications),
                'exact_duplicates': len(duplicate_transactions['exact_duplicates']),
                'near_duplicates': len(duplicate_transactions['near_duplicates'])
            },
            summary={
                'category_distribution': category_distribution,
                'uncategorized_analysis': uncategorized_analysis,
                'merchant_candidates': merchant_candidates,
                'suspicious_classifications': suspicious_classifications,
                'duplicate_transactions': duplicate_transactions
            },
            findings=self._create_findings(uncategorized_analysis, merchant_candidates,
                                          suspicious_classifications, duplicate_transactions),
            status=status
        )

        return result

    def _analyze_uncategorized_transactions(self, all_transactions: List[Transaction]) -> Dict[str, Any]:
        """Analyze uncategorized transactions and calculate metrics."""
        uncategorized = [t for t in all_transactions if t.category == 'Uncategorized']
        uncategorized_count = len(uncategorized)
        total_transactions = len(all_transactions)

        uncategorized_debit = sum(t.amount_paise for t in uncategorized if t.type == 'debit')
        uncategorized_credit = sum(t.amount_paise for t in uncategorized if t.type == 'credit')

        return {
            'uncategorized_count': uncategorized_count,
            'uncategorized_percentage': (uncategorized_count / total_transactions * 100) if total_transactions > 0 else 0,
            'uncategorized_debit_paise': uncategorized_debit,
            'uncategorized_credit_paise': uncategorized_credit,
            'target_met': uncategorized_count / total_transactions * 100 < 5 if total_transactions > 0 else True,
            'samples': uncategorized[:10]  # First 10 samples
        }

    def _normalize_merchant_name(self, name: str) -> str:
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

    def _find_merchant_normalization_candidates(self) -> List[Dict[str, Any]]:
        """Identify merchant names that likely represent the same entity."""
        with self.db.connection() as conn:
            # Get all unique merchant names
            cursor = conn.execute("""
                SELECT DISTINCT description
                FROM transactions
                WHERE description IS NOT NULL AND description != ''
            """)
            merchants = [row['description'] for row in cursor.fetchall()]

            # Group by normalized name
            merchant_groups = defaultdict(list)
            for merchant in merchants:
                normalized = self._normalize_merchant_name(merchant)
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
                            SELECT COUNT(*), SUM(CASE WHEN type = 'debit' THEN amount_paise ELSE 0 END),
                                   SUM(CASE WHEN type = 'credit' THEN amount_paise ELSE 0 END)
                            FROM transactions
                            WHERE description = ?
                        """, (variant,))
                        stats = cursor.fetchone()
                        variant_stats.append({
                            'variant': variant,
                            'count': stats[0],
                            'debit_paise': stats[1] or 0,
                            'credit_paise': stats[2] or 0
                        })

                    candidates.append({
                        'normalized_name': normalized,
                        'variants': variant_stats,
                        'total_transactions': sum(v['count'] for v in variant_stats)
                    })

            # Sort by total transactions descending
            candidates.sort(key=lambda x: x['total_transactions'], reverse=True)
            return candidates

    def _find_suspicious_classifications(self) -> List[Dict[str, Any]]:
        """Identify potentially incorrect transaction classifications."""
        suspicious = []

        with self.db.connection() as conn:
            # 1. Look for large transactions in unexpected categories
            cursor = conn.execute("""
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
                    'type': row['type'],
                    'issue': 'Large transaction in unexpected category',
                    'severity': 'HIGH'
                })

            # 2. Look for EMI payments not categorized as EMI
            cursor = conn.execute("""
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
                    'type': 'debit',
                    'issue': 'Potential EMI misclassified',
                    'severity': 'MEDIUM'
                })

            # 3. Look for salary/income not categorized properly
            cursor = conn.execute("""
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
                    'type': 'credit',
                    'issue': 'Potential salary/income misclassified',
                    'severity': 'HIGH'
                })

        return suspicious

    def _find_duplicate_transactions(self) -> Dict[str, Any]:
        """Identify exact and near duplicate transactions."""
        duplicates = {
            'exact_duplicates': [],
            'near_duplicates': []
        }

        with self.db.connection() as conn:
            # 1. Find exact duplicates (same description, amount, date)
            cursor = conn.execute("""
                SELECT description, amount_paise, date_iso, COUNT(*) as count
                FROM transactions
                GROUP BY description, amount_paise, date_iso
                HAVING COUNT(*) > 1
                ORDER BY COUNT(*) DESC
                LIMIT 5
            """)

            for row in cursor.fetchall():
                cursor.execute("""
                    SELECT id, date_iso, amount_paise
                    FROM transactions
                    WHERE description = ? AND amount_paise = ? AND date_iso = ?
                    ORDER BY id
                """, (row['description'], row['amount_paise'], row['date_iso']))

                duplicate_ids = [f"{r['id']} (₹{r['amount_paise']/100:.2f})" for r in cursor.fetchall()]

                duplicates['exact_duplicates'].append({
                    'description': row['description'],
                    'amount_paise': row['amount_paise'],
                    'date': row['date_iso'],
                    'count': row['count'],
                    'transaction_ids': ', '.join(duplicate_ids),
                    'severity': 'CRITICAL'
                })

            # 2. Find near duplicates (same description and amount, different dates)
            cursor = conn.execute("""
                SELECT description, amount_paise, COUNT(*) as count,
                       MIN(date_iso) as first_date, MAX(date_iso) as last_date
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
                        'count': row['count'],
                        'first_date': row['first_date'],
                        'last_date': row['last_date'],
                        'severity': 'MEDIUM'
                    })

        return duplicates

    def _determine_status(self, uncategorized_analysis: dict, merchant_candidates: list,
                         suspicious_classifications: list, duplicate_transactions: dict) -> AuditStatus:
        """Determine overall audit status."""
        uncategorized_rate = uncategorized_analysis['uncategorized_percentage']

        if uncategorized_rate >= 10:
            return AuditStatus.FAIL
        elif (uncategorized_rate >= 5 or len(merchant_candidates) > 0 or
              len(suspicious_classifications) > 0 or len(duplicate_transactions['exact_duplicates']) > 0):
            return AuditStatus.WARNING
        else:
            return AuditStatus.PASS

    def _create_findings(self, uncategorized_analysis: dict, merchant_candidates: list,
                         suspicious_classifications: list, duplicate_transactions: dict) -> List[Finding]:
        """Create findings from analysis results."""
        findings = []

        # Uncategorized findings
        if not uncategorized_analysis['target_met']:
            findings.append(Finding(
                description=f"Uncategorized rate {uncategorized_analysis['uncategorized_percentage']:.1f}% exceeds 5% target",
                severity="HIGH",
                details={
                    "type": "uncategorized_rate",
                    "current_rate": uncategorized_analysis['uncategorized_percentage'],
                    "target_rate": 5.0,
                    "uncategorized_count": uncategorized_analysis['uncategorized_count']
                }
            ))

        # Merchant normalization findings
        for candidate in merchant_candidates:
            findings.append(Finding(
                description=f"Merchant normalization needed: {candidate['normalized_name']} ({candidate['total_transactions']} transactions across {len(candidate['variants'])} variants)",
                severity="MEDIUM",
                details={
                    "type": "merchant_normalization",
                    "normalized_name": candidate['normalized_name'],
                    "variants": [v['variant'] for v in candidate['variants']],
                    "total_transactions": candidate['total_transactions']
                }
            ))

        # Suspicious classification findings
        for issue in suspicious_classifications:
            findings.append(Finding(
                description=f"Transaction {issue['id']}: {issue['description']} - {issue['issue']}",
                severity=issue['severity'],
                details={
                    "type": "suspicious_classification",
                    "transaction_id": issue['id'],
                    "description": issue['description'],
                    "category": issue['category'],
                    "amount_paise": issue['amount_paise'],
                    "issue": issue['issue']
                }
            ))

        # Exact duplicate findings
        for dup in duplicate_transactions['exact_duplicates']:
            findings.append(Finding(
                description=f"Exact duplicate: {dup['description']} (₹{dup['amount_paise']/100:.2f}, {dup['date']}) - {dup['count']} identical transactions",
                severity=dup['severity'],
                details={
                    "type": "exact_duplicate",
                    "description": dup['description'],
                    "amount_paise": dup['amount_paise'],
                    "date": dup['date'],
                    "count": dup['count'],
                    "transaction_ids": dup['transaction_ids']
                }
            ))

        # Near duplicate findings
        for dup in duplicate_transactions['near_duplicates']:
            findings.append(Finding(
                description=f"Near duplicate: {dup['description']} (₹{dup['amount_paise']/100:.2f}) - {dup['count']} similar transactions from {dup['first_date']} to {dup['last_date']}",
                severity=dup['severity'],
                details={
                    "type": "near_duplicate",
                    "description": dup['description'],
                    "amount_paise": dup['amount_paise'],
                    "count": dup['count'],
                    "first_date": dup['first_date'],
                    "last_date": dup['last_date']
                }
            ))

        return findings