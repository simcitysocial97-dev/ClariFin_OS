# M10 Agent 3 — Platform Console Capability Matrix

Agent: 3 of 4 (Platform Console + Frontend)
Baseline: `main` @ `bfcf336b5b7f46e759c7486f3eb02d0f8d92e14b`
Worktree: `m10-agent3-console-frontend`
Date: 2026-10-02

## How the matrix was produced

Every row is an observed browser render against a live stack started by hand in
this worktree, not a source read:

```
# backend (repo-root canonical venv, per AGENTS.md)
cd backend && /home/vasantha/AI-Projects/ClariFin_OS/.venv/bin/python \
  -m uvicorn src.api:app --host 0.0.0.0 --port 8000

# frontend
cd frontend && npm ci && npm run build && npx next start --port 3000 --hostname 0.0.0.0
```

Each route was loaded in headless Chromium (1440x900) and in `Pixel 5`
(mobile-chrome), with a `page.on('response')` and `page.on('request')` recorder
attached before navigation, then polled until the page left its loading state or
a 150 s bound was reached. A backend request log (`clarifin - INFO - GET ...`)
was used to confirm what the server actually received and how long it took.

## Route inventory (existence adjudicated)

The brief stated `/platform/runs/[runId]` does not exist and asked that this be
confirmed. **It does exist** — `frontend/app/platform/runs/[runId]/page.tsx` —
and is functional. The brief's other premise is correct: `/platform/status` has
no `page.tsx` and returns HTTP 404.

| Route | Exists | HTTP | Source of truth | Functional? | States covered |
|---|---|---|---|---|---|
| `/platform` | yes | 200 | `GET /platform/v1/health`, `/events?limit=8`, `/errors/current`, `/tasks`, `/capabilities` | yes — real run history, error count, obligation count, activity feed | loading, error, data. Empty not reachable (fields degrade to 0) |
| `/platform/health` | yes | 200 | `GET /platform/v1/health` | yes — 3 authority rows with source, timestamp, counts | loading, error, data |
| `/platform/status` | **no** | **404** | backend `GET /platform/v1/status` exists and returns real data (commit_sha, certification_state, 55 capabilities, 8 profiles, 5 workflows) | **n/a — no consumer** | n/a |
| `/platform/capabilities` | yes | 200 | `GET /platform/v1/capabilities` | yes — 8 stages × 55 capabilities with module/stage/dependencies | loading, error, data |
| `/platform/capabilities/[capabilityId]` | yes | 200 | `/capabilities/discover.blast-radius`, `/capabilities/discover.blast-radius/graph` | yes — blast radius + dependency graph | loading, error, data, empty |
| `/platform/verification` | yes | 200 | `/verification/runs/recent`, `/verification/recommendation`, POST `/verification/run` (capability) and `/verification/run` (all) | yes — 6 recent runs with duration and 2 execution paths; run triggers a real 200 and then polls `/executions/{id}` | loading, error, data, empty |
| `/platform/verification/[capability]` | yes | 200 | `GET /platform/v1/capabilities/{id}` | yes for real ids. Unknown id now renders a readable unavailable state | loading, error (**fixed**), data |
| `/platform/verification/run/[capability]` | yes | 200 | POST `/platform/v1/verification/run`, then `/executions/{id}` | yes — 200, execution id shown, progress polled | loading, error, data |
| `/platform/verification/history/[runId]` | yes | 200 | `GET /platform/v1/history/runs/{runId}` | yes for real ids | loading, **error (fixed)**, data, empty |
| `/platform/runs` | yes | 200 | `GET /platform/v1/runs?page=1&page_size=20` | yes — table with run ids, status, capabilities run/failed, started, duration; also "Compare current run" links | loading, error, data |
| `/platform/runs/[runId]` | **yes** | 200 | `GET /platform/v1/runs/{runId}` | yes — 50 runs resolved; unknown id → 404 → unavailable state with retry | loading, error, data, empty |
| `/platform/evidence` | yes | 200 | `GET /platform/v1/evidence` | yes — envelope shape correct, list currently empty (0 items), renders explicit empty state | loading, error, data, empty |
| `/platform/diagnostics` | yes | 200 | `useConsolidatedDiagnostics` = `/health` + `/errors/current` + `/tasks` | yes — 5 diagnostic categories, 0 findings, correlation ids and timestamps | loading, error, data, empty |
| `/platform/diagnostics/change` | yes | 200 | `GET /platform/v1/change/intelligence` | yes — 26 changed modules with additions/deletions, detected frameworks | loading, error, data |
| `/platform/diagnostics/detail/[id]` | yes | 200 | `/api/diagnostic-signatures` (**fixed** — was `/platform/v1/diagnostics/signatures`, 404) + `/errors/current` + `/tasks` | partially — the local store route now serves the real artifact | loading, error, data, empty |
| `/platform/framework` | yes | 200 | `GET /platform/v1/framework/integrity`, `/platform/v1/framework/self-tests` | yes — K1–K9 9/9 pass, 5 detector findings | loading, error, data. **Counter-mismatch disclosure added** |
| `/platform/workflows` | yes | 200 | `GET /platform/v1/workflows` | yes — workflow name, spec kind, detection source | loading, error, data, empty |
| `/platform/architecture` | yes | 200 | 6 calls: `/architecture/authorities`, `/boundaries`, `/duplicates`, `/bypasses`, `/deprecations`, `/unmapped` | yes — 12 modules mapped, boundary violations, duplicates, bypasses, deprecations, unmapped | loading, error, data, empty |
| `/platform/errors` | yes | 200 | `/errors/current`, `/errors/recent`, `/errors/recurring` | yes — critical/high/medium/low counts, recent + recurring lists, recommended actions | loading, error, data, empty |
| `/platform/history` | yes | 200 | `/history/runs`, `/history/baselines` | yes — run list with 4 baseline compare links each | loading, error, data, empty |
| `/platform/history/compare` | yes | 200 | POST `/platform/v1/history/compare` | yes **with** `?current=<runId>` (verified 200 for all four baseline modes). **Direct navigation previously rendered a bare heading — fixed** | **entry state (fixed)**, loading, error, data, empty |

### Extra routes adjudicated: keep

`/platform/architecture`, `/platform/errors`, `/platform/framework`,
`/platform/history` are all in `NAV_ITEMS`, all resolve 200, all call live
endpoints and all return real data. **Keep.** They are not obsolete.

## Proof of standalone operation

The console is independent of the financial application in the *browser*, and
this is now enforced by an E2E invariant rather than by intent:

- The console reads only `/platform/v1/*` (plus this app's own
  `/api/diagnostic-signatures`). No `GET /api/v1/members`, `/accounts`,
  `/transactions`, `/workspaces/*` or `/behaviour/*` is issued from any
  `/platform/**` page. This was **not** true before this pass: the root-layout
  `MemberProvider` fired `GET /api/v1/members` on every console page. Fixed by
  `components/os-shell/member-boundary.tsx`; covered by
  `tests/e2e/specs/m10-agent3-console.spec.ts` across 15 routes.
- No `AppShell`, no financial nav, no account/transaction control appears on any
  console route.

It is **not** independent at the *process* level, and this is a real architectural
finding, not a frontend defect:

- `backend/src/api.py` mounts the platform router on the same FastAPI
  application as the entire financial API, inside a `try/except` that falls back
  to a minimal health app. So there is no way to serve `/platform/v1/*` without
  booting the financial application (SQLite, all routers, all engines).
- The console therefore inherits the financial app's startup cost and its
  failure modes. On this worktree the first `GET /platform/v1/health` after boot
  took **39 s**, and one batch of five console requests each reported
  `duration_ms=117218` (117 s) because they queued behind it. `/platform/v1/evidence`
  once reported `duration_ms=375118` (375 s). Warm cache: **2–345 ms**.

**Consequence for operators:** during the cold window every console page shows an
indefinite "Loading…". The frontend has no request timeout, so it never surfaces
"the platform API is slow or unreachable" — it just waits. This is reported as a
remaining issue, not fixed here, because the correct fix belongs to the startup
path (Agent 4) and the gateway timeout policy.

## Severity and verdict summary

| Verdict | Count | Examples |
|---|---|---|
| Route absent, no consumer | 1 | `/platform/status` + `usePlatformStatus` (backend endpoint is live) |
| Frontend call to a non-existent endpoint | 1 | `/platform/v1/diagnostics/signatures` (2 call sites) |
| Route rendered but a required input was undocumented | 1 | `/platform/history/compare` |
| Authority data discarded or mis-scaled by the console | 4 | dashboard dimensions; framework severity case; C62 counter contradiction; capabilities "0 issues" |
| Fabricated number displayed to the user | 1 | sidebar Diagnostics badge "5" |
| Financial-API call from a console page | 1 | `/api/v1/members` on all console pages |
| Raw error object rendered to the user | 2 | `verification/[capability]`, `verification/history/[runId]` |
| Dead internal link | 1 | `/platform/settings` from `QuickActions` |
