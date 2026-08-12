# VEA-5 M6 — Deep Verification & Evidence Contract

**Status:** DONE — 2026-08-12
**Module:** `runtime/foundation/verification/evidence_contract.py` (new)
**Extensions:** `runtime/foundation/verification/reconciliation.py` (`_unit_results_from_any_evidence` v2-aware loader), `runtime/verify.py` (`cmd_exec_evidence` now emits v2 by default, `cmd_deep_contract`)
**Tests:** `runtime/tests/test_vea5_m6_evidence_contract.py` — 11 passed; all VEA-5 tests: 59 passed
**Verdict:** CERTIFIED

---

## Objective (narrowly scoped — A and B first)

Establish a deterministic, machine-readable evidence contract that extends M5's
persisted-artifact model into a scalable full-system verification architecture.
**A (finer per-unit evidence correlation) and B (Deep tier contract) are
implemented.** **C/D/E are defined as versioned, pluggable evidence *interfaces***
(measured, not imposed) — deliberately not a large implementation batch.

```
M6
├── A. Evidence Correlation            ✅ implemented (v2 schema)
├── B. Deep Tier Contract             ✅ implemented (ownership contract)
├── C. Test Quality Signals           ◐ interface defined
├── D. Full-System Verification       ◐ surfaces enumerated in B
└── E. Evidence → Diagnostic Pipeline ◐ node shape defined
```

## M6-A — Finer Per-Unit Evidence Correlation (v2 schema)

M5's `vea5-execution-evidence/v1` correlated a unit to a single overall
status/exit/evidence_ref — sufficient for the M5 gate but not for Phase-3. M6
introduces **`vea5-execution-evidence/v2`**:

```
unit_id
   ├── provenance
   └── attempts[]                      (one or more execution attempts)
        ├── attempt_index
        ├── command
        ├── start / end
        ├── duration
        ├── exit code
        ├── stdout / stderr refs
        └── artifacts[]                (evidence artifact references)
             ├── kind   (test-report | coverage | mutation | screenshots | video | log | ...)
             ├── ref
             ├── checksum
             └── metadata
```

**Hard invariant:** for every selected unit there is an unambiguous path
`unit_id -> execution attempt -> evidence artifact`. Implemented by
`UnitExecutionRecord` (one or more `ExecutionAttempt`s) and
`EvidenceArtifactRef`. `execution_evidence_v2_from_plan` guarantees every selected
unit has a record; a missing record is surfaced as an explicit `no-evidence`
attempt, **never silently dropped**.

**Backward compatibility:** `load_execution_evidence_any` accepts both v1 and v2,
normalizing to v2. `reconcile` (M5 gate) consumes v2 via
`_unit_results_from_any_evidence` (takes the primary status/exit of the last
attempt). The M5 workflow continues to work unchanged — `exec-evidence` now
defaults to v2 (use `--v1` for legacy).

## M6-B — Deep Tier Contract

Tier 3 becomes an explicit, first-class execution profile that **owns** expensive,
change-independent verification. Critical distinction:

```
PR   -> "what does THIS change require?"
DEEP -> "is the ENTIRE system still healthy?"
```

`DEEP_VERIFICATION_SURFACES` enumerates **13 surfaces** across 6 domains, each
declaring domain, description, command, backing catalog units, trigger cadence,
and evidence kinds:

| Domain | Surfaces |
|--------|----------|
| functional | deep-backend-suite, deep-runtime-suite, deep-frontend-suite |
| regression | deep-golden-regression, deep-large-dataset-regression, deep-cross-engine-regression |
| test-effectiveness | deep-mutation-testing, deep-coverage-analysis |
| ui | deep-playwright-e2e, deep-visual-ux-regression |
| performance | deep-performance-regression |
| security | deep-codeql, deep-dependency-security |

Heavy surfaces are **excluded from per-PR triggers** (schedule/manual/release;
security also merge). `deep_contract_manifest()` emits a machine-readable
`vea5-deep-contract/v1` artifact. DEEP ownership covers all 9 heavy/expensive
catalog units.

## M6-C / D / E — Evidence interfaces (defined, not fully implemented)

- **C — Test Quality Signals:** `TestQualitySignal` models the hierarchy
  TEST EXECUTION → COVERAGE → PROPERTY/CONTRACT → MUTATION → GOLDEN → LARGE
  DATASET. No arbitrary thresholds imposed — the framework first measures
  reality (per M6-C directive).
- **D — Full-System Surfaces:** realized as the DEEP surfaces in B (functional,
  regression, test-effectiveness, UI, performance, security), each pluggable and
  schedulable.
- **E — Evidence → Diagnostic Pipeline:** `FailureNormalizationNode` defines the
  `failure -> unit_id -> provenance -> capability -> impact_kind -> dependency ->
  affected_units -> execution_evidence -> normalized_signature` shape the later
  attribution layer (failure cluster + change attribution + pre-existing +
  environment → diagnostic verdict) will consume.

## What M6 deliberately does NOT do

- Does **not** fix every failing workflow.
- Does **not** impose 100% coverage or arbitrary project-wide thresholds.
- Does **not** complete mutation / golden / Playwright / UI / performance
  implementations (those become Track B / M10 parallel work).
- Does **not** rewrite or consolidate the nine workflows.
- Does **not** build the entire UI testing system.

It establishes the contract and integration points that make those capabilities
first-class, pluggable, measurable, attributable and schedulable.

## Acceptance gates — all met

- [x] M6-A v2 schema: unit_id → attempts → artifacts, unambiguous path. Round-trips.
- [x] Hard invariant: every selected unit has a record; missing → explicit `no-evidence`.
- [x] v1 → v2 backward compatibility (reconcile consumes both).
- [x] M6-B: DEEP owns the 6 domains / 13 surfaces; heavy surfaces not PR-triggered.
- [x] M6-B: `deep-contract` CLI + manifest artifact.
- [x] C/D/E interfaces defined as versioned schemas, no imposed thresholds.
- [x] Nine-workflow topology untouched; M5 CI path still valid (now v2).

## Verification

```
python3 -m pytest runtime/tests/test_vea5_m6_evidence_contract.py -q  → 11 passed
python3 -m pytest runtime/tests/test_vea5_*.py -q                     → 59 passed
python3 -m ruff check runtime/foundation/verification/evidence_contract.py \
                        runtime/verify.py runtime/foundation/verification/reconciliation.py → clean
CLI smoke: plan / exec-evidence (v2) / deep-contract / reconcile (v2) all OK
```

## Files changed

```
runtime/foundation/verification/evidence_contract.py   (new — M6-A v2 + M6-B contract + C/D/E interfaces)
runtime/foundation/verification/reconciliation.py      (v2-aware evidence loader for reconcile)
runtime/verify.py                                      (exec-evidence → v2 default; new deep-contract; dispatch + usage)
runtime/tests/test_vea5_m6_evidence_contract.py        (new, 11 tests)
.github/workflows/verification-reconcile.yml           (comment: M5-C/M6-A v2 artifact)
docs/verification/VEA5_M6_DEEP_VERIFICATION_EVIDENCE_CONTRACT.md  (this file)
docs/progress.md                                       (M6 summary inserted)
```

No backend/frontend production changes.
