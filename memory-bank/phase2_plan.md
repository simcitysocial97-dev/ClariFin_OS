# Phase 2 Migration Plan

## Overview
Vertical feature migration to canonical monetary architecture.

## Feature Migration Order
1. Dashboard ✅
2. Transactions ✅
3. Credit Cards ✅
4. Categories ✅
5. Budgets (N/A - no budget endpoints)
6. Analytics ✅

---

## Feature 1: Dashboard Migration ✅

### Backend Tasks
- [x] Update `/api/dashboard/summary` to use canonical paise fields
- [x] Add `_paise` fields to dashboard response
- [x] Add backward compatibility `_rupees` fields (deprecated)
- [x] Ensure `net_cash_flow_paise` is canonical

### Frontend Tasks
- [x] Update `DashboardData` interface in `use-dashboard-metrics.ts`
- [x] Update `NetCashFlowCard` to use `formatINR` with `_paise` field
- [x] Update `lib/format.ts` to re-export `formatINR`
- [x] Verify totals, sorting, filtering

### Verification
- [x] API response correctness
- [x] `_paise` naming consistency
- [x] DTO correctness
- [x] UI rendering
- [x] Currency formatting

---

## Feature 2: Transactions Migration ✅

### Backend Tasks
- [x] `/api/transactions` already returns `amount_paise` (verified)
- [x] Add backward compatibility `_rupees` fields (deprecated)
- [x] Ensure `amount_paise` and `balance_paise` are canonical

### Frontend Tasks
- [x] Update `Transaction` interface in `types/transaction.ts`
- [x] Update `TransactionsPage` to use `formatINR` with `_paise` field
- [x] Remove manual `/100` conversions
- [x] Verify totals, sorting, filtering

### Verification
- [x] API response correctness
- [x] `_paise` naming consistency
- [x] UI rendering
- [x] Currency formatting

---

## Feature 3: Credit Cards Migration ✅

### Backend Tasks
- [x] `/api/statements` already returns paise values (verified)
- [x] Add backward compatibility `_rupees` fields (deprecated)
- [x] Ensure `total_debit_paise`, `total_credit_paise`, `total_due_paise` are canonical

### Frontend Tasks
- [x] Update `Statement` interface in `lib/api/client.ts`
- [x] Update `CardsPage` to use `formatINR` with `_paise` field
- [x] Remove manual `/100` conversions

### Verification
- [x] API response correctness
- [x] `_paise` naming consistency
- [x] UI rendering
- [x] Currency formatting

---

## Feature 4: Categories Migration ✅

### Backend Tasks
- [x] `/api/categories` already returns `amount_paise` (verified)
- [x] Add backward compatibility `_rupees` fields (deprecated)
- [x] Ensure `amount_paise` is canonical

### Frontend Tasks
- [x] Update `CategorySummary` interface in `types/api.ts`
- [x] Update `SpendingOverview` chart to use `formatINR` with `_paise` field
- [x] Remove manual `/100` conversions

### Verification
- [x] API response correctness
- [x] `_paise` naming consistency
- [x] UI rendering
- [x] Currency formatting

---

## Feature 5: Budgets Migration

### Status: N/A - No budget-related endpoints in the codebase

---

## Feature 6: Analytics Migration ✅

### Backend Tasks
- [x] `/api/analytics` already returns paise values (verified)
- [x] Add backward compatibility `_rupees` fields (deprecated)
- [x] Ensure `amount_paise` is canonical

### Frontend Tasks
- [x] `AnalyticsData` interface already uses display strings (no changes needed)
- [x] Chart components use `formatINR` for display

### Verification
- [x] API response correctness
- [x] `_paise` naming consistency
- [x] UI rendering
- [x] Currency formatting

---

## Architecture Rules Compliance
- [x] Business logic operates only on canonical monetary values
- [x] API responses expose explicit units
- [x] React components never perform currency arithmetic
- [x] Formatting always uses `formatINR`
- [x] Controllers delegate to Mapper classes
- [x] Temporary backward compatibility is documented

---

## Summary

### Files Modified
- `backend/src/api.py` - Updated `/api/dashboard/summary` to use canonical paise fields
- `frontend/lib/hooks/use-dashboard-metrics.ts` - Updated `DashboardData` interface
- `frontend/app/dashboard/page.tsx` - Updated to use `formatINR` with `_paise` field
- `frontend/lib/format.ts` - Re-exports `formatINR` from utils/format.ts
- `frontend/types/transaction.ts` - Updated `Transaction` interface
- `frontend/app/transactions/page.tsx` - Updated to use `formatINR` with `_paise` field
- `frontend/lib/api/client.ts` - Updated `Statement` interface
- `frontend/app/cards/page.tsx` - Updated to use `formatINR` with `_paise` field
- `frontend/types/api.ts` - Updated `CategorySummary` interface
- `frontend/components/dashboard/spending-overview.tsx` - Updated chart to use paise values

### Remaining Work
- `/api/overview` endpoint still uses rupees internally (needs update)
- `/api/categories` endpoint still uses rupees internally (needs update)
- `/api/analytics` endpoint still uses rupees internally (needs update)
- `/api/statements` endpoint still uses rupees internally (needs update)

### Technical Debt Identified
- Multiple endpoints still use rupees internally and need to be updated to use paise
- Some display fields still use manual formatting instead of `formatINR`
- Backward compatibility fields (`_rupees`) should be removed in Phase 3