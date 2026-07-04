# P3.1 - Financial Inventory Reconciliation Audit

## Executive Summary

**Audit Status**: ⚠️ WARNING
**Generated**: 2026-06-23 18:21:51
**Total Findings**: 12

Some issues detected that require attention but no critical failures.

---

## Key Metrics

- **total_accounts**: 3
- **total_cards**: 4
- **total_loans**: 1
- **total_investments**: 0
- **total_recurring**: 1
- **orphaned_transactions**: 10
- **orphaned_loans**: 0
- **orphaned_recurring**: 1

---

## Detailed Findings

### 🟡 HIGH Findings (10)

**1. Transaction 92 references invalid account: CC1**
   - *Details*: data: {'transaction_id': 92, 'invalid_account_id': 'CC1'}

**2. Transaction 93 references invalid account: CC1**
   - *Details*: data: {'transaction_id': 93, 'invalid_account_id': 'CC1'}

**3. Transaction 94 references invalid account: CC1**
   - *Details*: data: {'transaction_id': 94, 'invalid_account_id': 'CC1'}

**4. Transaction 96 references invalid account: CC1**
   - *Details*: data: {'transaction_id': 96, 'invalid_account_id': 'CC1'}

**5. Transaction 98 references invalid account: CC1**
   - *Details*: data: {'transaction_id': 98, 'invalid_account_id': 'CC1'}

**6. Transaction 100 references invalid account: CC1**
   - *Details*: data: {'transaction_id': 100, 'invalid_account_id': 'CC1'}

**7. Transaction 105 references invalid account: CC1**
   - *Details*: data: {'transaction_id': 105, 'invalid_account_id': 'CC1'}

**8. Transaction 107 references invalid account: CC1**
   - *Details*: data: {'transaction_id': 107, 'invalid_account_id': 'CC1'}

**9. Transaction 109 references invalid account: CC1**
   - *Details*: data: {'transaction_id': 109, 'invalid_account_id': 'CC1'}

**10. Transaction 118 references invalid account: CC1**
   - *Details*: data: {'transaction_id': 118, 'invalid_account_id': 'CC1'}

### 🟠 MEDIUM Findings (2)

**1. Loans without linked accounts: 1**
   - *Details*: 

**2. Recurring transaction 'Test Subscription' references invalid account: 1**
   - *Details*: data: {'description': 'Test Subscription', 'invalid_account_id': '1'}

---

## Conclusion & Recommendations

⚠️ **ATTENTION REQUIRED**: Some issues were detected that should be reviewed.
- Review the findings above and address as appropriate
- Monitor trends over time
- Consider implementing automated corrections where possible

---

**Audit Completed**: 2026-06-23 18:21:51
**Status**: WARNING
