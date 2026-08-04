# Cross-Layer Intelligence — Program 7A

## Architecture

The cross-layer intelligence system connects the full application stack into a deterministic dependency graph:

```
Backend Engine
    ↓
Backend Service
    ↓
Router
    ↓
Endpoint
    ↓
Capability
    ↓
Mapper
    ↓
ViewModel
    ↓
Workspace
    ↓
Component
    ↓
Graph Renderer
    ↓
Verification Tests
```

This is **not** a code search utility. It is part of the **Verification Runtime** — providing deterministic blast-radius analysis for changed files.

## Generation Pipeline

### Generator

`tools/generators/build_cross_layer_map.py` scans the canonical layer directories:

| Layer | Directory | What it discovers |
|-------|-----------|-------------------|
| A: Engine → Service | `backend/src/services/**/*.py` | `from src.engines...` imports → service classes |
| B: Service → Router → Endpoint | `backend/src/routers/**/*.py` | Router classes, endpoint decorators, HTTP methods, service imports |
| C: Endpoint → Capability | `frontend/lib/capabilities/**/*.ts` | API paths, hooks, mappers, view models |
| D: Capability → Workspace → Renderer | `frontend/app/`, `frontend/components/`, `frontend/lib/graph/` | `useCapability()` → page → workspace → components → renderer |

### Output

The generator produces `runtime/generated/cross-layer-map.json` — a deterministic, sorted JSON artifact.

Example entry for `backend/src/engines/loan_engine/amortization.py`:

```json
{
  "engine": "backend/src/engines/loan_engine/amortization.py",
  "services": ["LoanService", "LoanSimulationService", "LoanAnalysisService"],
  "routers": ["backend/src/routers/loans.py"],
  "endpoints": ["GET /api/loans/{loan_id}/schedule", "..."],
  "capabilities": ["useLoansCapability"],
  "mappers": ["loansMapper"],
  "viewModels": ["LoansViewModel"],
  "pages": ["app/loans/page.tsx"],
  "workspace": ["LoansWorkspace"],
  "components": ["AmortizationSchedule", "..."],
  "graphRenderers": ["components/graph/renderer/graph-renderer.tsx"],
  "tests": ["backend/tests/unit/engines/loan/test_amortization.py", "..."]
}
```

### Regeneration

```bash
python3 tools/generators/build_cross_layer_map.py
```

Validate:

```bash
python3 -m json.tool runtime/generated/cross-layer-map.json
```

## Planner Integration

`runtime/foundation/verification/planner/planner.py` gains:

### `CrossLayerImpactPlanner`

```python
from runtime.foundation.verification.planner.planner import CrossLayerImpactPlanner

planner = CrossLayerImpactPlanner()
report = planner.analyze_cross_layer_impact(
    ["backend/src/engines/loan_engine/amortization.py"]
)
```

### `ImpactReport`

The report contains:
- `affected_engines`, `affected_services`, `affected_routers`, `affected_endpoints`
- `affected_capabilities`, `affected_mappers`, `affected_view_models`
- `affected_pages`, `affected_workspaces`, `affected_components`
- `affected_tests`, `affected_runtimes`, `affected_ui`
- `dependency_chains` — full chain from changed file down to tests
- `verification_plan` — minimal minimal verification plan

### Blast Radius Example

When `backend/src/engines/loan_engine/amortization.py` changes:
- → `LoanService`
- → `GET /api/loans/{id}/schedule`
- → `useLoansCapability`
- → `loansMapper`
- → `LoansViewModel`
- → `LoansWorkspace`
- → `AmortizationSchedule`
- → contract tests, Playwright, unit tests

Unrelated engines (Dashboard, Cashflow, Forecast) are **not** included.

## Evidence Integration

`runtime/system/evidence/aggregator.py` is enhanced to enrich failure reports.

When a failing test exists, the aggregator appends:
- **Dependency Chain** — the full cross-layer path
- **Likely Origin** — the backend layer likely causing the issue
- **Likely Consumer** — the frontend component consuming the failed layer
- **Suggested Layer** — the correct architectural layer to fix

### Example

```
FAILED: useLoansCapability.contract.test.ts

Dependency Chain:
    loan_engine/amortization.py
    → LoanService
    → GET /api/loans/{id}/schedule
    → useLoansCapability
    → LoansWorkspace
    → AmortizationTable

Likely Fix: Loan DTO changed. Update frontend/lib/schemas/loans.ts
NOT AmortizationTable.
```

The aggregator recommends the **correct architectural layer** instead of merely naming the failing test.

## CI Integration

### Backend Workflow (`.github/workflows/backend-verify.yml`)

1. Generate cross-layer map once: `python3 tools/generators/build_cross_layer_map.py`
2. Upload as artifact: `cross-layer-map`
3. Generate verification plan using the map
4. Run selective tests (unit, contract, property, integration, mutation as needed)

### Frontend Workflow (`.github/workflows/frontend.yml`)

1. Generate cross-layer map once
2. Upload as artifact for evidence collection
3. Reuse the same map artifact

The map is generated once and shared across all jobs. It is never regenerated independently in multiple jobs.

## Validation

### Generator

```bash
cd /home/vasantha/AI-Projects/ClariFin_OS
python3 tools/generators/build_cross_layer_map.py
python3 -m json.tool runtime/generated/cross-layer-map.json
```

### Planner

```python
from runtime.foundation.verification.planner.planner import CrossLayerImpactPlanner
planner = CrossLayerImpactPlanner()
report = planner.analyze_cross_layer_impact(["backend/src/engines/loan_engine/amortization.py"])
assert "LoanService" in report.affected_services
assert "useLoansCapability" in report.affected_capabilities
assert "AmortizationSchedule" in report.affected_components
```

### Evidence Aggregator

```python
from runtime.system.evidence.aggregator import EvidenceAggregator, _load_cross_layer_map
```

Both import successfully.

## Limitations

### Known Constraints

1. **Discovery is AST-based, not runtime-based.** Conditional imports (lazy imports) may be missed.
2. **Path matching uses substring heuristics.** Template literal variables in API paths may not match exactly.
3. **Graph renderer detection is global.** The graph renderer is shared across workspaces and may appear in all chains.
4. **DTO changes are inferred, not explicitly parsed.** The suggested layer is derived from capability names, not from actual DTO files.
5. **The map must be regenerated** when the source code structure changes (new directories/files).

### Future Improvements

- Add Playwright test discovery for workspace-specific E2E tests
- Parse TypeScript types more precisely for ViewModel detection
- Add graph adapter file discovery
- Support lazy-loaded imports

## No Business Logic Changes

Program 7A introduces zero changes to:
- Backend engines, services, routers, endpoints, DTOs
- Frontend capabilities, mappers, view models, workspaces, components
- Graph runtime, workspace runtime, navigation runtime
- Any business logic

It is purely an observability layer.