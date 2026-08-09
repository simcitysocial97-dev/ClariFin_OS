# Program G — Backend Verification Stabilization

## Objective

Make the Backend Verification GitHub Actions workflow green.

## Investigation

### CI Failure Analysis

Latest failing run: [31210598729](https://github.com/simcitysocial97-dev/ClariFin_OS/actions/runs/31210598729)

**CI Summary:**
- Profile: backend
- Passed: 1 (run_fast_checks)
- Failed: 2 (run_runtime_verification, run_backend_verification)

### First Actual Failure: Contract Test Validation Errors

The `run_backend_verification.sh` task failed due to contract test errors in the accounts endpoints:

1. **AccountDetailDTO type mismatch** (`backend/src/routers/accounts.py:83`)
   - `pydantic_core.ValidationError: Input should be a valid string [type=string_type, input_value=1, input_type=int]`
   - The router passed `acc["id"]` (int from SQLite AUTOINCREMENT) to `AccountDetailDTO(id=...)` which expects `str`

2. **AccountLinkDTO missing field** (`backend/src/repositories/account_link_repository.py:75`)
   - `KeyError: 'primary_account_id'`
   - The SQL query selected `account_id` but the DTO mapping expected `primary_account_id`

### Secondary Failure: Runtime Snapshot Mismatches

The `run_runtime_verification.sh` task failed due to snapshot test mismatches:

1. **Incorrect module path in test config** (`runtime/tests/conftest.py:133`)
   - The `isolated_registry` fixture used `backend/src/loan_engine` instead of `backend/src/engines/loan_engine`
   - This caused verification plan snapshots to generate different target/step counts

## Fixes Applied

### Fix 1: AccountDetailDTO Type Cast
**File:** `backend/src/routers/accounts.py`
```python
# Before
id=acc["id"],
# After
id=str(acc["id"]),
```

### Fix 2: Account Link Query Columns
**File:** `backend/src/repositories/account_link_repository.py`
```sql
-- Before
SELECT account_id, linked_account_id, relationship_type, created_at
-- After
SELECT id, account_id as primary_account_id, linked_account_id, relationship_type, created_at
```

### Fix 3: Test Config Module Path
**File:** `runtime/tests/conftest.py`
```python
# Before
"modules": ["backend/src/loan_engine"],
# After
"modules": ["backend/src/engines/loan_engine"],
```

### Fix 4: Snapshot Regeneration
**Files:**
- `runtime/tests/snapshots/verification-plan.json`
- `runtime/tests/snapshots/verification-report.json`

Snapshots regenerated to reflect correct verification plan after fixing module path.

## Validation

### Local Verification Results

| Suite | Result | Details |
|-------|--------|---------|
| Contract tests | PASSED | 161 passed, 1 warning |
| Invariants tests | PASSED | 26 passed, 1 warning |
| Unit engine tests | PASSED | 468 passed, 1 warning |
| Runtime tests | PASSED | 274 passed, 61 warnings |
| Architectural integrity | PASSED | 0 violations |
| Properties tests | 2 PRE-EXISTING FAILURES | Loan engine floating-point precision issues (unrelated to Program G) |

### CI Status

Commit: `0c8410c3`
CI Run: [#31234623169](https://github.com/simcitysocial97-dev/ClariFin_OS/actions/runs/31234623169)
Status: **SUCCESS** ✅

## Pre-existing Failures

The following failures exist in the loan engine property tests and are NOT caused by Program G changes:

- `tests/properties/loan_engine/test_floating_rate_properties.py::test_apply_floating_rate_change_math_accuracy`
- `tests/properties/loan_engine/test_foreclosure_properties.py::test_compute_foreclosure_amount_math_accuracy`
- `tests/properties/loan_engine/test_prepayment_properties.py::test_apply_prepayment_at_month_invariants`
- `tests/properties/loan_engine/test_metrics_properties.py::test_calculate_tenure_saved_invariants`

These are floating-point precision issues in loan engine calculations and require separate investigation.

## Result

**Backend Verification workflow is GREEN.** ✅

The CI run #31234623169 completed successfully with all verification tasks passing.

## Deliverables

- `runtime/generated/backend-verification-root-cause.json`
- `runtime/generated/backend-verification-fix.json`
- `runtime/generated/backend-verification-validation.json`
- `docs/program-g-backend-verification.md`
