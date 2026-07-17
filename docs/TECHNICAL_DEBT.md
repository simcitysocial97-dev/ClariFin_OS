# Technical Debt Register

This document records genuine architectural debt in the ClariFin_OS codebase. Each entry includes impact assessment and recommended remediation stage.

---

## TD-001: Duplicate `behavior`/`behaviour` Modules

| Field | Value |
|-------|-------|
| **ID** | TD-001 |
| **Title** | Duplicate US/UK spelling modules for behavior analysis |
| **Location** | `backend/src/engines/behavior_engine.py` and `backend/src/engines/behaviour_engine/` |
| **Why It Exists** | Historical migration from US to UK spelling; both versions kept for backward compatibility |
| **Impact** | - Code duplication and maintenance burden<br>- Confusion for developers<br>- Two sources of truth for same logic |
| **Priority** | MEDIUM |
| **Recommended Stage** | Stage 2.0 |
| **Estimated Effort** | 2 days (update imports, remove legacy files, update tests) |

**Details:**
- `behavior_engine.py` is deprecated and delegates to `behaviour_engine/` package
- `behavior_service.py` delegates to `behaviour_service.py`
- `routers/behavior.py` uses `BehaviorService` instead of `BehavourService`
- All new code should use UK spelling (`behaviour`)

---

## TD-002: Legacy Engine DB Access Pattern

| Field | Value |
|-------|-------|
| **ID** | TD-002 |
| **Title** | Engines with direct SQLite access violate layer purity |
| **Location** | `backend/src/engines/balance_engine.py`, `backend/src/engines/ledger_audit_engine.py` |
| **Why It Exists** | These engines were created before the repository pattern was fully established; used for audit and CLI tools |
| **Impact** | - Violates Repository Boundary Rule<br>- Makes testing harder (requires real DB)<br>- Not pure functions |
| **Priority** | LOW (acceptable per §9 of ARCHITECTURE_CONSTRAINTS.md) |
| **Recommended Stage** | Stage 2.0 (optional refactoring) |
| **Estimated Effort** | 3 days (create repository methods, refactor engine functions) |

**Details:**
- `balance_engine.py`: Functions `compute_running_balance`, `compute_account_balance`, `validate_statement_balance`, `get_accounts_list` all use `sqlite3.connect()` directly
- `ledger_audit_engine.py`: Read-only audit functions that query database directly
- Per ARCHITECTURE_CONSTRAINTS.md §9: "Acceptable for audit tools; refactor other engines"

---

## TD-003: Incomplete Capability Migration

| Field | Value |
|-------|-------|
| **ID** | TD-003 |
| **Title** | Frontend hooks partially migrated to capability pattern |
| **Location** | `frontend/lib/hooks/use-accounts.ts`, `frontend/lib/hooks/use-cashflow.ts`, `frontend/lib/hooks/use-behavior-score.ts`, `frontend/lib/hooks/use-behavior-insights.ts` |
| **Why It Exists** | Migration in progress; query hooks migrated but mutation hooks remain in compatibility layer |
| **Impact** | - Inconsistent import patterns<br>- Some hooks in `lib/hooks/`, some in `lib/capabilities/`<br>- Mutation hooks not using shared query runtime |
| **Priority** | LOW |
| **Recommended Stage** | Stage 1.13 |
| **Estimated Effort** | 1 day (migrate mutation hooks, update imports) |

**Details:**
- `useManagedAccounts` migrated to capability, but `useCreateAccount`, `useUpdateAccount`, `useDeleteAccount` remain in compatibility layer
- `useCashflow` fully migrated
- `useBehaviorScore` and `useBehaviorInsights` not yet migrated

---

## TD-004: Legacy Reconciliation Engine Wrapper

| Field | Value |
|-------|-------|
| **ID** | TD-004 |
| **Title** | `find_potential_matches_with_db()` backward compatibility |
| **Location** | `backend/src/engines/reconciliation_engine.py:514-547` |
| **Why It Exists** | Tests were written before pure function pattern was established |
| **Impact** | - Tests couple to database<br>- Not pure function testing |
| **Priority** | LOW |
| **Recommended Stage** | Stage 2.0 |
| **Estimated Effort** | 1 day (update tests to use pure function) |

---

## TD-005: Dual Router Paths for Behavior

| Field | Value |
|-------|-------|
| **ID** | TD-005 |
| **Title** | Two router paths for behavior endpoints |
| **Location** | `backend/src/routers/behavior.py` and `backend/src/routers/behaviour.py` |
| **Why It Exists** | Migration from US to UK spelling; both routers registered |
| **Impact** | - API confusion<br>- Two endpoints for same functionality<br>- `/api/behavior/*` vs `/api/v1/behaviour/*` |
| **Priority** | MEDIUM |
| **Recommended Stage** | Stage 2.0 |
| **Estimated Effort** | 1 day (remove legacy router, update frontend) |

---

## TD-006: Missing Type Safety in Some Engine Functions

| Field | Value |
|-------|-------|
| **ID** | TD-006 |
| **Title** | Some engine functions return `float` for monetary values |
| **Location** | `backend/src/engines/reconciliation_engine.py` |
| **Why It Exists** | Backward compatibility with existing API responses |
| **Impact** | - Mixed int/float for monetary values<br>- Potential precision issues in display |
| **Priority** | LOW |
| **Recommended Stage** | Stage 2.0 |
| **Estimated Effort** | 1 day (update return types, ensure paise integers) |

**Details:**
- `find_potential_matches` returns `"amount": amount_paise / 100` (float in rupees)
- Should return integer paise for consistency

---

## Summary

| ID | Title | Priority | Stage | Effort |
|----|-------|----------|-------|--------|
| TD-001 | Duplicate behavior/behaviour modules | MEDIUM | 2.0 | 2 days |
| TD-002 | Legacy engine DB access | LOW | 2.0 | 3 days |
| TD-003 | Incomplete capability migration | LOW | 1.13 | 1 day |
| TD-004 | Legacy reconciliation wrapper | LOW | 2.0 | 1 day |
| TD-005 | Dual router paths | MEDIUM | 2.0 | 1 day |
| TD-006 | Missing type safety in engines | LOW | 2.0 | 1 day |

**Total Estimated Remediation Effort:** 9 days (Stage 2.0)