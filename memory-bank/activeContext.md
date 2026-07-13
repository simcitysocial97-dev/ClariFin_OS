# Active Context

## Phase 0 Discovery Complete — Reconciliation Engine v2 Analysis

### Discovery Findings Summary

**Architecture Layers Verified:**
- Router → Service → Engine → Repository → SQLite flow confirmed
- Key violation: Engines have direct DB access (reconciliation_engine.py, behavior_engine.py)

**Matching Rules Found (reconciliation_engine.py):**
- Exact match: same amount, same date (0 days diff), different accounts
- Window match: same amount, date within 3 days, different accounts
- No disambiguation for multiple candidates
- Confidence: 0.4 (exact date) + 0.4 (exact amount) + 0.2 (transfer keywords)

**Existing Implementations:**
- Reconciliation: Engine, Repository, Service, Router, Model all exist
- Financial Events: Model exists but no table/repository (orphaned)
- Cash Flow: Repository exists but no engine
- Behaviour Engine: Two parallel systems (behavior_engine.py old, behaviour_engine/ new)
- Loan Engine: Full amortization schedule generation with reducing balance
- Credit Card Engine: Outstanding/interest calculations, no statement DB reads

### Key Technical Debt to Address
1. Engine purity violations (direct sqlite3.connect)
2. match_confidence REAL should be INTEGER basis points
3. interest_rate REAL should be INTEGER basis points
4. Duplicate behavior routers (US vs UK spelling)

### Phase 1 — Foundational Schema Changes (Completed)

**New migrations created:**
- `migration_006_household.py`: Adds `owner_id` and `household_id` columns to `accounts` table with backfill to `'self'`/`'primary'` defaults
- `migration_007_reconciliation_audit.py`: Adds `confidence_bps INTEGER` column to `reconciliations` with backfill from `match_confidence`, reports NULL/out-of-range rows, creates `reconciliation_audit_log` table with FK cascade

**Repositories extended:**
- `account_repository.py`: Added `get_household_accounts()`, `get_accounts_by_owner()`, `is_same_household()` (253→295 LOC, under 300 limit)
- `reconciliation_audit_repository.py` (new): `insert_audit_log()`, `get_audit_trail()` — split from reconciliation_repository.py to stay under 200 LOC
- `reconciliation_repository.py`: Added deprecation comment marking `match_confidence` as legacy, `confidence_bps` as authoritative

**Tests (26/26 passing):**
- `test_migration_confidence_bps.py` (4 tests): Backfill correctness, NULL handling, out-of-range flagging, idempotency
- `test_migration_household.py` (4 tests): Column addition, backfill, idempotency, new-account defaults
- `test_audit_repository.py` (6 tests): Insert/retrieve round-trip, multi-entry ordering, empty trail, FK violation (negative test), all-fields
- `test_household_repository.py` (12 tests): Multi-household querying, multi-owner filtering, `is_same_household` across boundaries with non-existent accounts

### Next Steps
- Phase 2: Engine purity refactor (remove direct sqlite3.connect from engines)
- Phase 3-8: Await specifications for implementation
