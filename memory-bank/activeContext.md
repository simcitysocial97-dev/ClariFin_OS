# Active Context

## Stage 0 Complete

### Documentation Created (July 16, 2026)
- `ARCHITECTURE_CONSTRAINTS.md` — Immutable rulebook (207 lines)
- `CODE_GENERATION_CONTRACT.md` — AI execution rules (180 lines)
- `CHANGE_CONFIDENCE_PIPELINE.md` — Staged validation (176 lines)
- `DECISIONS.md` — 8 architectural decisions (151 lines)
- `CAPABILITY_MATURITY.md` — 4-level framework (155 lines)
- `STAGE0_REVIEW.md` — Review report ready

### Verdict: ✅ READY for Stage 1
- Consistent paise-integer convention across all docs
- No duplicated validation tooling
- Practical Transaction Exploration example provided

## Stage 1.1 — Capability Registry (July 17, 2026)

### Changes Made
- Extended `memory-bank/capability-registry.yaml` with schema fields:
  - `maturity` (functional|analytical|explainable|optimized)
  - `frontend_routes` (Next.js page routes)
  - `backend_routes` (API endpoints)
  - `query_keys` (hierarchical React Query keys)
  - `explainability` (summary/evidence/calculation/source flags)
  - `status` (active|deprecated|maintenance)
- Created `backend/src/core/capability_registry.py` — runtime loader with validation
- Created `scripts/validate-registry.py` — CLI validation for registry integrity
- Created `backend/tests/test_capability_registry.py` — 14 unit tests

### Validation Added
- Duplicate ID detection
- Duplicate query key detection
- Missing dependency detection
- Circular dependency detection

### Verification
- ✅ Registry validation passes (11 capabilities, 22 query keys)
- ✅ All 14 registry tests pass
- ✅ ruff check passes
- ✅ verify-change.sh passes