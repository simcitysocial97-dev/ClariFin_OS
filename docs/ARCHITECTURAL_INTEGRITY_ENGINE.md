# Architectural Integrity Engine (Program 10)

The Architectural Integrity Engine (AIE) is the constitutional layer of the Financial OS.
Its responsibility is to ensure that the architecture can never silently drift away from
its intended design.

## Architecture

The AIE lives in `runtime/foundation/integrity/` and consists of seven files:

| File | Purpose |
|------|---------|
| `models.py` | Immutable dataclasses: `IntegrityReport`, `Violation`, `ViolationCategory`, `ViolationSeverity`, `RuleReference` |
| `registry.py` | The constitutional rule registry — 28 immutable rules with metadata |
| `scanner.py` | Deterministic source scanning using Python AST, text analysis, cross-layer map, and repository graph |
| `rules.py` | 28 individual rule check functions |
| `engine.py` | `ArchitecturalIntegrityEngine.evaluate()` — orchestrates scan + rules → report |
| `formatter.py` | Professional terminal formatter |
| `__init__.py` | Package exports |

## Rule Registry

The registry defines all constitutional rules as immutable metadata. Rules are categorized
into three classes:

### Structural Rules (13)

Dependency direction, layer boundaries, forbidden imports, and circular dependency detection.

| Rule ID | Name | Severity |
|---------|------|----------|
| ARCH-001 | Router may not import Engine | HIGH |
| ARCH-002 | Component may not call API directly | HIGH |
| ARCH-003 | Mapper must not import React | LOW |
| ARCH-004 | Workspace must not perform fetch | HIGH |
| ARCH-009 | No circular layer dependencies | CRITICAL |
| ARCH-011 | Service may not import Router | HIGH |
| ARCH-012 | DTO may not import Service | MEDIUM |
| ARCH-013 | Mapper must not import Capability | MEDIUM |
| ARCH-014 | ViewModel must not import Component | LOW |
| ARCH-015 | Workspace must not import Mapper directly | MEDIUM |
| ARCH-016 | Component may not import Engine | HIGH |
| ARCH-017 | DTO may not import Router | MEDIUM |
| ARCH-018 | Capability must not import Component | MEDIUM |

### Ownership Rules (8)

Single source of truth enforcement across the cross-layer map.

| Rule ID | Name | Severity |
|---------|------|----------|
| ARCH-005 | Capability required for every endpoint | HIGH |
| ARCH-006 | Every capability requires exactly one mapper | MEDIUM |
| ARCH-007 | Every mapper returns ViewModel | MEDIUM |
| ARCH-008 | No duplicate endpoint ownership | HIGH |
| ARCH-019 | Every mapper is referenced by exactly one capability | MEDIUM |
| ARCH-020 | Every ViewModel is referenced by exactly one mapper | LOW |
| ARCH-021 | Every component belongs to exactly one workspace | MEDIUM |
| ARCH-022 | Every workspace has at least one component | LOW |

### Evolution Rules (7)

Prevent architectural drift as the codebase grows.

| Rule ID | Name | Severity |
|---------|------|----------|
| ARCH-010 | Page must not bypass Workspace registration | HIGH |
| ARCH-023 | Every endpoint must appear in the cross-layer map | MEDIUM |
| ARCH-024 | Every graph renderer is owned by a workspace | LOW |
| ARCH-025 | Every public API endpoint has verification coverage | MEDIUM |
| ARCH-026 | Every capability has test coverage | MEDIUM |
| ARCH-027 | Every mapper file is referenced in the cross-layer map | LOW |
| ARCH-028 | No orphaned workspace pages | LOW |

## Violation Lifecycle

1. **Scan**: `ArchitecturalScanner` discovers source files, parses imports (AST for Python,
   text analysis for TypeScript), loads the cross-layer map and repository graph.
2. **Evaluate**: `ArchitecturalIntegrityEngine.evaluate()` runs every rule against the scan
   result. Each rule check function returns a list of `Violation` objects.
3. **Report**: `format_integrity_report()` renders the `IntegrityReport` as a professional
   terminal table with severity-colored output.

Violations are immutable and deterministic for a given repository state. The engine never
modifies code, repairs code, or rewrites files.

## How Integrity Differs from Verification

| Aspect | Verification (Program 7B) | Integrity (Program 10) |
|--------|--------------------------|----------------------|
| Purpose | Execute test suites against changed files | Detect architectural violations |
| Scope | Changed files only | Entire repository |
| Output | Test pass/fail per target | Constitutional rule violations |
| Mutation | Can trigger test execution | Read-only, never modifies code |
| Determinism | Depends on test results | Purely structural analysis |
| Artifacts consumed | Cross-layer map, graph, profiles | Cross-layer map, graph, source files |

## How Integrity Differs from Linting

| Aspect | Linting | Integrity |
|--------|---------|-----------|
| Focus | Code style, syntax, anti-patterns | Architectural layer boundaries |
| Rules | Style conventions | Constitutional architecture rules |
| Scope | Per-file or per-function | Cross-file, cross-layer |
| Output | Style violations | Architectural violations with suggested engineering actions |
| Determinism | Depends on linter config | Purely structural, no config needed |

## CLI Usage

```bash
python runtime/verify.py integrity
```

Example PASS output:

```
================================================
Architectural Integrity
PASS
Rules
28
Violations
0
Critical
0
High
0
Medium
0
Low
0
================================================
```

Example violation output:

```
ARCH-002
HIGH
frontend/components/dashboard/card.tsx
Direct API call detected.
Expected
Component → Capability → Mapper
Found
Component → fetch()
```

## Scanner Design

The scanner uses two parsing strategies:

1. **Python files**: Parsed with the `ast` module for exact import extraction.
2. **TypeScript files**: Text-level scanning for import statements, `fetch()` calls,
   and `useWorkspaceRegistration` usage.

The scanner produces an `ArchitecturalGraph` containing:
- `files`: All discovered source files with layer classification and import data
- `cross_layer_map`: The cross-layer map JSON
- `graph_nodes` / `graph_edges`: The repository graph from `index.json`
- `files_scanned`: Total count of scanned files
- `scan_errors`: Any errors encountered during scanning

## Layer Classification

Files are classified into canonical layers based on their path:

**Backend** (`backend/src/`):
- `engines/` → `backend_engine`
- `services/` → `backend_service`
- `routers/` → `backend_router`
- `core/dtos/`, `models/` → `backend_dto`
- `repositories/` → `backend_repository`

**Frontend** (`frontend/`):
- `lib/api/` → `frontend_api`
- `lib/capabilities/` → `frontend_capability`
- `lib/mappers/` → `frontend_mapper`
- `types/*view-model*` → `frontend_viewmodel`
- `lib/workspace/`, `lib/runtime/` → `frontend_workspace`
- `components/` → `frontend_component`
- `app/*/page.tsx` → `frontend_page`