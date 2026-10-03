# Remediation Gap Analysis & Follow-on Plan

**Date**: 2026-09-24  
**Scope**: Issues from BASELINE.md not yet resolved + defects introduced during M06b–M13 execution  
**Pre-requisite**: All milestones M00–M13 are implemented and committed (confirmed by git log)

---

## 1. Baseline Issues — Current Status

| # | Issue (from BASELINE.md) | Baseline State | Current State | Resolved? |
|---|---|---|---|---|
| B1 | 5 backend platform integration tests fail (`test_platform_api_phase3.py`, `test_platform_api_phase4.py`) | 5 failed / 3826 passed | Same 5 fail (out of scope — `/platform/v1/*` runtime defects) | ❌ Out of scope |
| B2 | `ruff check src/` — 3 errors, all in `platform.py` | 3 errors (F401×2, I001×1) | 3 errors remain in `platform.py` | ❌ Not resolved |
| B3 | `black --check src/` — 1 file (`platform.py`) | 1 file | Still fails on `platform.py` | ❌ Not resolved |
| B4 | `mypy src/` — 6 errors, all in `platform.py` | 6 errors | ~3 errors remain (import-not-found ×2, union-attr ×1) | ⚠️ Partially resolved |
| B5 | Frontend platform contract tests — 18 fail (ECONNREFUSED) | 18 failed / 1349 passed | Same (requires live backend) | ❌ Out of scope (environment) |
| B6 | Frontend TS errors — 3 errors | 3 errors | 2 fixed, 1 new introduced, 1 persists | ⚠️ Partially resolved |
| B7 | `npm run lint` — PASS | PASS | PASS | ✅ Resolved |
| B8 | `npm run build` — PASS | PASS | PASS | ✅ Resolved |
| B9 | `verify.sh quick` aborts on ruff | FAIL | FAIL (same root cause as B2) | ❌ Not resolved |

---

## 2. Defects Introduced During M06b–M13 Execution

| # | File | Error | Root Cause | Severity |
|---|---|---|---|---|
| I1 | `frontend/__tests__/utils/createMockResponse.ts:16` | `TS2693: 'MockResponse' only refers to a type, but is being used as a value` | Previous agent wrote `typeof MockResponse` instead of `MockResponse` — `MockResponse` is a `type` import so `typeof` resolves to the module namespace, not the interface | Medium |
| I2 | `frontend/lib/hooks/__tests__/use-platform-status.test.ts:11` | `TS6133: 'usePlatformStatus' is declared but its value is never read` | Pre-existing; import added but test body never calls the hook | Low |
| I3 | `backend/tests/integration/e2e/test_statement_upload_pipeline.py:43` | `assert isinstance(data, list)` fails — API returns `{transactions:[...], total:N, ...}` | Pre-existing assertion bug; response shape changed but test not updated | Medium |

---

## 3. Remaining Baseline Issues Requiring Action

### 3a. `platform.py` — ruff (3 errors), black (1 file), mypy (~3 errors)

These all live in the same file and share the same root cause: `platform.py` imports modules from `runtime.platform.*` and `runtime.foundation.verification.*` that either no longer exist or have shifted. The ruff I001 (import sort) and F401 (unused imports) are symptoms of the file having been partially refactored without full cleanup.

**Specific issues identified:**
- **ruff F401**: `runtime.platform.api.contracts._primitives.Status` — import removed but reference may remain elsewhere
- **ruff F401**: `runtime.platform.diagnostics.engine.build_diagnostic_recommendation` — import removed but reference may remain elsewhere  
- **ruff I001**: Import block ordering still incorrect
- **mypy import-not-found**: `runtime.foundation.verification.workflow_inspection` (line ~316)
- **mypy import-not-found**: `runtime.foundation.verification.capability_catalog` (line ~309)
- **mypy union-attr**: `dict[str, Any] | None` at line ~1034 — `.get("data", {}).get("recommendation", [])` where first `.get()` can return `None`

### 3b. `createMockResponse.ts` — TS2693 (introduced defect)

Line 16: `export const MOCK_RESPONSE: typeof MockResponse = {`  
Fix: Change `typeof MockResponse` → `MockResponse` (the interface itself, not its type-of).

### 3c. `use-platform-status.test.ts` — TS6133 (pre-existing)

Line 11: `import { usePlatformStatus } from '../use-platform-status';`  
The hook is imported but never called in any test. Tests only assert on `MOCK_STATUS` data directly.

**Two options:**
- (A) Remove the unused import
- (B) Add a test that actually calls `usePlatformStatus`

Recommended: **(A)** — minimal fix, preserves intent.

### 3d. `test_statement_upload_pipeline.py` — e2e assertion mismatch (pre-existing)

Line 43: `assert isinstance(data, list)` but the transactions endpoint returns a paginated dict.  
Fix: Update assertion to match actual response shape.

---

## 4. Implementation Plan

### Task 1 — Fix `platform.py` ruff/black/mypy

**File**: `backend/src/routers/platform.py`

**Steps:**
1. Run `ruff check backend/src/routers/platform.py` to enumerate exact current errors
2. Run `ruff check backend/src/routers/platform.py --fix` to auto-fix F401 and I001
3. Run `black backend/src/routers/platform.py` to reformat
4. Run `mypy backend/src/routers/platform.py` to identify remaining type errors
5. Fix mypy `union-attr` error at ~line 1034: change `diag_result.get("data", {}).get(...)` to use explicit None-check or `diag_result.get("data") or {}`
6. Address mypy `import-not-found` errors for `workflow_inspection` and `capability_catalog`:
   - Verify these modules exist: `find backend/src -name "workflow_inspection*" -o -name "capability_catalog*"`
   - If they exist elsewhere, fix import paths
   - If they don't exist, remove the imports and the code that uses them, OR add `# type: ignore[import-not-found]` comments with a rationale

**Verification:**
```bash
.venv/bin/python -m ruff check backend/src/routers/platform.py
.venv/bin/python -m black --check backend/src/routers/platform.py
.venv/bin/python -m mypy backend/src/routers/platform.py
```
All three must exit 0.

---

### Task 2 — Fix `createMockResponse.ts` TS2693

**File**: `frontend/__tests__/utils/createMockResponse.ts`

**Change** (line 16):
```typescript
// Before:
export const MOCK_RESPONSE: typeof MockResponse = {
// After:
export const MOCK_RESPONSE: MockResponse = {
```

**Verification:**
```bash
cd frontend && npx tsc --noEmit
```
Must show 0 errors (or only the pre-existing `use-platform-status.test.ts` error).

---

### Task 3 — Fix `use-platform-status.test.ts` TS6133

**File**: `frontend/lib/hooks/__tests__/use-platform-status.test.ts`

**Change**: Remove line 11 (`import { usePlatformStatus } from '../use-platform-status';`)

Rationale: The import is unused. Tests only validate mock data shape, not the hook behavior. If hook behavior testing is desired, it should be added as a separate task.

**Verification:**
```bash
cd frontend && npx tsc --noEmit
```
Must show 0 TS errors.

---

### Task 4 — Fix `test_statement_upload_pipeline.py` e2e assertion

**File**: `backend/tests/integration/e2e/test_statement_upload_pipeline.py`

**Change** (lines 37–43):
```python
# Before:
def test_transactions_after_upload(self, client: TestClient) -> None:
    """GET /transactions returns list after upload."""
    response = client.get("/api/v1/transactions")
    assert response.status_code in (200, 404, 500)
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)

# After:
def test_transactions_after_upload(self, client: TestClient) -> None:
    """GET /transactions returns paginated dict after upload."""
    response = client.get("/api/v1/transactions")
    assert response.status_code in (200, 404, 500)
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)
        assert "transactions" in data
        assert "total" in data
```

**Verification:**
```bash
.venv/bin/python -m pytest backend/tests/integration/e2e/test_statement_upload_pipeline.py -v --timeout=60
```
All 5 tests in the file must pass.

---

### Task 5 — Verify `verify.sh quick` passes

After Tasks 1–4 are complete:
```bash
./scripts/verify.sh quick
```
Must exit 0.

---

### Task 6 — Final regression sweep

Run the full test suites to confirm zero regressions:
```bash
.venv/bin/python -m pytest backend/tests/unit backend/tests/contract backend/tests/architecture -q --timeout=120
cd frontend && npx vitest run --reporter=verbose __tests__/use-cashflow.test.ts __tests__/use-accounts.test.ts __tests__/api-contracts/ lib/__tests__/event-bus.test.ts lib/__tests__/event-bus-wiring.test.ts
```

Expected:
- Backend: 3196+ passed, 0 failed (same as M13 baseline, minus 5 pre-existing platform integration failures)
- Frontend: all non-platform-contract tests pass; platform contract test file still fails with ECONNREFUSED (documented as environment limitation)

---

## 5. Out of Scope (Explicitly Deferred)

| Issue | Reason |
|---|---|
| 5 backend platform integration test failures | `/platform/v1/*` runtime defects; require dedicated investigation outside remediation program scope |
| 18 frontend platform contract test failures | Require live backend at `127.0.0.1:8000`; environment-dependent, documented in BASELINE.md |
| `runtime/generated/*.jsonl` telemetry files dirtying on every verification run | `.gitignore` / artifact policy decision needed (BASELINE issue #1) |
| CWD-dependent `DATABASE_PATH` resolution | Operational clarity issue, not a data-integrity defect (BASELINE issue #5) |
| `npm run type-check` vs `npm run build` TypeScript divergence | Separate audit item (BASELINE issue #6) |
| `behaviour`/`behavior` spelling unification | Explicitly deferred per D5 |

---

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `platform.py` mypy import-not-found errors cannot be resolved by path fixes alone | Medium | Medium | May need `# type: ignore` with documentation, or removal of dead code |
| Fixing `test_transactions_after_upload` reveals other e2e tests with similar shape mismatches | Low | Low | Run full e2e suite after fix; address any cascading failures |
| `createMockResponse.ts` fix breaks a consumer that relies on `typeof MockResponse` | Low | Low | grep for consumers of `MOCK_RESPONSE` constant before changing |

---

## 7. Execution Order

1. **Task 2** (createMockResponse) — independent, 2-line fix
2. **Task 3** (use-platform-status) — independent, 1-line delete
3. **Task 4** (e2e test assertion) — independent, self-contained
4. **Task 1** (platform.py) — highest effort, may uncover dependencies on other fixes
5. **Task 5** (verify.sh quick) — depends on Task 1
6. **Task 6** (regression sweep) — depends on all above

Tasks 2–4 can run in parallel. Task 1 should run after verifying no shared dependencies.
