# Frontend / Backend / Runtime Integration Architecture
## M9-C38 Canonical Architecture Contract
**Date:** 2026-08-20  
**Provenance:** HEAD `ae001714` → C38 stabilization commit tree

---

## 1. Canonical Topology

```
Browser (Chromium/Firefox/WebKit/Mobile)
    │
    │  CORS (localhost:3000 ↔ localhost:8000)
    ▼
Next.js Server (`next start`)  ← port 3000
    │                          ← middleware.ts handles legacy route redirects
    │
    ├─ UI Pages (App Router)
    │
    └─ API Gateway (`lib/api/gateway.ts`)  ← ONE boundary
           │
           │  apiFetch / apiFetchJson
           │  URL resolution: API_BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || http://localhost:8000
           ▼
FastAPI Backend (`uvicorn src.api:app`)  ← port 8000
           │
           ▼
SQLite (`backend/data/finance.db`)
```

**Invariant:** Every frontend HTTP call to the backend traverses exactly one boundary — `lib/api/gateway.ts`. No scattered `fetch(…)` to `localhost:8000`, no ad-hoc `NEXT_PUBLIC_API_URL` literals outside the gateway.

---

## 2. Serving Model

| Environment     | Command                  | Mode         | Middleware | trailingSlash |
|-----------------|--------------------------|--------------|------------|---------------|
| Local dev       | `npm start`              | server mode  | ✅ runs    | ✅ handled    |
| CI build        | `npm run build`          | server-mode output (`.next`) | —  | — |
| CI test-playwright | `python runtime/verify.py playwright` → `npm start` | server mode | ✅ runs | ✅ handled |
| Production      | `npm start` on host      | server mode  | ✅ runs    | ✅ handled    |
| ~~Static export~~ | **NOT USED**           | —            | ❌ broken  | ❌ broken     |

**Decision rationale:** `output: 'export'` was removed (previous CI-only setting). The app depends on `middleware.ts` for legacy-route compatibility (C34), which only runs under server mode. Static export + `python3 -m http.server` caused divergent behaviour between local (server) and CI (static), and broke legacy deep links. Since the frontend never proxies API calls (absolute backend URLs via CORS), there is no reason to use static export.

---

## 3. API Gateway Ownership

**File:** `frontend/lib/api/gateway.ts`  
**Owner:** Single source of truth for all frontend → backend transport.

### What lives here:
- **URL resolution:** `API_BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'`
- **Transport:** `apiFetch(path, init?, baseUrl?)` → returns `Response`
- **JSON shortcut:** `apiFetchJson(path, init?, baseUrl?)` → returns parsed JSON
- **Error taxonomy:** `ApiError(status, path, body)` with `transient` flag (5xx/429 transient; all other 4xx permanent)
- **Retry policy:** `transientRetryPolicy(failureCount, error)` — used by React Query layer, **not** inside gateway itself (gateway is fire-and-forget; retry is caller responsibility)

### Gateway invariants:
1. **No raw `fetch(...)` to `/api/*` anywhere else.** Proven by `frontend/lib/__tests__/gateway-invariance.test.ts`.
2. **No local `API_BASE` const.** All consumers import `API_BACKEND_URL` from gateway.
3. **No hardcoded backend URLs in hooks/components.** Zero `localhost:8000` or `NEXT_PUBLIC_API_URL` literals in consumer code.
4. **Path is relative to backend root.** Gateway normalizes: `base + path`. Path must start with `/api/...`.

---

## 4. Retry Ownership

| Layer                      | Owns? | Details |
|----------------------------|-------|---------|
| React Query (`query-provider.tsx`) | ✅ **YES** | `retry: transientRetryPolicy` — only transient errors retried |
| Gateway (`apiFetch`)       | ❌ NO | Throws immediately on non-ok; no internal retry loop |
| Individual hooks           | ❌ NO | Pure async; errors propagate to React Query which retries |
| Capability hooks           | ✅ YES | Use `transientRetryPolicy` via React Query |
| Playwright network requests| ❌ NO | Direct `request.newContext()` for health checks; no retry |
| `python runtime/verify.py` | ❌ NO | CLI orchestration only |

**Invariant:** Maximum per-request retries = 3 (transient only). No stacking of retries between layers.

---

## 5. Routing Ownership

| Layer             | Owner                       | Mechanism |
|-------------------|-----------------------------|-----------|
| Public routes     | Next.js App Router          | `frontend/app/[route]/page.tsx` |
| Legacy redirects  | `frontend/middleware.ts`    | `ROUTE_REDIRECTS` map in `lib/config/navigation.ts` |
| API endpoints     | FastAPI routers (`backend/src/routers/`) | OpenAPI-spec'd |
| Trailing slash    | Next.js config (`trailingSlash: true`) | Automatic 308 redirect server-side |

**Middleware contract:** Matcher excludes `_next/static`, `_next/image`, `favicon.ico`, and `api` prefix. Strips trailing slash before lookup, then issues 308 redirect to canonical route. Works under `next start` (server mode) but **would not work under static export**.

---

## 6. Server Lifecycle Ownership

### Playwright webServer
- **Command:** `npm start` (= `next start`)
- **reuseExistingServer:** `false` — **never** reuse an accidental pre-existing server. Playwright owns the lifecycle end-to-end.
- **Base URL:** `http://localhost:3000`
- **Startup proof:** Playwright polls until `GET /` returns 2xx before any test begins.
- **Backend startup:** Handled by `tests/global-setup.ts`:
  - Starts FastAPI via `uvicorn src.api:app --host 0.0.0.0 --port 8000` (if port 8000 free)
  - Health-checks `GET /api/banks` until healthy
  - Seeds deterministic fixture data via inline SQL into `backend/data/finance.db`

### CI `run_playwright_tests.sh`
- Builds first: `npm run build` (server-mode output → `dist/.next/`)
- Runs Playwright with `webServer.command = 'npm start'`
- `PLAYWRIGHT_PROJECT` env selects matrix shard

### Local `npm run test:e2e`
- Same webServer (Playwright starts its own `next start`)
- global-setup seeds fixtures automatically

---

## 7. Browser Readiness Semantics

**Rejected patterns:** `networkidle`, arbitrary `waitForTimeout`, relying on port-up signals alone.

**Approved readiness contract:**
```ts
await page.waitForSelector('[data-testid="app-shell"]') // or equivalent DOM marker
// OR:
await expect(page.locator('text=/Dashboard|Accounts|Cards/')).toBeVisible()
```
Readiness is asserted by **application state** (mounted shell + required UI visible), not by network idleness. This was the root cause class of the C37 Playwright goto-timeout failures: static export produced no real server, so `next start` artifacts were missing and the browser couldn't resolve client-side routes.

---

## 8. Contract Authority Chain

```
Backend DTO (Pydantic)
    ↓ @app.get(...) FastAPI route
OpenAPI spec (generated at runtime from FastAPI)
    ↓ openapi-typescript
frontend/types/api-generated.ts (reproducible)
    ↓ Zod schema definitions
frontend/lib/schemas/*.ts (consumer-facing, authoritative for frontend consumers)
    ↓ API Gateway
lib/capabilities/use-*-capability.ts (React Query hooks, typed)
    ↓ ViewModel mapping
frontend/components/*/... (UI consumes typed objects)
```

**Rules:**
- Backend DTO is **authoritative**. Never relax a backend contract to satisfy a frontend expectation.
- If frontend consumer disagrees with backend, fix the consumer or file a contract change ticket against the DTO.
- `frontend/generated/api-schema.json` is a derived artifact (OpenAPI snapshot). It is **not** the authority; it is evidence of what the backend exposed at generation time.
- `openapi-current.json` in `frontend/generated/` is a cached snapshot used by the contract gate. Regeneration (via `backend/uvicorn` + `/openapi.json` fetch) happens only when explicitly requested by the user or CI.

---

## 9. Verification Runtime

| Command                            | Owner                              | Scope                                           |
|------------------------------------|------------------------------------|--------------------------------------------------|
| `python runtime/verify.py quick`   | Quality gate                       | lint, typecheck, architecture scan, meta checks  |
| `python runtime/verify.py backend` | Backend + frontend unit test       | backend pytest + frontend vitest + build        |
| `python runtime/verify.py frontend`| Frontend verify                   | lint, typecheck, build, vitest (1238 tests)     |
| `python runtime/verify.py api-contracts` | API contract gate             | structural freshness, types regen, consumer integrity |
| `python runtime/verify.py contract-governance` | C30 governance           | mutation attack matrix (14 experiments)         |
| `python runtime/verify.py golden`  | Golden tests                       | 28 capability integration tests                 |
| `python runtime/verify.py playwright` | E2E Playwright suite            | 1392 tests × 6 projects (sharded per CI job)    |
| `python runtime/verify.py mutation`| Selective backend mutation testing | `run_mutation_selective.sh` — CI-only (90 min)  |
| `python runtime/verify.py runtime` | Full runtime checks                | 3-phase integration scan                        |

**CI parity rule (C38.10):** Every workflow command has an identical local equivalent. No engineering logic lives in YAML; all logic is in `runtime/verify.py` profiles + their supporting modules.

---

## 10. Known Defects (Post-C38 Audit)

| ID | Component                          | Symptom                                                                   | Root Cause                                      | Classification           |
|----|------------------------------------|---------------------------------------------------------------------------|-------------------------------------------------|--------------------------|
| D1 | `loan_engine` property test        | `test_apply_prepayment_at_month_reduce_emi_mode` fails (0.107% overshoot) | Financial invariant in reduce-EMI reprocessing tolerance is violated for extreme parameters | **LEGITIMATE APPLICATION BUG** (backend) |

- **Not introduced by C38.** Verified unmodified by C38 diff. Also fails with a fresh Hypothesis DB (not seed-dependent).
- **Not patched in this stabilization.** Fixing it requires deep financial-engineering analysis of the amortization recalculator and would need a separate M9 program. Weakening the tolerance to silence it would be a workaround (forbidden by §19 of the directive).
- **CI impact:** `verify.py quick` (quality gate) will fail until this is resolved. The defect is tracked in its own file `docs/architecture/knwon-defects-d1-loan-engine-prepayment.md`.

---

## 11. Governance

This document is the **architectural contract** for the frontend/backend/runtime integration. Any future change that violates the invariants below must be rejected or must include a formal exception with documented justification.

**Immutable invariants:**
1. All frontend HTTP calls to the backend traverse `lib/api/gateway.ts` — no bypass allowed.
2. The serving model is always `next start` — never static export.
3. `reuseExistingServer` in Playwright is always `false` — never accidentally reuse a stale server.
4. `transientRetryPolicy` lives only in React Query — the gateway does NOT retry internally.
5. `middleware.ts` is the single owner of legacy-route redirects — never duplicate redirect logic elsewhere.

Violations of these invariants are caught by:
- `frontend/lib/__tests__/gateway-invariance.test.ts` (source-scan invariant)
- `runtime/foundation/verification/api_contracts/gate.py` (contract freshness)
- Playwright webServer config (serve-model enforcement)
- Code review discipline enforced by this document

---

*Document generated as part of M9-C38 stabilization. Canonical reference for all future integration work.*
