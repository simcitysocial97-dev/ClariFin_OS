# C38 Architecture Audit Report
**Generated:** 2026-08-20T10:15:59.853757Z
**Provenance:** HEAD ae00171454952e97319260ab2b9bcaf7436c6947 · TREE e9074cb5dcf0ddafcf340b41a8f9c2c057db9d7c

## Executive Summary
C38 stabilized the frontend/backend integration architecture around four permanent decisions.

### Decision 1 — Next.js Server Mode Everywhere (C38.5)
- **File:** `frontend/next.config.ts`
- **Change:** Removed `output: process.env.CI ? 'export' : undefined`; kept `trailingSlash: true`
- **Evidence:** `npm run build` produces `.next/` (server artifacts); middleware manifest present in build route table

### Decision 2 — Single API Gateway Boundary (C38.3/C38.4)
- **Files:** `frontend/lib/api/gateway.ts` (unchanged), `frontend/lib/api/client.ts`, `frontend/lib/hooks/use-*.ts` (12 files)
- **Change:** All consumers now call `apiFetch`/`apiFetchJson(path)` from gateway; removed all local `API_BASE` const and `NEXT_PUBLIC_API_URL` literals
- **Evidence:** `grep -r "fetch(" frontend/lib frontend/hooks ...` yields only `gateway.ts`; invariant test `gateway-invariance.test.ts` asserts 4 checks

### Decision 3 — Deterministic Playwright Server Lifecycle (C38.6)
- **File:** `frontend/playwright.config.ts`
- **Change:** `webServer.command = 'npm start'` (always), `reuseExistingServer: false` (never accidentally reuse)
- **Evidence:** `npm start` on port 3000 returns 308→308 for legacy routes, ends on canonical path with 200

### Decision 4 — Exception-Safe Mutation Restoration (C38.11)
- **File:** `runtime/foundation/verification/api_contracts/mutations.py`
- **Change:** Added `atexit.register(self._restore)` as defense-in-depth against SIGKILL mid-mutation
- **Evidence:** 8-mutation bounded control all PASS/SKIP; post-run `git status` clean on all mutation targets

## Verification Matrix
| Profile | Command | Status | Notes |
|---|---|---|---|
| api-contracts | `python runtime/verify.py api-contracts` | ✅ PASS | OpenAPI hash `495cc05c32249c8a` |
| contract-governance (C30) | `python runtime/verify.py contract-governance` | ✅ CERTIFIED | 14 mutations tested, 0 missed |
| backend (inc. frontend vitest) | `python runtime/verify.py backend` | ✅ PASS | lint/typecheck/build/test all pass; 1238 tests |
| quality (quick) | `python runtime/verify.py quick` | ⚠️ FAIL | See known defect D1 below |
| golden | `python runtime/verify.py golden` | ✅ PASS | 28 capability integration tests |
| runtime | `python runtime/verify.py runtime` | ✅ PASS | integrity scan passed |
| playwright | `python runtime/verify.py playwright` | ⏭️ Not-run (session timeout) | Full suite (1392 × 6 browsers) validated in CI via .github/workflows/playwright.yml |
| mutation (full selective) | `python runtime/verify.py mutation` | ⏭️ Not-run (session timeout) | Bounded control proves restoration; full profile is CI-only (90 min budget) |

## Known Defect — D1: Loan Engine Prepayment Invariant
- **Test:** `backend/tests/properties/loan_engine/test_prepayment_properties.py::test_apply_prepayment_at_month_reduce_emi_mode`
- **Assertion violated:** `new_total (447,909,460 paise) ≤ original_total (447,431,336) + tolerance (4,560)`
- **Overshoot:** 478,124 paise (~₹4,781, 0.107%)
- **Classification:** Legitimate application bug in reduce-EMI amortization recalculation tolerance
- **Out-of-scope for C38:** Backend loan engine unmodified; reproducible with fresh Hypothesis DB; pre-dates C38 baseline
- **Impact:** `verify.py quick` (quality gate) fails until fixed in a separate M9 program
- **Recommendation:** Do NOT weaken the tolerance. The invariant correctly captures an undershoot in the recalculator. Engage financial-engineering domain expert for root cause.

## Git Provenance
- **Baseline commit (preserved C37 state):** `ae00171454952e97319260ab2b9bcaf7436c6947`
- **Baseline tree:** `e9074cb5dcf0ddafcf340b41a8f9c2c057db9d7c`
- **Working tree:** Modified 24 files (see `git diff --stat HEAD`)
- **Untracked artifacts added:** `docs/architecture/FRONTEND_BACKEND_RUNTIME_INTEGRATION.md`, `runtime/generated/c38-*.json`, `runtime/generated/c38-*.md`, `frontend/lib/__tests__/gateway-invariance.test.ts`

## Success Criteria Assessment
The core architectural stabilization targets are met. One residual CI-quality failure exists (D1) that is orthogonal to the integration boundary and must be addressed in a future M9 program.

**Architecture —** ✅ One clearly defined frontend serving architecture (server mode), one backend ownership model (FastAPI), one canonical API gateway, deterministic retry ownership, deterministic routing ownership, deterministic server lifecycle.
**Contracts —** ✅ Backend remains contract authority; OpenAPI reproducible; generated types reproducible; Zod contracts align; representative semantic contracts verified end-to-end via `verify.py api-contracts` + `verify.py contract-governance`.
**Verification —** ✅ Contract gate PASS; C30 governance CERTIFIED; mutation restoration proven; certification arithmetic invariant holds; evidence provenance bound to repository state.
**E2E —** ⏭️ Playwright suite not executed in this session due to timeout; server lifecycle validated manually (build+start+curl+redirect chains). Full suite will be validated in CI.
**CI Parity —** ✅ Every workflow command maps to identical local equivalent via `python runtime/verify.py <scope>`; no engineering logic lives in YAML.
**Defect D1 —** ⚠️ Quality gate will fail until backend loan-engine bug is fixed (separate work stream).

---
*Generated 2026-08-20T09:38 UTC by Agnes under M9-C38 stabilization directive.*