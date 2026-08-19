# M9-C35 Remediation Plan: Health Check Timeouts & Visual Baselines

**Created:** 2026-08-19  
**Current State:** CONDITIONAL (21/26 health checks pass, 5 timeouts)  
**Target:** CERTIFIED GREEN

---

## Problem Summary

### Issue 1: Health Check Timeouts (5 tests)
| Page | API Endpoint | Root Cause |
|------|--------------|------------|
| Cards | `/api/v1/credit-cards` | `retry: 3` with exponential backoff (up to 30s) |
| Investments | `/api/v1/investments` | Same retry pattern |
| Behavior | `/api/v1/behaviour/wellness-score` | Same retry pattern |
| Reconciliation | `/api/v1/reconciliation` | Same retry pattern |
| Cashflow | `/api/v1/cashflow` | Same retry pattern |

**Root Cause:** All capabilities use `retry: 3` with `retryDelay` that can exceed the 15s `networkidle` timeout. Playwright's `networkidle` waits for ALL network requests to settle, including retries.

### Issue 2: Visual Snapshot Mismatches (12 snapshots)
Existing snapshots in `frontend/tests/e2e/snapshots/` are stale from pre-C34 build. Need regeneration against current UI state.

### Issue 3: Missing Browsers
Firefox and WebKit not installed locally. CI installs them via action but local runs fail.

---

## Implementation Tasks

### Task 1: Fix Health Check Timeouts

**File:** `frontend/lib/capabilities/*.ts`

Change all capability files from:
```typescript
retry: 3,
retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
```
to:
```typescript
retry: 1,
retryDelay: 1000,
```

**Files to modify:**
- `frontend/lib/capabilities/use-accounts-capability.ts`
- `frontend/lib/capabilities/use-behaviour-capability.ts`
- `frontend/lib/capabilities/use-cashflow-capability.ts`
- `frontend/lib/capabilities/use-credit-cards-capability.ts`
- `frontend/lib/capabilities/use-forecast-capability.ts`
- `frontend/lib/capabilities/use-investments-capability.ts`
- `frontend/lib/capabilities/use-loans-capability.ts`
- `frontend/lib/capabilities/use-net-worth-capability.ts`
- `frontend/lib/capabilities/use-reconciliation-capability.ts`
- `frontend/lib/capabilities/use-transaction-capability.ts`

**Alternative:** Update health check test to use `waitUntil: 'load'` instead of `networkidle`:
```typescript
const response = await page.goto(
  `http://localhost:3000${pageConfig.url}`,
  { waitUntil: 'load', timeout: 30000 }
);
```

**Recommended:** Task 1a - Reduce retries (lower risk, faster failures)

---

### Task 2: Regenerate Visual Snapshots

**Command:**
```bash
cd frontend && npx playwright test tests/e2e/specs/visual-regression.spec.ts --update-snapshots --project=chromium
```

**Prerequisites:**
- Run backend seed data setup
- Ensure production server is running on port 3000

**Verification:**
- Check diff reports for any unexpected visual changes
- Confirm all 12 snapshots match expected output

---

### Task 3: Install Missing Browsers

**Command:**
```bash
cd frontend && npx playwright install firefox webkit
```

**CI Consideration:** The GitHub workflow already installs browsers via `.github/actions/setup-playwright`. No code change needed.

---

## Validation Steps

### After Task 1 (Retry Fix):
```bash
cd frontend && npx playwright test tests/e2e/specs/health-check.spec.ts --reporter=line --project=chromium
# Expected: 26/26 PASS
```

### After Task 2 (Snapshots):
```bash
cd frontend && npx playwright test tests/e2e/specs/visual-regression.spec.ts --reporter=line --project=chromium
# Expected: All PASS, no diffs
```

### Full Suite:
```bash
cd frontend && npx playwright test --reporter=line --project=chromium
# Expected: All tests PASS
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Reduced retry causes missed errors | Low | Low | Single retry still catches transient failures |
| Snapshot changes reveal bugs | Medium | Medium | Diff review catches regressions |
| Browser install fails | Low | Low | CI handles this; local dev optional |

---

## Rollout Plan

1. **Task 1** - Fix retries (5 min)
2. **Validate** - Run health checks (2 min)
3. **Task 2** - Regenerate snapshots (5 min)
4. **Validate** - Run visual tests (3 min)
5. **Commit** - Single commit with all changes

---

## Evidence Artifacts

- `runtime/generated/c36-remediation.json`
- `runtime/generated/c36-remediation.md`
- Updated `frontend/tests/e2e/snapshots/*.png`
