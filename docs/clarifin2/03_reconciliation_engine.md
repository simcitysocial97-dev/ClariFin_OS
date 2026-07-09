# Reconciliation Engine - ClariFinOS 2.0

*Complete money flow graph across all accounts*

---

## Purpose

Create a verifiable, auditable graph of all money movements. Every rupee that leaves one account must be accounted for when it appears in another. This engine is the **flagship capability** of ClariFinOS.

---

## Money Flow Types

### Internal Transfers
- **Same institution**: Within same bank (e.g., savings → checking)
- **Detection**: Same account_id pattern, complementary amounts

### Inter-Bank Transfers
| Method | Pattern | Confidence |
|--------|---------|------------|
| **UPI** | "UPI" in description, same amount within 1 day | High (0.9+) |
| **NEFT** | "NEFT" keyword, same amount 1-2 hours variance | High (0.9+) |
| **RTGS** | "RTGS" keyword, large amounts | High (0.9+) |
| **IMPS** | "IMPS" keyword, instant | High (0.9+) |
| **Wallet Transfer** | PhonePe/Paytm → bank | Medium (0.7+) |

### Credit Card Payments
- **Checking → Credit Card**: Payment of outstanding
- Detection: Large debit matching credit card statement amount

### Loan Payments
- **Checking → Loan**: EMI payment
- Detection: EMI keywords + amount matching

### Cash Operations
- **Cash Withdrawal**: ATM withdrawal from checking
- **Cash Deposit**: Cash added to account
- These are terminal nodes (cash leaves the tracked system)

---

## Matching Algorithms

### Priority Queue Architecture
```
Queue Priority:
1. Exact same amount, same date, different accounts (confidence: 1.0)
2. Same amount, date within 1 day (confidence: 0.9)
3. Same amount, date within 3 days (confidence: 0.8)
4. Partial amount match, transfer keywords (confidence: 0.6-0.7)
5. Manual review (confidence: 0.0)
```

### Matching Rules

#### Rule 1: Exact Match
```
IF abs(debit.amount_paise - credit.amount_paise) = 0
AND debit.date_iso = credit.date_iso
AND debit.account_id != credit.account_id
AND debit.type = 'debit' AND credit.type = 'credit'
THEN match_confidence = 1.0
```

#### Rule 2: Date Window Match
```
IF amount matches within tolerance (±₹1)
AND date_diff <= max_window_days (configurable, default 3)
AND different accounts
THEN match_confidence = 0.9 - (date_diff * 0.1)
```

#### Rule 3: Fuzzy Match (Future)
- Description similarity > 0.7
- Amount within 5%
- Date within 7 days
- Confidence: 0.6-0.8

---

## Confidence Score Formula

```
confidence = base_match_score
           + (description_similarity * 0.2)
           + (recency_factor * 0.1)

Where:
- base_match_score: 0.9 for amount+date match
- description_similarity: 1.0 if both contain transfer keywords
- recency_factor: 1.0 for same day, 0.5 for 1 day diff, 0.0 for 2+ days
```

---

## Explainability

### Match Explanation Template
```
[EXACT/WINDOW/FUZZY] Match: ₹{amount} transferred from {debit_account} ({debit_date}) to {credit_account} ({credit_date}), {days} days apart

Confidence factors:
- Amount match: +{amount_score}
- Date match: +{date_score}  
- Description similarity: +{desc_score}
```

### Why Not Matched
- Different amounts beyond tolerance
- Same account (not a transfer)
- Date difference exceeds window
- Both debits or both credits

---

## Transaction Graph

### Node Properties
```json
{
  "id": "txn_12345",
  "account_id": "hdfc_savings",
  "amount_paise": 50000,
  "date_iso": "2025-06-15",
  "type": "debit",
  "description": "UPI to ICICI",
  "is_reconciled": true,
  "counterpart_id": "txn_12346",
  "match_confidence": 0.9,
  "match_type": "upi"
}
```

### Edge Properties
```json
{
  "source_txn_id": 12345,
  "target_txn_id": 12346,
  "relationship": "transfer",
  "confidence": 0.9,
  "explanation": "UPI transfer detected",
  "reconciled_at": "2025-06-16T10:30:00Z",
  "reconciled_by": "system|user"
}
```

---

## Reconciliation Health Score

### Formula
```
Coverage Ratio = matched_transactions / total_transactions
Accuracy Score = correctly_matched / total_matched

Health Score = (Coverage Ratio * 0.6) + (Accuracy Score * 0.4) * 100
```

### Ratings
- **90-100**: Excellent - Most money flows understood
- **70-89**: Good - Some transfers missed
- **50-69**: Fair - Significant gaps
- **<50**: Poor - Manual review needed

---

## Audit Trail

### Reconciliation Actions Log
```sql
CREATE TABLE reconciliation_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reconciliation_id INTEGER REFERENCES reconciliations(id),
    action TEXT NOT NULL,  -- CONFIRM, REJECT, MODIFY, SPLIT
    actor TEXT NOT NULL,    -- user_id or 'system'
    timestamp TEXT DEFAULT (datetime('now')),
    reason TEXT,
    previous_state TEXT,    -- JSON snapshot
    new_state TEXT          -- JSON snapshot
);
```

### Fields Tracked
- Who confirmed/rejected
- When the action occurred
- Why (reason text)
- Previous and new state

---

## Rollback Capability

### Implementation
- Every reconciliation action is logged
- Undo button reverses the action
- Transactions return to pending state
- Cascade: if split, undo splits all parts

### Limitations
- Cannot undo reconciliations across months (historical lock)
- Manual overrides flagged for review

---

## Split/Merged Transactions

### Split Reconciliation
- One debit links to multiple credits
- Common for: Shopping with cashback, partial payments
- UI: Checkbox selection for each leg

### Merged Reconciliation
- Multiple debits link to one credit
- Common for: Multiple cash deposits, partial payments received
- User selects which debits combine

---

## Performance Requirements

| Metric | Target |
|--------|--------|
| Single transaction match | < 50ms |
| Full scan (1000 txns) | < 5s |
| Memory usage | < 100MB for 10K transactions |
| Concurrency | Thread-safe, WAL mode |

---

## Database Schema

### Required Changes to Existing
```sql
-- Add to transactions table
ALTER TABLE transactions ADD COLUMN is_reconciled INTEGER DEFAULT 0;
ALTER TABLE transactions ADD COLUMN reconciliation_group TEXT;  -- for splits

-- New tables
CREATE TABLE reconciliation_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reconciliation_id INTEGER REFERENCES reconciliations(id),
    action TEXT NOT NULL,
    actor TEXT NOT NULL,
    timestamp TEXT DEFAULT (datetime('now')),
    reason TEXT,
    previous_state TEXT,
    new_state TEXT
);

CREATE TABLE reconciliation_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern TEXT NOT NULL,  -- regex pattern
    match_type TEXT NOT NULL,  -- UPI, NEFT, CASH, etc.
    priority INTEGER DEFAULT 100,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE reconciliation_stats (
    date_iso TEXT PRIMARY KEY,
    total_transactions INTEGER,
    matched_count INTEGER,
    coverage_ratio REAL,
    health_score REAL
);
```

---

## Required APIs

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/reconciliation/scan` | POST | Run full match scan |
| `/api/v1/reconciliation/pending` | GET | List pending matches |
| `/api/v1/reconciliation/{id}` | GET | Single match details |
| `/api/v1/reconciliation/{id}/confirm` | POST | Confirm match |
| `/api/v1/reconciliation/{id}/reject` | POST | Reject match |
| `/api/v1/reconciliation/{id}/split` | POST | Split transaction |
| `/api/v1/reconciliation/{id}/undo` | POST | Rollback action |
| `/api/v1/reconciliation/stats` | GET | Health statistics |

---

## Testing Strategy

### Unit Tests
- Match confidence calculation
- Date window boundary conditions
- Description similarity scoring
- Partial amount tolerance

### Integration Tests
- Full scan with known dataset
- Confirm/reject workflows
- Split/undo operations
- Audit trail integrity

### Acceptance Criteria
- [ ] 95%+ match detection for clean data
- [ ] All matches have explanations
- [ ] Undo works within session
- [ ] Audit trail complete
- [ ] Health score accurate