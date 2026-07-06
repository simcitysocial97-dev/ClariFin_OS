# Phase 3 — Architecture Consolidation & Canonical API Stabilization Report

## Overview

This report documents the current state of architectural migration for ClariFin_OS. The Phase 1 canonical monetary architecture has been established, but several endpoints, DTOs, hooks, formatters, and frontend components remain outside the canonical pipeline.

---

## Deliverable 1: Remaining Legacy Endpoints

### Endpoints NOT Using Canonical Mapper Pipeline

| # | Endpoint | Status | Mapper Used | Issue |
|---|----------|--------|-------------|-------|
| 1 | `GET /api/transactions` | ⚠️ **LEGACY** | ❌ None (uses `enrich_transaction()`) | Manually divides `amount_paise / 100` at line 182, returns `amount` (rupees) field |
| 2 | `GET /api/overview` | ⚠️ **LEGACY** | ❌ None (manual construction) | All monetary fields are rupees only: `total_spend`, `this_month`, `last_month`, `monthly_average`. No `_paise` fields returned. Docstring lies ("Returns both _paise and _rupees"). |
| 3 | `GET /api/categories` | ⚠️ **LEGACY** | ❌ None (manual construction) | Returns `amount` (rupees), `percentage`, `amount_display`. No `_paise` fields. |
| 4 | `GET /api/analytics` | ⚠️ **LEGACY** | ❌ None (manual construction) | Returns `amount` (rupees), `avg_monthly`, etc. No `_paise` fields. |
| 5 | `GET /api/statements` | ⚠️ **LEGACY** | ❌ None (manual construction) | Returns `total_debit`, `total_credit`, `total_due`, `min_due` as rupees from DB. No `_paise` fields in response. |
| 6 | `GET /api/accounts/{account_id}/balance` | ⚠️ **LEGACY** | ❌ Raw engine result | Returns whatever `compute_account_balance()` returns. No DTO transformation. |
| 7 | `GET /api/accounts/{account_id}/running-balance` | ⚠️ **LEGACY** | ❌ Raw engine result | Returns raw `compute_running_balance()` output. No DTO transformation. |
| 8 | `GET /api/statements/{statement_id}/validate` | ⚠️ **LEGACY** | ❌ Raw engine result | Returns raw `validate_statement_balance()` output. |
| 9 | `GET /api/behavior/summary` | ⚠️ **LEGACY** | ❌ Raw profile | Returns raw `compute_behavior_profile()` output. |
| 10 | `GET /api/behavior/score` | ⚠️ **LEGACY** | ❌ Manual construction | Manually extracts indices from profile. Returns `financial_health_score`, `components` with plain scores. |
| 11 | `GET /api/behavior/insights` | ⚠️ **LEGACY** | ❌ Raw engine output | Returns raw insights/nudges from engine. |
| 12 | `GET /api/reconciliations` | ⚠️ **LEGACY** | ❌ Manual enrichment | Manually adds `amount_display`, `confidence_display`. Uses `amount` (rupees) from DB. |
| 13 | `GET /api/reconciliations/scan` | ⚠️ **LEGACY** | ❌ Raw engine output | Returns raw `find_potential_matches()` with manual enrichment of `amount_display`, `confidence_display`. |
| 14 | `POST /api/reconciliations/create` | ⚠️ **LEGACY** | ❌ | Takes `amount` parameter in rupees. |
| 15 | `GET /api/export/csv` | ⚠️ **LEGACY** | ❌ | Exports raw `amount` from DB (legacy rupees). |
| 16 | `GET /api/dashboard/summary` | ✅ **MIGRATED** | ✅ DashboardMapper | Returns canonical `_paise` fields. Only migrated endpoint besides `/api/accounts`. |
| 17 | `GET /api/accounts` | ✅ **MIGRATED** | ✅ AccountMapper | Returns both `balance_paise` and `balance_rupees`. |
| 18 | `GET/POST/PUT/DELETE /api/accounts/manage` | ⚠️ **LEGACY** | ❌ In-memory store | Uses `balance` (rupees) field. No paise. In-memory store loses data on restart (known bug R6). |
| 19 | `GET /api/audit/report` | ⚠️ **LEGACY** | ❌ Raw engine output | Non-financial, lower priority. |

### Summary: 16 out of 19 financial endpoints remain unmigrated.

---

## Deliverable 2: Remaining Duplicate Hooks

### Hook Inventory (frontend/lib/hooks/)

| File | Type | Endpoints Called | Status |
|------|------|------------------|--------|
| `use-async-query.ts` | React Query wrapper | Generic | ✅ Core wrapper |
| `use-async-mutation.ts` | React Query wrapper | Generic | ✅ Core wrapper |
| `use-query-finance.ts` | React Query hooks | `/api/overview`, `/api/behavior/score`, `/api/networth`, `/api/networth/trend`, `/api/cashflow/monthly`, `/api/cashflow/breakdown`, `/api/investments/allocation`, `/api/investments/summary`, `/api/loans`, `/api/recurring`, `/api/v2/imports` | ✅ Primary query hooks |
| `use-dashboard-metrics.ts` | React Query hook | `/api/dashboard/summary` | ✅ Dashboard metrics |
| `use-toast.ts` | Utility hook | None | ✅ Not a data hook |

### Duplicate Hook Analysis

**Previous audit identified:** 13 legacy hooks, 11 React Query hooks, 2 duplicate pairs (overview, networth).

**Current state:** The legacy hooks appear to have been removed. The `frontend/hooks/` directory now only contains `use-toast.ts`. All data-fetching hooks are in `frontend/lib/hooks/`.

**Verdict:** The React Query consolidation appears complete. No duplicate hooks remain. However, the `use-query-finance.ts` hooks shadow `use-dashboard-metrics.ts` — the dashboard metrics hook duplicates some functionality of the overview query. This should be investigated.

- `useDashboardMetricsQuery` (in `use-dashboard-metrics.ts`) calls `/api/dashboard/summary`
- `useOverviewQuery` (in `use-query-finance.ts`) calls `/api/overview`
- These are DIFFERENT endpoints, so NOT a true duplicate.
- But the frontend components may be using both for overlapping purposes.

---

## Deliverable 3: Remaining Duplicate DTOs

### Frontend Type Interface Duplications

| Interface | File | Fields | Status |
|-----------|------|--------|--------|
| `OverviewData` | `lib/api/client.ts:48` | `total_spend`, `this_month`, `last_month` (all rupees) | ❌ Defined inline, not in types/ |
| `Statement` | `lib/api/client.ts:75` | `total_debit_paise`, `total_credit_paise` | ✅ Has paise fields |
| `CategorySummary` | `types/api.ts:12` | `amount_paise`, `amount` (deprecated), `amount_display` | ⚠️ Has both paise and rupees |
| `AnalyticsData` | `types/api.ts:65` | `avg_monthly`, `biggest_txn_amount` (no paise suffix) | ❌ No paise fields |
| `MonthlyBreakdown` | `types/api.ts:27` | `amount` (no suffix) | ❌ No paise field |
| `DayOfWeekData` | `types/api.ts:32` | `amount` (no suffix) | ❌ No paise field |
| `MerchantData` | `types/api.ts:37` | `amount` (no suffix) | ❌ No paise field |
| `RecurringCharge` | `types/api.ts:46` | `avg_amount` (no suffix) | ❌ No paise field |
| `LargestTransaction` | `types/api.ts:56` | `amount` (no suffix) | ❌ No paise field |
| `Transaction` | `types/transaction.ts:11` | `amount_paise` (canonical), `amount_rupees` (deprecated) | ✅ Has paise fields |
| `AccountBalance` | `types/transaction.ts:49` | `balance_paise` | ✅ |
| `RunningBalanceEntry` | `types/transaction.ts:63` | `debit_paise`, `credit_paise`, `balance_paise` | ✅ |
| `StatementValidation` | `types/transaction.ts:76` | `computed_balance_paise`, `claimed_balance_paise`, `difference_paise` | ✅ |
| `Metadata` | `types/transaction.ts:103` | `creditLimit`, `totalAmountDue`, `minimumAmountDue` (no suffix) | ❌ Legacy card metadata, non-paise naming |
| `ParseResult.validation` | `types/transaction.ts:120` | `calculatedTotal`, `expectedTotal`, `bankTotal`, `difference` (no suffix) | ❌ |

### Backend DTOs

| DTO Class | File | Fields | Status |
|-----------|------|--------|--------|
| `AccountDTO` | `core/dtos/account_dto.py` | `balance_paise` (canonical), `balance_rupees` (deprecated) | ✅ |
| `AccountListResponse` | `core/dtos/account_dto.py` | `total_balance_paise` | ✅ |
| `TransactionDTO` | `core/dtos/transaction_dto.py` | `amount_paise` | ✅ (expected) |
| `DashboardSummaryDTO` | `core/dtos/dashboard_dto.py` | `net_cash_flow_paise`, `total_income_paise`, `total_expenses_paise`, `emi_paise` | ✅ |
| `OverviewDTO` | `core/dtos/dashboard_dto.py` | `total_spend_paise`, `this_month_paise`, `last_month_paise`, `monthly_average_paise` | ✅ |
| `CategoryBreakdownDTO` | `core/dtos/dashboard_dto.py` | `amount_paise`, `total_paise` | ✅ |

### Key Duplication Issues

1. **`OverviewData`** defined inline in `client.ts` but NO equivalent in `types/` — there is no shared canonical type for overview data.
2. **`CategorySummary.amount`** (deprecated rupees) still exists alongside `amount_paise`.
3. **`AnalyticsData`** fields all lack `_paise` suffix — these don't mirror the canonical DTO pattern.
4. **`Metadata`** uses camelCase card field names (`creditLimit`, `totalAmountDue`) instead of snake_case with paise suffix.
5. **`ParseResult.validation`** uses `calculatedTotal`, `expectedTotal` without paise suffix.

---

## Deliverable 4: Remaining Compatibility Fields

### Backend Compatibility Fields

| Field | Location | Purpose | Status |
|-------|----------|---------|--------|
| `balance_rupees` | `AccountDTO` | Backward compat during migration | **Still required** — `/api/accounts` endpoint needs checking if frontend still consumes it |
| `balance_rupees` | `AccountMapper` | Created during mapping | **Still required** — see above |
| `net_cash_flow_rupees` | `DashboardMapper` | Backward compat during migration | **Still required** |
| `total_spend_rupees` | `DashboardMapper` | Backward compat during migration | **Still required** |
| `amount_rupees` (expected) | `TransactionMapper` | Backward compat during migration | **Still required** (verify) |

### Frontend Compatibility Fields

| Field | Location | Purpose | Status |
|-------|----------|---------|--------|
| `amount_rupees` | `Transaction` type | Backward compat | **Still required** — frontend may still consume |
| `amount` | `CategorySummary` | Backward compat | **Still required** |
| `total_debit`, `total_credit`, `total_due` | `Statement` type | Backward compat in client.ts | **Still required** |
| `net_cash_flow_rupees` | (expected in types) | Backward compat | **Verify** |

### Safe Removal Candidates

None of the compatibility fields can be safely removed yet due to the large number of unmigrated endpoints and consumers.

---

## Deliverable 5: Remaining Formatting Violations

### Components NOT Using `formatINR()`

| File | Line(s) | Violation | Severity |
|------|---------|-----------|----------|
| `frontend/lib/format.ts` | 10-55 | **Duplicate formatter** — `formatCompactCurrency()`, `formatDisplayAmount()`, `formatCurrency()` exist alongside canonical `formatINR()` in `lib/utils/format.ts` | 🔴 **HIGH** — Two formatter systems |
| `frontend/app/accounts/page.tsx` | 58, 309 | **Duplicate formatINR** — Inline `formatINR` implementation copied into page component | 🔴 **HIGH** — Should import from `lib/utils/format.ts` |
| `frontend/app/accounts/page.tsx` | 136 | `initialData.balance_paise / 100` — **Manual division by 100** in form field | 🔴 **HIGH** |
| `frontend/components/dashboard/spending-overview.tsx` | 60-65 | **Custom formatting** — `rupees = paise / 100` then manual L/K formatting | 🟡 **MEDIUM** — Should use canonical formatter |
| `frontend/components/dashboard/bank-wise-chart.tsx` | 67 | `value / 1000` for chart tick formatting | 🟢 **LOW** — Chart axis formatting, not monetary |
| `frontend/app/cards/page.tsx` | 98-105 | Manual `Math.round(card.totalAmountDue * 100)` then `formatINR()` | 🟡 **MEDIUM** — Converts rupees→paise manually, should use `rupeesToPaise()` |

### Frontend Formatter Inventory

| Formatter | File | Parameters | Canonical? |
|-----------|------|-----------|------------|
| `formatINR(paise)` | `lib/utils/format.ts:25` | paise (int) | ✅ **Canonical** |
| `formatPaise(paise)` | `lib/utils/format.ts:71` | paise (int) | ✅ Alias for formatINR |
| `rupeesToPaise(rupees)` | `lib/utils/format.ts:87` | rupees (float) | ✅ Conversion utility |
| `paiseToRupees(paise)` | `lib/utils/format.ts:102` | paise (int) | ✅ Conversion utility |
| `formatPercentage(value)` | `lib/utils/format.ts:114` | value (float) | ✅ Percentage formatter |
| `formatDateDisplay(dateStr)` | `lib/utils/format.ts:126` | dateStr (string) | ✅ Date formatter |
| `truncateText(text)` | `lib/utils/format.ts:164` | text (string) | ✅ Text utility |
| `formatCompactCurrency(value)` | `lib/format.ts:10` | paise (int) | 🔴 **DUPLICATE** — Same as formatINR but with compact notation (L, K) |
| `formatDisplayAmount(value)` | `lib/format.ts:38` | paise (int) | 🔴 **DUPLICATE** — Another INR formatter |
| `formatCurrency(value)` | `lib/format.ts:65` | paise (int) | 🔴 **DUPLICATE** — Yet another INR formatter |
| `format_inr(amount)` | `backend/api.py:77` | rupees (float) | 🔴 **LEGACY** — Backend-only, uses rupees input, not paise |

### Backend Formatting Violations

| File | Line | Violation | Severity |
|------|------|-----------|----------|
| `backend/src/api.py:182` | `amount = amount_paise / 100` | **Manual division by 100** in `enrich_transaction()` | 🔴 **HIGH** — This is the root cause of all downstream rupees values |
| `backend/src/api.py:77` | `format_inr(amount)` | **Legacy formatter** — Takes rupees float, not paise int | 🟡 **MEDIUM** — Used for display only, but doesn't match canonical pattern |

---

## Deliverable 6: Remaining Architecture Violations

### Violation 1: Business Logic in Controllers

**File:** `backend/src/api.py`

| Function | Lines | Issue |
|----------|-------|-------|
| `enrich_transaction()` | 178-194 | **Business logic** — Computes derived display fields, converts paise→rupees. Should be in a service or mapper. |
| `compute_behavioral_insights()` | 212-301 | **Business logic** — Category drift analysis, spending trends, largest expense computation. ~90 lines of domain logic in controller. |
| `compute_is_large()` | 197-209 | **Business logic** — Computes average debit, flags large transactions. |
| `/api/overview` handler | 401-520 | **Business logic** — Manual metric computation (monthly totals, category charts, bank charts, behavioral insights). |
| `/api/categories` handler | 522-607 | **Business logic** — Manual category aggregation, monthly breakdown, percentage computation. |
| `/api/analytics` handler | 609-753 | **Business logic** — Manual analytics computation (spending trends, day-of-week, top merchants, recurring detection). |

These 6 functions/endpoints contain business logic that belongs in domain services.

### Violation 2: Raw Engine Responses Without DTO Layer

| Endpoint | Returns | Issue |
|----------|---------|-------|
| `GET /api/accounts/{account_id}/balance` | Raw `compute_account_balance()` dict | No DTO mapping, might leak internal structure |
| `GET /api/accounts/{account_id}/running-balance` | Raw `compute_running_balance()` list | No DTO mapping, `_paise` fields embedded in raw output |
| `GET /api/behavior/summary` | Raw `compute_behavior_profile()` | No DTO, internal structure exposed |
| `GET /api/behavior/insights` | Raw insight/nudge dicts | No DTO |
| `GET /api/reconciliations/scan` | Raw match dicts | No DTO |

### Violation 3: Controller Returns Rupees Instead of Paise

5 of the 6 unmigrated financial endpoints (`/api/overview`, `/api/categories`, `/api/analytics`, `/api/statements`, `/api/transactions`) all return monetary values as rupees floats (via `enrich_transaction()` or manual `sum(t.get("amount"))`).

The canonical architecture requires `_paise` suffix for all monetary API fields.

### Violation 4: In-Memory State Store

| File | Lines | Issue |
|------|-------|-------|
| `backend/src/api.py:1594-1595` | `_accounts_store`, `_account_id_counter` | **Mutable global state** — Loses data on restart, no paise support, bypasses canonical architecture |

### Violation 5: Backend Duplicate Formatter

`backend/src/api.py:77` defines `format_inr()` which is separate from the frontend's `formatINR()`. This is not necessarily a violation (different languages), but NOTE: it takes **rupees** (float), not **paise** (int), which is architecturally inconsistent with the canonical policy.

### Violation 6: Frontend Duplicate Formatter System

`frontend/lib/format.ts` contains 3 currency formatting functions that duplicate the canonical `formatINR()` in `frontend/lib/utils/format.ts`.

---

## Deliverable 7: Safe Removal Candidates for Phase 4

### Safe to Remove (No Internal Consumers)

| # | Item | Location | Reason |
|---|------|----------|--------|
| 1 | `balance_rupees` field | Backend `AccountDTO` | Only used by legacy frontend consumers — after endpoint migration, all consumers should use `balance_paise` |
| 2 | `amount_rupees` field | Backend `TransactionDTO` | Same as above |
| 3 | `net_cash_flow_rupees` field | Backend `DashboardSummaryDTO` | Same as above |
| 4 | `total_spend_rupees` field | Backend `OverviewDTO` | Same as above |
| 5 | `amount_rupees` field | Frontend `Transaction` type | After frontend migration to `amount_paise` |
| 6 | `amount` field | Frontend `CategorySummary` type | After frontend migration to `amount_paise` |
| 7 | `total_debit`, `total_credit`, `total_due` | Frontend `Statement` type (compat fields) | After statement endpoint migration |
| 8 | `updateTransactionCategory()` | Frontend `client.ts:274` | Endpoint was removed (see api.py line 1042-1046) — **DEAD CODE** |
| 9 | `deleteStatement()` | Frontend `client.ts:290` | Endpoint was removed — **DEAD CODE** |
| 10 | `formatCompactCurrency()` | Frontend `lib/format.ts` | Duplicate of `formatINR()` |

### Still Required (Consumers Exist)

| # | Item | Location | Reason |
|---|------|----------|--------|
| 1 | `format_inr()` | Backend `api.py:77` | Used by `enrich_transaction()` and legacy endpoints |
| 2 | `enrich_transaction()` | Backend `api.py:178` | Used by `/api/transactions`, `/api/overview`, `/api/categories`, `/api/analytics`, `/api/dashboard/summary` |
| 3 | `balance_rupees` | Frontend (verify) | May still be consumed by dashboard components |

### Blocked by Remaining Consumers

| # | Item | Blocked By | Notes |
|---|------|-----------|-------|
| 1 | `_accounts_store` | R6 (in-memory store) | All managed account endpoints depend on it. Need DB-backed store first. |
| 2 | `db.get_all_transactions_with_bank()` returning `amount` (rupees) | All legacy endpoints | 16 endpoints depend on rupees fields in raw DB results |

---

## Deliverable 8: Risks Identified

### 🔴 High Risk

| # | Risk | Description | Mitigation |
|---|------|-------------|------------|
| 1 | **R1: enrich_transaction() is everywhere** | `enrich_transaction()` is the root cause of all rupees propagation — it divides `amount_paise` by 100. Changing it breaks 5 endpoints + dashboard. | Migrate all 5 consumer endpoints to use TransactionMapper before changing or removing `enrich_transaction()`. |
| 2 | **R2: In-memory store bypasses architecture** | `_accounts_store` stores `balance` as rupees float, no paise, no persistence. Any code depending on `GET /api/accounts/manage` gets non-canonical data. | Replace with DB-backed store that uses paise. |
| 3 | **R3: Dual formatter system** | `lib/format.ts` and `lib/utils/format.ts` both format INR. `spending-overview.tsx` uses `lib/format.ts` and manually divides by 100. This risks inconsistent formatting. | Consolidate to `formatINR()` only. Remove `lib/format.ts`. |

### 🟡 Medium Risk

| # | Risk | Description | Mitigation |
|---|------|-------------|------------|
| 4 | **R4: Business logic in controllers** | `compute_behavioral_insights()` and manual aggregation in `/api/overview`, `/api/categories`, `/api/analytics` make the code hard to test and maintain. | Extract to domain services. |
| 5 | **R5: Frontend types don't mirror backend** | `AnalyticsData` has no `_paise` fields. `OverviewData` is inline in `client.ts`. This creates maintenance burden. | Define shared types in `types/` directory that exactly mirror backend DTOs. |
| 6 | **R6: TransactionMapper exists but unused** | `TransactionMapper` is defined in `core/mappers/transaction_mapper.py` but NO endpoint uses it. This represents wasted investment. | Migrate `/api/transactions` to use TransactionMapper. |

### 🟢 Low Risk

| # | Risk | Description | Mitigation |
|---|------|-------------|------------|
| 7 | **R7: Dead API functions** | `updateTransactionCategory()` and `deleteStatement()` in `client.ts` call endpoints that no longer exist (removed for ledger immutability). These will cause 404s if called. | Remove or mark as deprecated. |
| 8 | **R8: Chart formatting inconsistency** | `bank-wise-chart.tsx` and `spending-overview.tsx` use manual formatting for chart ticks. Chart.js/Recharts may not support `formatINR()` directly. | Create a chart-oriented wrapper around `formatINR()`. |

---

## Deliverable 9: Recommended Cleanup Order

### Phase 4 — Step 1: Migrate Remaining Endpoints (HIGHEST PRIORITY)

This should be done in dependency order:

```
Migration Order:
 1. /api/transactions → Use TransactionMapper
    (Blocked by: Nothing — TransactionMapper already exists)
 
 2. /api/statements → Create StatementDTO & StatementMapper
    (DB returns rupees; need to fix at DB layer or add conversion)
 
 3. /api/overview → Use OverviewDTO via DashboardMapper
    (Migrate from manual construction to DashboardMapper.to_overview_dto())
 
 4. /api/categories → Use CategoryBreakdownDTO via DashboardMapper
    (Migrate from manual construction to mapper)
 
 5. /api/analytics → Create AnalyticsDTO & AnalyticsMapper
    (No existing DTO for analytics; needs creation)
 
 6. Remove enrich_transaction() after all consumers migrated
```

### Phase 4 — Step 2: Consolidate Formatters

```
 1. Remove lib/format.ts (duplicate formatter system)
 2. Update spending-overview.tsx to use lib/utils/format.ts
 3. Remove inline formatINR from accounts/page.tsx
 4. Remove /100 violations in accounts/page.tsx
```

### Phase 4 — Step 3: Extract Business Logic

```
 1. Move compute_behavioral_insights() to domain service
 2. Move compute_is_large() to domain service
 3. Create OverviewService for /api/overview business logic
 4. Create CategoryService for /api/categories business logic
 5. Create AnalyticsService for /api/analytics business logic
```

### Phase 4 — Step 4: Fix Frontend Types

```
 1. Add paise fields to AnalyticsData
 2. Move OverviewData to types/ directory
 3. Add paise suffix to all monetary fields in types/api.ts
 4. Remove deprecated fields after verifying no consumers
```

### Phase 4 — Step 5: Clean Up

```
 1. Remove dead API functions (updateTransactionCategory, deleteStatement)
 2. Remove compatibility fields after all consumers migrated
 3. Replace _accounts_store with DB-backed store
```

---

## Summary Statistics

| Category | Count |
|----------|-------|
| Total API endpoints | 33 |
| Migrated to canonical mapper pipeline | 2 (6%) |
| Still using legacy monetary handling | 16 (48%) |
| Non-financial endpoints (no migration needed) | 15 (46%) |
| Duplicate hook pairs | 0 (✅ resolved since Phase 2 audit) |
| Duplicate DTOs/interfaces | 5 |
| Compatibility fields remaining | ~8 |
| Formatting violations (HIGH) | 4 |
| Formatting violations (MEDIUM) | 2 |
| Architecture violations | 6 categories |
| Safe removal candidates | 10 |
| Blocked removal candidates | 3 |

---

## Conclusion

**Phase 2 migrations** successfully established the canonical architecture for **2 endpoints** (`/api/accounts`, `/api/dashboard/summary`) and created the mapper/DTO infrastructure.

**Phase 3** reveals that **16 of 18 financial endpoints** still return legacy rupees values, and **5 controller functions** contain business logic that belongs in services.

**The migration is approximately 10% complete by endpoint count.**

The TransactionMapper exists but is unused. The DashboardMapper exists but only `/api/dashboard/summary` uses it. The majority of the API surface still flows through `enrich_transaction()` which divides `amount_paise / 100` on every response, undoing the canonical paise architecture at the API layer.

The recommended Phase 4 order is: **Endpoints → Formatters → Business Logic → Types → Cleanup**, starting with `/api/transactions` which has a ready-made mapper waiting to be used.

---

*Report generated: 2026-07-05*
*Architecture consolidation audit for Phase 3 completion milestone.*