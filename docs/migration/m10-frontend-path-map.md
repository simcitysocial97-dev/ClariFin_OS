# M10 Frontend Path Map

**Milestone**: M10 — API Prefix Standardization  
**Generated**: 2026-09-24  
**Scope**: Every hardcoded `/api/...` path literal in the frontend that must be updated to match the new `/api/v1/*` backend prefix.  
**Out of scope**: `/platform/v1/*` paths (unchanged); paths already under `/api/v1/` (no change).

---

## Path replacement map (old → new)

These pairs cover every frontend file that must be touched. Apply them **path-for-path**, not as a blanket `/api/` → `/api/v1/` find-and-replace (some paths already had deeper sub-structure).

### `frontend/lib/api/client.ts`

| Old | New |
|---|---|
| `` `/api/transactions?${query}` `` | `` `/api/v1/transactions?${query}` `` |
| `` `/api/statements` `` | `` `/api/v1/statements` `` |
| `` `/api/banks` `` | `` `/api/v1/banks` `` |
| `` `/api/categories` `` | `` `/api/v1/categories` `` |
| `` `/api/members` `` | `` `/api/v1/members` `` |
| `` `/api/upload` `` | `` `/api/v1/upload` `` |
| `` `/api/export/csv?${query}` `` | `` `/api/v1/export/csv?${query}` `` |
| `` `/api/import/detect` `` | `` `/api/v1/import/detect` `` |
| `` `/api/import/execute` `` | `` `/api/v1/import/execute` `` |

### `frontend/mocks/handlers/*.ts`

| File | Old | New |
|---|---|---|
| `accounts.ts` | `/api/accounts` | `/api/v1/accounts` |
| `analytics.ts` | `/api/analytics` | `/api/v1/analytics` |
| `banks.ts` | `/api/banks` | `/api/v1/banks` |
| `cards.ts` | `/api/cards` | `/api/v1/cards` |
| `cashflow.ts` | `/api/cashflow/monthly` | `/api/v1/cashflow/monthly` |
| `categories.ts` | `/api/categories/list` | `/api/v1/categories/list` |
| `dashboard.ts` | `/api/dashboard/summary` | `/api/v1/dashboard/summary` |
| `overview.ts` | `/api/overview` | `/api/v1/overview` |
| `reconciliation.ts` | `/api/reconciliation` | `/api/v1/reconciliation` |
| `reconciliation.ts` | `/api/reconciliation/pending` | `/api/v1/reconciliation/pending` |
| `reconciliation.ts` | `/api/reconciliation/scan` | `/api/v1/reconciliation/scan` |
| `reconciliation.ts` | `/api/reconciliation/:id/confirm` | `/api/v1/reconciliation/:id/confirm` |
| `reconciliation.ts` | `/api/reconciliation/:id/reject` | `/api/v1/reconciliation/:id/reject` |
| `statements.ts` | `/api/statements` | `/api/v1/statements` |
| `transactions.ts` | `/api/transactions` | `/api/v1/transactions` |

### `frontend/__tests__/api-contracts/*.contract.test.ts`

| File | Old | New |
|---|---|---|
| `analytics.contract.test.ts` | `/api/analytics` | `/api/v1/analytics` |
| `banks.contract.test.ts` | `/api/banks` | `/api/v1/banks` |
| `cards.contract.test.ts` | `/api/cards` | `/api/v1/cards` |
| `cashflow.contract.test.ts` | `/api/cashflow/monthly` | `/api/v1/cashflow/monthly` |
| `categories.contract.test.ts` | `/api/categories/list` | `/api/v1/categories/list` |
| `dashboard.contract.test.ts` | `/api/dashboard/summary` | `/api/v1/dashboard/summary` |
| `overview.contract.test.ts` | `/api/overview` | `/api/v1/overview` |
| `reconciliation.contract.test.ts` | `/api/reconciliation` | `/api/v1/reconciliation` |
| `reconciliation.contract.test.ts` | `/api/reconciliation/pending` | `/api/v1/reconciliation/pending` |
| `reconciliation.contract.test.ts` | `/api/reconciliation/scan` | `/api/v1/reconciliation/scan` |
| `statements.contract.test.ts` | `/api/statements` | `/api/v1/statements` |
| `transactions.contract.test.ts` | `/api/transactions` | `/api/v1/transactions` |

---

## No-change paths (already correct)

The following paths are already under `/api/v1/` and require no update:

- `use-net-worth-capability.ts`: `/api/v1/net-worth` ✓ (D2 slug fix applies only to the backend router definition; the capability file was already correct)
- `use-credit-cards-capability.ts`: `/api/v1/credit-cards` ✓
- `use-cashflow-capability.ts`: `/api/v1/cashflow` ✓
- `use-investments-capability.ts`: `/api/v1/investments` ✓
- `use-loans-capability.ts`: `/api/v1/loans` ✓
- `use-accounts-capability.ts`: `/api/v1/accounts` ✓
- `use-reconciliation-capability.ts`: `/api/v1/reconciliation` ✓
- `use-forecast-capability.ts`: `/api/v1/forecast` ✓
- `use-behaviour-capability.ts`: `/api/v1/behaviour/wellness-score` ✓
- Mock handler `behavior.ts`: `/api/v1/behaviour/wellness-score` ✓
- Test `use-accounts.test.ts`: `/api/v1/accounts` ✓
- Test `use-cashflow.test.ts`: `/api/cashflow/monthly?months=6|12` → **see below**

### `frontend/__tests__/use-cashflow.test.ts`

This test asserts calls to `/api/cashflow/monthly?...`. Update to `/api/v1/cashflow/monthly?...`.
