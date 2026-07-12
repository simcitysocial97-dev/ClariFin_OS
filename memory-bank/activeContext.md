# Active Context

## Current Phase: Behaviour Engine Phase 7 — Financial Wellness Score (COMPLETE)

### Phase 7 Implementation Summary

**Wellness Scoring Engine** (`backend/src/engines/behaviour_engine/wellness.py`)
- Implemented `compute_wellness_score()` function with composite scoring formula:
  - 30% Cashflow Health: cashflow_stability (0-1)
  - 20% Debt Health: (1 - (debt_cycle_score / 100))
  - 15% Savings Behaviour: max(0, savings_rate)
  - 20% Resilience: resilience_index (0-1)
  - 10% Lifestyle Control: 1 - min(max(lifestyle_inflation, 0), 1)
  - 5% Credit Behaviour: 0.5*(1-revolver_ratio) + 0.5*(1 - min(foir,1))
- Implemented `classify_wellness_band()` function with 5 bands:
  - 90-100: Excellent
  - 75-89: Healthy
  - 50-74: Developing
  - 25-49: Risk
  - <25: Critical
- All functions use Decimal for precise financial calculations
- All monetary values are integers in paise (₹1.00 = 100 paise)
- Functions are pure - no database access

**Tests**
- Created `backend/tests/test_behaviour_engine_wellness.py` with 20 comprehensive tests
- Test categories: score calculation, band classification, boundary conditions, determinism
- All 20 tests passing, validation: ruff clean, mypy clean

### Previous Phases (Reference)

#### Phase 1 Completion (Reference)
**Engine Layer** (`src/engines/account_engine/`)
- `lifecycle.py` — Account status transitions (ACTIVE/DORMANT/CLOSED)
- `dormant.py` — Dormancy detection (days since activity, configurable threshold)
- `balance.py` — Average balance, balance change, growth percentage (basis points)
- `cashflow.py` — Net flow, daily rate, income/expense ratio (basis points)
- `history.py` — Balance trend (IMPROVING/STABLE/DECLINING), velocity (paise/day)
- `metrics.py` — Aggregate deterministic account metrics

#### Behaviour Engine Phase 0 — Architecture Preparation (COMPLETE)
- Created `backend/docs/behaviour_engine_architecture.md` with input data sources, service boundaries, repository dependencies, and engine responsibilities
- Created `backend/src/models/financial_event.py` with FinancialEvent DTO, EventType Literal, FinancialEventBatch, and BehaviourInput interfaces

#### Behaviour Engine Phase 1 — Core Metrics (COMPLETE)
- Created `backend/src/engines/behaviour_engine/` package with pure functions
- Five metric modules: `utils.py`, `savings.py`, `cashflow.py`, `resilience.py`, `lifestyle.py`
- 10 functions for savings, cashflow, resilience, and lifestyle analysis

#### Behaviour Engine Phase 2 — Debt Intelligence (COMPLETE)
- Added debt metrics: `compute_credit_dependency_ratio`, `compute_debt_cycle_score`, `compute_foir`, `compute_credit_revolver_ratio`

#### Behaviour Engine Phase 3 — Pattern Detection (COMPLETE)
- Created `patterns.py` with 5 pattern detection functions for impulse transactions, recurring merchants, and subscription patterns

#### Behaviour Engine Phase 4 — Income Intelligence (COMPLETE)
- Created `income.py` with income classification and diversification analysis functions

#### Behaviour Engine Phase 5 — Account Intelligence (COMPLETE)
- Created `account.py` with account concentration, idle cash detection, and balance volatility analysis

#### Behaviour Engine Phase 6 — Financial Personality Classification (COMPLETE)
- Created `profile.py` with `classify_financial_personality()` function for 5 personality profiles

### Next Steps
- Integrate wellness scoring into the behaviour engine service layer
- Create API endpoints for wellness score retrieval and classification
- Update frontend dashboard to display wellness scores and bands
- Implement wellness score trend analysis over time

### CGC MCP Verification (Completed)

**Status:** CodeGraphContext MCP server is fully operational.

**Indexing Statistics:**
- 358 files indexed
- 2,790 functions parsed
- 249 classes extracted
- 1,590 parameters captured

**Tools Verified:**
- ✅ `find_code("SymbolName")` - Returns full source code with INDEX_SOURCE=true
- ✅ `execute_cypher_query` - Working for graph traversal
- ✅ `find_dead_code` - Identifies potentially unused functions
- ✅ `analyze_code_relationships` - Working for callers/callees analysis