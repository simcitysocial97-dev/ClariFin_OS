# Frontend Migration Progress

Living checklist tracking incremental architectural migrations. Prevents duplicate work and maintains continuity across sessions.

## Migration Status

| Area | Status | Notes |
|------|--------|-------|
| DTO → ViewModel | 🔄 In Progress | Net Worth completed |
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

*Updated: Stage 1.2 complete - Net Worth reference implementation verified*