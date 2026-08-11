# VEA-3 M1 — E-4 Causal Attribution Design

**Status:** CERTIFIED (evidence-backed by the repository)
**Milestone:** V3-M1
**Replaces:** `BL-003` (E-4 keyword/substring attribution)

---

## 1. What E-4 actually is, and where it lives

The "E-4 defect" has two sibling functions in `runtime/system/evidence/aggregator.py`:

* `_find_chain_for_failure(failure_type, cross_map)` — **first-entry guess**: iterates
  `cross_map.items()` and returns on the **first** iteration, regardless of which unit
  actually failed (`aggregator.py:722`).
* `_find_dependency_chain(test_name, cross_map)` — **substring guess**: matches a test name
  against engine/capability substrings (`aggregator.py:54-79`).

Both are called **only** from `EvidenceAggregator._build_attention`
(`aggregator.py:665,677,699`) to attach a guessed `dependency_chain` /
`likely_origin` / `likely_consumer` / `suggested_layer` enrichment to an "attention" item
when `unit_tests`, `property_tests`, or `contract_tests` report failure.

### Critical finding — the real attribution verdict is NOT E-4

The Phase 1.5 / Phase 2 verdict (`len(attributions)==6`, `in_blast_radius==()`,
`change_is_implicated is False`) is produced by
`runtime/foundation/intelligence/platform/attribution.py` —
`attribute_failures()` + `build_observed_failures()`. That path is **already
unit-keyed and graph/blast-radius based**:

* `build_observed_failures` takes `unit_id` verbatim from M5 evidence (inherited from the
  M3 manifest) — no string matching.
* `attribute_failures` joins `failure.unit_id` → `VerificationUnit` provenance →
  `BlastRadius.all_impacted` paths. Missing path → `ATTRIBUTION_UNKNOWN`.

The E-4 functions are **not** in that path. They are a tangential "attention enrichment"
heuristic. VEA-2 deliberately left them in place (`VEA2_PHASE2_CERTIFICATION.md` §3). This
milestone replaces them with graph traversal so the *entire* evidence system is free of
keyword/substring attribution.

---

## 2. What information is available from `unit_id`

A `VerificationUnit` (`optimizer.py:29`) and the M3 run-manifest step carry C11 provenance:

```json
"provenance": {
  "capabilities": ["api-contracts"],
  "impact_kinds": ["contract_backend"],
  "source": "registry-workflow-mapping",
  "contributing_units": ["backend-unit", "unit-targeted"],
  "workflow": "backend"
}
```

So from a `unit_id` we can resolve, via the canonical provider, the capabilities and impact
kinds that justified the unit — **identity, not inference**.

---

## 3. Canonical graph authority (reuse, do NOT rebuild)

`runtime.foundation.architecture` provider is the single source of truth (provider.py:1-21).
It exposes exactly the graph traversal infrastructure the spec demands:

* `chains.get_chain_map(arch)` — engine root path → full chain projection
  (engine, endpoints, capabilities, mappers, viewModels, components, workspaces…),
  all derived from provider state, **no heuristics** (`chains.py:100`).
* `chains.chain_for_path(path, arch)` — resolves the chain **owning** a path via
  `architecture.engine_for_path(path)` (provider ownership, not substring)
  (`chains.py:144`).
* `get_architecture()` — the canonical `Architecture` with `engines`, `capabilities`,
  `ownership`, `execution`, `dependency` graphs (`provider.py:203`).
* `Engine` model (`models.py:294`) carries `capabilities`, `endpoints`, `services`,
  `routers`, `implementation_modules`, `tests` — the explicit relationship edges.

The legacy `CROSS_LAYER_MAP_PATH` override in `aggregator.py` already routes through
`get_chain_map()` (aggregator.py:36). We reuse `chains.get_chain_map()` directly.

---

## 4. Exact traversal (the design)

```
ObservedFailure.unit_id
   ↓  (manifest step provenance: capabilities, impact_kinds, source)
VerificationUnit provenance
   ↓  resolve capabilities → provider Capability.engines
canonical capability/impact graph
   ↓  for each impacted engine, take chains.get_chain_map()[engine.path]
dependency traversal (engine → endpoints → capabilities → mappers → viewModels)
   ↓  only explicit provider edges
affected chain
   ↓
attribution enrichment (dependency_chain, likely_origin, likely_consumer, suggested_layer)
```

### Resolution rules (unit-keyed, never substring)

1. **Primary key:** the failing unit's `provenance.capabilities`. Each capability name maps
   to a provider `Capability`, whose `.engines` are exactly the engines that own it
   (`provider.py:559`). This is identity resolution, not keyword matching.
2. **Impact-kind fallback:** if no capability resolves, use `provenance.impact_kinds` to
   select the impacted entity kind and resolve the owning engine via
   `chain_for_path()` on the impacted entity's path.
3. **Chain assembly:** from the resolved engine(s), walk the provider-derived chain
   (`engine → services → endpoints → capabilities → mappers → viewModels → workspace →
   components`) exactly as the existing `get_chain_map` projection already enumerates.
4. **`likely_origin` / `likely_consumer`:** `likely_origin` = resolved engine path;
   `likely_consumer` = the capability that owns the engine (the inverse of step 1).
5. **`suggested_layer`:** derived from the capability identity
   (`frontend/lib/schemas/<cap>.ts`), exactly as today but from the *resolved* capability,
   not the first map entry.

### Missing-edge behaviour → `UNKNOWN`

* No `unit_id` / provenance at all → return `{}` (no enrichment; caller treats as
  `UNKNOWN`). We do **not** fabricate.
* `unit_id` present but resolves to no capability and no impacted path → `{}` (UNKNOWN).
* A capability resolves but its engine has no chain entry (stale module path, see BL-005) →
  `{}` (UNKNOWN), never first-entry fallback.
* Provider artifacts absent (`ArchitectureNotDiscovered`) → `{}` (UNKNOWN), never substring
  guess.

`UNKNOWN` is therefore "no graph edge established", which is exactly the spec's required
answer, and it is preserved (not coerced into a blast-radius guess).

---

## 5. Legacy function handling

`_find_chain_for_failure` and `_find_dependency_chain` are **left in the file** (per
§0.3 — no opportunistic deletion) but **no longer called** by any production path. Their
status is documented: obsolete, retained for forensic comparison, removal deferred to a
separate cleanup decision. The new function `_resolve_chain_for_failure` replaces them in
`_build_attention`.

---

## 6. Callers of E-4 (verified)

`grep` confirms the only callers are inside `aggregator.py::_build_attention`
(lines 665, 677, 699). No other module imports these functions. Replacing the call sites
does not ripple beyond the aggregator.

---

## 7. Gate

Design is evidence-backed (the provider, chains module, optimizer provenance, and manifest
shape were all read from the live repository). Proceeding to M2 implementation.
