# Engineering Workspace — Program 9

## Architecture

Engineering Workspace is a terminal-first presentation and navigation layer
over existing engineering artifacts produced by Programs 7–8.

It does not generate engineering information. It only consumes:

- `runtime/generated/dashboard.json`
- `runtime/generated/engineering-history.json`
- `runtime/generated/engineering-health.md`
- `runtime/generated/engineering-analytics.json`
- `runtime/generated/verification-report.md`
- `runtime/generated/cross-layer-map.json`
- `runtime/generated/verification-performance.json`
- `runtime/generated/dependency-growth.json`
- `runtime/generated/flaky-tests.json`
- `runtime/generated/cost-analysis.json`
- Diagnostic reports
- Risk reports
- Affected test plans

## Workspace Responsibilities

The Engineering Workspace is responsible for:

1. Loading existing runtime artifacts into immutable models
2. Presenting engineering status in beautiful terminal tables
3. Providing deterministic navigation over cross-layer dependencies
4. Surfacing verification history, metrics, and execution status

It is explicitly NOT responsible for:

- Generating verification plans
- Executing tests
- Producing analytics
- Modifying any artifact
- Mutating repository state

## Relationship with Programs 7–8

| Program | Responsibility | Workspace Interaction |
|---------|---------------|----------------------|
| Program 7A | Cross-layer dependency intelligence | Consumes `cross-layer-map.json` |
| Program 7B | Verification orchestration | Consumes `verification-cache.json`, `verification-report.md` |
| Program 8 | Developer intelligence, diagnostics, repair, risk, affected tests | Consumes `engineering-history.json`, `engineering-health.md`, `engineering-analytics.json` |

The workspace is a read-only consumer. Programs 7–8 continue to own artifact generation.

## Commands

### `python runtime/verify.py status`

Display repository status, verification status, planner status,
cross-layer status, engineering health, recent failures,
current verification cache, and risk summary.

Example:

```bash
python runtime/verify.py status
```

### `python runtime/verify.py metrics`

Render verification counts, local vs CI metrics, cache hit rate,
average duration, failure rate, flaky tests, dependency growth,
and risk distribution.

Example:

```bash
python runtime/verify.py metrics
```

### `python runtime/verify.py history`

Display recent verification events, recent failures, recent engineering
reports, timeline, and verification trends.

Example:

```bash
python runtime/verify.py history
```

### `python runtime/verify.py deps <file_path>`

Explore dependency chain for a given file.

Example:

```bash
python runtime/verify.py deps backend/src/engines/loan_engine/amortization.py
```

Output layers:

```
Engine
  ↓
Service
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
Page
  ↓
Workspace
  ↓
Renderer
  ↓
Tests
```

### `python runtime/verify.py verify-status`

Display verification profiles, last execution, cache usage,
planner decision, execution history, and pending verification.

Example:

```bash
python runtime/verify.py verify-status
```

## Modules

| Module | Purpose |
|--------|---------|
| `workspace.py` | Loads existing artifacts into immutable models |
| `models.py` | Immutable dataclasses for workspace data |
| `status.py` | Status workspace rendering |
| `metrics.py` | Metrics workspace rendering |
| `history.py` | History workspace rendering |
| `dependencies.py` | Dependency explorer rendering |
| `verification.py` | Verification workspace rendering |
| `formatter.py` | Professional terminal formatting |

## Immutable Models

All workspace models use frozen dataclasses. No model instance can be
modified after creation. This guarantees deterministic rendering and
thread-safe consumption.

## Deterministic Rendering

The workspace never mutates state. It reads artifacts and renders them.
Output is deterministic for identical input artifacts.

## Terminal Formatting

The formatter adapts to terminal width, uses Unicode box-drawing characters
when supported, and falls back to plain ASCII when not.

## No Browser UI

There is no React dashboard, no web server, and no browser interface.
The Engineering Workspace is terminal-only.
