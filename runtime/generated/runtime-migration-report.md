# Program 13.2 — Runtime Canonical Architecture Migration

**Status:** COMPLETE (certification CERTIFIED) · **Date:** 2026-08-06

## Objective

Migrate the Engineering Runtime so that **every subsystem consumes ONE canonical
architecture provider** built from the Program 13.1 constitutional artifacts, and
eliminate all legacy "Python file == Engine" assumptions. No production
backend/frontend code was modified.

## Canonical Architecture Package

`runtime/foundation/architecture/` is the single source of architectural truth:

| Module | Role |
|--------|------|
| `ids.py` | Canonical ID scheme (`engine:`, `module:`, `router:`, `endpoint: METHOD /path`, …) |
| `models.py` | Engine / EngineModule / Detector / Facade / Endpoint / Router / Service / Repository / Capability / Workspace / Component / Mapper / DTO / ViewModel / Artifact / Graph |
| `provider.py` | `ArchitectureProvider` — singleton, pure consumer of canonical artifacts |
| `discovery.py` | The single 8-phase discovery pipeline (`run_discovery`) |
| `sources.py` | Phase 1 catalogue of legacy discovery sources + residual-signal scanner |
| `cross_layer.py` | `cross-layer-map-v2.json` — one chain per canonical engine, 0 duplicate owned endpoints |
| `migration_reports.py` | Phases 4/5/6/9 deliverable generators |

Every other runtime subsystem must read through
`runtime.foundation.architecture.get_architecture()` — no independent discovery,
no `*.py == Engine` heuristic, no path/filename guessing.

## Key Defect Fixed

`runtime/analyze_engine_topology.py` derived capabilities from the defective
`cross-layer-map.json`, which **dropped `useReconciliationCapability`** and
invented 7 phantom `<engine>.py` keys. Replaced with evidence-based derivation
(capability `fetch()` base path → router prefix+endpoint → owning engine).
Result: `reconciliation_engine.capabilities == ('useReconciliationCapability',)`
— the Program 13.1 capability gap is closed.

## Runtime Audits Migrated to the Provider

| Audit | Before | After |
|-------|--------|-------|
| `audit/cross_layer.py` | read legacy map; failed on internal engines + shared routers | consumes provider; internal engines reported as known debt, shared routers permitted |
| `audit/knowledge.py` | inconsistent (saved≠rebuilt index) | consistent — indexer now merges provider entities; index regenerated |
| `audit/artifact_ownership.py` | hardcoded 81-entry registry (36 unowned warnings) | consumes canonical `artifact-ownership-v3.json` (137 artifacts, 0 unknown) |

`runtime/foundation/knowledge/indexer.py` now merges provider-sourced
endpoints/capabilities/workspaces (10 capabilities, 76 endpoints, 8 workspaces).

## Legacy Generator Retired

`tools/generators/build_cross_layer_map.py` is now a **delegating shim** that
writes the canonical `cross-layer-map-v2.json` and a legacy-compatible
`cross-layer-map.json` (13 chains, no phantom `.py` keys). The defective
generator is removed from the architecture-authority role.

## Deliverables Generated

- `runtime-discovery-sources.json` (Phase 1)
- `cross-layer-map-v2.json` (Phase 3) — 13 chains, 0 duplicate owned endpoints
- `architecture-provider.json` — provider snapshot (13 engines, 10 capabilities, 76 endpoints)
- `knowledge-migration-report.json` (Phase 4) — 85 entities
- `artifact-ownership-v3.json` (Phase 5) — 137 artifacts, 0 unknown
- `dependency-graph-v2.json` (Phase 6) — ownership / execution / dependency as 3 distinct graphs
- `runtime-consistency.json` (Phase 9) — **6/6 consistency checks PASS**
- `engineering-platform-audit-v2.json` (Phase 10) — **CERTIFIED**
- `runtime-migration-report.md` (Phase 10) — this document

## Certification Result

`python runtime/verify.py audit` → **CERTIFIED**, all 19 sections PASS,
0 critical / high / medium / low issues.

## Remaining / Deferred (non-blocking)

- `runtime/foundation/integrity/scanner.py` still uses a hardcoded
  `_ENGINE_DIRS` list of single-file engines; it classifies by the
  `backend/src/engines/` path prefix (correct), so certification is unaffected.
  Could be derived from the provider in a follow-up.
- Other runtime consumer modules (`planner.py`, `affected.py`, `workspace.py`,
  `dependency_growth.py`) read the now-canonical `cross-layer-map.json`
  transitively; no independent engine discovery remains.
