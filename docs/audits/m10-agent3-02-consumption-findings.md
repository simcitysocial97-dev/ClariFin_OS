# M10 Agent 3 — Frontend / Backend Consumption Findings

Agent: 3 of 4 · Baseline `bfcf336` · 2026-10-02

Method: every route in `backend/src/routers/*.py` was extracted and compared
against every backend path literal in `frontend/**` (excluding `node_modules`,
`dist`, `.next`, `test-results`, `api-schema.json`, `generated/`). Mismatches
were then confirmed against a live API with `curl` and, where relevant, in a
browser with a request recorder.

---

## 1. Frontend calls to endpoints that do not exist

### 1.1 `/api/overview` — 404 (fixed)

`frontend/lib/hooks/use-query-finance.ts:43` requested `/api/overview`. The
backend registers overview at `/api/v1/overview` only
(`backend/src/routers/transactions.py`). Confirmed: `GET /api/overview` → **404**,
`GET /api/v1/overview` → 200.

The only consumer is `components/upload/upload-modal.tsx:53,81`, which calls it
purely to invalidate cached totals after a statement upload. The failure was
invisible: `useAsyncQuery.refetch` resolves through
`queryClient.invalidateQueries`, which does not reject, so the upload reported
success while the overview cache was never refreshed and the dashboard kept
showing pre-upload totals.

**Fixed.** Path corrected to `/api/v1/overview`; the phantom
`exclude_transfers` / `member` query parameters were dropped because the
registered route takes no such parameters, so sending them implied filtering
that is not applied.

### 1.2 `/platform/v1/diagnostics/signatures` — 404 (fixed)

Two call sites:

- `frontend/lib/hooks/use-platform-diagnostics.ts` → `useDiagnosticSignatures`
- `frontend/app/platform/diagnostics/detail/[id]/page.tsx:314` → `fetchDiagnosticDetail`

The platform router exposes `/diagnostics` (GET), `/diagnose` (POST) and
`/diagnose/register` (POST). There is no signatures route. Confirmed 404 in the
backend request log on every load. Consequence: the "Failure Signature" section
of `/platform/diagnostics/detail/[id]` was permanently unrenderable, and the page
always fell through to "Diagnostic finding not found" even for ids that exist.

**Fixed** to this app's own route handler `/api/diagnostic-signatures`, whose own
docstring already declared that intent ("provides the frontend with failure
signature data that would otherwise require a backend endpoint"). Two supporting
changes were required:

- `SAME_ORIGIN_BASE_URL` added to `lib/api/gateway.ts`. `apiFetch` prefixes
  `API_BACKEND_URL` for relative paths, so a same-origin call would silently
  have been sent to FastAPI, which has no such route.
- `app/api/diagnostic-signatures/route.ts` resolved the artifact against
  `process.cwd()`, which is `frontend/` under `next dev` / `next start`, while
  the artifact lives at the repository root
  (`runtime/generated/diagnostic-signatures.json`). It therefore always returned
  the empty store. Now probes both candidate roots.

### 1.3 `/api/v1/categories` vs `/api/v1/categories/list` — contract ambiguity (open)

`frontend/lib/hooks/use-categories.ts` and `frontend/lib/hooks/use-query-finance.ts`
call `/api/v1/categories`; `frontend/lib/hooks/use-category-analytics.ts` calls
`/api/v1/categories/list`. Both are registered on the backend, and the
frontend's own contract test (`tests/e2e/specs/transaction-import.spec.ts:236`)
already documents that it covers 15 of 17 registered category routes. Two
variants of the same read is at minimum a maintenance hazard. Not changed here:
picking one without a decision on the other risks a behaviour change for no
observed user-visible defect.

### 1.4 `tools/e2e_seed.py` — calls four non-existent paths (open, not mine)

`tools/e2e_seed.py` calls `/api/transactions`, `/api/banks`, `/api/members`,
`/api/accounts`, `/api/import/detect`, `/api/import/execute`. None of those
paths exist (they are all `/api/v1/...`). The seed tool therefore cannot seed
anything. It is outside the Agent 3 file-ownership boundary (`tools/`, not
`frontend/`), so it is reported rather than fixed.

---

## 2. Backend capabilities with no frontend consumer

Counted from the route tables. "Consumed" means some file in `frontend/**`
requests the path.

### 2.1 Financial application

| Router | Registered | Consumed | Unconsumed endpoints |
|---|---|---|---|
| `insights.py` | 8 | 0 | **all 8** — including `/insights/`, `/insights/score`, `/insights/summary`, `/insights/trends`, `/insights/forecast`, `/insights/anomalies`, `/insights/patterns`, `/insights/compare` |
| `credit_cards.py` | 14 | 0 | **all 14** — the entire credit-card engine: `/credit-cards`, `/credit-cards/statements`, `/statements/{id}`, `/utilization`, `/spending`, `/fees`, `/rewards`, `/payments`, … (the `/workspaces/credit-cards` summary DTO *is* consumed, but it is produced by a different router) |
| `behavior.py` | 1 | 1 | — (compatibility alias only) |
| `behaviour.py` | 7 | 1 | 6: `/behaviour/patterns`, `/behaviour/trends`, `/behaviour/insights`, `/behaviour/score`, `/behaviour/debt-health`, `/behaviour/spending-patterns` — only `/behaviour/wellness-score` is consumed |
| `cashflow.py` | 4 | 3 | 1: `/cashflow/categories` |
| `accounts.py` | 19 | 15 | 4: `/accounts/categories`, `/accounts/types`, `/accounts/summary`, `/accounts/insights` |
| `loans.py` | 8 | 1 | 7: `/loans/{id}`, `/loans/{id}/amortization`, `/loans/{id}/schedule`, `/loans/{id}/history`, `/loans/summary`, `/loans/insights`, `/loans/calculate-emi` |
| `insights/*` additional | — | 0 | `spend-patterns`, `forecast`, `portfolio` |
| `ai.py` | 4 | 1 | 3: `/ai/chat`, `/ai/explain`, `/ai/recommendations` |
| `workspaces/reconciliation.py` | 2 | 1 | 1: `/workspaces/reconciliation/verify` |
| `imports.py` | 3 | 3 | — |
| `statements.py` | 8 | 3 | 5: `/statements/{id}`, `/statements/{id}/transactions`, `/statements/period/{month}`, `/statements/search`, `/statements/pending` |
| `members.py` | 5 | 1 | 4: `/members/{id}` (PUT/DELETE), `/members/{id}/accounts`, `/members/switch` |
| `analytics.py` | 2 | 1 | 1: `/analytics/insights` |
| `search.py` | 2 | 0 | **all 2** — `/search/`, `/search/suggestions` |
| `export.py` | 3 | 0 | **all 3** — `/export/`, `/export/{format}`, `/export/schedule` |
| `recurring.py` | 2 | 0 | **all 2** — `/recurring/`, `/recurring/patterns` |
| `networth.py` | 2 | 0 | **all 2** — `/net-worth/`, `/net-worth/history` (the workspace is fed by `/workspaces/net-worth` instead) |
| `networth_projection.py` | 2 | 0 | **all 2** — `/net-worth/projection`, `/net-worth/projection/history` |
| `savings.py` | 1 | 0 | `/savings/goals` |
| `budgets.py` | 2 | 0 | `/budgets`, `/budgets/categories` |
| `health.py` | 1 | 0 | `/health` (financial-app health; distinct from `/platform/v1/health`) |

Net: **~30 registered financial endpoints have no frontend consumer at all**,
including three whole feature areas — the insights engine, the credit-card
engine, and global search — plus export and recurring-charge detection, both of
which have first-class backend services.

### 2.2 Platform API

`GET /platform/v1/status` returns real data and has **no consumer**:
`frontend/lib/hooks/use-platform-status.ts` exists and calls it, but no page
imports the hook. `POST /platform/v1/diagnostics/diagnose` and
`POST /platform/v1/diagnostics/diagnose/register` are also unconsumed.
`POST /platform/v1/history/compare` **is** consumed, via the
`/platform/history/compare` route — but that route has no entry state without a
query parameter, so it is not reachable by direct navigation (fixed).

---

## 3. Stubbed, hardcoded and fabricated data

### 3.1 Fabricated financial deltas and confidences — **fixed**

`frontend/components/command-center/metrics/metrics-strip.tsx` attached a
hardcoded period-over-period delta and a hardcoded confidence to every one of its
seven metrics:

```ts
{ id: 'net-worth',  valuePaise: netWorth, deltaPaise: 1820000, // Placeholder
  deltaPercent: 2.8, confidence: 97, … }
{ id: 'liquidity',  deltaPaise: 450000,  deltaPercent: 1.2, confidence: 95, … }
{ id: 'debt-ratio', valuePaise: Math.round(debtRatio * 10000), … confidence: 90 }
```

The Command Center therefore told the user that net worth was up ₹18,200
(+2.8%) at 97% confidence on every render, with no data behind any of it. The
graph carries no prior-period balance, so **no** real change is reportable — the
deltas are now omitted entirely rather than invented. Confidence is taken from
the nodes that produced the value, and omitted when those nodes carry none.

### 3.2 Ratios rendered as money — **fixed**

The same file multiplied `investmentReturn`, `debtRatio`, `forecastConfidence`
and `automationSuccess` by 10000 to make a plausible-looking paise magnitude, and
declared the results as `valuePaise`. A 42% debt ratio was displayed as
**"₹4,20,000.00"**. `MetricData` now carries an explicit `format` and
`MetricTile` gained an optional `format` prop (default `'money'`, so every
existing money caller is unchanged).

### 3.3 "Monthly Cashflow" that was not a month — **fixed**

`transactions.slice(0, 30)` labelled "Monthly Cashflow": 30 arbitrary
transactions in whatever order the backend returned them. Transactions are now
bucketed by their own `date` into a calendar month, the most recent month is
reported, and the label names it (`Monthly Cashflow · Jun 2026`) so the number
is self-describing.

### 3.4 Hardcoded console claims — **fixed**

- `app/platform/page.tsx` — `CapabilitiesSummary` rendered
  `subtitle="${stages} stages · 0 issues"`. The `/platform/v1/capabilities`
  payload contains no issue count at all; the "0 issues" was a claim the console
  could not support. Now reports only what the API returned.
- `components/platform/sidebar.tsx` — the Diagnostics entry carried
  `badge: '5'`, so every console page displayed a red "5" next to Diagnostics
  including the Diagnostics page itself, which simultaneously stated
  "0 finding(s)". Removed; see the remaining-issues note on restoring it live.

### 3.5 Authority data discarded by the console — **fixed**

`app/platform/page.tsx` passed `domains={[]}` to `DimensionsGrid` and the grid
resolved each of its eight labels against `data.domains` — which only carries the
sub-authority breakdown (Verification, EventStore, Framework Integrity). Seven of
eight badges rendered **UNKNOWN** while `/platform/v1/health` was reporting
`backend: HEALTHY`, `frontend: HEALTHY`, `database: HEALTHY`,
`architecture: SAFE`, `verification: CURRENT`, `evidence: VALID`, `ai: READY`.
The top-level fields are authoritative; the grid now uses them, and the
sub-authority `domains` array is rendered as the "Domain Breakdown" table that
previously never appeared (the hardcoded `[]` guaranteed it could not).

### 3.6 Severity case mismatch — **fixed**

`app/platform/framework/page.tsx` looked up `SEVERITY_COLORS[finding.severity]`
with a lowercase-keyed table, while `/platform/v1/framework/integrity` returns
mixed-case severities (`low`, `MEDIUM`, `LOW`). Every upper-case finding fell
through to the grey `info` styling, so a MEDIUM artifact-integrity defect was
rendered as an informational note. Lookup is now case-insensitive.

### 3.7 Stale product branding — **fixed**

`app/settings/page.tsx` displayed "**FinTrack** — Bank Statement Parser Dashboard"
in the About block, on a product whose shell, nav and platform console all say
ClariFin. Corrected to "ClariFin — Financial OS". (A second occurrence remains in
`components/onboarding/tutorial.tsx:17`, "Welcome to Bank Statement Parser" —
same defect class, left alone because it is tutorial copy rather than a product
identity surface; listed below.)

### 3.8 Non-fabricating fallbacks reviewed and deliberately kept

- `useAsyncQuery.hasLoaded` (`lib/hooks/use-async-query.ts:35`) returns
  `isFetching || data !== undefined`, which is `true` while a *first* load is in
  flight. It makes the initial load render as "empty" for a moment. It is not a
  fabricated value — it is an existing truthfulness regression for the empty
  state, worth fixing, but it is a behaviour change on every consumer and was not
  made in this pass.
- `use-cashflow`, `use-net-worth`, `use-categories` guard `catch` blocks that
  rethrow, so there is **no** `return []` / `return {}` fabrication in any
  finance hook. This is the correct pattern; it is recorded as a positive finding.

---

## 4. Frontend money arithmetic

Money representation rules were checked, not assumed. Findings:

| Location | Expression | Verdict |
|---|---|---|
| `components/command-center/metrics/metrics-strip.tsx` | `Math.round(ratio * 10000)` for `investmentReturn`, `debtRatio`, `forecastConfidence`, `automationSuccess`, declared as `valuePaise` | **violation — fixed.** A dimensionless ratio was given a money unit and a magnitude, so it rendered as rupees. |
| `lib/schemas/analytics.ts` | `z.number().int()` on `avg_monthly`, `spending_trend[].average`, `day_of_week[].amount`, `biggest_transaction.amount` | **contract violation — fixed.** These are rupee magnitudes; a rupee average is fractional (`avg_monthly: 9974.17`). The false constraint made the frontend stricter than the authority and rejected a valid 200 response. `.int()` retained on genuine counts (`rank`, `count`, `frequency`, `unique_merchants`). |
| `lib/utils/format.ts` `formatINR` | paise → INR | correct. Indian lakh/crore grouping, negative sign preserved. |
| `components/primitives/data-display/money-value.tsx` | paise → INR | correct. |
| `components/primitives/metric-tile/metric-tile.tsx` `formatChange` | paise → INR | correct. |
| `net-worth-summary.tsx`, `account-breakdown.tsx`, `composition-chart.tsx`, `trend-chart.tsx` | `formatINR(...)` | correct. |

**Note on a false positive, recorded so it is not "fixed" later:** an
`innerText` scrape of `/net-worth` produces strings like `₹85,000.0085.0%`.
This is a *text-extraction* artifact — the two spans are separated by
`ml-1` margin, which `innerText` does not emit. A screenshot confirms the
rendered output is `₹85,000.00  85.0%` with correct spacing. No code change was
made here.

### 4.1 Behaviour score: the backend double-scales it — **frontend corrected, backend bug open**

The same score rendered two different values on two screens: a bare number on
`/dashboard` and "1.0%" on `/behaviour`, from one
`GET /api/v1/behaviour/wellness-score`.

The frontend held two contradictory beliefs, both symptoms of a backend defect:
`lib/schemas/behavior-score.ts` claimed "The score is expressed in basis points
(0-10000 == 0-100%)" and validated `.max(10000)`;
`components/behaviour/behaviour-score.tsx` divided by 100 and compared against
`>= 800` / `>= 600`; `components/dashboard/behavior-score-card.tsx` read
`financial_health_score ?? score` and applied a `> 100 ? /100 : ` guess.

**The authority required three rounds of evidence, and my first conclusion was
wrong.** I initially read the documentation — `WellnessScoreResponse.score` is
"between 0 and 100" (`backend/src/models/behaviour.py:31`) and
`compute_wellness_score` returns `wellness_score * 100` clamped to `[0, 100]`
(`backend/src/engines/behaviour_engine/wellness.py:88-89`) — tightened the
schema to `.max(100)`, and removed the `/100`. **That broke `/behaviour`**:
against real data the endpoint returns `{"score": "7561.45", "band":
"Excellent"}`, so the validator rejected a valid HTTP 200,
`useBehaviourCapability` threw "API response shape mismatch", the workspace
rendered an error alert, and `behavior.spec.ts` failed on both projects. Only
running the suite surfaced this; reading the code would not have.

The real behaviour is a **double scale in the backend**:

| Step | Location | Effect |
|---|---|---|
| `compute_wellness_score` returns `wellness_score * 100`, clamped to `[0,100]` | `engines/behaviour_engine/wellness.py:88-89` | produces a 0-100 value |
| `wellness_score_bps = int(wellness_score * 10000)` | `services/behaviour_service.py:217` | multiplies an **already 0-100** value by 10000 |
| `get_wellness_score` reads that column into the response with no division | `services/behaviour_service.py:328-333`, `:548` | emits 0-1,000,000 as `score` |
| `classify_wellness_band` thresholds at 90/75/50/25 | `engines/behaviour_engine/wellness.py:109-118` | returns "Excellent" for anything ≥ 90 |

The no-data path returns a hardcoded `Decimal("100")`
(`services/behaviour_service.py:276-289`), which is why an empty database masks
the defect entirely — and why the first conclusion looked defensible.

**What the frontend now does, without rescaling a value it was handed:** the
validator accepts the authority's real output; `components` keeps its genuine
0-100 bound (`behaviour_service.py:292` documents those as already 0-100 and
they are not double-scaled); `/behaviour` and `/dashboard` show the score as
stated, do not fill or colour a ring from an out-of-range value, and say so
(`data-testid="behaviour-score-out-of-range"`,
`data-testid="dashboard-score-out-of-range"`). A dashboard bug fixed in passing:
`strokeDasharray={(score / 100) * 283}` with a score of 7561 is ~27× the
circumference, so the ring drew multiple overlapping arcs; the fill is now
clamped to the documented range.

**Backend fix required** (not Agent 3's boundary): `behaviour_service.py:217`
should store one scale and `get_wellness_score` should convert on read. Until
then the wellness score and its band are not trustworthy, and
`financial_intelligence_service.py:868` propagates the same value onward.

### 4.2 Charts binding to keys the API does not emit — **fixed**

`components/dashboard/cashflow-chart.tsx` bound the X axis to `month_label` and
the expense bar to `expense_paise`. `GET /api/v1/cashflow/monthly` returns
`{ month, income_paise, expenses_paise, net_paise, transaction_count }` — the
field names are asserted by `frontend/__tests__/use-cashflow.test.ts`. Result:
the X axis rendered with **no labels at all** and the expense bar **never
rendered**. Corrected to `month` (with a tick formatter) and `expenses_paise`.
The tooltip formatter returned `[value, '']`, suppressing the series name; it now
returns the series name and labels the month.
