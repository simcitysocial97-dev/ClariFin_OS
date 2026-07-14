# US/UK Consolidation Recommendation Note

**Date:** 13/07/2026
**Author:** AI Agent
**Status:** For consideration - not yet executed

## Current State

The codebase currently maintains two parallel behaviour systems due to spelling conventions:
- **US System (LIVE):** `routers/behavior.py`, `services/behavior_service.py`, `engines/behavior_engine.py`
- **UK System (NEW):** `routers/behaviour.py`, `services/behaviour_service.py`, `engines/behaviour_engine/`

## Architectural Differences

| Aspect | US (behavior_engine.py) | UK (behaviour_engine/) |
|--------|------------------------|------------------------|
| Architecture | Monolithic single file | Modular (8 files) |
| Database Access | Direct `sqlite3.connect()` calls | Pure functions (no DB) |
| Financial Events | Not integrated | Integrated (Phase 6/7) |
| Cashflow Engine | Not integrated | Integrated (Phase 7) |
| India-Specific Signals | Partial (via detect_india_risk_patterns) | Full (8 dedicated functions) |
| API Routes | `/api/behavior/*` | `/api/v1/behaviour/*` |

## Recommended Consolidation Strategy

### Phase 1: Assessment (Recommended timing: after US system stabilizes)
1. **Feature parity audit:** Compare US vs UK endpoints
   - US: `/summary`, `/score`, `/insights`
   - UK: `/profile`, `/wellness-score`, `/debt-health`, `/cashflow-health`, `/patterns`, `/recommendations`, `/monthly-report`, plus new Phase 8 endpoints

2. **Traffic analysis:** Identify which API routes are actively used by production clients
   - Router registration order in `api.py` may indicate route precedence
   - Check frontend imports for `api/behavior/*` vs `api/v1/behaviour/*`

### Phase 2: Migration Path
**Option A: UK → US (Merge new into old)**
- Pros: Preserves existing US route structure
- Cons: Re-introduces monolithic architecture, DB calls in engine layer
- Required changes:
  - Refactor US `behavior_engine.py` to extract pure functions (breaking change)
  - Update router imports to new modular structure
  - Potential downtime during migration

**Option B: US → UK (Merge old into new)**
- Pros: Maintains clean modular architecture, preserves engine purity
- Cons: Breaking change for existing API clients
- Required changes:
  - Update frontend to use `/api/v1/behaviour/*` routes
  - Rename UK files to remove "behaviour" spelling for universal compatibility
  - Archive US files (do not delete - rollback option)

**Option C: Gradual dual-write (Recommended)**
- Run both systems in parallel temporarily
- New endpoints only on UK system
- Add feature flag to route to UK implementation
- Migrate endpoints one-by-one
- Deprecate US system after verification

### Phase 3: Implementation
1. Create canonical `behaviour_engine/` structure (merge UK enhancements)
2. Create backward-compatible router wrapper:
   - US routes delegate to UK service with response format translation
   - New routes remain on UK structure
3. Add deprecation warnings to US endpoints
4. Update ARCHITECTURE.md to remove duplicate entry

## When to Execute

Execute consolidation when:
1. US endpoints are stable (confirmation via user)
2. UK Phase 8 signals are validated in production
3. Frontend migration plan is confirmed (to avoid breaking changes)
4. A maintenance window is available for API route updates

## Specific Recommendations

- **Do NOT delete US files immediately** - archive with clear naming convention
- **Consider API versioning** - keep v1 on UK, migrate US to v0 or deprecate
- **Maintain both repositories** during transition - use UK as source of truth for new logic
- **Update `.clinerules`** post-consolidation to remove duplicate code warnings

---

**Next Steps:** This recommendation requires user approval before implementation.