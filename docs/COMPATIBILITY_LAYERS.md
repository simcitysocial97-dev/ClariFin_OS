# Compatibility Layers Inventory

This document catalogs all compatibility shims in the codebase that exist for backward compatibility during migration. These layers should NOT be removed until all dependent code is migrated.

---

## Backend Compatibility Layers

### 1. `backend/src/common/database.py`

| Field | Value |
|-------|-------|
| **Location** | `backend/src/common/database.py` |
| **Purpose** | Provides deprecated `get_db()` function for legacy code that hasn't migrated to repository pattern |
| **Current Usage** | Tests, legacy scripts, and any code not yet updated to use repositories directly |
| **Removal Condition** | All code uses repository classes directly; no imports of `get_db()` remain |
| **Recommended Removal Stage** | Stage 2.0 (Post-implementation cleanup) |

```python
def get_db() -> FinanceDB:
    """DEPRECATED: Returns a FinanceDB instance. Use repositories instead."""
```

---

### 2. `backend/src/engines/behavior_engine.py`

| Field | Value |
|-------|-------|
| **Location** | `backend/src/engines/behavior_engine.py` |
| **Purpose** | Legacy compatibility shim; delegates to `BehaviourService` and `behaviour_engine/` package |
| **Current Usage** | Tests in `test_behavior_engine.py`, legacy imports |
| **Removal Condition** | All code imports from `src.engines.behaviour_engine` package instead |
| **Recommended Removal Stage** | Stage 2.0 |

**Functions:**
- `compute_behavior_profile(db_path)` → delegates to `BehaviourService.compute_profile()`
- `get_cached_behavior_profile(db_path)` → delegates to `BehaviourService`
- `set_cached_behavior_profile(db_path, profile)` → delegates to `BehaviourService`
- `invalidate_behavior_cache()` → delegates to `invalidate_behaviour_cache()`

---

### 3. `backend/src/services/behavior_service.py`

| Field | Value |
|-------|-------|
| **Location** | `backend/src/services/behavior_service.py` |
| **Purpose** | Legacy compatibility wrapper; delegates to `BehaviourService` |
| **Current Usage** | `backend/src/routers/behavior.py` |
| **Removal Condition** | Router `behavior.py` removed or updated to use `BehavourService` directly |
| **Recommended Removal Stage** | Stage 2.0 |

---

### 4. `backend/src/routers/behavior.py`

| Field | Value |
|-------|-------|
| **Location** | `backend/src/routers/behavior.py` |
| **Purpose** | Legacy router using `BehaviorService` (US spelling) instead of `BehavourService` (UK spelling) |
| **Current Usage** | API endpoints at `/api/behavior/*` |
| **Removal Condition** | All endpoints migrated to `/api/v1/behaviour/*` or router removed |
| **Recommended Removal Stage** | Stage 2.0 |

**Endpoints:**
- `GET /api/behavior/summary`
- `GET /api/behavior/score`
- `GET /api/behavior/insights`

---

### 5. `backend/src/engines/reconciliation_engine.py::find_potential_matches_with_db()`

| Field | Value |
|-------|-------|
| **Location** | `backend/src/engines/reconciliation_engine.py:514-547` |
| **Purpose** | Backward-compatible wrapper that accepts `db_path` instead of transaction lists |
| **Current Usage** | Tests in `test_reconciliation.py`, `test_reconciliation_determinism.py` |
| **Removal Condition** | All tests use pure `find_potential_matches(debits, credits, ...)` function |
| **Recommended Removal Stage** | Stage 2.0 |

---

## Frontend Compatibility Layers

### 6. `frontend/lib/hooks/use-accounts.ts`

| Field | Value |
|-------|-------|
| **Location** | `frontend/lib/hooks/use-accounts.ts` |
| **Purpose** | Re-exports migrated `useManagedAccounts` hook; contains mutation hooks not yet migrated |
| **Current Usage** | Components using `useCreateAccount`, `useUpdateAccount`, `useDeleteAccount` |
| **Removal Condition** | Mutation hooks migrated to capability module |
| **Recommended Removal Stage** | Stage 1.13 (Accounts capability complete) |

**Migrated:**
- `useManagedAccounts` → re-exported from `@/lib/capabilities/accounts`

**Not Migrated:**
- `useCreateAccount`
- `useUpdateAccount`
- `useDeleteAccount`

---

### 7. `frontend/lib/hooks/use-cashflow.ts`

| Field | Value |
|-------|-------|
| **Location** | `frontend/lib/hooks/use-cashflow.ts` |
| **Purpose** | Re-exports migrated `useCashflow` hook |
| **Current Usage** | Components using `useCashflow` |
| **Removal Condition** | All imports updated to use `@/lib/capabilities/cashflow` directly |
| **Recommended Removal Stage** | Stage 1.13 (Cashflow capability complete) |

---

### 8. `frontend/lib/hooks/use-behavior-score.ts`

| Field | Value |
|-------|-------|
| **Location** | `frontend/lib/hooks/use-behavior-score.ts` |
| **Purpose** | Compatibility layer for behavior score hook |
| **Current Usage** | `BehaviorScoreCard` component |
| **Removal Condition** | Migrated to capability module |
| **Recommended Removal Stage** | Stage 1.13 (Behaviour capability) |

---

### 9. `frontend/lib/hooks/use-behavior-insights.ts`

| Field | Value |
|-------|-------|
| **Location** | `frontend/lib/hooks/use-behavior-insights.ts` |
| **Purpose** | Compatibility layer for behavior insights hook |
| **Current Usage** | `InsightsPanel` component |
| **Removal Condition** | Migrated to capability module |
| **Recommended Removal Stage** | Stage 1.13 (Behaviour capability) |

---

## Summary

| Layer | Type | Status | Removal Stage |
|-------|------|--------|---------------|
| `common/database.py` | Backend | Deprecated | Stage 2.0 |
| `engines/behavior_engine.py` | Backend | Deprecated | Stage 2.0 |
| `services/behavior_service.py` | Backend | Deprecated | Stage 2.0 |
| `routers/behavior.py` | Backend | Legacy | Stage 2.0 |
| `reconciliation_engine.py::find_potential_matches_with_db` | Backend | Compatibility | Stage 2.0 |
| `hooks/use-accounts.ts` | Frontend | Partial migration | Stage 1.13 |
| `hooks/use-cashflow.ts` | Frontend | Re-export only | Stage 1.13 |
| `hooks/use-behavior-score.ts` | Frontend | Compatibility | Stage 1.13 |
| `hooks/use-behavior-insights.ts` | Frontend | Compatibility | Stage 1.13 |