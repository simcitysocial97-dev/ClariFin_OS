# M9-C68: Canonical API Contract

## Enterprise Architecture Decision

This document establishes the single source of truth for all backend-to-frontend API contracts.
Legacy `/api/*` endpoints that duplicate v1 functionality have been consolidated.

## Account Domain — CONSOLIDATED TO V1

| Operation | Legacy Path (DEPRECATED) | Canonical Path | Service | Response Shape |
|-----------|-------------------------|----------------|---------|----------------|
| List | `GET /api/accounts/manage` | `GET /api/v1/accounts` | AccountService | `list[AccountDetailDTO]` |
| Create | `POST /api/accounts/manage` | `POST /api/v1/accounts` | AccountService | `{success, account}` |
| Update | `PUT /api/accounts/manage/{id}` | `PUT /api/v1/accounts/{id}` | AccountService | `{success, account}` |
| Delete | `DELETE /api/accounts/manage/{id}` | `DELETE /api/v1/accounts/{id}` | AccountService | `{success}` |
| Balance | `GET /api/accounts/{id}/balance` | N/A | AccountService | N/A (use /metrics) |
| Running Balance | `GET /api/accounts/{id}/running-balance` | N/A | AccountService | N/A (use /balance-history) |

**Rationale**: Both legacy and v1 used `AccountService`. V1 provides proper DTOs, timing logs, and is the superset. Legacy router (`managed_accounts.py`) removed.

**Frontend Migration**:
- `use-accounts.ts`: Migrated from `/api/accounts/manage*` to `/api/v1/accounts*`
- Response wrapping: V1 returns plain array; hook wraps to `{accounts, total}` for backward compatibility
- Schema updated: `bank→institution`, `account_type→type`, `is_active(int)→status(string)`, `created_at→opened_date`

## Domain-by-Domain Consolidation Status

### Accounts ✅ COMPLETE
- Legacy `/api/accounts/manage*` → REMOVED
- Canonical: `/api/v1/accounts*`
- Frontend: Migrated `use-accounts.ts`

### Credit Cards ⚠️ PARTIAL (Different Services)
- Legacy `/api/cards` uses `StatementService` (statement-derived data)
- V1 `/api/v1/credit-cards` uses `CreditCardService` (card-level CRUD)
- **Decision**: Keep both — serve different purposes (statement integration vs card management)

### Loans ⚠️ NO CHANGE (Different Purposes)
- Legacy `/api/loans*` = Full CRUD via `LoanService`
- V1 `/api/v1/loans` = Aggregation summary via `LoansWorkspaceService`
- **Decision**: Keep legacy as canonical for CRUD; v1 workspace is supplemental analytics

### Investments ⚠️ NO CHANGE (Different Purposes)
- Legacy `/api/investments*` = Full CRUD via `InvestmentService`
- V1 `/api/v1/investments` = Aggregation summary via `InvestmentsWorkspaceService`
- **Decision**: Keep legacy as canonical for CRUD

### Cashflow ⚠️ NO CHANGE (Different Purposes)
- Legacy `/api/cashflow/monthly` = Monthly breakdown via `CashflowService`
- V1 `/api/v1/cashflow` = Summary via `CashflowWorkspaceService`
- **Decision**: Keep legacy as canonical for time-series data

### Reconciliation ⚠️ NO CHANGE (Different Purposes)
- Legacy `/api/reconciliation*` = Full CRUD + scan/confirm/reject via `ReconciliationService`
- V1 `/api/v1/reconciliation` = Summary via `ReconciliationWorkspaceService`
- **Decision**: Keep legacy as canonical for operational workflows

### Networth ⚠️ NO CHANGE (Different Services)
- Legacy `/api/networth` = `NetWorthService`
- V1 `/api/v1/net-worth` = `NetWorthWorkspaceService`
- **Decision**: Keep legacy as-is (no duplicate functionality)

### Dashboard / Overview / Analytics ✅ NO CHANGE
- These are standalone endpoints with no v1 equivalents
- `GET /api/dashboard/summary` — canonical
- `GET /api/overview` — canonical
- `GET /api/analytics` — canonical

### Platform Console ✅ ALREADY CANONICAL
- All `/platform/v1/*` endpoints are the single source of truth
- No legacy equivalents exist

## Money/Financial Data Contract

All monetary values use **integer paise** throughout the stack:
- Backend DTOs: `balance_paise: int`, `amount_paise: int`
- Frontend schemas: `z.number().int()`
- Formatter: `formatPaise(paise: number): string` in `lib/formatters/index.ts`
- No floating-point money arithmetic in frontend

## Type System Status

| Metric | Before C68 | After C68 |
|--------|-----------|-----------|
| TypeScript errors | 29 | 0 |
| Lint errors | 0 | 0 |
| Backend unit tests | 2950 passed | 2950 passed |
| Backend contract tests | 161 passed | 161 passed |
| Backend integration tests | 3111 passed | 3111 passed |

## Deprecated Files

The following files are now dead code (no router registration, no consumers):
- `backend/src/routers/managed_accounts.py` — replaced by `accounts.py` (v1)
- `frontend/types/api-generated.ts` entries for `/api/accounts/manage` — stale generated types

## Frontend Hook → Backend Endpoint Mapping

| Hook | Endpoint | Status |
|------|----------|--------|
| `useManagedAccounts` | `GET /api/v1/accounts` | ✅ Migrated |
| `useCreateAccount` | `POST /api/v1/accounts` | ✅ Migrated |
| `useUpdateAccount` | `PUT /api/v1/accounts/{id}` | ✅ Migrated |
| `useDeleteAccount` | `DELETE /api/v1/accounts/{id}` | ✅ Migrated |
| `useCards` | `GET /api/cards` | ⚠️ Legacy (statement-derived) |
| `useCashflow` | `GET /api/cashflow/monthly` | ⚠️ Legacy (time-series) |
| `useInvestments` | `GET /api/investments` | ⚠️ Legacy (CRUD) |
| `useLoans` | `GET /api/loans` | ⚠️ Legacy (CRUD) |
| `useNetWorth` | `GET /api/networth` | ⚠️ Legacy (separate service) |
| `useReconciliations` | `GET /api/reconciliation` | ⚠️ Legacy (operational) |
| `useDashboardMetrics` | `GET /api/dashboard/summary` | ✅ Canonical |
| `useOverview` | `GET /api/overview` | ✅ Canonical |
| `useAnalytics` | `GET /api/analytics` | ✅ Canonical |
| `useBehaviorScore` | `GET /api/v1/behaviour/wellness-score` | ✅ Already v1 |
| `usePlatformStatus` | `GET /platform/v1/status` | ✅ Platform |
| `usePlatformHealth` | `GET /platform/v1/health` | ✅ Platform |
| `usePlatformRuns` | `GET /platform/v1/runs` | ✅ Platform |
| `usePlatformWorkflows` | `GET /platform/v1/workflows` | ✅ Platform |
