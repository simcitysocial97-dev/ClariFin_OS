# Backend Modernization Progress - COMPLETED

## Summary of Changes

### Phase 1: Schema Consistency Report - COMPLETE
- **Canonical Schema**: `amount_paise INTEGER` (stored in paise)
- **DEPRECATED**: `amount REAL` column removed from INSERT statements
- **Reconciliations Schema**: Updated to use `amount_paise INTEGER` instead of `amount REAL`

### Files Modified

1. **backend/src/db.py**
   - Changed reconciliations table schema from `amount REAL` to `amount_paise INTEGER`

2. **backend/src/repositories/transaction_repository.py**
   - Removed `amount` column from INSERT statements in `insert_transactions()`
   - Removed `amount` column from INSERT statements in `insert_csv_transactions()`
   - Cleaned up unused variables (`amount`, `raw_description`)

3. **backend/tests/test_reconciliation.py**
   - Fixed `populated_db` fixture to use `amount_paise` instead of `amount`
   - Removed `debit` and `credit` from INSERT (they are GENERATED columns)
   - Added `ReconciliationRepository` import
   - Fixed tests to use `ReconciliationRepository` instead of non-existent `db` methods

4. **backend/tests/test_reconciliation_determinism.py**
   - Fixed INSERT statements to use `amount_paise` 
   - Removed `debit`/`credit` from INSERT (GENERATED columns)
   - Fixed `amount` to `amount_paise` in test assertions

5. **backend/tests/test_repository_smoke.py**
   - Fixed INSERT statements to use `amount_paise` instead of `amount`

6. **backend/tests/test_audit_minimal.py**
   - Fixed INSERT to use `amount_paise` instead of `amount`

7. **backend/tests/test_behavior_engine.py**
   - Completely rewritten with canonical schema (`amount_paise INTEGER`, `debit INTEGER`, `credit INTEGER`)
   - Fixed all fixtures to match new schema

8. **backend/tests/test_db.py**
   - Rewritten to use repositories instead of non-existent `db` methods
   - Added proper imports

9. **backend/tests/test_determinism.py**
   - Fixed `amount` to `amount_paise` in UPDATE test

10. **backend/scripts/generate_synthetic_data.py**
    - Updated INSERT to use `amount_paise` instead of deprecated `amount` column
    - Fixed type hints from `Dict`/`List` to `dict`/`list`

### Test Results
- **93 tests passing** (was 0 before)
- All schema consistency issues resolved
- All tests use the canonical `amount_paise INTEGER` column

### Phase 2: Dependency Cleanup - COMPLETE
- Removed polluted root `.venv` (756MB, unrelated packages: reflex, redis, socketio)
- Removed incomplete `backend/venv` (missing key packages)
- Created clean `backend/venv` with 45 packages from canonical requirements.txt
- All imports verified: fastapi, pydantic, pandas, pdfplumber, camelot, cachetools, pytest
- Fixed package.json to reference `backend/venv` instead of root `.venv`
- Updated .gitignore with `env/` entry for completeness

### Next Steps

- Removed obsolete amount column migration code from `_create_tables()` (13 lines)
- Removed legacy amount column drop logic from `_run_migrations()` (93 lines)

---

## CGC Token Efficiency Audit - COMPLETED

### Changes Made
- **Updated .clinerules Section 2**: Clarified that `find_code` returns complete source code (INDEX_SOURCE=true) and `read_file` should NOT be called after it
- **Updated .clinerules Section 3**: Fixed Phase A wording to emphasize source is already available in CGC results
- **Updated .cgcignore**: Added `**/error-context.md` and `**/__snapshots__/**` patterns to reduce index bloat from test artifacts
- **Updated CGC .env**: Added `TOOL_RESULT_LIMITS={"find_code": 10, "analyze_code_relationships": 10, "execute_cypher_query": 20}` to limit response sizes

### Token Savings Expected
- Eliminated duplicate `read_file` after `find_code`: ~300-500 tokens per symbol lookup
