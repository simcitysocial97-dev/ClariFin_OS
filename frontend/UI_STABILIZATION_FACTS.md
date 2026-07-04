# ClariFin OS - Frontend UI Stabilization Facts

> **Purpose:** Baseline documentation for future tasks. No guessing. No hallucinating.
> **Last Updated:** 2026-01-03
> **Scope:** Frontend ONLY (Next.js 16.1.6, React 19.2.3, TypeScript 5)

---

## Commands

From `frontend/package.json`:

```json
{
  "dev": "next dev",
  "build": "next build",
  "start": "next start",
  "lint": "eslint",
  "test": "playwright test",
  "test:ui": "playwright test --ui",
  "test:debug": "playwright test --debug",
  "test:parser": "npx tsx scripts/test-semantic-parser.ts",
  "test:metadata:generate": "node scripts/generate-expected-metadata.js",
  "test:metadata": "npx tsx scripts/test-metadata.ts",
  "validate": "cd ../backend && ./venv/bin/python -m src.validate_pipeline"
}
```

**Note:** No explicit `typecheck` script exists. Use `npx tsc --noEmit` for type checking.

---

## API Client Functions (existing)

Source: `frontend/lib/api/client.ts` (69 total functions)

### Transactions
- `fetchTransactions(params?)` - Filterable list with pagination
- `updateTransactionCategory(id, category, subcategory?)` - Update category only

### Loans
- `fetchLoans(status?)`, `fetchLoan(loanId)` - List/detail
- `createLoan(data)`, `updateLoan(loanId, data)`, `deleteLoan(loanId)` - CRUD
- `fetchLoanPayments(loanId)`, `createLoanPayment(loanId, data)` - Payments
- `fetchAmortizationSchedule(loanId)`, `fetchLoanSummary(loanId)` - Analytics
- `simulatePrepayment(loanId, data)` - Prepayment simulation

### Import / Upload History
- `uploadStatement(file, member?)` - PDF upload
- `fetchStatements()` - List uploaded statements
- `deleteStatement(id)` - Remove statement
- `detectImportColumns(file)` - CSV column detection
- `executeImport(filename, mapping)` - Execute CSV import

### Dashboard / Overview
- `fetchOverview()` - Dashboard summary data
- `fetchBanks()` - List of banks
- `fetchCategoryList()` - List of categories
- `fetchMembers()` - List of members
- `createMember(name, color)` - Create member

### Accounts
- `fetchAccounts()`, `fetchAccount(id)` - List/detail
- `createAccount(account)`, `updateAccount(id, account)`, `deleteAccount(id)` - CRUD

### Cards
- `fetchCards(accountId?)`, `fetchCard(id)` - List/detail
- `createCard(card)`, `updateCard(id, card)`, `deleteCard(id)` - CRUD

### Investments
- `fetchInvestments(activeOnly?)`, `fetchInvestment(id)` - List/detail
- `createInvestment(data)`, `updateInvestment(id, data)`, `deleteInvestment(id)` - CRUD
- `fetchInvestmentSummary()`, `fetchAssetAllocation()` - Analytics

### Recurring
- `fetchRecurringTransactions(activeOnly?)` - List recurring
- `createRecurringTransaction(data)`, `updateRecurringTransaction(id, data)`, `deleteRecurringTransaction(id)` - CRUD
- `detectRecurringTransactions()` - Auto-detect recurring

### Income
- `fetchIncomeSources(activeOnly?)` - List income sources
- `createIncomeSource(data)`, `updateIncomeSource(id, data)`, `deleteIncomeSource(id)` - CRUD

### Cashflow
- `fetchMonthlyCashflow(months?)`, `fetchCashflowBreakdown(month?)`, `fetchCashflowSummary()` - Cashflow data

### Net Worth
- `fetchNetWorth()`, `fetchNetWorthTrend(months?)` - Net worth data

### Projections
- `fetchNetWorthProjection(months?, equityReturn?, debtReturn?)` - Net worth forecast
- `fetchLoanPayoffProjection(loanId)` - Loan payoff timeline
- `calculateGoal(data)` - Goal achievement calculator
- `calculateWhatIf(data)` - What-if scenario simulator

### Snapshots
- `fetchSnapshots(limit?)`, `fetchSnapshot(month)` - List/detail
- `generateSnapshot(month?)`, `backfillSnapshots()` - Generate/backfill

### Categories
- `fetchCategories(params?)` - Category breakdown
- `fetchAnalytics()` - Analytics data

### Export
- `exportCSV(params?)` - Export transactions as CSV
- `exportJSON()` - Full database export
- `exportCSVDownload()` - CSV ZIP download
- `importBackup(data, confirm?)` - Import backup data

### Health/Diagnostics
- `fetchHealthDetailed()` - Detailed health check
- `fetchDiagnostics()` - Diagnostic issues

---

## Hooks (existing)

Source: `frontend/lib/hooks/use-finance-data.ts` (40+ hooks)

### Data Fetching Hooks (return { data, loading, error, refetch })
- `useOverview()` - Dashboard overview
- `useTransactions(params?)` - Transaction list with filters
- `useStatements()` - Upload history
- `useCategories(params?)` - Category breakdown
- `useAnalytics()` - Analytics data
- `useBanks()` - Bank list
- `useCategoryList()` - Category list
- `useMembers()` - Member list
- `useAccounts()` - Account list
- `useAccount(id)` - Single account
- `useCards(accountId?)` - Card list
- `useCard(id)` - Single card
- `useLoans()` - Loan list
- `useLoan(id)` - Single loan
- `useLoanPayments(id)` - Loan payments
- `useAmortizationSchedule(id)` - Amortization data
- `useLoanSummary(id)` - Loan summary
- `useInvestments()` - Investment list
- `useInvestment(id)` - Single investment
- `useInvestmentSummary()` - Investment summary
- `useAssetAllocation()` - Asset allocation
- `useIncomeSources()` - Income source list
- `useRecurringTransactions()` - Recurring transactions
- `useNetWorth()` - Net worth
- `useNetWorthTrend(months?)` - Net worth trend
- `useMonthlyCashflow(months?)` - Monthly cashflow
- `useCashflowBreakdown(month?)` - Cashflow breakdown
- `useCashflowSummary()` - Cashflow summary
- `useNetWorthProjection(months?)` - Net worth projection
- `useSnapshots(limit?)` - Monthly snapshots

### Action Hooks (mutation operations)
- `useUpload()` - `{ uploading, error, result, upload(file, member?) }`
- `useUpdateCategory()` - `{ updating, error, update(id, category, subcategory?) }`
- `useDeleteStatement()` - `{ deleting, error, deleteStatement(id) }`
- `useExportCSV()` - `{ exporting, error, exportCSV(params?) }`
- `useCreateAccount()` - `{ creating, error, createAccount(account) }`
- `useUpdateAccount()` - `{ updating, error, updateAccount(id, account) }`
- `useDeleteAccount()` - `{ deleting, error, deleteAccount(id) }`
- `useCreateCard()` - `{ creating, error, createCard(card) }`
- `useUpdateCard()` - `{ updating, error, updateCard(id, card) }`
- `useDeleteCard()` - `{ deleting, error, deleteCard(id) }`
- `useCreateLoan()` - `{ creating, error, createLoan(loan) }`
- `useUpdateLoan()` - `{ updating, error, updateLoan(id, loan) }`
- `useDeleteLoan()` - `{ deleting, error, deleteLoan(id) }`
- `useCreateLoanPayment()` - `{ creating, error, createLoanPayment(loanId, payment) }`
- `useSimulatePrepayment()` - `{ simulating, error, result, simulatePrepayment(loanId, data) }`
- `useCreateInvestment()` - `{ creating, error, createInvestment(investment) }`
- `useUpdateInvestment()` - `{ updating, error, updateInvestment(id, investment) }`
- `useDeleteInvestment()` - `{ deleting, error, deleteInvestment(id) }`
- `useCreateIncomeSource()` - `{ creating, error, createIncomeSource(data) }`
- `useUpdateIncomeSource()` - `{ updating, error, updateIncomeSource(id, data) }`
- `useDeleteIncomeSource()` - `{ deleting, error, deleteIncomeSource(id) }`
- `useCreateRecurringTransaction()` - `{ creating, error, createRecurringTransaction(data) }`
- `useUpdateRecurringTransaction()` - `{ updating, error, updateRecurringTransaction(id, data) }`
- `useDeleteRecurringTransaction()` - `{ deleting, error, deleteRecurringTransaction(id) }`
- `useDetectRecurring()` - `{ detecting, error, detected, detectRecurring() }`
- `useCalculateGoal()` - `{ calculating, error, result, calculateGoal(data) }`
- `useCalculateWhatIf()` - `{ calculating, error, result, calculateWhatIf(data) }`
- `useGenerateSnapshot()` - `{ generating, error, generateSnapshot(month?) }`
- `useBackfillSnapshots()` - `{ backfilling, error, backfillSnapshots() }`

---

## Known UI Stubs / Mock Data Components

Based on audit of `memory-bank/FRONTEND_AUDIT_REPORT.md` and codebase inspection:

### Using Mock Data (NOT connected to backend)
| File | Issue |
|------|-------|
| `components/categories/category-budget-list.tsx` | Uses `mockCategoryBudgets` - NOT connected to real budget API |
| `components/categories/merchant-rules-table.tsx` | Uses `mockMerchantRules` - NOT connected to rules API |
| `components/import/import-history-list.tsx` | Uses `mockImportHistory` - NOT connected to import history API |

### Components with Manual Paise Formatting (potential bugs)
| File | Issue |
|------|-------|
| `components/projections/goal-planner.tsx` | Tooltip formatter: `Number(value) / 100` - value may already be in rupees |
| `components/investments/allocation-chart.tsx` | Manual formatting: `₹${(value / 100).toFixed(0)}` |

### Type Safety Issues
| File | Issue |
|------|-------|
| `components/income/income-streams-table.tsx` | Uses `any[]` for income sources |
| `components/recurring/subscriptions-table.tsx` | Uses `any[]` for subscriptions |
| `components/recurring/upcoming-bills-timeline.tsx` | Uses `any[]` for bills |
| `components/recurring/monthly-obligations-summary.tsx` | Uses `any` for obligations |
| `app/analytics/page.tsx` | 6 occurrences of `@ts-expect-error` for recharts |

---

## Prioritized Checklist (Top 6 Items)

### 1. Connect Category Budget List to Real API
**Files:** `components/categories/category-budget-list.tsx`, `app/categories/page.tsx`
**DOD:** Component fetches real budget data from backend (create endpoint if needed) instead of using `mockCategoryBudgets`

### 2. Connect Merchant Rules Table to Real API
**Files:** `components/categories/merchant-rules-table.tsx`
**DOD:** Component fetches/saves merchant rules from/to backend API (create endpoint if needed) instead of using `mockMerchantRules`

### 3. Connect Import History List to Real API
**Files:** `components/import/import-history-list.tsx`
**DOD:** Component fetches real import history from backend API instead of using `mockImportHistory`

### 4. Fix Paise Formatting in Goal Planner Tooltip
**Files:** `components/projections/goal-planner.tsx`
**DOD:** Tooltip formatter uses `formatPaise` utility consistently; verify no double-division of paise values

### 5. Fix Paise Formatting in Investment Allocation Chart
**Files:** `components/investments/allocation-chart.tsx`
**DOD:** Replace manual `₹${(value / 100).toFixed(0)}` with `formatPaise` utility

### 6. Add Type Safety to Recurring/Income Components
**Files:** `components/income/*.tsx`, `components/recurring/*.tsx`
**DOD:** Replace all `any[]` types with proper TypeScript interfaces from `types/` directory

---

## API Endpoint Reference (Frontend-Backend Contract)

| Feature | GET | POST | PUT | DELETE |
|---------|-----|------|-----|--------|
| Transactions | `/api/transactions` | - | `/api/transactions/:id/category` | - |
| Loans | `/api/loans`, `/api/loans/:id` | `/api/loans` | `/api/loans/:id` | `/api/loans/:id` |
| Loan Payments | `/api/loans/:id/payments` | `/api/loans/:id/payments` | - | - |
| Amortization | `/api/loans/:id/amortization` | - | - | - |
| Statements | `/api/statements` | `/api/upload` | - | `/api/statements/:id` |
| Import | `/api/import/detect` | `/api/import/execute` | - | - |
| Accounts | `/api/accounts` | `/api/accounts` | `/api/accounts/:id` | `/api/accounts/:id` |
| Cards | `/api/cards` | `/api/cards` | `/api/cards/:id` | `/api/cards/:id` |
| Investments | `/api/investments` | `/api/investments` | `/api/investments/:id` | `/api/investments/:id` |
| Recurring | `/api/recurring` | `/api/recurring` | `/api/recurring/:id` | `/api/recurring/:id` |
| Income | `/api/income-sources` | `/api/income-sources` | `/api/income-sources/:id` | `/api/income-sources/:id` |
| Cashflow | `/api/cashflow/*` | - | - | - |
| Net Worth | `/api/networth/*` | - | - | - |
| Projections | `/api/projections/*` | `/api/projections/goal`, `/api/projections/what-if` | - | - |
| Snapshots | `/api/snapshots` | `/api/snapshots/generate`, `/api/snapshots/backfill` | - | - |
| Categories | `/api/categories` | - | - | - |
| Analytics | `/api/analytics` | - | - | - |
| Export | `/api/export/csv`, `/api/export/json` | - | - | - |
| Health | `/api/health/detailed`, `/api/diagnostics` | - | - | - |

---

## Notes for Future Tasks

1. **No new API routes** should be invented without checking this list first
2. **No new scripts** should be invented - use the exact npm scripts documented above
3. **Mock data components** are clearly marked - prioritize replacing these
4. **Type safety gaps** are documented - use proper types from `types/` directory
5. **All hooks return consistent patterns** - either `{ data, loading, error, refetch }` or action-specific state

---

*This document is READ-ONLY for reference. Update only when codebase actually changes.*
