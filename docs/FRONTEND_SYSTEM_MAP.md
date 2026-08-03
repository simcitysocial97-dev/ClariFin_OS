# FRONTEND SYSTEM MAP — ClariFin_OS

**Generated:** 2026-08-03  
**Scope:** `frontend/` (Next.js 15, React 19, TypeScript 5.7)  
**Backend:** FastAPI at `http://localhost:8000`

---

## 1. LAYER DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────┐
│  Browser / User                                                     │
└──────────────────┬──────────────────────────────────────────────────┘
                   │ HTTP (Next.js Server Components + Client Hooks)
                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  app/ (Next.js App Router Pages)                                    │
│     dashboard/page.tsx    ← useDashboardMetrics()                   │
│     accounts/page.tsx     ← inline fetch + useManagedAccounts()     │
│     loans/page.tsx        ← useLoans() + inline mutations           │
│     cards/page.tsx        ← useCards() + useStatementsQuery()       │
│     investments/page.tsx  ← useInvestments() + inline mutations     │
│     net-worth/page.tsx    ← useNetWorthCapability()                 │
│     cashflow/page.tsx     ← useCashflowCapability()                 │
│     behaviour/workspace-page.tsx  ← useBehaviourCapability()        │
│     forecast/workspace-page.tsx   ← useForecastCapability()         │
│     reconciliation/page.tsx   ← usePendingReconciliations()         │
│     transactions/workspace-page.tsx                               │
│     command-center/page.tsx                                             │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ Capability / Hook
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  lib/capabilities/  (intelligent workspaces with filters, evidence) │
│  lib/hooks/         (simple data-fetching hooks)                    │
│     Both layers use @tanstack/react-query                           │
│     Both layers apply Zod runtime validation                        │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ Map raw API JSON → ViewModels
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  lib/mappers/  (11 mappers: accounts, behaviour, cashflow, ...)     │
│  lib/schemas/  (9 Zod schemas: dashboard-metrics, cashflow, ...)     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ Typed ViewModels
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  types/   (api.ts, api-generated.ts, financial.ts, view-models)     │
│     api.ts ............. HANDWRITTEN API types (canonical)          │
│     api-generated.ts ... Auto-generated OpenAPI (minimal usage)     │
│     *view-model.ts ..... Frontend domain models per module          │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  components/  (39 component directories + shared primitives)        │
│     primitives/  Surface, Panel, Stack, Grid, MoneyValue            │
│     ui/          shadcn/ui primitives (Button, Dialog, etc.)        │
│     /dashboard, /accounts, /loans, /cards, /cashflow, ...           │
└─────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  lib/api/client.ts  (fetch wrappers with Zod validation)            │
│  lib/hooks/use-query-finance.ts (aggregated transaction/statements) │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ fetch()
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Backend FastAPI  http://localhost:8000                             │
│  Routers → Services → Repositories → SQLite (data/finance.db)       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. CANONICAL API TYPE SOURCE

### Import Count Table

| Type Source | File Size | Production Imports | Test Imports | Total | Status |
|---|---|---|---|---|---|
| `types/api.ts` | 250 lines | 0 (re-exported via client.ts) | 0 | 0 | **WORKING CONTRACT** |
| `types/api-generated.ts` | 2,497 lines | 1 (`credit-cards-mapper.ts`) | 2 (`fvf.test.ts`) | 3 | **MINIMAL USE** |
| `types/index.ts` | 183 lines | N/A (re-exports api-generated) | — | — | PASS-THROUGH |

### Usage Analysis

```
types/api.ts
  ├─ Re-exported by: lib/api/client.ts (CategorySummary, MonthlyBreakdown, UncategorizedPattern, Transaction)
  ├─ Used by: components, hooks indirectly through client.ts types
  ├─ Defines: Account, Loan, Investment, NetWorth, AmortizationEntry, PrepaymentRequest
  └─ Hand-written to match ACTUAL backend responses

types/api-generated.ts
  ├─ Generated by: openapi-typescript from api-schema.json
  ├─ Only production consumer: lib/mappers/credit-cards-mapper.ts (imports CreditCardSummaryDTO)
  ├─ Endpoint definitions are mostly stub-only (responses: { 200: { content: { "application/json": unknown } } })
  └─ NOT wired to any service — generic operation shapes, no typed response payloads
```

### Decision

**Canonical type source = `types/api.ts`** (handwritten, matches actual backend)

`types/api-generated.ts` should be migrated to full typed operations or deprecated. Migration plan: enrich operations with proper response schemas derived from `types/api.ts`.

---

## 3. HOOK DEPENDENCY GRAPH

```
useDashboardMetrics()
  ↓ GET /api/dashboard/summary
  ↓ DashboardService
  ↓ core/db.schema.py (transactions, reconciliations)

useAccounts() [deprecated — replaced by capability]
  ↓ GET /api/accounts/manage
  ↓ AccountService

useManagedAccounts()
  ↓ GET /api/accounts/manage
  ↓ AccountService (managed_accounts router)

useLoans()
  ↓ GET /api/loans
  ↓ LoanService

useLoanSchedule(loanId)
  ↓ GET /api/loans/{id}/schedule
  ↓ LoanService

usePrepaymentSimulation()
  ↓ POST /api/loans/{id}/prepayment-simulation
  ↓ LoanSimulationService

useInvestments()
  ↓ GET /api/investments
  ↓ InvestmentService

useNetWorth()
  ↓ GET /api/networth
  ↓ NetWorthService

useCards()
  ↓ GET /api/cards
  ↓ StatementService (cards_statements router)

useStatementsQuery()
  ↓ GET /api/statements
  ↓ StatementService

useReconciliations()
  ↓ GET /api/reconciliations
  ↓ ReconciliationService

usePendingReconciliations()
  ↓ GET /api/reconciliations/pending
  ↓ ReconciliationService

useScanReconciliations()
  ↓ GET /api/reconciliations/scan
  ↓ ReconciliationService

useBehaviorScore()
  ↓ GET /api/behavior/score
  ↓ BehaviourService

useBehaviorInsights()
  ↓ GET /api/behavior/insights
  ↓ BehaviourService

useCashflow(months)
  ↓ GET /api/cashflow/monthly?months=N
  ↓ CashflowService

useOverviewQuery()
  ↓ GET /api/overview
  ↓ (overview endpoint — unused by dashboard)

useTransactionsQuery()
  ↓ GET /api/transactions
  ↓ TransactionService

// Capability hooks (workspace pattern)
useAccountsCapability()
  ↓ GET /api/v1/accounts
  ↓ AccountService (accounts v1 router)
  ↓ accountsMapper.mapAccountsDTO()

useNetWorthCapability()
  ↓ GET /api/networth
  ↓ NetWorthService
  ↓ netWorthMapper.mapNetWorthDTO()

useCashflowCapability()
  ↓ GET /api/v1/cashflow
  ↓ CashflowService (cashflow_workspace router)
  ↓ cashflowMapper.mapCashflowDTO()

useBehaviourCapability()
  ↓ GET /api/v1/behaviour
  ↓ BehaviourService (behaviour_workspace router)
  ↓ behaviourMapper.mapBehaviourDTO()

useForecastCapability()
  ↓ (endpoint TBD — see Route Matrix)
  ↓ FinancialIntelligenceService

useInvestmentsCapability()
  ↓ (endpoint TBD)
  ↓ InvestmentService

useLoansCapability()
  ↓ (endpoint TBD)
  ↓ LoanService

useReconciliationCapability()
  ↓ (endpoint TBD)
  ↓ ReconciliationService

useTransactionCapability()
  ↓ (endpoint TBD)
  ↓ TransactionService

useCreditCardsCapability()
  ↓ (endpoint TBD)
  ↓ CreditCardService
```

---

## 4. ROUTE → WORKSPACE MATRIX

| Frontend Route | Page File | Uses Capability | Backend Endpoint | Service | Status |
|---|---|---|---|---|---|
| `/` | `app/page.tsx` | — | redirect → `/dashboard` | — | OK |
| `/dashboard` | `app/dashboard/page.tsx` | No (direct hook) | `GET /api/dashboard/summary` | DashboardService | OK |
| `/accounts` | `app/accounts/page.tsx` | No (dual fetch) | `GET /api/accounts` + `GET/POST/PUT/DELETE /api/accounts/manage` | AccountService | DUAL PATH |
| `/loans` | `app/loans/page.tsx` | No (direct hook) | `GET /api/loans`, `GET /{id}/schedule`, `POST /{id}/prepayment-simulation` | LoanService | OK |
| `/cards` | `app/cards/page.tsx` | No (dual hook) | `GET /api/cards` + `GET /api/statements` + `GET /api/v1/credit-cards/{id}/*` | StatementService, CreditCardService | DUAL PATH |
| `/investments` | `app/investments/page.tsx` | No (direct hook) | `GET /api/investments`, `POST /api/investments`, `PUT/DELETE /api/investments/{id}` | InvestmentService | OK |
| `/net-worth` | `app/net-worth/page.tsx` | Yes | `GET /api/networth` | NetWorthService | OK |
| `/cashflow` | `app/cashflow/page.tsx` | Yes | `GET /api/v1/cashflow` | CashflowService | OK |
| `/behaviour` | `app/behaviour/workspace-page.tsx` | Yes | `GET /api/v1/behaviour` | BehaviourService | **NO page.tsx** |
| `/forecast` | `app/forecast/workspace-page.tsx` | Yes | *(endpoint unresolved)* | FinancialIntelligenceService | **NO page.tsx** |
| `/reconciliation` | `app/reconciliation/page.tsx` | No (direct hook) | `GET /api/reconciliations/pending` | ReconciliationService | OK |
| `/transactions` | `app/transactions/page.tsx` → `workspace-page.tsx` | ? | *(workspace entry point)* | TransactionService | OK (delegates) |
| `/command-center` | `app/command-center/page.tsx` | No | *(client-side state)* | — | OK |
| `/settings` | `app/settings/page.tsx` | No | *(static/local)* | — | OK |

---

## 5. COMPONENT CONTRACT VERIFICATION

### Dashboard
```
DashboardPage
  ├─ NetCashFlowCard     → data.net_cash_flow_paise      → GET /api/dashboard/summary
  ├─ SavingsRateCard     → data.savings_rate              → GET /api/dashboard/summary
  ├─ EMIRatioCard        → data.emi_ratio                 → GET /api/dashboard/summary
  ├─ BufferDaysCard      → data.buffer_days               → GET /api/dashboard/summary
  ├─ CashflowChart       → (internal chart data)          → separate query?
  ├─ CategorySpendChart  → (internal chart data)          → separate query?
  ├─ BehaviorScoreCard   → (separate behavior score?)     → GET /api/behavior/score
  ├─ InsightsPanel       → (separate insights?)           → GET /api/behavior/insights
  ├─ AnalyticsSummaryBar → (analytics data)               → GET /api/analytics
  ├─ RecurringChargesWidget → (analytics data)           → GET /api/analytics
  ├─ TopMerchantsWidget    → (analytics data)           → GET /api/analytics
  └─ RecentTransactions  → data.recent_transactions       → GET /api/dashboard/summary
```
**Finding:** Dashboard composite endpoint (`/api/dashboard/summary`) must return ALL fields above. If not, this is a multi-query page.

### Accounts
```
AccountsPage
  ├─ Computed accounts (raw fetch /api/accounts)          → AccountService
  ├─ Managed accounts (useManagedAccounts hook)           → AccountService (/manage)
  ├─ Total balance (inline sum)                           → computed_total + managed_total
  ├─ Add/Edit/Delete dialogs                              → POST/PUT/DELETE /api/accounts/manage
  └─ CommandCenter registration                           → commandCenterRuntime
```
**Finding:** Two separate data sources fetched in parallel. No single endpoint.

### Loans
```
LoansPage
  ├─ useLoans()                                           → GET /api/loans
  ├─ LoanCard (render)                                    → Loan DTO from hook
  ├─ AmortizationDrawer                                   → useLoanSchedule(id) → GET /api/loans/{id}/schedule
  ├─ Prepayment simulation                                → usePrepaymentSimulation()
  ├─ Create/Edit/Delete mutations                         → POST/PUT/DELETE /api/loans
  └─ Inline monetary math (paise/100 for form display)    → MANUAL CONVERSION
```
**Finding:** Form displays rupees (divided by 100), stores paise (multiplied by 100). Frontend arithmetic present.

### Cards
```
CardsPage
  ├─ useCards()                                           → GET /api/cards
  ├─ useStatementsQuery()                                 → GET /api/statements
  ├─ CardPortfolioHeader                                  → cardsData.summary
  ├─ CreditCardTile                                       → individual card
  ├─ StatementHistoryDrawer                               → filtered statements
  └─ Validation (inline fetch to /api/v1/credit-cards/{id}/*)  → HARDCODED URL
```
**Finding:** Dual fetch. Validation endpoint uses hardcoded localhost URL bypassing API_BASE.

### Net Worth
```
NetWorthPage
  ├─ useNetWorthCapability()                              → GET /api/networth
  ├─ netWorthMapper.mapNetWorthDTO(raw)                   → ViewModel transform
  ├─ NetWorthSummary                                      → dto fields
  ├─ CompositionChart                                     → dto assets/liabilities breakdown
  ├─ TrendChart                                           → historical data
  └─ InsightsPanel                                        → dto.insights
```
**Finding:** Clean capability→mapper→viewmodel path. Single endpoint.

### Cashflow
```
CashflowPage
  ├─ useCashflowCapability()                              → GET /api/v1/cashflow
  ├─ cashflowMapper.mapCashflowDTO(raw)                   → ViewModel transform
  ├─ CashflowSummary                                      → dto summary
  ├─ MonthlyTrend                                         → dto.monthly
  ├─ CategoryBreakdown                                    → dto.categories
  └─ InsightsPanel                                        → dto.insights
```
**Finding:** Clean capability path. Single endpoint.

### Behaviour
```
BehaviourPage (workspace-page.tsx)
  ├─ useBehaviourCapability()                             → GET /api/v1/behaviour
  ├─ behaviourMapper.mapBehaviourDTO(raw)                 → ViewModel transform
  ├─ BehaviourScore                                       → dto.wellness_score
  ├─ SpendingPatterns                                     → dto.spending_patterns
  ├─ WellnessRadar                                        → dto.wellness_radar
  ├─ SavingsRate                                          → dto.savings_rate
  ├─ DebtHealth                                           → dto.debt_health
  └─ InsightsPanel                                        → dto.insights
```
**Finding:** Clean capability path. No page.tsx wrapper exists.

### Forecast
```
ForecastPage (workspace-page.tsx)
  ├─ useForecastCapability()                              → endpoint TBD
  ├─ forecastMapper.mapForecastDTO(raw)                   → ViewModel transform
  ├─ ForecastSummary                                      → dto.summary
  ├─ NetWorthProjection                                   → dto.net_worth_projections
  ├─ CashflowProjection                                   → dto.cashflow_projections
  ├─ ScenarioComparison                                   → dto.scenarios
  └─ InsightsPanel                                        → dto.insights
```
**Finding:** No page.tsx wrapper exists. Workspace-page.tsx is the only entry.

### Reconciliation
```
ReconciliationPage
  ├─ usePendingReconciliations()                          → GET /api/reconciliations/pending
  ├─ ReconciliationSummaryBar                             → summary stats
  ├─ ReconciliationMatchCard (×N)                         → match list
  └─ CommandCenter registration                           → commandCenterRuntime
```
**Finding:** Direct hook pattern. No capability wrapper.

---

## 6. STATE FLOW AUDIT

### Duplicate Queries Detected

| Page | Duplicate Fetch 1 | Duplicate Fetch 2 | Conflict |
|---|---|---|---|
| `/accounts` | `fetch('/api/accounts')` raw | `useManagedAccounts()` → `/api/accounts/manage` | Same domain, different endpoints |
| `/cards` | `useCards()` → `/api/cards` | `useStatementsQuery()` → `/api/statements` | Separate concerns but co-located |
| `/dashboard` | `useDashboardMetrics()` | `useOverview()` (commented unused) | Dormant duplicate |

### Duplicate Caches

| Query Key | Consumed By | StaleTime | Duplicate Of |
|---|---|---|---|
| `['accounts', 'managed']` | accounts/page.tsx | 5 min | — |
| `['accounts']` (v1, via capability) | accounts/workspace-page.tsx | 5 min | Different endpoint `/api/v1/accounts` |
| `['dashboard', 'summary']` | dashboard/page.tsx | 30s | — |
| `['overview']` | use-query-finance.ts (unused) | 5 min | Dormant |
| `['cashflow', 'monthly', N]` | use-cashflow.ts | 5 min | — |
| `['cashflow']` (capability) | cashflow/page.tsx | 5 min | DIFFERENT endpoint `/api/v1/cashflow` |
| `['networth']` | use-networth.ts | 2 min | — |
| `['netWorth']` (capability) | net-worth/page.tsx | 5 min | SAME endpoint `/api/networth` |
| `['behaviour']` (capability) | behaviour/workspace-page.tsx | 5 min | — |
| `['behavior', 'score']` | use-behavior-score.ts | 10 min | DIFFERENT from capability |
| `['behavior', 'insights']` | use-behavior-insights.ts | 10 min | — |

### Frontend Monetary Arithmetic

**Total occurrences of rupee↔paise conversion: 70**

| Location | Conversion | Fields Affected |
|---|---|---|
| `hooks/use-cards.ts` | `rupeesToPaise(x)` × 5 | credit_limit, current_outstanding, minimum_due, total_outstanding, total_credit_limit |
| `hooks/use-reconciliation.ts` | `rupeesToPaise(x)` × 3 + `confidenceToBps(x)` × 3 | amount, match_confidence |
| `hooks/use-overview.ts` | `rupeesToPaise(x)` × 2 | category_chart.value, monthly_chart.amount |
| `app/accounts/page.tsx` | `Math.round(parseFloat(x) * 100)` × 2 | balance form input |
| `app/loans/page.tsx` | `(value / 100).toString()` + `Math.round(x * 100)` × 4 | principal, outstanding, emi form display/storage |
| `app/investments/page.tsx` | `(value / 100).toString()` + `Math.round(x * 100)` × 2 | invested_paise, current_value_paise form display/storage |

**Rule violation:** Backend returns paise. Frontend hooks for cards/reconciliation/overview convert FROM rupees TO paise, implying the backend is returning rupees for those endpoints. This is a contract mismatch.

---

## 7. RENDERING PIPELINE

```
Backend DTO (Python Pydantic)
    ↓ JSON response (paise integers)
    ↓
Http Response
    ↓
Hook fetch() + Zod schema validate()
    ↓ (optionally: rupeesToPaise conversion — VIOLATION)
    ↓
ViewModel (types/*-view-model.ts)
    ↓ (optionally: mapper.transform())
    ↓
Capability state (Zustand or react-query cache)
    ↓
Workspace page component
    ↓
Presentational widgets (components/*/*)
    ↓
MoneyValue primitive (paise → formatted ₹)
```

**Single-path requirement check:**
- Dashboard: ✅ single endpoint, no mapper (inline construction)
- Accounts: ❌ dual endpoint (computed + managed)
- Loans: ✅ single endpoint, inline CRUD
- Cards: ❌ dual endpoint (cards + statements)
- Net Worth: ✅ single endpoint via capability
- Cashflow: ✅ single endpoint via capability
- Behaviour: ✅ single endpoint via capability
- Forecast: ⚠️ workspace only, no page wrapper
- Reconciliation: ✅ single endpoint
- Investments: ✅ single endpoint, inline CRUD

---

## 8. IMPORT GRAPH STATISTICS

### Top Imported Modules (Production Code)

```
  47  @tanstack/react-query
  31  react
  28  @/lib/hooks/*
  24  @/components/*
  18  @/lib/capabilities/*
  15  @/lib/mappers/*
  12  @/types/*
  10  @/lib/api/client
   8  @/lib/schemas/*
   7  @/lib/command-center
   6  lucide-react
   5  @/components/primitives/*
   4  @/lib/utils/format
   3  zod
```

### Most Depended-On Hooks

```
useLoans            → 3 consumers (loans/page, workspace, simulations)
useInvestments      → 2 consumers (investments/page, workspace)
useNetWorth         → 2 consumers (net-worth hook + capability)
useCashflow         → 2 consumers (hook + capability)
useManagedAccounts  → 1 consumer (accounts/page)
useDashboardMetrics → 1 consumer (dashboard/page)
useCards            → 1 consumer (cards/page)
useReconciliations  → 1 consumer (reconciliation/page)
```

### Most Depended-On Capabilities

```
useAccountsCapability    → accounts/workspace-page.tsx
useNetWorthCapability    → net-worth/page.tsx
useCashflowCapability    → cashflow/page.tsx
useBehaviourCapability   → behaviour/workspace-page.tsx
useForecastCapability    → forecast/workspace-page.tsx
```

---

## 9. DUPLICATE MATRIX

| Old Pattern | New Pattern | Actual Usage | Recommendation |
|---|---|---|---|
| `hooks/use-accounts.ts` (raw fetch) | `capabilities/use-accounts-capability.ts` (mapped) | Both exist; page uses raw, workspace uses capability | VERIFY — decide which path is canonical for /accounts |
| `hooks/use-cashflow.ts` (raw /api/cashflow/monthly) | `capabilities/use-cashflow-capability.ts` (/api/v1/cashflow) | Both exist; page uses capability, hook unused by pages | COMPATIBILITY — raw hook may be dead code |
| `hooks/use-networth.ts` (raw /api/networth) | `capabilities/use-net-worth-capability.ts` (/api/networth + mapper) | Both exist; page uses capability, hook unused by pages | COMPATIBILITY — raw hook may be dead code |
| `hooks/use-behavior-score.ts` | `capabilities/use-behaviour-capability.ts` | Both exist; score hook NOT used by any page | VERIFY — dead code candidate |
| `hooks/use-behavior-insights.ts` | `capabilities/use-behaviour-capability.ts` | Both exist; insights hook NOT used by any page | VERIFY — dead code candidate |
| `hooks/use-overview.ts` | `use-query-finance.ts/useOverviewQuery` | Both exist; overview NOT rendered by any page | COMPATIBILITY — dormant code |
| `hooks/use-analytics.ts` | Dashboard widget queries | analytics hook exists but dashboard uses separate widget queries | VERIFY — potential dead code |
| `types/api.ts` | `types/api-generated.ts` | api.ts is active contract; api-generated has 1 consumer | COMPATIBILITY — api-generated should be enriched or removed |
| `app/accounts/page.tsx` | `app/accounts/workspace-page.tsx` | Both exist at same route path — NEXT.js would conflict | **CRITICAL** — only one can be active |
| `app/loans/page.tsx` | `app/loans/workspace-page.tsx` | Both exist — NEXT.js would conflict | **CRITICAL** — only one can be active |
| `app/cards/page.tsx` | `app/cards/workspace-page.tsx` | Both exist — NEXT.js would conflict | **CRITICAL** — only one can be active |
| `app/investments/page.tsx` | `app/investments/workspace-page.tsx` | Both exist — NEXT.js would conflict | **CRITICAL** — only one can be active |
| `app/reconciliation/page.tsx` | `app/reconciliation/workspace-page.tsx` | Both exist — NEXT.js would conflict | **CRITICAL** — only one can be active |
| `app/forecast/workspace-page.tsx` | (no page.tsx) | Missing thin wrapper | **MISSING** |
| `app/behaviour/workspace-page.tsx` | (no page.tsx) | Missing thin wrapper | **MISSING** |

---

## 10. PLACEHOLDER / UNUSED STRUCTURES

| Path | Assessment |
|---|---|
| `hooks/use-overview.ts` | Dormant — no page consumes it |
| `hooks/use-analytics.ts` | Unknown consumer — may be used by dashboard sub-widgets |
| `hooks/use-behavior-score.ts` | Likely dead — no page imports it directly |
| `hooks/use-behavior-insights.ts` | Likely dead — no page imports it directly |
| `types/api-generated.ts` | Minimal usage (1 prod import) — auto-generated stub |
| `generated/` directory | Unknown purpose — need inspection |
| `mocks/` directory | Test fixtures — not production concern |
| `tools/` directory | Utility scripts — not part of app runtime |
| `proxy.ts` | Development proxy config — not runtime code |
| `app/forecast/page.tsx` | MISSING — forecast route has no entry page |
| `app/behaviour/page.tsx` | MISSING — behaviour route has no entry page |

---

## 11. MAJOR FINDINGS

1. Two API type sources coexist: `types/api.ts` (active, 250 lines) and `types/api-generated.ts` (auto-generated stub, 2,497 lines, only 1 production import).
2. Six pages have both a `page.tsx` and a `workspace-page.tsx` at the same route, creating a Next.js routing conflict where the first file alphabetically wins.
3. Five hooks exist as raw fetchers (`use-cashflow`, `use-networth`, `use-behavior-score`, `use-behavior-insights`, `use-overview`) that are either dormant or superseded by capability wrappers.
4. Three pages (accounts, loans, investments) perform inline paise↔rupee arithmetic at the form boundary (`* 100` and `/ 100`), violating the paise-canonical contract.
5. `use-cards.ts` applies `rupeesToPaise()` to card data that the backend already returns in paise, indicating a backend contract gap.
6. `use-reconciliation.ts` applies both `rupeesToPaise()` and `confidenceToBps()` conversions, again suggesting the backend returns non-canonical units for these endpoints.
7. `use-overview.ts` converts category and monthly chart values from rupees to paise, but the dashboard page does not use this hook.
8. The `/accounts` page performs two independent fetches: one raw `fetch('/api/accounts')` for computed accounts and one via `useManagedAccounts()` for persistent accounts — there is no unified endpoint.
9. The `/cards` page similarly dual-fetches: `useCards()` for card summaries and `useStatementsQuery()` for statement history.
10. `forecast/page.tsx` and `behaviour/page.tsx` are missing — only `workspace-page.tsx` exists at those routes, making them unreachable via normal navigation without explicit import.
11. The dashboard aggregates data from multiple independent endpoints (`/api/dashboard/summary`, `/api/behavior/score`, `/api/behavior/insights`, `/api/analytics`) with no single source of truth.
12. Seven workspace router/service pairs on the backend (`/api/v1/*`) have frontend capability hooks but no corresponding thin `page.tsx` wrappers except for net-worth, cashflow, and behaviour.
13. `types/index.ts` re-exports from `api-generated.ts` but the generated types have `unknown` response bodies — they provide no compile-time safety.
14. Card validation in `cards/page.tsx` hardcodes `http://localhost:8000` instead of using `API_BASE`, breaking proxy and production deployments.
15. The `useAccountsCapability` hook fetches from `/api/v1/accounts` while `useManagedAccounts` fetches from `/api/accounts/manage` — these are semantically different data sets (computed vs persistent) but share the same route name domain.

---

## 12. ACTION ITEMS

| Priority | Item | File(s) | Effort |
|---|---|---|---|
| P0 | Resolve route conflicts (page.tsx vs workspace-page.tsx) | accounts, loans, cards, investments, reconciliation | Low — rename or delete one |
| P0 | Create forecast/page.tsx thin wrapper | app/forecast/ | Low |
| P0 | Create behaviour/page.tsx thin wrapper | app/behaviour/ | Low |
| P1 | Eliminate frontend paise↔rupee arithmetic | hooks/use-cards.ts, use-reconciliation.ts, use-overview.ts, app/pages | Medium — fix backend contract or centralize converter |
| P1 | Consolidate dual-fetch patterns | accounts/page.tsx, cards/page.tsx | Medium — add unified endpoint or merge data client-side |
| P1 | Remove dormant hooks | use-overview.ts, use-behavior-score.ts, use-behavior-insights.ts, use-analytics.ts | Low — verify no consumer then delete |
| P2 | Decide canonical type source strategy | types/api.ts vs api-generated.ts | Medium — either enrich generated or deprecate |
| P2 | Fix hardcoded localhost in cards validation | app/cards/page.tsx | Trivial |
| P3 | Standardize all pages to use capability+workspace pattern | accounts, loans, cards, investments, reconciliation | High — systematic migration |
