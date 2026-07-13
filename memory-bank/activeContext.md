# Active Context

## Current Phase: Behaviour Engine Phase 8 — Persistence Layer + Service Layer (COMPLETE)

### Phase 8 + Service Layer Implementation Summary

**Database Schema Migration** (`backend/scripts/migration_005_behaviour_engine.py`)
- Created 4 new tables: `behaviour_snapshots`, `behaviour_patterns`, `behaviour_alerts`, `financial_profiles`
- All scores stored as INTEGER basis points (bps) for precision (10000 = 1.0)
- Added version column to behaviour_snapshots for future schema changes
- Added alert_code column to behaviour_alerts for unique alert identification
- Added config_json and metadata_json fields for extensibility
- Created comprehensive indexes for performance optimization
- Migration is idempotent with IF NOT EXISTS clauses

**Repository Layer** (`backend/src/repositories/`)
- Created `alert_repository.py` for behaviour alert operations
- Created `behaviour_repository.py` for behaviour snapshot operations
- Created `pattern_repository.py` for behaviour pattern operations
- All repositories inherit from BaseRepository and follow the same patterns
- Implemented CRUD operations with proper data mapping and type conversion
- Added household_id support with 'default' as the default value
- Implemented basis points to Decimal conversion for all score fields
- Added comprehensive query methods for different use cases

**Service Layer** (`backend/src/services/behaviour_service.py`)
- Created `BehaviourService` class with dependency injection for repositories
- Implemented 6 methods:
  - `compute_financial_profile()`: Fetches data, calls engines, persists snapshots, returns profile
  - `get_wellness_score()`: Returns latest wellness score with band and components
  - `get_debt_health()`: Returns debt health metrics (FOIR, credit dependency, revolver ratio)
  - `get_cashflow_health()`: Returns cashflow stability, surplus, income/expense stability
  - `get_patterns()`: Returns recent behaviour patterns (IMPULSE, SUBSCRIPTION, etc.)
  - `generate_monthly_summary()`: Generates comprehensive monthly financial summary
- All calculations delegated to behaviour_engine pure functions
- All persistence delegated to repositories
- Proper error handling with AppError and NotFoundError
- Added `_generate_alerts()` helper for financial alert generation

**Test Coverage** (`backend/tests/test_behaviour_service.py`)
- Created 12 comprehensive test functions covering all service methods
- Tests use mocks for repositories to verify engine delegation
- Tests cover success cases, error handling, and edge cases
- All tests pass with correct assertion values matching model expectations
- Fixed repository method call signatures (days parameter instead of limit)
- Fixed snapshot field names to match repository output format

### Key Design Decisions

1. **Monetary Precision**: All monetary values stored as INTEGER paise, all scores stored as INTEGER basis points
2. **Household Support**: Added household_id column with 'default' as default value for future multi-user support
3. **Extensibility**: Added JSON fields (config_json, metadata_json) for additional configuration without schema changes
4. **Versioning**: Added version column to behaviour_snapshots for future algorithm changes
5. **Alert Management**: Added alert_code for unique alert identification and resolution tracking

### Previous Phases (Reference)

#### Phase 7 Completion (Reference)
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

#### Behaviour Engine Phase 0 — Architecture Preparation (COMPLETE)
- Created `backend/docs/behaviour_engine_architecture.md` with input data sources, service boundaries, repository dependencies, and engine responsibilities
- Created `backend/src/models/financial_event.py` with FinancialEvent DTO, EventType Literal, FinancialEventBatch, and BehaviourInput interfaces

### Phase 10 Completion: Recommendation Engine

**Recommendation Engine** (`backend/src/engines/recommendation_engine/`)
- Created `recommendations.py` with 4 deterministic recommendation rules:
  - `check_debt_dependency()`: IF ratio > 20% → "Your lifestyle is partly funded by borrowed money"
  - `check_foir()`: IF ratio > 50% → "Fixed obligations are high"
  - `check_liquidity()`: IF months < 3 → "Emergency fund required"
  - `detect_subscription_growth()`: Detects subscription changes for "Review subscriptions"

**Recommendation Model** (in `recommendations.py`)
- `Recommendation` class with title, reason, metric, severity, suggested_action
- Severity levels: LOW, MEDIUM, HIGH, CRITICAL
- All functions are pure - no database access

**Test Coverage** (`backend/tests/test_recommendation_engine.py`)
- 34 tests covering all rules with positive/negative cases
- Tests for required fields, determinism, and sorting by severity
- All tests pass

### Next Steps

1. **API Endpoints**: Implement API endpoints for behaviour data retrieval and alert management
2. **Frontend Integration**: Update frontend to display behaviour patterns, alerts, and financial profiles
3. **Data Pipeline**: Create scheduled jobs to generate daily behaviour snapshots and detect patterns
4. **Alert Processing**: Implement alert generation and notification system

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