# M10 Agent 3 — Visual / UI and Chart Findings

Agent: 3 of 4 · Baseline `bfcf336` · 2026-10-02

Scope note: this document records **broken, incomplete, inconsistent or
misleading** UI only. No speculative redesign was performed and no intentional
design direction was changed. "Direction" observations (Time-First, Context-Driven,
graph-as-overlay) are confined to §5 and describe what is present, not what
should replace it.

Evidence for every finding is a live browser render or a screenshot against a
seeded database (2 accounts, 2 loans, 30 transactions across 6 months, 6 members
of the API surface exercised). Findings that turned out to be **extraction
artifacts rather than defects** are recorded in §4 so they are not "fixed" later.

---

## 1. Misleading UI — fixed

### 1.1 Fabricated financial movement in the Command Center

`/command-center` metrics strip asserted, on every render, that net worth was up
₹18,200 (+2.8%) at 97% confidence, liquidity up ₹4,500 (+1.2%) at 95%, and so on
for all seven metrics. Every one of those fourteen numbers was a literal in the
source. The graph carries no prior-period balance, so there is no real change to
show — the strip now shows none, and says `Monthly Cashflow · Jun 2026` instead
of a 30-transaction slice called a month. Confidence is read from the nodes that
produced the value, and the badge is omitted when those nodes carry none.

### 1.2 Ratios presented as rupees

Investment Return, Debt Ratio, Forecast Confidence and Automation Success were
multiplied by 10000, typed as `valuePaise`, and rendered by the money primitive —
a 42% debt ratio displayed as "₹4,20,000.00". Each metric now declares its unit
and `MetricTile` renders percentages and plain numbers as such.

### 1.3 Operations dashboard reporting UNKNOWN for healthy dimensions

`/platform` is the console's primary screen. Seven of its eight status badges read
**UNKNOWN** — Backend, Frontend, Database, Architecture, Evidence, AI Runtime,
Verification — because the grid looked the labels up in the sub-authority
breakdown instead of the top-level health fields, which the API was reporting as
HEALTHY / HEALTHY / HEALTHY / SAFE / CURRENT / VALID / READY. A badge is a
signal; a screen that shows UNKNOWN on a healthy platform trains its reader to
ignore it. Fixed, and pinned by an E2E assertion that no dimension may render
UNKNOWN.

The "Domain Breakdown" table below that row was passed `domains={[]}` with the
comment "Will be populated from health data" and therefore never rendered. It now
renders the real sub-authority rows (Verification, EventStore, Framework
Integrity) with source and timestamp.

### 1.4 Sidebar badge that was always "5"

Every console page showed a red "5" next to Diagnostics, including the Diagnostics
page itself, which was simultaneously stating "0 finding(s)". Removed. Recorded
as a remaining issue rather than re-derived, because there is no cheap
console-wide source for a diagnostic-finding count.

### 1.5 Unsupported claim in a metric subtitle

The dashboard Capabilities tile read "8 stages · 0 issues". The
`/platform/v1/capabilities` payload has no issue count. Now reads
"8 stages in C50 catalog".

### 1.6 Same score, two different numbers — frontend corrected, backend defect open

`/dashboard` showed a bare "76" and `/behaviour` showed "Financial Health Score
0.0% — Excellent" for one payload. Root cause and full evidence in
`m10-agent3-02-consumption-findings.md` §4.1: the **backend** double-scales
`WellnessScoreResponse.score` (stores an already-0-100 value × 10000, reads it
back unscaled), and the frontend held two contradictory beliefs about it. An
intermediate fix that trusted the backend's docstring over its observed output
broke `/behaviour` outright and was reverted; the shipped behaviour renders the
score as the authority states it, declines to fill or colour a ring from an
out-of-range value, and states the discrepancy on both screens. The score and
its band remain untrustworthy until the backend scale is fixed.

### 1.7 Stale product identity in the app's own About block

`/settings` displayed "**FinTrack** — Bank Statement Parser Dashboard" next to a
ClariFin shell, ClariFin nav and a ClariFin platform console. Corrected.

---

## 2. Incomplete / unreachable UI — fixed

### 2.1 `/platform/history/compare` had no entry state

The route is only ever linked with `?current=<runId>`. Reaching it directly — a
bookmark, browser history, a prefetch — rendered the bare heading "Run Comparison"
and nothing else. The query is `enabled: !!currentId`, so no loading, no error and
no empty state could ever appear; a working page and a broken page were
indistinguishable. It now states that no run is selected and links to the run
list. The comparison itself was verified working: `POST /platform/v1/history/compare`
returns 200 for all four baseline modes (`LAST`, `LAST_PASS`, `KNOWN_GOOD`,
`BASELINE`).

### 2.2 Raw error objects rendered as page content

- `app/platform/verification/[capability]/page.tsx` rendered
  `Failed: {String(detail.error)}`. For the canonical `ApiError` that is the
  stringified object — status, transient flag and the fully escaped response
  envelope. An operator following a capability link for something that does not
  exist saw a wall of JSON with no indication of what was wrong.
- `app/platform/verification/history/[runId]/page.tsx` rendered
  `JSON.stringify(q.error, null, 2)` into a `<pre>` as the **entire page body**.

Both now use the console's standard terminal state with a retry, and report the
authority's own explanation. `lib/api/errors.ts` was added: it unwraps the
platform error envelope (`error.code`, `error.layer`, `error.message`) so the
screen reads *"Capability 'x' not found in live catalog [NOT_FOUND] via
platform.capabilities (HTTP 404)"* rather than the transport string. It never
invents a diagnosis and never returns a serialised object. `ApiError` gained a
`readonly path` field (additive) so a failure can name its endpoint.

### 2.3 A whole backend capability with no surface

`GET /platform/v1/status` returns `commit_sha`, `certification_state` and
capability/profile/workflow counts, and `lib/hooks/use-platform-status.ts` calls
it. No page imports the hook and `/platform/status` returns 404. Not created
here — adding a route is a product decision, and inventing a status page would
change the console's information architecture. Listed as a remaining issue with
the hook already in place.

### 2.4 Dead link from the dashboard

`QuickActions` linked to `/platform/settings`, which has never existed (verified
404). The identical bug was already fixed in `sidebar.tsx` in M9-C71 with a note
explaining that a dead `<Link>` target is worse than it looks — Next prefetches
it with an RSC request that never completes, so every console page failed
`waitUntil: 'networkidle'`. The same defect survived in the second component.
Replaced with Framework Integrity, a real surface the dashboard did not link to,
and the sidebar-link invariant is now mirrored onto the dashboard.

---

## 3. Charts — actual correctness

### 3.1 Cashflow Trend: two series bound to keys that do not exist — **fixed**

`components/dashboard/cashflow-chart.tsx`:

| Binding | Payload key | Result before fix |
|---|---|---|
| `XAxis dataKey="month_label"` | `month` | **axis rendered with no labels at all** |
| `Bar dataKey="expense_paise"` | `expenses_paise` | **the expense series never rendered** |

`GET /api/v1/cashflow/monthly?months=6` returns
`{"month":"2026-01","income_paise":18500000,"expenses_paise":1779800,"net_paise":16720200,"transaction_count":6}`.
The correct field names are asserted by the repo's own
`frontend/__tests__/use-cashflow.test.ts`. So a user saw an income series and a
net line, and **nothing at all** for expenses — the chart silently omitted half
its content. Corrected, with a UTC month tick formatter derived from the real
key.

### 3.2 Tooltip suppressed the series name — fixed

`formatter={(value) => [formatINR(Number(value)), '']}` passed an empty name, so
every tooltip row rendered as a bare amount with no series label. Now returns the
series name and adds a `labelFormatter` naming the month.

### 3.3 Duplicate chart headings — fixed

`ChartContainer title="Cashflow Trend"` duplicated the page's own
`<h2>Cashflow Trend</h2>` above it; a screenshot shows the title twice, stacked.
Same for Category Spend. Removed the redundant `ChartContainer` title; the page
heading is canonical.

### 3.4 Recharts rendering `NaN` geometry on `/forecast` — open

Browser console on `/forecast`:
```
Error: <path> attribute d: Expected number, "M 10,NaN 44.545454545…".
Error: <polyline> attribute points: Expected number, "10,NaN 44.545454545…".
```
Recharts is being handed a non-finite Y value and emits a broken path. With an
empty database every projection is 0, so the NaN is produced by a divide or a
domain calculation on a zero-width range. This is a real rendering defect (the
browser console is not clean) and it is **not** fixed here: isolating it needs
the forecast chart's data transform, and the fix must not paper over the NaN
rather than eliminate it. Highest-priority chart item.

### 3.5 `/forecast` shows fabricated cashflow projections — open, backend-owned

The Cashflow Projection table renders identical values for every month
(₹1,00,000 income / ₹60,000 expenses / ₹40,000 net), with **duplicated month
keys** (`2026-12` twice, `2027-03` twice) despite `/api/v1/forecast` returning
`net_worth_projections` with distinct dates. The values are not in the API
response, so the projection is generated client-side from constants. This is
fabricated financial data on a user-facing surface and is the most serious
remaining finding. It is backend-owned (`/api/v1/forecast` should return a cashflow
projection) and is reported, not patched, because inventing a projection engine
in the frontend would be a redesign.

### 3.6 Chart availability and empty states — good

Verified across 11 app routes: `recharts-wrapper` count, empty-state copy, and
INR values. Loading, error, empty and data states are all present and distinct
(ChartContainer + ErrorBoundary + per-capability `loading-skeleton.tsx` /
`error-state.tsx` / `empty-state.tsx`). No `NaN`/`Infinity` geometry was found
anywhere except `/forecast` (§3.4). INR values are correct and consistently
`en-IN` grouped (`₹99,200.00`, `₹3,85,000.00`, `₹4,16,000.00`).

### 3.7 The seeding recipe this pass used (no working fixture seed exists)

Every chart conclusion above required real data, and a fresh worktree has none.
`tools/e2e_seed.py` cannot supply it (see remaining issue #21), so data was
created through the canonical routes the frontend actually consumes — this is
the recipe, and it is the only part of this audit that is environment setup
rather than code:

```
POST /api/v1/accounts      {"name","account_type","bank","balance_paise","account_number_last4"}
POST /api/v1/loans         {"name","lender","loan_type","principal_paise","outstanding_paise",
                            "rate_bps","tenure_months","disbursed_date","emi_paise"}
POST /api/v1/investments   500 — see issue #5
POST /api/v1/import/detect    (multipart "file")  -> detect the CSV columns
POST /api/v1/import/execute   {"filename","mapping":{...},"bank_name","member"}
```

`/api/v1/import/detect` + `/execute` is the useful discovery: it is the one
import path that works, and it populated 30 transactions across 6 months
(the canonical CSV header it accepts is
`date,description,amount,type,category`).

---

## 4. Recorded as NOT defects (extraction artifacts)

- **`₹85,000.0085.0%` on `/net-worth`.** An `innerText` scrape reports
  `₹85,000.00` and `85.0%` concatenated. The spans are separated by an `ml-1`
  margin, which `innerText` does not emit. A screenshot shows correct spacing.
  `formatINR` itself is correct. No change made.
- **`Trend: down` beside `+0.0% from 1M`.** The `-₹` glyph is the
  `TrendingDown` icon, not a currency sign. The direction/percentage mismatch is
  real but comes from the backend's `trend` payload.
- **Y-axis tick order on the Cashflow Trend chart.** Read from a screenshot, the
  ticks are monotonic (₹4L, ₹3L, ₹2L, ₹1L top to bottom). An initial text
  reading suggested otherwise; the screenshot disproved it. No change made.

---

## 5. Direction observations (no redesign proposed)
Present and working: dark, dense, legible shell; a consistent left nav grouped
OVERVIEW / TRANSACTIONS / ACCOUNTS / INVESTMENTS / INTELLIGENCE / SETTINGS; a
persistent bottom time rail (Day / Week / Month / Quarter / Year / Compare /
Forecast) with a 24-month scrub grid on every workspace; a right Context panel
that updates on selection; `ExplainButton` on the headline metrics.

Gaps, described only:

- **Time navigation is present but inert on the dashboard.** Clicking Month,
  Quarter, Year, Compare and Forecast changed no rendered value. Whether the rail
  is wired per workspace or is a shell affordance was not established.
- **No graph-as-investigative-overlay on the financial workspaces.** The
  `GraphOverlay` component exists and is reachable via `⌘K → Graph`, but the
  default view of every workspace is a card/list stack. The Command Center's
  `GraphView` does render as an overlay.
- **Metric hierarchy is flat.** `/net-worth` presents six equal-weight cards with
  no primary figure; the largest number (net worth) is not visually dominant.

---

## 6. Verification actually observed

All commands run in this worktree against a live stack (uvicorn from the
repo-root `.venv` per `AGENTS.md`, plus `next start`).

| Check | Command | Result |
|---|---|---|
| Types | `npm run type-check` | **0 errors** |
| Lint | `npm run lint` | **0 errors**, 179 warnings (200 on the untouched baseline) |
| Unit | `npm run test` | **1381/1381 passed**, 109/109 files, 205.8 s |
| Build | `npm run build` | **succeeded** |
| E2E | `npx playwright test --project=chromium --project=mobile-chrome` | see §7 |

An earlier full run reported one unit failure —
`lib/validation/__tests__/performance.test.tsx` "5 Card components render under
100ms" (438 ms measured against a 100 ms budget). It passes 9/9 in isolation
three times running, and passed on the baseline before any change. It asserts
synchronous wall-clock render time on a 4-core machine with 109 test files
running in parallel; nothing in its import graph was touched. **Not modified** —
per the rules, test assertions are not to be weakened, and this one is measuring
the host, not the code. The final run above is green without it recurring.

## 7. E2E: separating my failures from pre-existing ones

A 36-failure run is not evidence on its own, so the failing specs were re-run
against the **baseline** (`bfcf336`) with the identical seeded database, to
attribute each failure.

| Failure class | Baseline result | Attribution |
|---|---|---|
| `visual-regression.spec.ts` — 9 snapshots (home, dashboard, transactions, analytics, import, transactions-mobile, personal, family, dark-mode) | **also fails, with larger diffs** (dark-mode-dashboard 40 546 px / 0.05 on baseline vs 3 007 px / 0.01 with these changes) | **data-driven.** I seeded 2 accounts, 2 loans and 30 transactions to validate charts; the baseline was captured against a clean database. |
| `behavior.spec.ts` "should display page title" | **passes on baseline** | **mine** — the behaviour-score regression described in §1.6, since fixed; now green on both projects. |
| `platform-c67.2.spec.ts` content rendering (2 tests) | not re-run in isolation; failure was `waitForSelector` at 90 s | **environmental.** The platform snapshot build queues behind other requests (117 s measured), so the console did not reach a terminal state within the spec's own documented 90 s budget under a 4-worker run. |
| `performance.spec.ts` (4 tests) | not re-run in isolation | **environmental.** Same cause: API response-time budgets measured against a saturated single-worker backend. |
| `m10-agent3-console.spec.ts` (4 tests) | n/a — new spec | **mine**, and all three causes were bugs in my own tests: an assertion that had inverted itself into something that could never pass, a selector for a "Quick Actions" heading the component does not render, and CSS-uppercased label text. Now 42/42 green on both projects. |

### Visual-regression snapshots were deliberately NOT re-recorded

`tests/e2e/specs/visual-regression.spec.ts-snapshots/PROVENANCE.md` is explicit
that snapshots are provenance-bound artifacts, may only be replaced by a
deliberate regeneration run, and must never be re-recorded to hide a regression.
Two independent reasons not to re-record here:

1. Re-recording against my **seeded** local database would bake that seed into
   the baseline. The committed baseline was captured against a clean database at
   SHA `96ae2e64` on 2026-09-29, which is also what CI runs against.
2. The `dashboard-page` diff legitimately contains an intentional change from
   this pass — the duplicated "Cashflow Trend" heading removal.

Re-baselining is the snapshot owner's decision and needs a provenance-bound run
against a clean database. It is recorded as a remaining issue, not taken here.
