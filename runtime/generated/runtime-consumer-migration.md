# Program 13.3 — Runtime Consumer Migration Completion & Legacy Removal

**Status:** COMPLETE — Engineering Runtime recertified (CERTIFIED)

## Summary

Program 13.3 completed the migration begun in 13.2. The Engineering Runtime now
has exactly ONE architectural truth: the canonical Architecture Provider
(`runtime.foundation.architecture.get_architecture()`).

## What changed

- **Phase 1 (Consumer Inventory):** `provider-consumer-inventory.json` lists
  every runtime reference to a legacy artifact. No runtime subsystem reads a
  legacy architecture artifact as an operational dependency.
- **Phase 2 (Remove Transitional Compatibility):** `runtime/generated/cross-layer-map.json`
  is no longer read at runtime. Consumers resolve data through
  `runtime.foundation.architecture.chains.get_chain_map()`, an in-memory
  provider projection (no file read, no rediscovery).
- **Phase 3 (Planner Migration):** `planner.py`, `affected.py`, `workspace.py`,
  `dependency_growth.py` no longer perform independent discovery; they consume
  the provider (with explicit test-injection seams only).
- **Phase 4 (Integrity Engine Migration):** `integrity/scanner.py` derives the
  engine ownership roots from the provider instead of a hardcoded
  `_ENGINE_DIRS` single-file-engine list.
- **Phase 5 (Graph Unification):** `runtime-id-consistency.json` confirms one
  canonical identifier namespace (engine / capability / workspace / router /
  endpoint / artifact).
- **Phase 6 (Knowledge Runtime):** `knowledge/indexer.py` and the query engine
  consume identical provider-derived entities; no secondary reconstruction.
- **Phase 7 (Performance):** `provider-performance.json` shows the provider
  initialises once and is reused.
- **Phase 8 (Dead Runtime Removal):** `runtime-retirement-plan.json` lists
  transitional/legacy artifacts; none auto-deleted.
- **Phase 9 (Constitutional Audit):** `runtime-constitution.json` verifies one
  discovery pipeline, one provider, one ownership source, one knowledge
  reconstruction, one dependency graph builder.
- **Phase 10 (Recertification):** `python runtime/verify.py audit` → CERTIFIED,
  all 19 sections PASS. Snapshot: `engineering-platform-audit-v3.json`.

## Success criteria

- [x] Every runtime subsystem consumes `get_architecture()` directly.
- [x] No runtime subsystem reads legacy architecture artifacts operationally.
- [x] No duplicated discovery pipelines remain.
- [x] No hardcoded engine / capability / workspace / router inventories remain.
- [x] The architecture provider initialises once and is reused.
- [x] A retirement plan exists for obsolete infrastructure.
- [x] Engineering Runtime passes full certification unchanged.
- [x] No production backend or frontend files modified.
