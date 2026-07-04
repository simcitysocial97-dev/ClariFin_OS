# ═══════════════════════════════════════════════════════════════
# COMPREHENSIVE FRONTEND CODEBASE AUDIT REPORT
# ═══════════════════════════════════════════════════════════════

## FILE COUNT
- Total TypeScript files: 202
- Total exports found: 307
- Total imports found: 611

## TYPESCRIPT ERRORS SUMMARY
- Total errors: 228
- Module not found: 0
- Export not found: 2
- Type mismatches: 152 (TS2339, TS2769, TS2349, TS2554)
- Unused variables/parameters: 28 (TS6133, TS6198)
- Other: 51 (TS2451, TS7006)

## ERRORS BY FILE

### lib/hooks/use-finance-data.ts (27 errors)
- Line 65, 81, 97, 153, 209, 225, 261, 317, 333, 349, 401, 417, 445, 485, 501, 517, 593, 609, 625, 702, 718, 734, 770, 786, 802: Unused parameters (TS6133, TS6198)
- Line 417-429, 445-456: Type mismatch - queryFn signature incorrect (TS2769)

### app/accounts/page.tsx (22 errors)
- Line 134-137, 142-144, 201, 215, 218-224, 229, 235, 237: Property does not exist on type 'never' (TS2339)
- Line 134-137: Cannot redeclare block-scoped variable 'accounts' (TS2451)

### app/loans/page.tsx (21 errors)
- Line 45-48, 58-64, 136, 195: Property does not exist on type 'never' (TS2339)
- Line 58, 64, 67-68, 136, 195: Implicit any type (TS7006)
- Line 58, 64: Expected 0 arguments, but got 1 (TS2554)

### app/cards/page.tsx (15 errors)
- Line 139-142, 147-151, 235, 240, 250: Property does not exist on type 'never' (TS2339)
- Line 147-151, 235, 240, 250: Implicit any type (TS7006)

### app/transactions/page.tsx (11 errors)
- Line 109-119, 167, 556, 565-566: Property does not exist on type 'never' (TS2339)
- Line 109, 119: Expected 0 arguments, but got 1 (TS2554)
- Line 556, 565-566: Implicit any type (TS7006)

### components/recurring/subscriptions-table.tsx (9 errors)
- Line 43-46: Property does not exist on type 'never' (TS2339)

### components/income/income-streams-table.tsx (9 errors)
- Line 109-114: Property does not exist on type 'never' (TS2339)

### components/snapshots/snapshot-trigger-card.tsx (8 errors)
- Line 13-15: Property does not exist on type 'never' (TS2339)

### components/projections/whatif-simulator.tsx (6 errors)
- Line 40-41, 46, 178: Property does not exist on type 'never' (TS2339)
- Line 46, 178: This expression is not callable (TS2349)

### components/networth/networth-history-chart.tsx (6 errors)
- Line 82, 120-121: Property does not exist on type 'never' (TS2339)
- Line 120-121: Implicit any type (TS7006)

### components/cashflow/cashflow-chart.tsx (6 errors)
- Line 107-108, 111-112: Property does not exist on type 'never' (TS2339)
- Line 107, 112: Expected 0 arguments, but got 1 (TS2554)

### app/dashboard/page.tsx (6 errors)
- Line 87-89: Property does not exist on type 'never' (TS2339)

### app/categories/page.tsx (6 errors)
- Line 89, 211, 297: Property does not exist on type 'never' (TS2339)
- Line 89, 211, 297: Implicit any type (TS7006)
- Line 89: Expected 0 arguments, but got 1 (TS2554)

### components/upload/upload-modal.tsx (4 errors)
- Line 11: **Export not found** - `useUpload` not exported from `@/lib/hooks/use-finance-data` (TS2305)
- Line 11: **Export not found** - `useOverview` not exported from `@/lib/hooks/use-finance-data` (TS2305)
- Line 37-38: Property does not exist on type 'never' (TS2339)

## PATH ALIAS CONFIGURATION
- tsconfig.json aliases configured: **YES**
  - `@/*` maps to `./*`
- next.config.ts properly set up: **NO**
  - Missing webpack alias configuration for `@/*` path

## ORPHANED/UNUSED EXPORTS ANALYSIS

### Lib Modules - Existing vs Imported
**Existing lib modules:**
- format
- use-accounts
- use-api-error
- use-async-mutation
- use-async-query
- use-cards
- use-finance-data
- use-queries
- use-query-finance
- utils

**Lib modules actually imported:**
- api/client
- context/member-context
- format
- hooks/use-finance-data
- hooks/use-query-finance
- providers/query-provider
- store/use-app-store
- utils

### Potentially Orphaned Exports
The following lib modules are **NOT directly imported** (may be used via re-exports):
- `use-accounts` - Functions exist in `use-finance-data.ts` instead
- `use-api-error` - May be unused
- `use-async-mutation` - May be unused
- `use-async-query` - May be unused
- `use-cards` - Functions exist in `use-finance-data.ts` instead
- `use-queries` - May have duplicate `useImportsQuery` in `use-query-finance.ts`
- `hooks/use-query-finance` - Used for typed query hooks
- `providers/query-provider` - Used in layout.tsx
- `store/use-app-store` - Used in sidebar.tsx
```

## MASTER FIX PLAN

### GROUP 1 - Missing Files/Exports (CREATE THESE)
1. `useUpload` hook in `lib/hooks/use-finance-data.ts`
   - Should handle file upload functionality
   - Return type: `{ upload, uploading, progress }`
2. `useOverview` hook in `lib/hooks/use-finance-data.ts`
   - Should return overview data
   - Return type: `{ data, isLoading, error }`

### GROUP 2 - Type Definition Issues (UPDATE HOOKS)
All hooks in `lib/hooks/use-finance-data.ts` need proper generic type parameters:
- `useAccounts()` - needs `useQuery<Account[]>` type
- `useCards()` - needs `useQuery<Card[]>` type
- `useLoans()` - needs `useQuery<Loan[]>` type
- `useTransactions()` - needs `useQuery<Transaction[]>` type
- `useCategories()` - needs `useQuery<Category[]>` type
- `useInvestments()` - needs `useQuery<Investment[]>` type
- `useRecurringTransactions()` - needs `useQuery<RecurringTransaction[]>` type
- `useSnapshots()` - needs `useQuery<Snapshot[]>` type
- `useCashflow()` - needs `useQuery<Cashflow[]>` type
- `useAnalytics()` - needs `useQuery<Analytics>` type
- `useNetWorth()` - needs `useQuery<NetWorth>` type
- `useNetWorthForecast()` - needs `useQuery<Forecast[]>` type
- `useAmortizationSchedule()` - needs `useQuery<AmortizationEntry[]>` type
- `useStatements()` - needs `useQuery<Statement[]>` type
- `useIncomeStreams()` - needs `useQuery<IncomeStream[]>` type
- `useRecurringCharges()` - needs `useQuery<RecurringCharge[]>` type
- `useV2Imports()` - needs `useQuery<ImportItem[]>` type
- `useCalculateGoal()` - needs proper queryFn signature fix
- `useCalculateWhatIf()` - needs proper queryFn signature fix

### GROUP 3 - Dead Code (ARCHIVE/DELETE)
- `lib/hooks/use-accounts.ts` - Duplicate exports exist in `use-finance-data.ts`
- `lib/hooks/use-cards.ts` - Duplicate exports exist in `use-finance-data.ts`
- `lib/hooks/use-queries.ts` - Duplicate `useImportsQuery` and `useOverviewQuery` exist in `use-query-finance.ts`
- `lib/hooks/use-async-mutation.ts` - May be replaced by `useAsyncMutation` in `use-finance-data.ts`
- `lib/hooks/use-async-query.ts` - May be replaced by `useAsyncQuery` in `use-finance-data.ts`

### GROUP 4 - Circular Dependencies (REFACTOR)
No circular dependencies detected in the current error set.

## RECOMMENDED APPROACH

**Option A: Quick Fix (Recommended)**
1. Add missing `useUpload` and `useOverview` exports to `use-finance-data.ts`
2. Add proper generic type parameters to all hooks in `use-finance-data.ts`
3. Fix `useCalculateGoal` and `useCalculateWhatIf` queryFn signatures
4. Remove duplicate hook files (`use-accounts.ts`, `use-cards.ts`, `use-queries.ts`)
5. Update `next.config.ts` to add webpack alias for `@/*` path

**Option B: Full Cleanup**
- All of Option A plus:
- Consolidate all hook logic into a single file
- Add proper TypeScript interfaces for all data types
- Remove unused `__test` exports
- Add proper error handling and loading states

## AFFECTED FILES SUMMARY
- lib/hooks/use-finance-data.ts (27 errors)
- app/accounts/page.tsx (22 errors)
- app/loans/page.tsx (21 errors)
- app/cards/page.tsx (15 errors)
- app/transactions/page.tsx (11 errors)
- components/recurring/subscriptions-table.tsx (9 errors)
- components/income/income-streams-table.tsx (9 errors)
- components/snapshots/snapshot-trigger-card.tsx (8 errors)
- components/projections/whatif-simulator.tsx (6 errors)
- components/networth/networth-history-chart.tsx (6 errors)
- components/cashflow/cashflow-chart.tsx (6 errors)
- app/dashboard/page.tsx (6 errors)
- app/categories/page.tsx (6 errors)
- components/upload/upload-modal.tsx (4 errors)
- components/snapshots/snapshot-history-table.tsx (4 errors)
- components/recurring/upcoming-bills-timeline.tsx (4 errors)
- components/recurring/monthly-obligations-summary.tsx (4 errors)
- components/income/income-trend-chart.tsx (4 errors)
- components/projections/networth-forecast.tsx (5 errors)
- components/networth/assets-liabilities-columns.tsx (3 errors)
- components/income/income-summary-cards.tsx (3 errors)
- app/investments/page.tsx (3 errors)
- app/settings/page.tsx (2 errors)
- app/analytics/page.tsx (2 errors)
- components/loans/loan-form.tsx (2 errors)
- components/investments/investment-form.tsx (2 errors)
- components/import/import-history-list.tsx (2 errors)
- components/projections/goal-planner.tsx (3 errors)

---
**WAITING FOR USER DECISION before proceeding with fixes.**