# P2.5 - Production Route Truth Audit

## 🎯 Objective
Determine which failures reported in P2.4 are **real production defects** vs **stale tests**, **dead code**, or **legacy architecture no longer used**.

## 🔍 Evidence Gathering Summary

### Phase 1: Router Surface Mapping ✅
**17 Production Routers Identified**:

| ROUTER | ROUTE | HTTP METHOD | ENDPOINT HANDLER | STATUS |
|--------|-------|-------------|------------------|--------|
| accounts | /api/accounts | POST | create_account | ✅ WORKING |
| cards | /api/cards | POST | create_card | ✅ WORKING |
| transactions | /api/transactions | GET | get_transactions | ❌ MISSING METHOD |
| dashboard | /api/overview | GET | get_overview | ❌ MISSING METHOD |
| dashboard | /api/dashboard/summary | GET | api_dashboard_summary | ❌ MISSING METHOD |
| dashboard | /api/statements | GET | get_statements | ❌ MISSING METHOD |
| dashboard | /api/cashflow/monthly | GET | api_cashflow_monthly | ❌ ENGINE MISMATCH |
| dashboard | /api/cashflow/breakdown | GET | api_cashflow_breakdown | ❌ ENGINE MISMATCH |
| dashboard | /api/networth | GET | api_networth | ❌ ENGINE MISMATCH |
| dashboard | /api/networth/trend | GET | api_networth_trend | ❌ ENGINE MISMATCH |
| dashboard | /api/networth/allocation | GET | api_networth_allocation | ❌ ENGINE MISMATCH |
| recurring | /api/recurring | GET/POST | get/create_recurring | ✅ WORKING |
| imports | /api/imports | GET | list_imports | ❌ MISSING METHOD |
| upload | /api/upload | POST | upload_file | ✅ WORKING |
| loans | /api/loans | GET/POST | get/create_loan | ✅ WORKING |
| investments | /api/investments | GET/POST | get/create_investment | ✅ WORKING |
| snapshots | /api/snapshots | GET | get_snapshots | ❌ MISSING METHOD |

## 📊 Missing Method Investigation ✅

### 1. `get_overview_stats()`

**References Found**:
- `backend/src/routers/dashboard.py:211`

**Classification**: **ACTIVE PRODUCTION**
- ✅ Called by production route `/api/overview`
- ✅ Used by dashboard overview endpoint
- ❌ Method does not exist in FinanceDB class
- **Impact**: Dashboard overview broken

### 2. `get_all_transactions_with_bank()`

**References Found**:
- `backend/src/routers/dashboard.py:214` (dashboard summary)
- `backend/src/routers/dashboard.py:500` (dashboard summary)
- `backend/src/routers/transactions.py:43` (transactions listing)

**Classification**: **ACTIVE PRODUCTION**
- ✅ Called by 3 production routes
- ✅ Critical for transaction listing and dashboard
- ❌ Method does not exist in FinanceDB class
- **Impact**: Transaction listing and dashboard broken

### 3. `get_statements_paginated()`

**References Found**:
- `backend/src/routers/dashboard.py:622`

**Classification**: **ACTIVE PRODUCTION**
- ✅ Called by production route `/api/statements`
- ✅ Used for statement management
- ❌ Method does not exist in FinanceDB class
- **Impact**: Statement management broken

### 4. `list_statement_imports()`

**References Found**:
- `backend/src/routers/imports.py:938`
- `backend/src/db/repos/imports_repo.py:155` (method exists in repo)

**Classification**: **ACTIVE PRODUCTION**
- ✅ Called by production route `/api/imports`
- ✅ Method exists in imports_repo but not exposed in FinanceDB
- ❌ Missing FinanceDB wrapper method
- **Impact**: Statement import tracking broken

## 🔧 Engine Architecture Investigation ✅

### Cashflow Engine Mismatch

**Evidence**:
```python
# Router calls (backend/src/routers/dashboard.py:753):
result = compute_monthly_cashflow(DB_PATH, months=months)

# Engine signature (backend/src/engines/cashflow_engine.py:29):
def compute_monthly_cashflow(db: "FinanceDB", months: int = 12) -> list[dict]:
```

**Classification**: **ACTIVE PRODUCTION BREAKAGE**
- ✅ Engine expects `FinanceDB` object
- ❌ Router passes `DB_PATH` string
- **Root Cause**: Architecture inconsistency
- **Impact**: All cashflow endpoints broken

### Net Worth Engine Mismatch

**Evidence**:
```python
# Router calls (backend/src/routers/dashboard.py:804, 821):
result = compute_net_worth(DB_PATH)
result = compute_net_worth_trend(DB_PATH, months=months)

# Engine signatures (backend/src/engines/networth_engine.py:27, 122):
def compute_net_worth(db: "FinanceDB") -> dict:
def compute_net_worth_trend(db: "FinanceDB", months: int = 12) -> list[dict]:
```

**Classification**: **ACTIVE PRODUCTION BREAKAGE**
- ✅ Engine expects `FinanceDB` object
- ❌ Router passes `DB_PATH` string
- **Root Cause**: Architecture inconsistency
- **Impact**: All net worth endpoints broken

## 🎯 Production Path Verification ✅

### FinanceDB vs DB_PATH Architecture

**Current State**:
- **New Pattern**: Most routers use `db = get_db()` (FinanceDB object)
- **Old Pattern**: Some routers pass `DB_PATH` string directly to engines
- **Inconsistency**: Engines expect FinanceDB but some routers pass strings

**Evidence of FinanceDB Pattern (Working)**:
```python
# Accounts router (WORKING):
db = get_db()
result = db.create_account(account)

# Cards router (WORKING):
db = get_db()
result = db.create_card(card)

# Recurring router (WORKING):
db = get_db()
recurring_id = db.insert_recurring_transaction(recurring_dict)
```

**Evidence of DB_PATH Pattern (Broken)**:
```python
# Dashboard router (BROKEN):
from src.engines.cashflow_engine import compute_monthly_cashflow
result = compute_monthly_cashflow(DB_PATH, months=months)
```

## 🏷️ Production Truth Matrix

| ISSUE | REAL PRODUCTION BUG? | EVIDENCE | IMPACT |
|-------|---------------------|----------|--------|
| `get_overview_stats` missing | ✅ YES | Called by `/api/overview` route | Dashboard broken |
| `get_all_transactions_with_bank` missing | ✅ YES | Called by 3 routes | Transactions & dashboard broken |
| `get_statements_paginated` missing | ✅ YES | Called by `/api/statements` | Statement management broken |
| `list_statement_imports` missing | ✅ YES | Called by `/api/imports` | Import tracking broken |
| Cashflow engine mismatch | ✅ YES | DB_PATH vs FinanceDB | All cashflow endpoints broken |
| Net worth engine mismatch | ✅ YES | DB_PATH vs FinanceDB | All net worth endpoints broken |

## ✅ Safe to Fix

**Critical Production Issues**:
1. `get_overview_stats()` - Add to FinanceDB
2. `get_all_transactions_with_bank()` - Add to FinanceDB
3. `get_statements_paginated()` - Add to FinanceDB
4. `list_statement_imports()` - Add to FinanceDB (wrapper for existing repo method)
5. **Engine Architecture** - Unify to use FinanceDB objects consistently

## ❌ Do Not Fix (Not Real Issues)

**None identified** - All reported issues are real production problems

## ⚠️ Needs Human Decision

**Architecture Strategy**:
- Should we migrate all engines to use FinanceDB objects?
- Should we keep DB_PATH for some legacy compatibility?
- Decision affects: cashflow_engine, networth_engine, snapshot_engine

## 📊 Summary

### Active Breakages (6/6 are real production issues)
1. ✅ `get_overview_stats` - Dashboard overview
2. ✅ `get_all_transactions_with_bank` - Transaction listing
3. ✅ `get_statements_paginated` - Statement management
4. ✅ `list_statement_imports` - Import tracking
5. ✅ Cashflow engine architecture mismatch
6. ✅ Net worth engine architecture mismatch

### False Positives: 0
- No test-only failures found
- No dead code found
- All reported issues affect production

### Stale Tests: 0
- All test failures correspond to real production issues

### Legacy Architecture
- DB_PATH string pattern used in some engines
- FinanceDB object pattern used in most routers
- Inconsistency causes production failures

## 🎯 Recommendations

1. **Fix Critical Methods**: Add 4 missing FinanceDB methods
2. **Unify Architecture**: Standardize on FinanceDB objects
3. **Test Coverage**: All failures represent real issues - fix them
4. **No Dead Code**: All reported methods are actively used

**Priority**: All 6 issues are critical production breakages requiring immediate attention.