# Program J — Canonical Provider Registry Regeneration

**Status: GATE PASSED**
**Date:** 2026-08-08
**Scope:** Generated architecture metadata + the generator declaration lists that feed it. No backend source modified.

---

## J.1 — Registry Generation Path

The registry self-declares its pipeline:

```
single_discovery_pipeline: runtime.foundation.architecture.discovery
```

**Established mechanism identified:**

| Layer | Component |
|---|---|
| Snapshot writer | `runtime/foundation/architecture/provider.py::export_snapshot()` |
| Schema | `architecture-provider-v1` |
| Output | `runtime/generated/architecture-provider.json` |
| Source artifacts (6) | `architecture-inventory.json`, `engine-topology.json`, `ownership-graph.json`, `execution-graph.json`, `engine-normalization.json`, `artifact-ownership-v2.json` |
| Upstream generators | `runtime/analyze_architecture.py`, `analyze_engine_topology.py`, `analyze_ownership.py`, `analyze_execution.py`, `analyze_engine_normalization.py` |

**The canonical provider implementation (`provider.py`) was NOT modified**, per guardrail. Only its *inputs* were corrected, and the snapshot was regenerated through `export_snapshot()`.

### Root cause of the drift

The phantom paths were **not** discovery output. They were **hardcoded declaration constants** in the upstream generator scripts:

| Generator | Constant | Contained |
|---|---|---|
| `analyze_architecture.py` | `SINGLE_FILE_ENGINES` | `nudge_engine.py`, `insight_generator.py` |
| `analyze_architecture.py` | `ENGINE_FACADES` | `behavior_engine.py` |
| `analyze_engine_topology.py` | `SINGLE_FILE_ENGINES`, `PARKED_FACADE` | all three |
| `analyze_engine_normalization.py` | `PARKED` | `behavior_engine.py`, `cashflow_engine.py.parked` |

The generators scan the real filesystem for modules but used these static sets to *classify* engines. When the modules were deleted (and `cashflow_engine.py` un-parked), the constants were never updated — so every regeneration faithfully re-emitted the phantoms.

---

## J.2 — The Four Phantom Paths Reconciled

For each, I verified filesystem absence, searched all references, and determined the migration outcome **before** changing any declaration.

| # | Phantom path | Exists? | Why it was stale | Resolution |
|---|---|---|---|---|
| 1 | `backend/src/engines/insight_generator.py` | **NO** | Absorbed into `behaviour_engine/insights.py` (`generate_behavioral_insights`, `generate_summary_text` — both exported from the package `__init__`) | Removed from `SINGLE_FILE_ENGINES` |
| 2 | `backend/src/engines/nudge_engine.py` | **NO** | Absorbed into `behaviour_engine/nudges.py` (`generate_nudges`, `get_top_nudge`, `get_nudge_summary` — all exported) | Removed from `SINGLE_FILE_ENGINES` |
| 3 | `backend/src/engines/behavior_engine.py` | **NO** | `behaviour_engine/` package migration is **complete**; the legacy file was deleted | `ENGINE_FACADES` / `PARKED_FACADE` emptied |
| 4 | `backend/src/engines/cashflow_engine.py.parked` | **NO** | The engine was **un-parked** — the live `.py` exists (mtime 2026-08-07 > provider snapshot 2026-08-06) | Removed from `PARKED`; registered as a live engine (J.3) |

**No source file was deleted to make the registry match.** All four reconciliations were achieved by correcting stale metadata declarations.

Additional stale narrative strings corrected (they named phantom engines in generated `notes`): `analyze_engine_normalization.py`, `analyze_ownership.py`, `analyze_execution.py`.

**Logic defect fixed:** `analyze_engine_normalization.py` emitted a `duplicate` finding for the behaviour domain **unconditionally**, asserting that `behavior_engine.py` coexists with the package. It is now guarded by `if "behavior_engine" in PARKED`, matching the adjacent `partial` block's existing pattern.

---

## J.3 — `cashflow_engine.py` Registered

Verified the file is live and required (Program H evidence retained):
- backs the `household_cashflow` capability
- exercised by `tests/capability/household_cashflow/test_capability.py` and `tests/properties/cashflow/test_engine_properties.py`
- used as the changed-file fixture in 3 meta-verification test modules

Registered via the established mechanism — added to `SINGLE_FILE_ENGINES` in both `analyze_architecture.py` and `analyze_engine_topology.py`, and removed from the `PARKED` map.

**The engine source file was not modified in any way.**

Result in the regenerated registry:
```
OK  cashflow_engine   single_file   backend/src/engines/cashflow_engine.py
```

---

## J.4 — Regeneration (not hand-editing)

Executed the generators in dependency order, then the provider snapshot:

```bash
python3 runtime/analyze_architecture.py          # inventory + summary
python3 runtime/analyze_engine_topology.py       # topology
python3 runtime/analyze_ownership.py             # ownership graph
python3 runtime/analyze_execution.py             # execution graph
python3 runtime/analyze_engine_normalization.py  # normalization
python3 -c "...provider.export_snapshot()"       # architecture-provider.json
```

**No generated JSON was hand-edited.**

### Before / After

| Metric | Before | After |
|---|---|---|
| Engines | 13 | **12** |
| Phantom engine paths | **4** | **0** |
| `cashflow_engine` registered | **NO** | **YES** |
| Facades | 3 (2 phantom) | **1** (real) |
| Parked engines | 2 (both phantom) | **0** |
| Duplicate findings | 1 (phantom) | **0** |
| Partial migrations | 1 (phantom) | **0** |
| Engine modules | 46 | 48 |
| Artifacts | 131 | 137 |

Normalization summary after regeneration:
```
legacy(single_file): 4  partial: 0  duplicate: 0  parked: 0
orphan: 1  facade: 1  impl_modules: 51
```

### Validation of the regenerated registry

```
=== ENGINES: 12 ===
  OK  account_engine            package      backend/src/engines/account_engine
  OK  balance_engine            single_file  backend/src/engines/balance_engine.py
  OK  behaviour_engine          package      backend/src/engines/behaviour_engine
  OK  cashflow_engine           single_file  backend/src/engines/cashflow_engine.py
  OK  credit_card_engine        package      backend/src/engines/credit_card_engine
  OK  financial_events          package      backend/src/engines/financial_events
  OK  financial_intelligence    package      backend/src/engines/financial_intelligence
  OK  ledger_audit_engine       single_file  backend/src/engines/ledger_audit_engine.py
  OK  loan_engine               package      backend/src/engines/loan_engine
  OK  recommendation_engine     package      backend/src/engines/recommendation_engine
  OK  reconciliation_engine     single_file  backend/src/engines/reconciliation_engine.py
  OK  transaction_intelligence  package      backend/src/engines/transaction_intelligence

PHANTOM PATHS: NONE
```

**Whole-registry path audit** (engines, engine_modules, detectors, facades, routers, services, repositories, mappers, dtos):
```
NON-EXISTENT backend paths across ALL registry sections: 0
duplicate engine ids: 0
```

**Determinism:** re-running `export_snapshot()` produced a byte-identical payload except `generated_at`.
```
DETERMINISTIC (ignoring timestamp): True
```

### Residual string matches — verified benign

Four regenerated artifacts still contain the substrings `behavior_engine` / `insight_generator` / `nudge_engine`. Each was inspected and is **legitimate**, not a phantom path:

| Match | Nature |
|---|---|
| `backend/tests/unit/engines/behavior/test_behavior_engine.py` | A **real test file that exists on disk** (its path retains the American spelling; it imports the correct `behaviour_engine.core`) |
| "behaviour_engine migration is COMPLETE… were removed…" | My own corrected explanatory note |
| Docstring in inventory mentioning `nudge_engine`, `insight_generator` | Verbatim source docstring captured from a runtime audit module — source text, not a path claim |

Other historical audit snapshots under `runtime/generated/` (e.g. `repository-cleanup-*.json`, `engineering-platform-audit-v*.json`) still reference the old names. These are **point-in-time records of past programs**, not the canonical registry, and are outside Program J's scope.

---

## J.5 — Registry Consumer Validation

| Suite | Result |
|---|---|
| `tests/architecture` + `tests/meta` | **111 passed** — identical to the Program H baseline |
| `git diff --check` | clean |

**No test was weakened.** The registry was corrected at its generation input, exactly as Step J.5 requires.

---

## Gate Results

| Gate criterion | Result |
|---|---|
| Registry generation succeeds | **PASS** |
| Registry internally consistent | **PASS** — 0 duplicate IDs |
| Phantom paths gone | **PASS** — 0 of 4 remain |
| `cashflow_engine.py` represented correctly | **PASS** — canonical single-file engine |
| Registry validation passes | **PASS** — 0 non-existent paths registry-wide |
| Architecture/meta tests green | **PASS** — 111 passed |
| Runtime verification rules modified | **NONE** |
| Production engine behavior modified | **NONE** |
| Canonical provider implementation modified | **NONE** |

### Files changed (Program J)

**Generator inputs (5):** `runtime/analyze_architecture.py`, `analyze_engine_topology.py`, `analyze_engine_normalization.py`, `analyze_execution.py`, `analyze_ownership.py`

**Regenerated artifacts (7):** `architecture-inventory.json`, `architecture-inventory-summary.json`, `architecture-provider.json`, `engine-normalization.json`, `engine-topology.json`, `execution-graph.json`, `ownership-graph.json`

**Backend source files modified: NONE**
**Files deleted: NONE**
