# C38 Runtime Topology
**Generated:** 2026-08-20T10:17:13.642610+00:00
**Provenance:** HEAD `ae00171454952e97319260ab2b9bcaf7436c6947` · TREE `e9074cb5dcf0ddafcf340b41a8f9c2c057db9d7c`

## Canonical Topology Diagram
```
Browser
   │
   ▼
Next.js Server (port 3000, server mode)
   │  middleware.ts → legacy-route 308 redirects
   │
   ├─ UI Pages (App Router)
   │
   └─ API Gateway (`lib/api/gateway.ts`) ← ONE boundary
          │ apiFetch / apiFetchJson
          │ URL: API_BACKEND_URL || http://localhost:8000
          ▼
FastAPI Backend (port 8000)
          │
          ▼
SQLite (`backend/data/finance.db`)
```

### Key Decisions (C38 stabilization)
1. **Single serving model:** `next start` server mode everywhere. Static export removed from CI because middleware (legacy-route redirects) and SPA routing do NOT work under static hosting. The frontend never needs Next.js to proxy API traffic (absolute CORS URLs used instead), so server mode is sufficient for all environments including production.
2. **Single API gateway:** All frontend HTTP to the backend traverses `lib/api/gateway.ts`. Raw `fetch(` calls to `/api/*` are forbidden outside gateway (enforced by `gateway-invariance.test.ts`). `NEXT_PUBLIC_API_URL` and `localhost:8000` literals are forbidden in consumer code.
3. **Deterministic Playwright lifecycle:** `webServer.command = 'npm start'` for ALL environments. `reuseExistingServer: false` ensures no accidental stale-server dependency. Global-setup seeds backend fixtures.
4. **Exception-safe mutation restoration:** `FailureInjector.run_experiments` uses `try/finally` + `atexit.register(self._restore)` defense-in-depth against SIGKILL mid-experiment.

### Owner Map
| Responsibility                  | Authoritative owner                       | File                                    |
|---------------------------------|-------------------------------------------|-----------------------------------------|
| Backend API                     | FastAPI                                   | `backend/src/api.py`                    |
| API URL resolution              | API gateway                               | `frontend/lib/api/gateway.ts`           |
| API retry semantics             | React Query layer                         | `frontend/components/query-provider.tsx`|
| Frontend routing                | Next.js App Router                        | `frontend/app/**`                       |
| Legacy route compatibility      | Middleware                                | `frontend/middleware.ts`                |
| Browser readiness               | Application DOM state (not networkidle)  | Test assertions per page               |
| E2E server lifecycle            | Playwright webServer + global-setup       | `frontend/playwright.config.ts`, `tests/global-setup.ts` |
| Contract authority              | Backend DTO/OpenAPI                       | `backend/src/core/dtos/`               |
| Generated types                 | OpenAPI generation                        | `frontend/types/api-generated.ts`       |
| Semantic validation             | Zod + contract gate                       | `frontend/lib/schemas/*.ts` + `gate.py` |
| Verification orchestration      | `runtime/verify.py`                       | `runtime/verify.py`                     |
| CI execution                    | GitHub Actions                            | `.github/workflows/*.yml`              |
| Evidence                        | `runtime/generated/`                      | All *.json/*.md/*.ljson artifacts       |

### Verification Command Matrix (local ↔ CI parity)
| Workflow                 | Local command                                      | CI command                          |
|--------------------------|----------------------------------------------------|-------------------------------------|
| frontend-verify          | `python runtime/verify.py frontend`                | same                                |
| backend-verify           | `python runtime/verify.py backend`                 | same                                |
| api-contracts            | `python runtime/verify.py api-contracts`           | same                                |
| quality                  | `python runtime/verify.py quick`                   | same                                |
| golden                   | `python runtime/verify.py golden`                  | same                                |
| mutation                 | `python runtime/verify.py mutation` (timeout cap)  | same + 90min budget                 |
| playwright               | `python runtime/verify.py playwright`              | same + shard matrix                 |
| verification-runtime     | `python runtime/verify.py runtime`                 | same                                |

### Artifact Provenance Hashes
```
HEAD   = ae00171454952e97319260ab2b9bcaf7436c6947
TREE   = e9074cb5dcf0ddafcf340b41a8f9c2c057db9d7c
openapi  = 495cc05c32249c8a
gateway  = 50f2274e03f75877
nextconfig= c4b12d5680f07995
pw.config= acf5e8144b6a35f3
middleware= 0626bcd82c217002
client   = 844e38ab7ea0618d
types    = b47d7e386b6dbd61
mutations= 11834f7cef8c4001
invariant= f74d387fd8554e14
```

---
*M9-C38 Runtime Topology — canonical reference.*