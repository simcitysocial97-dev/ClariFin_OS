# M9-C38 Final Certification Report
**Generated:** 2026-08-20T10:19:19.811619+00:00
**Baseline Provenance:** HEAD `ae00171454952e97319260ab2b9bcaf7436c6947` · TREE `e9074cb5dcf0ddafcf340b41a8f9c2c057db9d7c`

## Status Summary
- **Architecture Stabilization:** ✅ COMPLETE
- **Contract Chain Validation:** ✅ PASS
- **C30 Governance:** ✅ CERTIFIED
- **Mutation Restoration:** ✅ PROVEN (try/finally + atexit)
- **Known Defects:** 1 — see D1 below

## Verification Results Matrix
| Profile | Command | Status | Notes |
|---|---|---|---|
| api-contracts | `python runtime/verify.py api-contracts` | ✅ PASS | OpenAPI hash stable; consumer integrity OK |
| contract-governance (C30) | `python runtime/verify.py contract-governance` | ✅ CERTIFIED | 62 surfaces; 14 mutations; 0 missed |
| backend | `python runtime/verify.py backend` | ✅ PASS | lint/typecheck/build/test 1238 all pass |
| quality (quick) | `python runtime/verify.py quick` | ⚠️ FAIL | D1: loan-engine prepayment property test fails (0.107% overshoot) — legitimate backend bug, out of scope |
| golden | `python runtime/verify.py golden` | ✅ PASS | 28 capability integration tests |
| runtime | `python runtime/verify.py runtime` | ✅ PASS | Integrity scan + all runtime checks |
| playwright smoke | `npx playwright test health-check.spec.ts --project=chromium` | ✅ PASS | 27 tests; all pages 200; legacy redirects resolve; 16 backend API calls 200 OK; zero 404/5xx |

## Architecture Decisions Made
### 1. Unified Server Mode (C38.5)
- Removed `output: process.env.CI ? 'export' : undefined` from `next.config.ts`
- Canonical serving model: `next start` everywhere (local, CI, production)
- Rationale: app depends on middleware.ts legacy-route redirects which only run under server mode; no need for static export since API is absolute-URL CORS

### 2. Single API Gateway Boundary (C38.3/C38.4)
- Migrated `lib/api/client.ts` + 12 hooks through `apiFetch`/`apiFetchJson` from gateway
- Removed all scattered `NEXT_PUBLIC_API_URL` and `localhost:8000` literals from consumers
- Added `gateway-invariance.test.ts` (4 checks) that scans source to prevent future bypass

### 3. Deterministic Playwright Lifecycle (C38.6)
- `webServer.command = 'npm start'` for ALL envs (CI and local)
- `reuseExistingServer: false` to prevent accidental stale-server dependency
- Global-setup seeds backend fixtures and health-checks port 8000

### 4. Exception-Safe Mutation Restoration (C38.11)
- Hardened `FailureInjector.run_experiments` with `atexit.register(self._restore)` defense-in-depth
- Verified bounded 8-mutation control: all PASS/SKIP; post-run git status clean
- Restored `frontend/generated/openapi-current.json` from HEAD after prior SIGKILL corrupted it mid-mutation

## Success Criteria Map
The architecture targets are fully met. One orthogonal backend defect (D1) prevents the quality gate from being green.

**Architecture** ✅ — One clearly defined frontend serving architecture (server mode), one clearly defined backend ownership model (FastAPI), one canonical API gateway, no unexplained direct API consumers, retry ownership deterministic, routing ownership deterministic, server lifecycle ownership deterministic, browser readiness does not depend on networkidle.
**Contracts** ✅ — Backend remains contract authority; OpenAPI reproducible; generated types reproducible; Zod contracts align; representative semantic contracts verified end-to-end.
**Verification** ✅ — Contract gate PASS; C30 governance CERTIFIED; mutation restoration proven; certification arithmetic invariant PASS; evidence provenance bound to repository state.
**E2E** ⏭️ Partially validated in-session (chromium smoke 27/27 PASS). Full 1392-test matrix validated in CI via `.github/workflows/playwright.yml` shard model.
**CI Parity** ✅ — Every workflow command has identical local equivalent via `python runtime/verify.py <scope>`.
**Defect D1** ⚠️ Quality gate will fail until backend loan-engine bug resolved in separate M9 program.

## Known Defect — D1
- **Test:** `backend/tests/properties/loan_engine/test_prepayment_properties.py::test_apply_prepayment_at_month_reduce_emi_mode`
- **Assertion violated:** `new_total (447,909,460 paise) ≤ original_total (447,431,336) + tolerance (4,560)`
- **Overshoot:** 478,124 paise (~₹4,781, 0.107%)
- **Classification:** Legitimate application bug in reduce-EMI amortization recalculation tolerance — **not introduced by C38**. Reproducible with fresh Hypothesis DB (not seed-dependent). Loan engine source clean vs HEAD.
- **Impact:** `verify.py quick` (quality gate) fails until fixed.
- **Recommendation:** Engage financial-engineering domain expert for root cause analysis. Do NOT weaken tolerance (that would mask genuine undershoot).

## Git Provenance
- Baseline commit (preserved C37 state): `ae00171454952e97319260ab2b9bcaf7436c6947`
- C38 stabilization changes: staged and ready to commit
- Artifact provenance hashes computed for all key files

---
*M9-C38 Final Certification — generated 2026-08-20T10:19:19.811619+00:00.*