# Verification Ecosystem Integration Audit — Execution Progress

**Phase:** VEA-1 complete → VEA-2 Phase 1 in progress
**Execution mode:** Autonomous, milestone-driven
**Current status:** VEA-2 PHASE 1 — CERTIFICATION PASS (code); C10 CI parity PENDING

---

## VEA-1 Summary (Complete)

VEA-1 audit certified the verification ecosystem. See `docs/verification/VEA1_AUDIT_REPORT.md`.

**Finding:** The repository has substantial verification intelligence, but information is lost
at the boundaries between components. The system understands change→impact but fails to
propagate that understanding through verification planning and execution.

**Authority:** `runtime.foundation.architecture` provider is canonical for capabilities/chains.
`verification.yaml` registry has stale module paths. `profiles.py` tasks are audit-only
(never executed). `CrossLayerImpactPlanner` correctly computes blast radius but orchestrator
discards it before planning.

---

## VEA-2 Phase 1 — Integration Backbone Repair

### Current Milestone

**Acceptance: Backend DTO change → frontend verification**

Status: `DONE`

---

### Milestone Status

| Milestone | Status | Evidence |
|-----------|--------|----------|
| GAP-001: Changed-file detection (CI parity) | DONE | `orchestrator.py:_collect_changed_files()` now uses merge-base diff + untracked |
| GAP-003: Canonical capability paths | DONE | Verified provider paths are canonical; registry sync deferred to Phase 2 |
| GAP-004: Complete entity-kind recognition | DONE | Optimizer + blast radius now handle dto, mapper, view_model, model |
| GAP-002: Blast radius → planner wiring | DONE | Orchestrator passes blast_radius_scopes into PlanningContext |
| C4: Backend mapper/router → frontend bridge | DONE | `_enrich_backend_bridge_impact()` propagates standalone backend mapper/router to frontend consumers via chain map |
| Acceptance: DTO specimen | DONE | See acceptance test below |
| Acceptance: C4 backend mapper/router specimen | DONE | See acceptance test below |
| C10: CI changed-file parity (code) | DONE | `test_ci_and_local_changed_file_parity` proves CI env == local override == default |
| C11: Verification plan explainable (provenance) | DONE | `VerificationUnit.provenance` carries capabilities/impact_kinds/source on every unit |

---

### Changes Made (Phase 1)

#### 1. `runtime/foundation/verification/orchestrator.py`
- **GAP-001 fix**: `_collect_changed_files()` now supports:
  - Merge-base diff via `GITHUB_BASE_REF`, `GITHUB_REF...`, `GITHUB_SHA`, or `VERIFICATION_BASE_REF`
  - Untracked file detection via `git ls-files --others --exclude-standard`
  - Proper filtering (generated/, node_modules, pyc) via extracted `_filter_changed_files()`
- **GAP-002 fix**: `generate_plan()` now consumes `self._cross_layer_report` and passes
  - `changed_capabilities`, `changed_endpoints`, `blast_radius_scopes` into `PlanningContext`
  - New `_derive_scopes_from_impact()` maps impact signals to verification scopes
- Added `map_path` parameter to `VerificationOrchestrator.__init__` (test-injection seam)

#### 2. `runtime/foundation/verification/planner/planner.py`
- Added `blast_radius_scopes` field to `PlanningContext` dataclass
- `_merge_scopes()` now accepts and merges blast-radius-derived scopes
- `ImpactReport` extended with `affected_dtos` and `affected_models` fields
- `analyze_cross_layer_impact()` now falls back to intelligence `compute_blast_radius()` for
  files not resolved by chain-map lookup (DTOs, mappers, etc.)
- `_build_minimal_plan()` now triggers `run_frontend=True` for mapper/view_model impact
- Added `_enrich_from_intelligence()`, `_append_uniq()`, `_build_dependency_chains()` helpers

#### 3. `runtime/foundation/intelligence/platform/optimizer.py`
- **GAP-004 fix**: `impacted()` now recognizes `dto` kind → contract verification
- Added `backend-unit` suite (runs when any backend entity kind impacted)
- Added `frontend-typecheck-build` suite (runs `npx tsc --noEmit && npm run build` when frontend impacted)
- Extended frontend file detection to include frontend mapper paths

#### 4. `runtime/foundation/intelligence/platform/blast.py`
- Added `_enrich_dto_mapper_impact()` — bridges DTO→mapper→frontend gap using chain map
- Added `_infer_engine_from_dto()` — infers owning engine from DTO file name
- Added `_resolve_frontend_entity()` and `_resolve_frontend_path()` helpers
- DTOs now propagate to frontend mappers and view models via chain-map bridge
- Added `_enrich_backend_bridge_impact()` — C4: standalone backend `mapper`/`router`
  changes propagate to the frontend mappers/view models the owning engine consumes
  (bridges the cross-layer gap that ownership edges alone cannot reach)

#### 5. `runtime/tests/test_snapshots.py`
- Updated `test_verification_report_snapshot` to call `analyze_cross_layer()` before `generate_plan()`
- This ensures the snapshot test exercises the GAP-002 end-to-end path

#### 6. `runtime/tests/snapshots/verification-report.json`
- Regenerated to reflect GAP-002 behavior (blast radius → frontend scope escalation)

#### 7. `runtime/foundation/intelligence/platform/optimizer.py` (C11 provenance)
- Added `capabilities`, `impact_kinds`, `source` fields to `VerificationUnit`
- `to_dict()` now emits a nested `provenance` block (capabilities/impact_kinds/source)
- Every selected unit is populated with the affected capabilities, the blast-radius
  kinds that triggered it, and the evidence source (`ownership`, `blast-radius`,
  `chain-map+blast-radius`, `runtime-change`)

#### 8. `runtime/tests/test_engineering_intelligence.py`
- Added C11 tests: `test_every_selected_unit_carries_provenance`,
  `test_frontend_selection_provenance_records_chain_map_source`
- Added C4 tests: `test_backend_mapper_change_propagates_to_frontend`,
  `test_backend_router_change_propagates_to_frontend`,
  `test_backend_bridge_impact_is_evidence_backed`

#### 9. `runtime/tests/test_orchestrator.py` (C10 parity)
- Added `test_ci_and_local_changed_file_parity` — proves GITHUB_BASE_REF ==
  VERIFICATION_BASE_REF == default local path (same normalization + filtering)
- Added `test_changed_file_filter_excludes_generated_and_node_modules`

#### 10. Lint cleanup (pre-existing)
- Removed unused imports across runtime (`ruff --fix`): executor.py `typing.Any`,
  test_snapshots.py `pytest`, plus 129 other safe F401/F541 findings
- Fixed `planner.py` `datetime.utcnow()` deprecation → `datetime.now(timezone.utc)`
- 36 unsafe-fixable findings (dead assignments, generated-file E402, intentional
  `__init__` re-export) left untouched to avoid weakening unrelated code

---

### Acceptance Test Results

**Test: Backend DTO change → frontend verification**

```
CHANGE: backend/src/core/dtos/loans_dto.py

BLAST RADIUS (intelligence pipeline):
  dto: dto:backend/src/core/dtos/loans_dto.py
  dto: dto:backend/src/core/dtos/__init__.py
  mapper: mapper:backend/src/core/mappers/loan_mapper.py
  mapper: mapper:frontend/lib/mappers/loans-mapper.ts    ← NEW (enrichment)
  view_model: AmortizationEntryViewModel                 ← NEW (enrichment)

OPTIMIZER SELECTED:
  contracts-schemathesis
  backend-unit
  frontend-unit
  frontend-typecheck-build

ORCHESTRATOR PLAN (verify.py backend):
  bash .github/scripts/run_backend_verification.sh
  bash .github/scripts/run_fast_checks.sh
  bash .github/scripts/run_frontend_verification.sh     ← NEW (escalation)

PRE-FIX: 0 verification units (DTO → nothing)
POST-FIX: 4 verification units including frontend
```

**Test: Backend engine change → frontend verification**

```
CHANGE: backend/src/engines/loan_engine/emi.py

OPTIMIZER SELECTED:
  unit-targeted, contracts-schemathesis, backend-integration,
  backend-unit, frontend-unit, frontend-typecheck-build

ORCHESTRATOR PLAN:
  run_backend_verification.sh + run_frontend_verification.sh + run_fast_checks.sh

Impacted scopes: [contracts, property, backend, quick, frontend]
```

**Test: Frontend-only change → restraint**

```
CHANGE: frontend/types/loans-view-model.ts

SELECTED: frontend-unit + frontend-typecheck-build
SKIPPED: backend, contracts, integration (no backend entities impacted)
```

**Test: C4 — standalone backend mapper → frontend propagation**

```
CHANGE: backend/src/core/mappers/loan_mapper.py

INDIRECT (blast radius):
  mapper:frontend/lib/mappers/loans-mapper.ts    ← NEW (C4 bridge)
  view_model:AmortizationEntryViewModel         ← NEW (C4 bridge)

Evidence: graph=chain-map, via=backend/src/core/mappers/loan_mapper.py,
          relation=consumed-by / view-model
```

**Test: C4 — backend router → frontend propagation**

```
CHANGE: backend/src/routers/accounts.py

INDIRECT (blast radius):
  capability:useAccountsCapability
  mapper:frontend/lib/mappers/accounts-mapper.ts   ← NEW (C4 bridge)
  view_model:AccountDetailViewModel               ← NEW (C4 bridge)
```

---

### Test Suite

```
runtime/tests/ — 281 passed, 0 failed
ruff check (changed files) — All checks passed
ruff check (runtime/) — 36 pre-existing unsafe findings remain (left untouched)
```

---

### Validated Assumptions

| Assumption | Validated? |
|------------|------------|
| Chain map is provider-derived (canonical) | ✅ |
| Intelligence `compute_blast_radius` traces graph correctly | ✅ (with DTO enrichment) |
| Orchestrator `_cross_layer_report` was discarded before planning | ✅ (fixed) |
| Optimizer missed `dto` kind | ✅ (fixed) |
| Frontend build missing from CI | ⚠️ (optimizer now selects it; script fix in Phase 2) |

---

### Remaining Work (Phase 2+)

| Task | Gap | Priority |
|------|-----|----------|
| **C10 real-CI parity run** (confirm GITHUB_BASE_REF populated end-to-end) | GAP-001 | High |
| Add `--junitxml` to all test commands | GAP-005 | High |
| Add `npm run build` to `run_frontend_verification.sh` | GAP-006 | High |
| Sync `verification.yaml` capability modules to provider paths | GAP-003 | High |
| Structured failure classification in EvidenceAggregator | GAP-009 | Medium |
| Capability→test ownership mapping | GAP-008 | Medium |
| CI changed-file input for GITHUB_EVENT_PATH | GAP-001 | Medium |

---

### Known Limitations (Phase 1)

1. Frontend mapper/mapper kind not yet registered as a test-owning kind in optimizer
2. DTO→mapper and backend-bridge enrichment use name-based engine inference (not graph edges); coverage gaps possible when a mapper/router name does not match any engine keyword
3. Frontend dev environment not available locally (node_modules not installed)
4. `npm run build` not yet added to CI verification script (Phase 2)