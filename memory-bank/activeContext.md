# Active Context

## Current Phase: Behaviour Engine Phase 8 — Persistence Layer (COMPLETE)

### Phase 8 Implementation Summary

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

**Test Coverage** (`backend/tests/`)
- Created `test_behaviour_repository.py` with 6 comprehensive test functions
- Created `test_alert_repository.py` with 7 comprehensive test functions
- Created `test_pattern_repository.py` with 8 comprehensive test functions
- Tests cover CRUD operations, constraints, isolation, and edge cases
- All tests use temporary databases for isolation
- Tests verify basis points conversion and data mapping

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

### Next Steps

1. **Service Layer Integration**: Create BehaviourService to orchestrate repository calls and engine functions
2. **API Endpoints**: Implement API endpoints for behaviour data retrieval and alert management
3. **Frontend Integration**: Update frontend to display behaviour patterns, alerts, and financial profiles
4. **Data Pipeline**: Create scheduled jobs to generate daily behaviour snapshots and detect patterns
5. **Alert Processing**: Implement alert generation and notification system

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