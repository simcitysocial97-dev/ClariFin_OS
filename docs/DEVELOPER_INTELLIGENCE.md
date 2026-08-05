# Developer Intelligence Layer — Program 8

## Architecture

The Developer Intelligence Layer is a **deterministic, read-only** analysis engine that consumes repository state and produces engineering intelligence. It does not execute tests, modify files, or change any runtime behavior.

### Input Sources

| Source | Program | Purpose |
|--------|---------|---------|
| CrossLayerMap | 7A | Dependency chain mapping |
| Planner | 7B | Verification planning |
| Verification Profiles | 7B | Profile expansion |
| Observability History | 7C | Telemetry and risk context |
| Engineering Dashboard | 7C | Health and cost data |
| Git Diff | Git | Changed file detection |
| Git Status | Git | Working tree state |

### Output Models

| Model | Purpose |
|-------|---------|
| DiagnosticReport | Full diagnostic analysis of changes |
| RepairSuggestion | Deterministic engineering guidance |
| RiskReport | Quantified engineering risk score |
| AffectedTestPlan | Minimal deterministic test execution plan |

### Package Structure

```
runtime/foundation/intelligence/
    __init__.py          # Package exports
    models.py            # Immutable dataclasses
    diagnostics.py       # DeveloperDiagnostics engine
    repair.py            # RepairGuidance engine
    affected.py          # AffectedTestPlanner engine
    risk.py              # RiskAnalyzer engine
    formatter.py         # Terminal output formatting
```

## Flow

### Diagnostic Flow

1. Read changed files from git diff
2. Feed files into CrossLayerImpactPlanner (Program 7A)
3. Build dependency chains from the cross-layer map
4. Identify affected capabilities, workspaces, endpoints, and tests
5. Estimate verification profile and duration
6. Produce a DiagnosticReport

### Repair Guidance Flow

1. Consume dependency chains from the diagnostic report
2. For each changed entity type (capability, endpoint, router, mapper, view_model, workspace, graph_renderer, component), generate a deterministic suggestion
3. Every suggestion references the dependency graph
4. No speculative or heuristic recommendations

### Risk Calculation Flow

1. Consume the impact report from CrossLayerImpactPlanner
2. Score each changed layer type with a deterministic weight
3. Apply cross-layer depth multiplier
4. Classify severity based on score thresholds
5. Produce a RiskReport with score (0-100), severity, and reasons

### Affected Test Planner Flow

1. Consume the impact report from CrossLayerImpactPlanner
2. Classify affected tests by category (backend, frontend, runtime, playwright, contracts)
3. Produce a minimal, deterministic test plan with no unrelated tests

## Risk Scoring

| Factor | Weight |
|--------|--------|
| Engine changed | +15 |
| Service changed | +10 |
| Router changed | +12 |
| Endpoint changed | +10 |
| Capability changed | +10 |
| Mapper changed | +8 |
| ViewModel changed | +6 |
| Page changed | +5 |
| Workspace changed | +8 |
| Component changed | +4 |
| Graph renderer changed | +7 |
| Test changed | +3 |
| Cross-layer depth > 3 | +10 |
| Cross-layer depth > 1 | +5 |

### Severity Thresholds

| Score | Severity |
|-------|----------|
| 0-29 | LOW |
| 30-59 | MEDIUM |
| 60-79 | HIGH |
| 80-100 | CRITICAL |

## CLI Commands

```bash
python runtime/verify.py diagnose    # Full diagnostic analysis
python runtime/verify.py affected    # Affected test plan
python runtime/verify.py repair      # Repair guidance
python runtime/verify.py risk        # Risk analysis
```

## Design Principles

1. **Deterministic** — No heuristics, no randomness, no LLM
2. **Read-only** — Never modifies files or executes tests
3. **Composable** — Consumes Program 7 outputs (planners, profiles, telemetry)
4. **Immutable** — All output models use frozen dataclasses
5. **No business logic changes** — Only analyzes, never mutates