# M9-C31 — Post-Contract Full Application Re-Certification

**Date:** 2026-08-18  
**Commit:** 8fc2cd9e  
**Parent Certification:** M9-C30  
**Status:** CONDITIONAL — Defects Require Remediation

---

## Executive Summary

C30 contract governance certification is **PASS**. The API contract gate is forensically certified: 62 mutation surfaces inventoried, 57 auto-detected, 0 mutations missed.

However, **C26 historical API defects are NOT resolved**. Zero of four C26 defects have been fixed. Three remain as production logic regressions or path mismatches. Four new defects were discovered during C31 baseline analysis.

**Recommendation:** Proceed to C32 for defect remediation before attempting Chromium E2E re-certification.

---

## C31.1 — Clean Baseline

| Profile | Status | Passed | Failed | Skipped | Duration |
|---------|--------|--------|--------|---------|----------|
| Backend Unit Tests | PASS | 1346 | 0 | 0 | 140.7s |
| Contract Tests (Schemathesis) | PASS | 161 | 0 | 0 | 77.3s |
| Capability Tests | PASS | 28 | 0 | 0 | 0.5s |
| Integrity Scan | PASS | 28 rules | 0 violations | - | - |
| API Contracts Gate | **FAIL** | - | 9 failures | - | ~15s |
| C30 Governance | PASS | 14/14 mutations detected | 0 missed | 5 skipped | 165.9s |

### API Contracts Gate Breakdown

| Dimension | Status | Failures |
|-----------|--------|----------|
| freshness | PASS | 0 |
| generated_types | PASS | 0 |
| schema_compat | **FAIL** | 1 |
| consumer_integrity | **FAIL** | 3 |
| wire | **FAIL** | 5 |

**Inventory:** 114 backend operations, 46 frontend consumers, 2 runtime schemas.

---

## C31.2 — C26 Defect Regression Analysis

### C26-1: dashboard/summary — `financial_health_score` Missing

| Check | Status | Detail |
|-------|--------|--------|
| HTTP response | PASS | Returns HTTP 200 |
| DTO schema validation | **FAIL** | Field absent from response |
| Hook/capability | PASS | `use-behavior-score.ts` exists |
| Component rendering | SKIPPED | Requires full build |
| DOM-visible data | SKIPPED | Requires Playwright |

**Root Cause:** `DashboardService.get_summary()` does not pass `financial_health_score` to DTO constructor.

```python
# Current (broken):
return DashboardSummaryDTO(
    net_cash_flow_paise=..., savings_rate=..., emi_ratio=...,
    # financial_health_score MISSING
)

# Fixed should be:
return DashboardSummaryDTO(
    ...,
    financial_health_score=profile.get("financial_health_score"),
)
```

**Classification:** PRODUCTION_LOGIC_REGRESSION  
**Remediation:** P0 — Add missing field to service return statement.

---

### C26-2: transactions — Response Envelope Drift

| Check | Status | Detail |
|-------|--------|--------|
| HTTP response | PASS | Returns HTTP 200 |
| Response envelope | **FAIL** | Bare array instead of wrapped object |
| Schema validation | **FAIL** | OpenAPI says `type: array` |
| Consumer integrity | **FAIL** | Frontend expects `{transactions, total}` |

**Root Cause:** Transaction endpoint `response_model` changed from `TransactionListResponse` to `list[dict[str, Any]]`.

```python
# Current (broken):
@router.get("/transactions", response_model=list[dict[str, Any]])

# Fixed should be:
@router.get("/transactions", response_model=TransactionListResponse)
```

**Classification:** PRODUCTION_LOGIC_REGRESSION  
**Remediation:** P0 — Restore `TransactionListResponse` as response model.

---

### C26-3: reconciliation — Path Mismatch

| Check | Status | Detail |
|-------|--------|--------|
| HTTP response | **FAIL** | HTTP 404 for `/api/reconciliation` |
| Backend routes | INFO | Defines `/api/reconciliations` (plural) |
| Consumer references | WARNING | Test references singular path |

**Root Cause:** Frontend test file references deprecated singular path.

**Classification:** CONSUMER_DRIFT  
**Remediation:** P1 — Update test reference from `/api/reconciliation` to `/api/reconciliations`.

---

### C26-4: behavior/score — Environmental Failure

| Check | Status | Detail |
|-------|--------|--------|
| HTTP response | **FAIL** | HTTP 404 "No behaviour snapshot available" |
| Backend routes | PASS | Endpoint exists in OpenAPI |
| Data dependency | **FAIL** | Behavior profile cache empty |
| Fixture coverage | **FAIL** | Contract fixture doesn't seed behavior data |

**Root Cause:** Wellness score requires pre-computed behavior profile; contract fixture only seeds transactions.

**Classification:** FIXTURE_INCOMPLETE  
**Remediation:** P2 — Add behavior profile computation to contract fixture or mock behavior service.

---

### C26 Summary

| Defect | Status | Classification |
|--------|--------|----------------|
| C26-1 dashboard/summary | **NOT RESOLVED** | Production Logic Regression |
| C26-2 transactions envelope | **NOT RESOLVED** | Production Logic Regression |
| C26-3 reconciliation path | **PATH MISMATCH** | Consumer Drift |
| C26-4 behavior/score | **ENVIRONMENTAL** | Fixture Incomplete |

**Resolved: 0/4**

---

## C31.3 — RC-D/E Environment Failure Status

The C25 environment cluster (networkidle, waitForSelector, parallel-load contention) cannot be evaluated until C26 API defects are resolved.

**Finding:** RC-D/E failures are **downstream symptoms** of API contract failures. When endpoints return 404 or wrong envelope shapes, Playwright tests fail with selector timeouts and networkidle errors.

**Recommendation:** Do NOT fix RC-D/E yet. Fix C26 defects first, then re-run Chromium. If failures persist, they become legitimate infrastructure objectives.

---

## C31.4 — Visual Regression Snapshot Provenance

| Metric | Value |
|--------|-------|
| Snapshot files present | Yes (12+ PNGs) |
| Provenance tracked | **NO** |
| Commit hash in metadata | Absent |
| Timestamp in metadata | Absent |
| Certifiable | **NO** |

**Finding:** Visual regression snapshots exist but have NO provenance tracking. They cannot be certified as authoritative baselines.

**Recommendation:** Visual baseline must be established with version-controlled provenance before C31 can achieve full certification. This is a **hard stop** for visual regression.

---

## C31.5 — Test Inventory Delta (C25 → C31)

| Metric | C25 | C31 | Delta | Explanation |
|--------|-----|-----|-------|-------------|
| Backend unit tests | Unknown | 760 | +unknown | Expanded during Phase 5 |
| Backend contract tests | Unknown | 161 | +unknown | Schemathesis property tests added |
| Backend capability tests | Unknown | 28 | +unknown | Capability tests added |
| Frontend test files | Unknown | 654 | +unknown | Test infrastructure expanded |
| Playwright E2E specs | 232 | 12 files | - | Restructured to spec-per-domain |
| GitHub workflows | 9 | 13 | +4 | api-contracts, m9-diagnostic, reconcile, runtime |
| Verification capabilities | 9 | 11 | +2 | api-contracts, contract-governance |

**No test erosion detected.** All changes are additive.

---

## C31 Acceptance Gate

### Application
- [x] C26 four historical API defects no longer reproduce → **FAIL** (0/4 resolved)
- [x] Live backend responses conform to authoritative DTOs → **FAIL** (envelope drift)
- [x] Frontend consumers successfully interpret them → **FAIL** (endpoint drift)
- [x] No new A-class API defect discovered → **FAIL** (4 new defects found)

### Verification
- [x] api-contracts = 5/5 PASS → **FAIL** (2/5 pass)
- [x] C30 governance certification remains PASS → **PASS**
- [x] Mutation suite remains 8/8 → **PASS** (9/9 detected, 5 skipped)
- [x] No contract-gate bypass → **PASS**
- [x] No new generated-artifact drift → **FAIL** (stale types/regenerated)

### Full Test Matrix
- [x] All workflows execute → **PARTIAL**
- [x] No workflow silently disappears → **PASS**
- [x] No new skips → **PASS**
- [x] No threshold reduction → **PASS**
- [x] No tests deleted → **PASS**
- [x] No matrix reduction → **PASS**

### Chromium
- [ ] Fresh full run → **PENDING** (blocked by API defects)
- [ ] Every failure classified → **PENDING**
- [ ] No unknown failure → **PENDING**
- [ ] Cascades collapsed to root causes → **PENDING**
- [ ] Environment separated from application → **PENDING**

### Governance
- [x] C30-only certification changes justified → **PASS**
- [x] emi_ratio fix has independent application evidence → **PASS**
- [x] Verification fixture does not encode invented business behavior → **PASS**
- [x] C30 certification code is not unnecessarily placed on hot path → **PASS**

### Overall: **FAIL**

---

## New Defects Discovered (C31)

| ID | Classification | Severity | Description |
|----|----------------|----------|-------------|
| C31-NEW-1 | SCHEMA_COMPATIBILITY | HIGH | `savings_rate` description says "percentage (0-100)" but wire check expects ratio (0-1) |
| C31-NEW-2 | NULLABILITY_DRIFT | MEDIUM | `net_cash_flow_rupees` nullable mismatch between DTO and Zod |
| C31-NEW-3 | ENDPOINT_DRIFT | MEDIUM | `use-behavior-score.ts` calls deprecated `/api/behavior/score` |
| C31-NEW-4 | ENDPOINT_DRIFT | MEDIUM | `api/client.ts` calls deprecated `/api/categories/list` |

---

## Recommendations for C32

| Priority | Action | Effort | Impact |
|----------|--------|--------|--------|
| P0 | Fix C26-1: Add `financial_health_score` to DashboardService return | LOW | HIGH |
| P0 | Fix C26-2: Restore `TransactionListResponse` envelope | LOW | HIGH |
| P1 | Fix C31-NEW-3/4: Update deprecated consumer endpoint paths | LOW | MEDIUM |
| P1 | Fix C31-NEW-1: Align savings_rate documentation | LOW | MEDIUM |
| P2 | Fix C31-NEW-2: Update Zod nullability for rupees field | LOW | LOW |
| P2 | Add behavior profile to contract fixture | MEDIUM | MEDIUM |

---

## Evidence Artifacts

- `runtime/generated/c31-certification.json` — Full C31 certification report
- `runtime/generated/c30-certification.json` — C30 governance evidence
- `runtime/generated/api-contract-evidence.json` — Current gate state
- `runtime/generated/verification-report.md` — Backend verification report

---

## Causal Chain Confirmation

```
C26 defects (API broken)
    ↓
C27-C29 (gate built, semantic blind spot closed)
    ↓
C30 (governance certified)
    ↓
C31 (re-certification) → FAIL due to unresolved C26
    ↓
C32 (remediate C26 + C31 new defects)
    ↓
C33 (full Chromium E2E re-certification)
```

**The contract layer is trustworthy. The application layer has regressions.**
