# M10 Agent 3 — Remaining Concrete Product Issues (prioritised)

Agent: 3 of 4 · Baseline `bfcf336` · 2026-10-02

Every item is specific and reproducible. Each carries the reproduction, the
owner boundary, and what was deliberately *not* done and why — so a later pass
does not repeat the investigation or mistake a deliberate omission for an
oversight.

Severity key: **P0** fabricated or actively wrong money/health information shown
to a user · **P1** feature surface that does not work · **P2** inconsistency or
missing polish with a real cost · **P3** cleanup.

---

## P0

### 1. `/forecast` renders fabricated cashflow projections, with duplicate months

**Reproduction.** Start backend + frontend, open `/forecast`, read the Cashflow
Projection table. Every row shows `2026-11 … 2027-03` with identical
₹1,00,000.00 income / ₹60,000.00 expenses / ₹40,000.00 net, and the month keys
**repeat** (`2026-12` twice, `2027-03` twice).

**Evidence.** `GET /api/v1/forecast` returns
`summary`, `net_worth_projections` (with distinct `date` values), `scenarios`,
`insights` — and **no cashflow projection series at all**. The figures on screen
therefore originate in the frontend from constants.

**Impact.** Fabricated future income and expense presented to a user as a
projection, in the same table as real net-worth projections. This is the single
most serious finding in this pass.

**Owner.** Backend: `/api/v1/forecast` should return the cashflow projection. The
frontend should not synthesise one. Not fixed here — writing a projection engine
in the frontend would be a redesign, and hard-coding different constants would
just relocate the fabrication.

**Suggested resolution.** Either have `/api/v1/forecast` return
`cashflow_projection: [{month, income_paise, expenses_paise, net_paise}]`, or
remove the Cashflow Projection table until it does. Removing is the correct
interim step; the current state is worse than absent.

### 2. Recharts emits `NaN` geometry on `/forecast`

**Reproduction.** Open `/forecast` with an empty or zero-range projection and
read the browser console:

```
Error: <path> attribute d: Expected number, "M 10,NaN 44.545454545…".
Error: <polyline> attribute points: Expected number, "10,NaN 44.545454545…".
```

**Impact.** A user-facing chart renders a broken path. The browser console is not
clean on a primary route.

**Owner.** Frontend (`components/forecast/**`). **Must be fixed together with
#1** — once the fabricated series is gone the NaN source may disappear, and
patching the chart alone would hide the symptom while the fabricated table
remained.

### 3. Platform Console cold start is unusable: no request timeout, indefinite "Loading…"

**Reproduction.** Restart the backend and open any `/platform/**` page. The first
`GET /platform/v1/health` after boot took **39 s** in this worktree. On a
subsequent cold pass a batch of five console requests each logged
`duration_ms=117218` (117 s); `/platform/v1/evidence` once logged
`duration_ms=375118` (375 s). Warm cache: 2–345 ms.

**Impact.** For up to two minutes after a backend start, every console page shows
an indefinite "Loading…". `lib/api/gateway.ts` sets no timeout and no
`AbortSignal`, so a slow-but-alive API is indistinguishable from a hung one. The
console's own `ConsoleUnavailableState` is unreachable in this scenario.

**Owner.** Shared. The startup cost is Agent 4's (a 39 s first health snapshot is
a startup-path problem). The missing request timeout is frontend. **Not fixed
here**: adding a timeout without a value justified by measurement risks turning a
slow-but-correct console into a falsely-degraded one, and the console is
explicitly forbidden from computing its own health verdict
(`components/platform/console-state.tsx`).

**Suggested resolution.** A conservative `AbortSignal.timeout` (30 s) that
surfaces the existing `ConsoleUnavailableState` with a retry, plus a backend
warm-up that builds the health snapshot before the port opens.

---

## P1

### 4. Three entire backend feature areas have no frontend surface

All registered, all 200, all unconsumed by anything in `frontend/**`:

| Area | Routes | Examples |
|---|---|---|
| Insights engine | 8 | `/insights/`, `/insights/score`, `/insights/summary`, `/insights/trends`, `/insights/forecast`, `/insights/anomalies`, `/insights/patterns`, `/insights/compare` |
| Credit-card engine | 14 | `/credit-cards`, `/credit-cards/statements`, `/statements/{id}`, `/utilization`, `/spending`, `/fees`, `/rewards`, `/payments` |
| Global search | 2 | `/search/`, `/search/suggestions` |

Plus: export (`/export/`, `/export/{format}`, `/export/schedule`), recurring-charge
detection (`/recurring/`, `/recurring/patterns`), savings goals, budgets, and
6 of 7 behaviour endpoints (`/behaviour/patterns`, `/trends`, `/insights`,
`/score`, `/debt-health`, `/spending-patterns` — only `/wellness-score` is used).

**Reproduction.** `curl` each path → 200. `grep -r` the path in `frontend/` → no
hit.

**Impact.** The nav advertises "Cards" and "INTELLIGENCE" but the Cards page
reads only the `/workspaces/credit-cards` summary DTO — the card statements,
utilisation, fees and rewards the engine computes are unreachable. Likewise
nothing in the UI can search, export, or read behaviour trends or debt health.

**Owner.** Product + frontend. Not built here — each is a feature, and the brief
explicitly forbids beginning unrelated product features.

### 5. `/api/v1/investments` POST returns HTTP 500 — the Investments page cannot be populated

**Reproduction.**
```
curl -X POST http://localhost:8000/api/v1/investments \
  -H 'Content-Type: application/json' \
  -d '{"name":"X","investment_type":"equity","invested_paise":1000,
       "current_value_paise":2000,"units":1.5}'
# -> {"error":{"message":"Internal server error","status_code":500}}
```

**Evidence (exact).**
```
backend/src/routers/investments.py:48  create_investment
backend/src/services/investment_service.py:76
TypeError: InvestmentRepository.create() got an unexpected keyword argument 'buy_price_paise'
```

The request body is schema-valid: `InvestmentCreate` (`backend/src/routers/investments.py:14-24`)
declares `buy_price_paise: int | None = None`, and the frontend sends exactly the
documented fields. The service passes the kwarg to a repository that does not
accept it.

**Impact.** The Investments workspace is permanently empty. `useCreateInvestment`
surfaces only "Failed to create investment", so the 500 is invisible to the user.
This is why chart validation had to be done on other workspaces.

**Owner.** Backend (`investment_service.py:76` — drop the kwarg or add it to the
repository signature). Reported, not edited, per the file-ownership boundary.

### 6. `/platform/v1/framework/integrity`: severity counters do not reconcile with the findings

**Reproduction.** `curl http://localhost:8000/platform/v1/framework/integrity`:
`total_findings: 5`, `critical_count: 0`, `high_count: 0`, `medium_count: 0`,
`low_count: 0`, `info_count: 0` — while `findings[]` carries severities `low`,
`MEDIUM`, `low`, `MEDIUM`, `LOW`.

**Impact.** The Framework Integrity page showed "Total 0 / Critical 0 / High 0 /
Medium 0 / Low 0" next to "Detector Findings (5)". The severity counters appear
to be keyed lowercase against uppercase emissions. The console now **discloses**
the contradiction (`data-testid="framework-counter-mismatch"`) rather than hiding
it, because the console must not recompute an authority's tally
(`components/platform/console-state.tsx`). The backend counters still need fixing.

**Owner.** Backend (C62 integrity authority). Two defects: the counter keying, and
the inconsistent severity casing that made the frontend's severity colours fail
(fixed on the frontend side).

### 6.5 `WellnessScoreResponse.score` is double-scaled — the score and its band are untrustworthy

**Reproduction.** With at least one transaction in the database:
```
curl http://localhost:8000/api/v1/behaviour/wellness-score
# {"score":"7561.45","band":"Excellent", ...}
```
`WellnessScoreResponse.score` is documented "between 0 and 100"
(`backend/src/models/behaviour.py:31`) and `compute_wellness_score` clamps to
`[0, 100]` (`backend/src/engines/behaviour_engine/wellness.py:88-89`), but
`compute_financial_profile` stores `wellness_score_bps =
int(wellness_score * 10000)` (`backend/src/services/behaviour_service.py:217`) —
scaling an already-0-100 value by 10000 again — and `get_wellness_score` reads
that column into the response with no division
(`behaviour_service.py:328-333`, `:548`).

**Impact.** The score and the band are both wrong for any household with real
data. `classify_wellness_band` thresholds at 90/75/50/25, so it returns
"Excellent" for any value ≥ 90, including 7561.45 — the band carries no
information. `financial_intelligence_service.py:868` propagates the same value
into financial intelligence, so it contaminates that surface too. The no-data
path returns a hardcoded `Decimal("100")` (`behaviour_service.py:276-289`),
which is why this is invisible on an empty database — and why the frontend
carried two contradictory beliefs about the scale for as long as it did.

**Owner.** Backend. Store one scale and convert on read. This was found in
M10 Agent 3 while attempting the frontend-side fix; the frontend no longer
rescales the value, but only a backend fix makes the number meaningful.

### 7. Time navigation on the dashboard is inert

**Reproduction.** Open `/dashboard`, click `Month`, `Quarter`, `Year`, `Compare`,
`Forecast` in the bottom time rail. No rendered value changes (verified by
comparing extracted INR values before and after each click).

**Impact.** The rail is present on every workspace and is the app's primary
Time-First affordance; on the dashboard it does nothing.

**Owner.** Frontend. Not fixed here because the intended contract — whether the
rail is per-workspace or a shell-level affordance, and what it should filter —
was not established, and guessing would change behaviour across all workspaces.

### 8. `tools/e2e_seed.py` cannot seed anything

**Reproduction.** `PYTHONPATH=backend python3 tools/e2e_seed.py`. It calls
`/api/transactions`, `/api/banks`, `/api/members`, `/api/accounts`,
`/api/import/detect`, `/api/import/execute`. Every one of those returns 404; the
registered paths are all `/api/v1/...`. The script's own docstring claims
`AGENTS.md`-style canonical seeding and is referenced in a Playwright hook
comment.

**Impact.** There is no working E2E fixture seed. The database in a fresh
worktree is empty, which is why the financial app renders entirely in empty
states on a clean checkout and why chart validation requires manual seeding.

**Owner.** `tools/` — outside Agent 3's boundary. Reported.

---

## P2

### 9. `GET /platform/v1/status` is live but has no surface

`/platform/status` returns 404; `lib/hooks/use-platform-status.ts` exists,
calls the endpoint, and is imported by nothing. The endpoint returns
`commit_sha`, `certification_state`, and capability/profile/workflow counts —
i.e. exactly the "what build is this" question an operator asks first.

**Recommendation.** Add the route, or delete the hook. The hook is already
written and the endpoint already exists; only a `page.tsx` is missing.

### 10. `POST /platform/v1/diagnostics/diagnose` and `/diagnose/register` are unconsumed

The Diagnostics surface is entirely read-only: it reports findings but offers no
way to run a diagnosis or register a result. A user reading
`ci_continue_on_error_intentional` or `stale_artifacts` findings has no action
available. This is the "read-only console" limitation made concrete: the sidebar
footer says "No AI, no remediation", so the *intent* is documented, but the
diagnose endpoints exist and are unwired.

### 11. Two variants of the same read: `/api/v1/categories` and `/api/v1/categories/list`

`use-categories.ts` and `use-query-finance.ts` call `/api/v1/categories`;
`use-category-analytics.ts` calls `/api/v1/categories/list`. Both are registered.
Consolidate on one.

### 12. Second "Bank Statement Parser" string

`components/onboarding/tutorial.tsx:17` — "Welcome to Bank Statement Parser", on a
product that is ClariFin OS. Same class as the `/settings` About block fixed in
this pass; left because it is tutorial copy rather than a product identity
surface. One-line change.

### 13. `useAsyncQuery.hasLoaded` reports `true` during the first load

`lib/hooks/use-async-query.ts:35` returns `isFetching || data !== undefined`,
which is `true` while the very first request is in flight. Consumers that gate an
empty state on `hasLoaded && !data` will flash "no data" before data arrives.
Not fabricated data, but a truthfulness regression in the empty state. Affects
every consumer of the hook, so it needs its own pass.

### 14. Nav advertises surfaces that are summary-only

The left nav lists Cards, Loans, Investments, Behaviour and Forecast. Loans and
Investments are reached through their `/workspaces/*` DTOs only — the loan
amortisation schedule, payment-progress, interest-analysis and EMI calculator
(eight registered endpoints) and the investment update/delete endpoints are all
unreachable. The nav therefore promises more than the pages deliver.

### 15. No live diagnostic count in the console nav

The sidebar's Diagnostics badge was hardcoded "5" and is now absent, because a nav
badge may only carry a live number and there is no cheap console-wide source for
it. Deriving it in the layout would add an unconditional diagnostic query to
every console page. A `/platform/v1/diagnostics` aggregate (the endpoint exists and
returns `evidence_count` and `classification`) would make this cheap.

### 16. Metric hierarchy is flat on `/net-worth`

Six equal-weight cards; the primary figure (net worth) is not visually dominant.
Recorded as an observation — fixing it is design work, not a defect repair.

---

## P3

### 17. `lib/hooks/use-query-finance.ts` duplicates `use-overview.ts`

Two independent `fetchOverview` implementations, two different response types
(`OverviewData` vs `Overview`), and now two different validators (one Zod, one
none) for the same endpoint. This is how the `/api/overview` 404 survived: the
duplicated file had no schema to catch it. Consolidating removes a whole class of
drift.

### 18. `lib/validation/__tests__/performance.test.tsx` is a timing flake

`5 Card components render under 100ms` asserts a synchronous wall-clock render
budget. On this 4-core machine it failed once during the full parallel run
(438 ms measured) and passed 9/9 three times in isolation, and passed on the
baseline before any change. Nothing I touched is in its import graph. Not
modified — per the rules, test assertions are not to be weakened, and this one is
measuring the machine, not the code. Recorded so a future CI red is not blamed on
this pass.

### 19. Backend dev-loop ergonomics: `localhost` resolves to `::1` first

`getent hosts localhost` returns `::1` first on this host. Binding uvicorn to
`127.0.0.1` (rather than `0.0.0.0`, which `scripts/launch.sh` uses) makes the
frontend's `http://localhost:8000` requests fail to connect with **no browser
network error visible in a naive probe** — the requests simply hang. Two of my own
early probe scripts misread this as "the console makes no API calls". Not a
product defect, but a real trap for the next agent; `scripts/launch.sh` already
avoids it.
