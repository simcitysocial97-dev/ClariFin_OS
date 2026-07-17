# Frontend Migration Progress

Living checklist tracking incremental architectural migrations. Prevents duplicate work and maintains continuity across sessions.

## Migration Status

| Area | Status | Notes |
|------|--------|-------|
| DTO → ViewModel | 🔄 In Progress | Net Worth completed |
| Chart Runtime | ✅ Complete | Shared modules created, CashflowChart migrated |
| Query Factory | ⏳ Pending | Starts S1.3 |
| Explainability Runtime | ⏳ Pending | Starts S1.4 |
| Workspace Runtime | ⏳ Pending | Starts S1.5 |

## Stage 1.2 — Data Transformation Layer

### Completed Work

- [x] Created `frontend/lib/contracts/shared/money.ts` - Single source of truth for Money type
- [x] Created `frontend/lib/contracts/api/networth.ts` - NetWorth API contract (DTO validation schema)
- [x] Created `frontend/lib/models/networth.ts` - NetWorth ViewModel (domain-friendly model)
- [x] Created `frontend/lib/mappers/networth.ts` - Pure mapper function
- [x] Updated `frontend/lib/hooks/use-networth.ts` - Hook now uses mapper
- [x] Updated `frontend/components/dashboard/widgets/money-position-widget.tsx` - Component uses ViewModel
- [x] Created `frontend/lib/mappers/__tests__/networth.test.ts` - Mapper tests

### Architecture Pattern Established

```
Backend DTO
     ↓
Contract Validation (Zod) → frontend/lib/contracts/api/
     ↓
Mapper (pure function) → frontend/lib/mappers/
     ↓
Domain/ViewModel → frontend/lib/models/
     ↓
Hook → frontend/lib/hooks/
     ↓
Component → frontend/components/
     ↓
formatINR(...) (presentation)
```

### Money Type Consolidation

| Before | After |
|--------|-------|
| `frontend/lib/money.ts` (handwritten) | ✅ Kept for backward compatibility |
| `frontend/lib/schemas/transaction.ts` (Zod) | ✅ Moved to `contracts/shared/money.ts` |
| No single source of truth | ✅ `contracts/shared/money.ts` is canonical |

### Files Created

| File | Purpose |
|------|---------|
| `lib/contracts/shared/money.ts` | Money contract type |
| `lib/contracts/api/networth.ts` | NetWorth API DTO schema |
| `lib/models/networth.ts` | NetWorth ViewModel |
| `lib/mappers/networth.ts` | DTO → Model transformation |
| `lib/mappers/__tests__/networth.test.ts` | Mapper unit tests |

### Files Modified

| File | Change |
|------|--------|
| `lib/hooks/use-networth.ts` | Uses contract + mapper |
| `components/dashboard/widgets/money-position-widget.tsx` | Uses ViewModel |

### Reference Implementation: Net Worth

The NetWorth capability demonstrates the pattern:

1. **Contract** (`contracts/api/networth.ts`): Zod schema validates API response
2. **Mapper** (`mappers/networth.ts`): Pure function transforms snake_case → camelCase, derives `trend` flag
3. **Model** (`models/networth.ts`): Type-safe interface for components
4. **Hook** (`hooks/use-networth.ts`): Returns Model, not DTO
5. **Component** (`money-position-widget.tsx`): Uses Model, formats with `formatINRCompact()`

### Remaining Migration Plan

| Capability | Status | Dependencies |
|------------|--------|------------|
| Transactions | ⏳ Pending | Follows NetWorth pattern |
| Loans | ⏳ Pending | Follows NetWorth pattern |
| Accounts | ⏳ Pending | Follows NetWorth pattern |
| Cashflow | ⏳ Pending | Follows NetWorth pattern |
| Investments | ⏳ Pending | Follows NetWorth pattern |
| Behavior | ⏳ Pending | Follows NetWorth pattern |

### Risks

| Risk | Status | Mitigation |
|------|--------|------------|
| Components using raw `_paise` fields | ✅ Addressed | NetWorth updated, others follow later |
| Duplicate Money types | 🔄 Partial | Contracts/Money is canonical, old files still exist |
| Breaking changes to hook return types | ✅ Addressed | Test the NetWorth flow before proceeding |
| TypeScript strict mode compliance | ⏳ Pending | Will validate in Phase F |

---

## Stage 1.8 — Chart Runtime Extraction

### Completed Work

- [x] Created `frontend/lib/chart/recharts.ts` - Shared dynamic imports for Recharts components
- [x] Created `frontend/lib/chart/chart-config.ts` - Shared chart constants (margins, heights, grid, axis, tooltip, legend)
- [x] Created `frontend/lib/chart/chart-colors.ts` - Semantic color tokens for charts
- [x] Updated `frontend/lib/utils/format.ts` - Fixed `formatINRCompact()` to use integer precision (no decimals)
- [x] Migrated `frontend/components/dashboard/cashflow-chart.tsx` - Now uses shared chart modules
- [x] Updated `frontend/lib/utils/__tests__/format.test.ts` - Fixed test expectations for compact format

### Files Created

| File | Purpose |
|------|---------|
| `lib/chart/recharts.ts` | Dynamic imports for Recharts components (SSR-safe) |
| `lib/chart/chart-config.ts` | Shared chart configuration constants |
| `lib/chart/chart-colors.ts` | Semantic color tokens for chart series |

### Files Modified

| File | Change |
|------|--------|
| `lib/utils/format.ts` | Fixed `formatINRCompact()` integer precision |
| `components/dashboard/cashflow-chart.tsx` | Migrated to use shared chart modules |
| `lib/utils/__tests__/format.test.ts` | Updated test expectations |

### Reference Implementation: CashflowChart

The CashflowChart demonstrates the chart runtime pattern:

1. **Dynamic Imports**: All Recharts components imported from `lib/chart/recharts.ts`
2. **Shared Config**: Margins, heights, grid, axis props from `lib/chart/chart-config.ts`
3. **Color Tokens**: Semantic colors from `lib/chart/chart-colors.ts`
4. **Formatter**: Uses `formatINR()` from `lib/utils/format.ts`

### Duplication Eliminated

| Pattern | Before | After |
|---------|--------|-------|
| Recharts imports | 11 inline `dynamic()` calls | 1 import from `recharts.ts` |
| Chart margins | Repeated `{top: 20, right: 30, ...}` | `CHART_MARGINS.default` |
| Grid config | Repeated `strokeDasharray='3 3'` | `CARTESIAN_GRID_PROPS` |
| Axis styling | Repeated tick styles | `AXIS_TICK_STYLE` |
| Tooltip style | Repeated contentStyle objects | `TOOLTIP_CONTENT_STYLE` |
| Legend config | Repeated wrapper styles | `LEGEND_WRAPPER_STYLE` |

### Validation Results

- ✅ Type-check: `tsc --noEmit` passes
- ✅ Unit tests: 94/94 tests pass
- ✅ Build: Next.js production build succeeds

### Next Steps

- [ ] Migrate remaining charts to use shared modules (NetWorth, Spending, etc.)
- [ ] Extract shared tooltip component if custom tooltips are needed
- [ ] Add chart-specific formatters (dates, percentages) to `format.ts`

---

## Stage 1.9 — Capability Runtime Consolidation

### Completed Work

- [x] Created canonical capability folder structure: `frontend/lib/capabilities/<capability>/`
- [x] Migrated Cashflow as reference implementation following new structure
- [x] Created `frontend/lib/capabilities/cashflow/contracts/api.ts` - Cashflow API contract
- [x] Created `frontend/lib/capabilities/cashflow/models/model.ts` - Cashflow ViewModel
- [x] Created `frontend/lib/capabilities/cashflow/mappers/mapper.ts` - DTO → ViewModel transformation
- [x] Created `frontend/lib/capabilities/cashflow/services/api.ts` - API service functions
- [x] Created `frontend/lib/capabilities/cashflow/hooks/useCashflow.ts` - Hook using useAppQuery
- [x] Created `frontend/lib/capabilities/cashflow/index.ts` - Public entry point
- [x] Updated `frontend/components/dashboard/cashflow-chart.tsx` - Uses new capability module
- [x] Removed deprecated `frontend/lib/schemas/cashflow.ts`
- [x] Removed cashflow query key from `frontend/lib/query/queryKeys.ts` (now in capability)

### Canonical Capability Structure Established

```
frontend/lib/capabilities/<capability>/
    contracts/
        api.ts          # API contract (Zod validation schema)
    mappers/
        mapper.ts       # Pure DTO → ViewModel transformation
    models/
        model.ts        # Domain-friendly ViewModel interface
    hooks/
        useCapability.ts # React Query hook (uses useAppQuery)
    services/
        api.ts          # API service functions (fetch wrappers)
    index.ts            # Public entry point (single export)
```

### Architecture Pattern Established

```
Backend DTO
      ↓
Contract Validation (Zod) → capabilities/<cap>/contracts/api.ts
      ↓
Service Layer → capabilities/<cap>/services/api.ts
      ↓
Query Runtime (useAppQuery) → capabilities/<cap>/hooks/
      ↓
Mapper (pure function) → capabilities/<cap>/mappers/mapper.ts
      ↓
ViewModel → capabilities/<cap>/models/model.ts
      ↓
Component → frontend/components/
      ↓
formatINR(...) (presentation)
```

### Key Principles

1. **Single Entry Point**: Each capability exposes only `index.ts` - no deep imports
2. **Service Layer**: All `fetch()` calls live in `services/api.ts` - hooks never call fetch directly
3. **Query Keys**: Capability-specific keys defined within the capability, not in global `queryKeys.ts`
4. **Shared Runtimes**: Query Runtime, Runtime State, Explainability, Chart, and Utils remain in `lib/runtime/`, `lib/query/`, `lib/explainability/`, `lib/chart/`, `lib/utils/`
5. **Capability Logic**: All capability-specific logic stays inside the capability folder

### Files Created

| File | Purpose |
|------|---------|
| `lib/capabilities/cashflow/contracts/api.ts` | Cashflow API DTO schema |
| `lib/capabilities/cashflow/models/model.ts` | Cashflow ViewModel |
| `lib/capabilities/cashflow/mappers/mapper.ts` | DTO → Model transformation |
| `lib/capabilities/cashflow/services/api.ts` | API service functions |
| `lib/capabilities/cashflow/hooks/useCashflow.ts` | React Query hook |
| `lib/capabilities/cashflow/index.ts` | Public entry point |

### Files Modified

| File | Change |
|------|--------|
| `components/dashboard/cashflow-chart.tsx` | Uses new capability module |
| `lib/query/queryKeys.ts` | Removed cashflow key (now in capability) |

### Files Removed

| File | Reason |
|------|--------|
| `lib/schemas/cashflow.ts` | Migrated to `capabilities/cashflow/contracts/api.ts` |

### Validation Results

- ✅ Type-check: `tsc --noEmit` passes
- ✅ Unit tests: 94/94 tests pass
- ✅ Build: Next.js production build succeeds
- ⚠️ Lint: Pre-existing errors in test files (not related to migration)

### Reference Implementation: Cashflow

The Cashflow capability demonstrates the canonical pattern:

1. **Contract** (`contracts/api.ts`): Zod schema validates API response
2. **Service** (`services/api.ts`): `fetchCashflow()`, `fetchMonthlyCashflow()`, `fetchCashflowSummary()`
3. **Hook** (`hooks/useCashflow.ts`): Uses `useAppQuery` with service functions
4. **Mapper** (`mappers/mapper.ts`): Pure function transforms DTO → ViewModel
5. **Model** (`models/model.ts`): Type-safe interface for components
6. **Index** (`index.ts`): Single public export point

### Next Steps

- [ ] Migrate remaining capabilities to canonical structure (Accounts, Loans, Investments, Cards, Behavior, Analytics, Reconciliation)
- [ ] Extract shared capability utilities (common mapper patterns, query key helpers)
- [ ] Add explainability integration to capability hooks
- [ ] Document capability migration guide for team

### Benefits Achieved

| Benefit | Before | After |
|---------|--------|-------|
| **Consistency** | Each capability organized differently | Single canonical structure |
| **Discoverability** | Logic scattered across lib/ | All capability logic in one place |
| **Maintainability** | Duplicate patterns | Reusable capability template |
| **Onboarding** | Learn ad-hoc structure | Follow established pattern |
| **Testing** | Inconsistent test locations | Co-located with capability code |

---
*Updated: Stage 1.9 complete - Capability runtime consolidation established, Cashflow migrated as reference*

## Stage 1.10 — Accounts Capability Migration

### Completed Work

- [x] Created `frontend/lib/capabilities/accounts/contracts/api.ts` - Accounts API contract (Zod validation schema)
- [x] Created `frontend/lib/capabilities/accounts/models/model.ts` - Accounts ViewModel (domain-friendly model)
- [x] Created `frontend/lib/capabilities/accounts/mappers/mapper.ts` - Pure DTO → ViewModel transformation
- [x] Created `frontend/lib/capabilities/accounts/services/api.ts` - API service functions
- [x] Created `frontend/lib/capabilities/accounts/hooks/useAccounts.ts` - Hook using useAppQuery
- [x] Created `frontend/lib/capabilities/accounts/index.ts` - Public entry point
- [x] Updated `frontend/lib/hooks/use-accounts.ts` - Compatibility shim re-exporting migrated hook
- [x] Updated `frontend/app/accounts/page.tsx` - Uses new AccountModel with camelCase fields

### Files Created

| File | Purpose |
|------|---------|
| `lib/capabilities/accounts/contracts/api.ts` | Accounts API DTO schema |
| `lib/capabilities/accounts/models/model.ts` | Accounts ViewModel |
| `lib/capabilities/accounts/mappers/mapper.ts` | DTO → Model transformation |
| `lib/capabilities/accounts/services/api.ts` | API service functions |
| `lib/capabilities/accounts/hooks/useAccounts.ts` | React Query hook |
| `lib/capabilities/accounts/index.ts` | Public entry point |

### Files Modified

| File | Change |
|------|--------|
| `lib/hooks/use-accounts.ts` | Compatibility shim re-exporting useManagedAccounts and Account type |
| `app/accounts/page.tsx` | Uses AccountModel with camelCase fields (accountType, balancePaise, accountNumberLast4) |
| `lib/hooks/use-cashflow.ts` | Compatibility shim re-exporting useCashflow and types |
| `lib/query/queryKeys.ts` | Restored cashflow key (pre-existing issue from Stage 1.9) |

### Validation Results

- ✅ Type-check: `tsc --noEmit` passes
- ✅ Unit tests: 94/94 tests pass

### Reference Implementation: Accounts

The Accounts capability follows the canonical pattern:

1. **Contract** (`contracts/api.ts`): Zod schema validates API response
2. **Service** (`services/api.ts`): `fetchManagedAccounts()` with Zod validation
3. **Hook** (`hooks/useAccounts.ts`): Uses `useAppQuery` with shared query keys
4. **Mapper** (`mappers/mapper.ts`): Pure function transforms snake_case → camelCase
5. **Model** (`models/model.ts`): Type-safe interface for components
6. **Index** (`index.ts`): Single public export point

### Notes

- Mutation hooks (create/update/delete) remain in `lib/hooks/use-accounts.ts` for future migration
- Computed accounts endpoint (`/api/accounts`) is not part of this migration
