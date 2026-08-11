# VEA-2 Phase 2 — Evidence Integrity (Certification)

**Status:** CERTIFIED (Milestones M0–M7 complete)
**Predecessors:** `VEA2_PHASE1_CERTIFICATION.md`, `VEA2_PHASE1_5_REAL_WORLD_DIAGNOSIS.md`
**Execution ledger:** `docs/progress.md`
**Deferred-item register:** `docs/verification/VEA_BACKLOG.md`
**Spec:** `.kilo/plans/1786342506938-vea2-phase2-evidence-integrity.md`

---

## 1. Objective and result

Phase 1.5 proved the *concept* of cross-layer attribution on a real failure, but it
relied on hand-feeding failure paths parsed out of raw CI logs. Phase 2 establishes a
durable **identity spine** so that attribution runs automatically on real pipeline
output, with the verification unit as the only join key — never a string match against a
command or test name.

```
VerificationUnit.id ──► VerificationStep.unit_id ──► ExecutionResult.unit_id ──► Evidence.unit_id
        │                                                                              │
        └────────────── provenance (capabilities, impact_kinds, source) ───────────────┘
```

**Result: the Phase 1.5 verdict is now reproduced with zero manual parsing.**

---

## 2. Identity spine (M1–M3)

| Layer | Field / artifact | Where |
|-------|-----------------|-------|
| Plan | `VerificationUnit.id` (optimizer, 10 closed units) | `optimizer.py` |
| Execution step | `VerificationStep.unit_id`, `.provenance` | `models/model.py` (M1) |
| | populated via `units_for_workflow()` | `planner/planner.py` (M3) |
| Result | `ExecutionResult.unit_id`, `.provenance` | `orchestrator.py` (M3) |
| Manifest (join key) | `runtime/generated/evidence/run-manifest.json` (`run-manifest/v1`) | `orchestrator.py` (M3) |
| Evidence | `EvidenceSummary.frontend` (E-2), `EvidenceSummary.unit_failures` (E-3) | `aggregator.py` (M5) |

The mapping `UNIT_TO_WORKFLOW` is **enumerated, not inferred** (`registry/registry.py`,
M2). Every one of the 10 optimizer units is either mapped or an intentional `UNMAPPED`.
`UNMAPPED` is a first-class, reportable outcome — never silently dropped.

**Live inventory (current `run-manifest.json`):**

```
schema:    run-manifest/v1
steps:     3
unit_ids:  ['UNMAPPED', 'backend-unit', 'runtime-self-test']
unmapped:  1 entry (run_fast_checks.sh — no UNIT_TO_WORKFLOW decision)
```

The single `UNMAPPED` entry is a genuine, surfaced gap (`BL-009` tracks the
step-ordering variance that produces it), not a swallowed failure.

---

## 3. Evidence artifacts produced (M4–M5)

* `runtime/generated/evidence/backend/backend-verification.json` — per-suite phases
  (`unit-engines`, `contracts`, `properties`, `invariants`), `backend-verification/v1`.
* `runtime/generated/evidence/backend/*-junit.xml` — **E-1 closed**: JUnit XML written
  per suite; `TestResultCollector` now parses **861** passed tests (vs. the prior
  unreadable blob).
* `runtime/generated/evidence/frontend/frontend-verification.json` —
  `frontend-verification/v1`, self-identifying via `VERIFICATION_UNIT_ID`.
* `EvidenceSummary.frontend` — **E-2 closed**: the frontend was previously
  structurally unrepresentable; a red frontend build can no longer be reported as `pass`.
* `EvidenceSummary.unit_failures` — **E-3 closed**: failures joined to units and
  provenance via the manifest, **by workflow**, never by substring.

The join in `_collect_unit_failures` contains **no** `startswith` / `endswith` /
`in command` / `re.search` (asserted by `TestUnitKeyedFailures::test_join_is_by_workflow_not_by_position`
and by the negative test `test_unrelated_manifest_entry_is_never_borrowed`).

**E-4 deliberately left in place and untouched** (`_find_chain_for_failure` /
`_find_dependency_chain`). Verified mechanically: `git diff --stat aggregator.py` →
1 file changed, **248 insertions, 0 deletions**. Phase 2 bypasses E-4; it does not
build on it. Owned by Phase 3 (`VEA_BACKLOG.md` BL-003).

---

## 4. Attribution reproduced automatically (M6)

`build_observed_failures(unit_failures)` adapts M5 evidence into `ObservedFailure`
records. The `unit_id` is read verbatim from the evidence (which inherited it from the
M3 manifest); no log parsing, no inference. `attribute_failures` is **unchanged**.

```
python runtime/verify.py diagnose-failures
```

Ran end-to-end on real evidence (no manual steps) and produced the §18 CROSS-LAYER
FAILURE diagnostic:

```
Failure attribution:
  observed=1  in-blast-radius=0  outside=0  unknown=1

NO FAILURE IS ATTRIBUTABLE TO THIS CHANGE.
  Every observed failure lies outside the blast radius that justified running these units.
  Do NOT modify the changed files to make this verification green.

Unattributed (insufficient evidence):
  lint: failure has no resolvable file path
```

This is the Phase 1.5 verdict shape, produced by the production command instead of by a
forensic engineer reading logs.

### 4.1 Verdict identical to Phase 1.5 (the specimen)

`runtime/tests/test_diagnose_failures.py::test_adapter_reproduces_phase1_5_verdict_from_artifacts_alone`
feeds the **exact** specimen failure set (the 6 real frontend paths that failed for the
loan-engine change at `b9074020`) through the artifact adapter and asserts:

```
len(report.attributions) == 6
report.in_blast_radius == ()              # in_blast_radius = 0
report.outside_blast_radius == 6
report.change_is_implicated is False
```

Identical to the Phase 1.5 manual result. The Phase 1.5 suite itself
(`test_failure_attribution.py` + `test_cross_layer_planner.py`, **25 tests**) passes
**unmodified** — verdict semantics were not touched.

### 4.2 Manual-step count

| | Phase 1.5 | Phase 2 |
|---|-----------|---------|
| Steps to produce the diagnostic | ≈ 15 forensic (grep logs, map files, hand-build `ObservedFailure`) | **0** (one command: `verify.py diagnose-failures`) |

---

## 5. Test strength

Every new test suite was mutation-checked. Two real gaps were found and closed by
negative tests:

* **Mutant B (M5):** the E-3 join fell back to the *first* manifest entry when no
  workflow matched — i.e. the E-4 "first entry wins" defect in a new format. Survived
  the first draft; killed after adding
  `test_unrelated_manifest_entry_is_never_borrowed` + `test_join_is_by_workflow_not_by_position`.
* **Mutant (M6):** "forcing the join to always match" — drop the `UNMAPPED` branch so an
  unjoinable failure is matched against the radius by its real path. Killed by
  `test_unjoinable_failure_is_attribution_unknown`.

Both mutants were reverted; suites restored green.

### Counts

```
runtime/tests (excl. slow M4 backend suite)   291 baseline → 412 passed
  M1 +18  M2 +29  M3 +34  M4 +31  M5 +2  M6 +8   (cumulative)
Phase 1.5 attribution suite                   25 passed, UNMODIFIED
ruff check (changed files)                     All checks passed
```

---

## 6. Regression / restraint gates

| Gate | Result |
|------|--------|
| Executed CI commands byte-identical to pre-Phase-2 | **Yes** — M3/M4 preserved command vocab and exit contracts; verified by command-list diff (M3) and both-directions exit-contract tests (M4) |
| Frontend lint pre-existing errors | **34** (corrected M0 baseline), composition unchanged: `set-state-in-effect`15 `exhaustive-deps`8 `react/no-children-prop`3 `static-components`2 `purity`2 `immutability`2 `no-sync-scripts`1 `no-assign-module-variable`1. A change here would signal scope leak; it is unchanged |
| Backend application code changed | **No** |
| `.github/workflows/` modified | **No** (STOP condition honored) |
| Items in `VEA_BACKLOG.md` touched | **No** |
| 9-workflow CI topology | **Unchanged** from M0 baseline |

> **Note on the lint count.** M0 corrected the spec's "31" to **34** using the measured,
> proven value (the hard invariant `PROVEN over PROBABLE`). The certification gate is the
> *proven* 34, which is what Phase 2 preserves.

---

## 7. Phase 3 handoff

Phase 2 delivers the join key that Phase 3 needs but could never build before:

1. **E-4 replacement** (`BL-003`): replace `_find_chain_for_failure` /
   `_find_dependency_chain` keyword matching with graph traversal over the now-unit-keyed
   evidence. The identity spine means Phase 3 can join failures to units and provenance
   directly, instead of guessing by test-name keywords.
2. **`UNMAPPED` inventory** (`M2`/`M3`): the surfaced `UNMAPPED` entries (e.g.
   `run_fast_checks.sh`) are the precise list of executions with no unit-mapping
   decision — the input to a mapping-coverage closure.
3. **CI workflow topology audit** (Group E, `§2.1`): deferred to post-Phase-2. Now
   possible for the first time, because `run-manifest.json` makes execution equivalence
   between workflows *demonstrable from evidence*, not argued from YAML.

---

## 8. Completion gate — final status

| Criterion | Met |
|-----------|-----|
| Identity spine plan→step→result→evidence | ✅ |
| Mapping enumerated + coverage-tested + `UNMAPPED` visible | ✅ |
| Backend + frontend per-phase evidence; JUnit produced & consumed | ✅ |
| `EvidenceSummary` represents frontend; failures joinable to units + provenance | ✅ |
| Attribution on real artifacts, zero manual parsing, `UNKNOWN` preserved, no inference | ✅ |
| 291 baseline tests pass unmodified; new tests mutation-checked; nothing weakened | ✅ |
| CI commands byte-identical; lint 34 unchanged; backend unchanged; workflows untouched | ✅ |
| Ledger complete; no `IN_PROGRESS`→`DONE` without artifacts | ✅ |

**VEA-2 Phase 2 is complete.**
