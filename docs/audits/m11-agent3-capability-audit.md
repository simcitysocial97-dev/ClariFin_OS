# M11 — Agent 3: Unconsumed backend capabilities (Task 16)

Audit date: 2026-10-02
Baseline: `c5c38b91` (branch `m11/parallelism-correctness`)

---

## Correction to the M10 audit before the findings

M10's remaining-issues report (`docs/audits/m10-agent3-04-remaining-issues.md`,
§P1-4) named three areas with no frontend surface:

| M10 area | M10 claim | Verified at `c5c38b91` |
|---|---|---|
| Insights engine | 8 registered endpoints, no frontend consumer | **`backend/src/routers/insights.py` does not exist** |
| Credit-card engine | 14 registered endpoints | exists; **10** registered (see Area A) |
| Global search | 2 registered endpoints | **`backend/src/routers/search.py` does not exist** |

`git cat-file -e bfcf336:backend/src/routers/insights.py` and the equivalent for
`search.py` both fail. Neither router exists at M10's own baseline `bfcf336`, nor
at `c5c38b91`, nor at any commit touching those paths. M10's area names were
carried forward from a tree it could not have read. Two of its three areas are
therefore not findings.

The audit below was re-derived from the **live OpenAPI schema** of the running
application, not from documentation. `FinancialIntelligenceService` and
`insights`-equivalent functionality *is* registered and *is* unconsumed — M10
simply never named it.

---

## Method

1. Enumerate the authoritative route table from `src.api.app.openapi()`,
   excluding `/platform/*`: **89 registered paths, 158 operations.**
2. Extract every `/api/v1/...` literal from `frontend/**` excluding
   `node_modules`, `.next` and `api-generated.ts`: **44 distinct literals.**
3. Normalise `{param}` segments and match base-to-base.
4. Probe each candidate area live against a seeded database.

Result: **68 registered paths have no frontend consumer.**

### The three areas, as finally determined

Two independent lines of evidence were used, because the M10 report could not
be relied on and one of Agent 2's reports overlapped mine:

* **M10's report** named Insights and Global search. Neither router exists at
  any commit it measured, so both are discarded (see the correction above).
* **Agent 2** reported, independently and from live seeding, that
  `behaviour/patterns` was structurally empty and `behaviour/profile` returned
  500. Both were in this milestone's ownership and were fixed (see Area C).
* **This audit**, from the live OpenAPI schema, identified the credit-card,
  loan-simulation and financial-intelligence surfaces as the three largest
  unconsumed areas.

Agent 2's two reports and Area C below are the same underlying finding reached
from two directions: the behaviour domain was the largest cluster of broken or
unreachable capability, not the insights/search areas M10 named.

---

## Classification

### Area A — Credit-card engine

| Step | Evidence |
|---|---|
| Backend capability | `src/engines/financial_intelligence/credit.py`, `src/services/credit_card_service.py` |
| Endpoint | `/api/v1/credit-cards/{card_id}/{outstanding,utilization,metrics,next-statement-date,statements,payments,emi-conversion,foreclosure}` — 8 registered |
| Contract | `CreditCardSummaryDTO`, `StatementDTO`, `EmiConversionDTO`, `ForeclosureDTO` |
| Frontend hook | **none** — only `use-cards` (bare `GET /api/v1/cards`) |
| Workspace/page | `/cards` (`lib/workspace/workspace-registry.ts:212`) |
| Renderer | `cards-summary` only |
| User action | none |

**Classification: MISSING PRODUCT SURFACE.**

Not speculative: the workspace registry *declares* the missing capability
itself — `description: 'Credit cards and statements'`,
`supportedCommands: ['add', 'validate', 'refresh']`,
`inspectorSections: ['context', 'evidence']`. "statements" is unimplemented and
the `validate` command has no control. The page renders a summary while the nav
invites the user into a card detail view that does not exist.

Live: every endpoint responds (404 for a card id that does not exist is correct
behaviour; `statements` returns `[]`; the three POSTs return 422 naming the
required field). Nothing is broken here — it is unbuilt, not faulty.

### Area B — Loan simulation / analysis engine

| Step | Evidence |
|---|---|
| Backend capability | `src/engines/loans/{prepayment,foreclosure,rate_change,priority,surplus_allocation,amortization}.py` |
| Endpoint | `/api/v1/loans/{loan_id}/{schedule,payments,prepayment-simulation,foreclosure-simulation,rate-change-simulation,analysis/prepayment-vs-foreclosure}` plus `/loans/analysis/{priority,surplus-allocation}` — 8 registered |
| Contract | Pydantic request/response models per simulation; `AmortizationScheduleRow` |
| Frontend hook | **none** — `use-loans` only calls `GET /api/v1/loans` |
| Workspace/page | `/loans` (`workspace-registry.ts:230`) |
| Renderer | `loans-summary` only |
| User action | none |

**Classification: MISSING PRODUCT SURFACE.**

Again declared by the product itself, more explicitly than Area A:
`description: 'Loan management and amortization'`,
`supportedCommands: ['add', 'edit', 'delete', 'schedule', 'simulate', 'refresh']`,
`inspectorSections: ['context', 'amortization', 'simulation']`,
`supportedSelections: ['loan']`.

Three of the six declared commands — `schedule`, `simulate`, and selecting a
loan for the `amortization`/`simulation` inspector sections — have no control
and no endpoint call. The entire prepayment-vs-foreclosure engine, which is the
product's most valuable loan feature, is unreachable from the UI.

Live: all respond; 404 for a missing loan is correct; POSTs return 422 naming
the required field. Unbuilt, not faulty.

### Area C — Behaviour domain (Agent 2's two reports; repaired)

8 registered paths: `/api/v1/behaviour`, `/cashflow-health`, `/debt-health`,
`/monthly-report`, `/patterns`, `/profile`, `/recommendations`,
`/wellness-score`. The frontend consumes **one** of them
(`/wellness-score`). The workspace page reads `/api/v1/behaviour`.

| Step | Evidence |
|---|---|
| Backend capability | `BehaviourService`, `engines/behaviour_engine/*`, `PatternRepository` |
| Endpoint | 8 registered; only `/wellness-score` consumed by the frontend |
| Contract | `WellnessScoreResponse`, `DebtHealthResponse`, `CashflowHealthResponse`, `MonthlySummaryResponse`, `FinancialPattern` |
| Frontend hook | `use-behaviour` → `/api/v1/behaviour`; `use-behaviour-score` → `/wellness-score` |
| Workspace/page | `/behaviour` (`workspace-registry.ts:303`) |
| Renderer | behaviour summary + radar |
| User action | none beyond the score read |

**Classification: INCOMPLETE/BROKEN** — five distinct defects, all repaired.

This is the area both this audit and Agent 2 landed on, from opposite
directions. Agent 2 seeded a real database and hit two 500s; this audit read the
source and found three more fabrications. All six are fixed:

1. **`GET /behaviour/profile` → 500 `UNIQUE(household_id, snapshot_date)`.**
   `behaviour_snapshots` has `UNIQUE(household_id, snapshot_date)` — one
   snapshot per household per day — but `create_snapshot` issued a bare
   `INSERT`. `compute_financial_profile` runs on demand, so the second call of
   the same day always failed. Reproduced exactly: call 1 → 200, call 2 → 500,
   call 3 → 500. Fixed by UPDATE-then-INSERT.

2. **`GET /behaviour/patterns` → structurally always `[]`.**
   `PatternRepository.create_pattern` is the only writer of
   `behaviour_patterns` and had **zero callers** anywhere — no router, service,
   startup hook or job. The table could never hold a row, so no seeding could
   change it, and the three other readers of the same table saw nothing either.
   Fixed by detecting patterns from the household's own transactions and
   persisting them through `create_pattern` from inside
   `BehaviourService.get_patterns` — the canonical `/api/v1/*` path. That service
   already establishes on-demand computation (`get_wellness_score` computes a
   snapshot when none exists), so detection on read adds no second architecture.
   `create_pattern` also needed the same UPDATE-then-INSERT treatment against
   `UNIQUE(pattern_type, pattern_key, household_id)`.

3. **Three readers expected a row shape the mapper does not produce.**
   `get_patterns`, `generate_monthly_summary` and `_compute_subscription_alerts`
   read `p["strength_bps"]` and `p["total_amount_paise"]`.
   `PatternRepository._map_pattern_row` emits `strength` (0-100) and
   `total_amount` (rupees). All three were `KeyError` → HTTP 500, so **even a
   correctly populated table could not be served**. The unit test
   `test_get_patterns_success` passed throughout because its `sample_patterns`
   fixture used the same phantom shape — the test was green while the product
   was broken. The fixture now states the mapper's shape, and
   `BehaviourService._to_financial_pattern` converts at the boundary into the
   `FinancialPattern` contract (strength 0-1, `total_amount_paise` integer
   paise).

4. **Five non-persisted snapshot keys read with `[]` across three methods.**
   `debt_cycle_score`, `credit_dependency_ratio`, `credit_revolver_ratio`,
   `income_stability_score` and `expense_stability_score` are exposed by the API
   responses but are **not** columns on `behaviour_snapshots` and are not
   produced by `_map_snapshot_row`. Reading them off a snapshot raised
   `KeyError` in `get_debt_health`, `get_cashflow_health`,
   `get_monthly_summary` and `_generate_alerts` — i.e. HTTP 500 on
   `/behaviour/debt-health`, `/behaviour/cashflow-health`,
   `/financial-intelligence/outlook` and `/financial-intelligence/report` for
   every household with a snapshot. Fixed with one shared
   `_on_demand_metrics()` that computes all five from live transactions,
   accounts, loans and cards, so the read path and `compute_financial_profile`
   cannot disagree.

   `get_monthly_summary` additionally returned a hardcoded `foir=Decimal("0.4")`
   and `band="MODERATE"`, both annotated *"Simplified - would compute from
   latest data"* — the monthly report asserted a debt position the household may
   not have. Both are now computed.

5. **`get_patterns`'s second parameter was named `limit`** and documented as
   "maximum number of patterns" while being passed straight to
   `get_recent_patterns(days=...)`. The router's own parameter is `days`
   (default 30), so the default of 5 silently narrowed a 30-day query to 5 days
   for any caller relying on the default. Renamed to `days`.

Live on a seeded household: all 8 behaviour paths return 200, two patterns are
detected and persisted (`IMPULSE zara impulse buy` 0.7429 / 25 txns,
`SUBSCRIPTION netflix subscription` 0.2571 / 6 txns), and re-reading is
idempotent.

### Area D — Financial-intelligence engine (also repaired; no UI built)

8 registered paths: `/cashflow-forecast`, `/credit-forecast`,
`/liquidity-forecast`, `/outlook`, `/priorities`, `/recommendations`,
`/recommendations/{recommendation_id}`, `/report`. **Zero frontend consumers,
and no `WorkspaceName` in `workspace-registry.ts`** — so on the product's own
terms this area is `INTENTIONALLY BACKEND-ONLY`.

**Classification: INTENTIONALLY BACKEND-ONLY, but was INCOMPLETE/BROKEN behind
that label** — four defects, all repaired. No UI was created: with no workspace
registration, no nav entry, and no declared intent, a surface here would be
inventing product scope.

1. **`get_debt_health` raised `KeyError: 'debt_cycle_score'`** — the first of the
   five non-persisted snapshot reads. HTTP 500 on `/outlook` and `/report` for
   every household with a snapshot. Fixed (see Area C, item 4).

2. **`financial_goals.priority` did not exist.** `get_household_goals` ordered
   by it and `create_goal` inserted it; the DDL never declared it:
   `OperationalError: no such column: priority` → HTTP 500 on `/priorities` and
   `/report`. Fixed by adding the column to the DDL **and** to
   `_MIGRATION_COLUMNS` so pre-existing databases are brought up to date. The
   column was added rather than priority being stripped from the repository,
   `update_goal` and the engine, because the domain genuinely models one.

3. **`RecommendationService.get_recommendations` returned hardcoded sample data.**
   ```python
   borrowed_lifestyle_ratio = Decimal("0.35")   # "35% of income goes to debt"
   foir = Decimal("0.45")                       # "45% debt-to-income ratio"
   liquidity_months = 1
   current_subscriptions = []                   # "No subscriptions in demo"
   ```
   Every household received identical advice. Fixed: the profile is derived from
   the household's own transactions, accounts, loans and cards through
   `compute_borrowed_lifestyle_ratio` / `compute_foir` /
   `compute_liquidity_months`, and below 5 recorded transactions the response is
   `status: "insufficient_data"` with an empty list and a stated reason.

   The derivation also exposed a real arithmetic error: `compute_foir` divides a
   **monthly** obligation by **monthly** income, and the implementation passed a
   multi-month income total, understating FOIR by the number of months observed
   (a 0.70 ratio reported as 0.2333 over three months). Fixed by dividing by the
   distinct months present.

4. **Two more fabrication and serialisation defects in the same service.**
   - `r.dict() if hasattr(r, "dict") else r` — `Recommendation` is a plain class
     with its own `to_dict()` and has neither `dict` nor `model_dump`, so the raw
     domain object reached FastAPI's serialiser and the endpoint returned HTTP
     500 *"Unable to serialize unknown type: Recommendation"*. Fixed to `to_dict()`.
   - `get_recommendation_details` returned a fixed "Build Emergency Fund" payload
     for **any** id, carrying the fabricated evidence line *"63% of Indians
     cannot cover a ₹50,000 emergency (RBI survey)"* and a static
     `confidence: 0.95`. Fixed: it resolves against the recommendations actually
     derived for the household and reports `found: false` otherwise.

All eight endpoints now return HTTP 200 on a seeded database.

---

No UI was created for Areas A and B. Creating it would mean eight new endpoints'
worth of schema, hooks, renderers and controls per area — and the brief is
explicit that UI must not be created merely to increase coverage. What is
recorded instead is that both areas are *declared* product surface with named
missing capabilities, so the gap is a product backlog item, not a defect to be
closed opportunistically.

The one vertical slice built in this milestone is the investments create
mutation (Task 17), where the justification was different: the endpoint
existed, the hook existed, the mutation was the only write path in the
workspace, and it returned HTTP 500 for every payload. That is a broken
advertised capability, not an absent one.

---

## Areas deliberately NOT built

No UI was created for Areas A or B. Building it would mean eight endpoints'
worth of schema, hooks, renderers and controls per area, and the brief is
explicit that UI must not be created merely to increase coverage. Both areas
are recorded as *declared* product surface with specifically named missing
capabilities — `workspace-registry.ts` states `"Credit cards and statements"`
and `"Loan management and amortization"` and lists the commands
`schedule` and `simulate` — so the gap is a product backlog item with a named
scope, not a defect to be closed opportunistically.

Area D is `INTENTIONALLY BACKEND-ONLY` on the product's own evidence (no
workspace registration, no nav entry), so no surface was invented there either.

The one vertical slice built in this milestone is the investments create
mutation (Task 17), where the justification was different: the endpoint existed,
the hook existed, the mutation was the only write path in the workspace, and it
returned HTTP 500 for every payload. That is a broken *advertised* capability,
not an absent one.

---

## Summary table

| Area | Registered paths | Frontend consumers | Declared in `workspace-registry.ts`? | Classification | Action taken |
|---|---|---|---|---|---|
| A — Credit-card engine | 10 | 0 (`/cards` bare only) | Yes — `"Credit cards and statements"`, commands `add`/`validate`/`refresh` | **MISSING PRODUCT SURFACE** | Classified; no UI built |
| B — Loan simulation / analysis | 10 | 0 (`/loans` bare only) | Yes — `"Loan management and amortization"`, commands `schedule`/`simulate` | **MISSING PRODUCT SURFACE** | Classified; no UI built |
| C — Behaviour domain | 8 | 1 (`/wellness-score`) | Yes — `/behaviour`, `inspectorSections` incl. `patterns` | **INCOMPLETE/BROKEN** | **5 defects fixed**, detection wired |
| D — Financial-intelligence | 8 | 0 | **No** | **INTENTIONALLY BACKEND-ONLY**, was INCOMPLETE/BROKEN | **4 defects fixed**; no UI built |
| — Insights engine (M10) | 0 | — | — | **router does not exist** | Rejected; see correction |
| — Global search (M10) | 0 | — | — | **router does not exist** | Rejected; see correction |

---

`FinancialGoalRepository.create_goal(goal_id: str, ...)` types the id as `str`
while `financial_goals.id` is `INTEGER PRIMARY KEY AUTOINCREMENT`, so any
non-numeric id raises `sqlite3.IntegrityError: datatype mismatch`. No registered
endpoint calls `create_goal` — `get_household_goals` is the only reader — so
nothing is currently reachable through the API. It is the same class of
repository/DDL drift as the investments defect and is worth a follow-up.

---

## Additional finding, out of scope, reported not fixed

`FinancialGoalRepository.create_goal(goal_id: str, ...)` types the id as `str`
while `financial_goals.id` is `INTEGER PRIMARY KEY AUTOINCREMENT`, so any
non-numeric id raises `sqlite3.IntegrityError: datatype mismatch`. No registered
endpoint calls `create_goal` — `get_household_goals` is the only reader — so
nothing is currently reachable through the API. It is the same class of
repository/DDL drift as the investments defect and is worth a follow-up.

---

## Verification

New test files, all passing:

| File | Tests | Covers |
|---|---|---|
| `backend/tests/unit/services/test_m11_forecast_provenance.py` | 46 | Task 12 — calendar arithmetic, empty/sparse/populated, placeholder tripwire, mapper contradiction rejection, net-worth authority equality |
| `backend/tests/unit/services/test_m11_wellness_score_scale.py` | 17 | Task 14 — engine range pinned, write/read round trip, band informativeness, migration idempotence |
| `backend/tests/integration/cross_layer/test_journey_investment_mutation.py` | 19 | Task 17 — POST 200, DDL column contract, positional-shift tripwire, full create→DB→GET→update→delete chain, id-type consistency |
| `backend/tests/unit/services/test_m11_unconsumed_capabilities.py` | 30 | Area C/D — debt-health/outlook/report reachability, `priority` column + migration, recommendation derivation vs the demo profile, absence of the fabricated RBI statistic, live 200 on all audited endpoints, and a guard asserting `insights.py`/`search.py` do not exist |
| `backend/tests/unit/services/test_m11_behaviour_workspace_provenance.py` | 17 | The behaviour workspace fabrication factory |
| `backend/tests/unit/services/test_m11_behaviour_snapshot_and_patterns.py` | 28 | Agent 2's two reports — snapshot upsert, pattern detection wired in, the three phantom reader keys, the five non-persisted snapshot reads |

Two pre-existing test files were corrected because they **pinned the defects
rather than the contract**, and would otherwise have blocked the fixes:

- `backend/tests/unit/services/test_behaviour_service.py` — `sample_patterns`
  used `strength_bps`/`total_amount_paise`, a row shape matching neither the raw
  row nor `PatternRepository._map_pattern_row`'s output. Because the service was
  written against that phantom shape, the test passed while
  `GET /api/v1/behaviour/patterns` returned HTTP 500 against the real repository.
  Now states the mapper's shape.
- `backend/tests/unit/services/test_recommendation_networth_services.py` — two
  tests asserted the fabricated demo profile: one asserted a non-empty list
  *"the demo profile yields"*, the other patched `_demo_profile`, a method that
  never existed (`create=True`), so the patch was a no-op and the assertion
  actually exercised the hardcoded constants. Both keep their intent — in
  particular *"discriminates the engine from a no-op wrapper"* — but the input
  is now real recorded data plus a real EMI in the `loans` table, so a HIGH
  severity result can only come from the engine having inspected real figures.

Full backend suite (`unit`, `contract`, `integration/cross_layer`, `capability`,
`properties`, `domain`, `architecture`): **3957 passed, 0 failed.**
`runtime/tests/test_e2e_seed_reproducibility.py` (Agent 2's): **8 passed** — the
two seed-surface tests that were red on the `behaviour/profile` 500 are green.