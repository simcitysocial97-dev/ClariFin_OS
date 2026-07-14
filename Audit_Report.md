# ClariFin_OS Backend Architecture Audit Report
# Principal Architect Review — Post Phase 9.5 (Verification Pass)

---

## Legend: Observed vs Inferred

- **Observed**: Verified by direct inspection of source code.
- **Inferred**: Derived from structure, naming, tests, or documentation without full source verification.
- **Unverified**: Claim requires further inspection.

---

## PHASE 1: Executive Summary & System Topology

... (unchanged from previous version) ...

---

## PHASE 18: VERIFICATION FINDINGS — Financial Events Lifecycle

### 18.1 CREATE TABLE for financial_events (Observed)

**Source:** `backend/scripts/migration_financial_events.py` lines 19-52

```sql
CREATE TABLE IF NOT EXISTS financial_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Event classification
    event_type TEXT NOT NULL,

    -- Transaction linkage (JSON array stored as TEXT)
    transaction_ids TEXT NOT NULL,

    -- Amount fields
    amount_paise INTEGER DEFAULT 0,
    asset_change_paise INTEGER DEFAULT 0,
    liability_change_paise INTEGER DEFAULT 0,
    expense_paise INTEGER DEFAULT 0,
    income_paise INTEGER DEFAULT 0,

    -- Temporal fields
    date_iso TEXT NOT NULL,
    month_bucket TEXT NOT NULL,

    -- Account linkage
    account_id TEXT,
    counterparty_account_id TEXT,

    -- Categorization
    category TEXT,
    subcategory TEXT,
    sub_type TEXT,
    provider TEXT,

    -- Multi-user support
    household_id TEXT DEFAULT 'primary',
    owner_id TEXT DEFAULT 'self',

    -- Lifecycle tracking
    lifecycle_state TEXT DEFAULT 'open',
    settled_by_event_id INTEGER,
    outstanding_paise INTEGER DEFAULT 0,
    superseded_by INTEGER,

    -- Confidence (new authoritative field alongside deprecated float)
    confidence REAL DEFAULT 0.0,
    confidence_bps INTEGER,

    -- Notes
    notes TEXT,

    -- Audit
    reviewed_by_user INTEGER DEFAULT 0,

    -- Timestamps
    created_at TEXT DEFAULT (datetime('now'))
)
```

**No immutability triggers defined** — Unlike transactions table (db.py lines 386-401) which has `prevent_transaction_update` and `prevent_transaction_delete` triggers, financial_events has NO such triggers.

---

### 18.2 Settlement Logic — Exact Code (Observed)

**Source:** `backend/src/repositories/financial_event_repository.py` lines 133-163

```python
def update_lifecycle(
    self,
    event_id: int,
    lifecycle_state: LifecycleState,
    outstanding_paise: int = 0,
    settled_by_event_id: int | None = None,
) -> bool:
    """
    Update lifecycle state of an event.
    ...
    """
    with self._get_conn() as conn:
        cur = conn.execute(
            """
            UPDATE financial_events
            SET lifecycle_state = ?, outstanding_paise = ?, settled_by_event_id = ?
            WHERE id = ?
            """,
            (lifecycle_state, outstanding_paise, settled_by_event_id, event_id),
        )
        updated = cur.rowcount > 0
        conn.commit()
    return updated
```

**This is an UPDATE on the existing row** — Not an INSERT of a new event.

**Source:** `backend/src/services/financial_events_service.py` lines 59-77 (calling update_lifecycle)

```python
# Apply lifecycle updates
for update in proposal.lifecycle_updates:
    self.event_repo.update_lifecycle(
        event_id=update["event_id"],
        lifecycle_state=update["lifecycle_state"],
        outstanding_paise=update["outstanding_paise"],
    )
```

**Source:** `backend/src/engines/financial_events/lineage_walker.py` lines 152-182 (producing lifecycle_updates)

```python
# Calculate outstanding after this payment
advance_outstanding = int(matched_advance.get("outstanding_paise", 0) or 0)
payment_amount = int(event.get("liability_change_paise", 0) or 0)
# liability_change_paise for repayment is negative, use absolute value
if payment_amount < 0:
    payment_amount = abs(payment_amount)

new_outstanding = max(0, advance_outstanding - payment_amount)
new_state = "settled" if new_outstanding == 0 else "partially_settled"

proposed_links.append({
    "event_id": event_id,
    "linked_event_id": matched_advance_id,
    "link_type": "settles",
})

lifecycle_updates.append({
    "event_id": matched_advance_id,
    "lifecycle_state": new_state,
    "outstanding_paise": new_outstanding,
})
```

---

### 18.3 Test Exercising Settlement Path (Observed)

**Source:** `backend/tests/test_financial_events.py` lines 250-278

```python
def test_full_payment_creates_settled_state():
    """Test that full payment updates advance to settled state."""
    events = [
        {
            "id": 1,
            "event_type": "credit_card_cash_advance",
            "date_iso": "2025-01-01",
            "account_id": "CC1",
            "lifecycle_state": "open",
            "liability_change_paise": 100000,
            "outstanding_paise": 100000,
        },
        {
            "id": 2,
            "event_type": "liability_repayment",
            "date_iso": "2025-01-15",
            "account_id": "CC1",
            "lifecycle_state": "open",
            "liability_change_paise": -100000,
        },
    ]

    proposal = walk_lineage(events)

    assert len(proposal.lifecycle_updates) == 1
    assert proposal.lifecycle_updates[0]["lifecycle_state"] == "settled"
    assert proposal.lifecycle_updates[0]["outstanding_paise"] == 0
```

**Assertion:** `proposal.lifecycle_updates[0]["lifecycle_state"] == "settled"` and `assert proposal.lifecycle_updates[0]["outstanding_paise"] == 0`

---

### 18.4 Financial Events Mutability — Resolution (Observed)

**Contradiction Resolved:**

The Mutation Matrix in Phase 11 claimed "FinancialEvent: Immutable after creation" but this is **false**.

Evidence:
1. **No triggers** — `financial_events` table has NO `prevent_update` or `prevent_delete` triggers (unlike `transactions` table in db.py lines 386-401)
2. **UPDATE statement exists** — `financial_event_repository.py` line 155 performs `UPDATE financial_events SET lifecycle_state = ?, outstanding_paise = ?`
3. **Service orchestrates mutations** — `financial_events_service.py` lines 59-77 calls `update_lifecycle()` on existing rows

**Corrected State Ownership:**

| Object | Can Mutate? | Where | Notes |
|--------|-------------|-------|-------|
| FinancialEvent | **Yes** | FinancialEventsService | `lifecycle_state`, `outstanding_paise`, `settled_by_event_id` updated via `update_lifecycle()`; no trigger enforcement |

---

## PHASE 19: Previous Audit Report (Unchanged)

... (rest of previous Audit_Report.md content remains) ...

---

/* REMAINING CONTENT FROM PHASE 1-17 REMOVED FOR BREVITY - SEE COMMIT c7c4ee4c */