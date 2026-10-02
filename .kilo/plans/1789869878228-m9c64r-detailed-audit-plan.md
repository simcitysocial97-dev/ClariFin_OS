# M9-C64-R — Detailed Audit Plan: Remaining Gaps

**Date:** 2026-09-20
**Current State:** Phases A–P completed; Phases I, J, K, Q scenarios incomplete; Phases R–AD partial or missing.
**Goal:** Complete all remaining forensic validation phases and produce every required artifact before C64 certification review.

---

## Current Artifact Status

| Required Artifact | Status | Lines |
|---|---|---|
| `progress.md` | Created but stale | 81 |
| `canonical-call-chain.json` | Created (6 transitions) | 141 |
| `scenario-matrix.json` | Created (5 scenarios) | 61 |
| `transition-contracts.json` | Created (6 transitions) | 72 |
| `identity-continuity.json` | Created | 42 |
| `obligation-reconciliation.json` | Created | 35 |
| `execution-reconciliation.json` | Created | 39 |
| `failure-injection-evidence.json` | Created | 18 |
| `fault-injection-summary.json` | Created | 46 |
| `residual-findings.json` | Created | 76 |
| `final-reconciliation.md` | Created (executive summary) | 143 |
| `pipeline-traces/` | Created (11 files) | 22,226 |
| **`evidence-reconciliation.json`** | **MISSING** | — |
| **`outcome-reconciliation.json`** | **MISSING** | — |
| **`console-reconciliation.json`** | **MISSING** | — |

---

## Gap Analysis

### Missing Scenario Tests (Phases I, J, K, Q)

| Phase | Description | Blocked By |
|---|---|---|
| I | Platform Console component change traced through framework | No specific blocker; needs target component identified |
| J | Cross-layer change (frontend + backend simultaneously) | Needs explicit paired file selection |
| K | Temporary configuration divergence in verification.yaml vs consumer | Needs controlled yaml edit + restore |
| Q | Stale/mismatched generated artifact detection | Needs artifact tamper + detector verification |

### Incomplete Audit Phases (R–AD)

| Phase | Description | Current Coverage |
|---|---|---|
| R | Function-to-function contract audit (all transitions) | 6/13 transitions documented |
| S | Negative contract testing (invalid/missing inputs) | Not started |
| T | Outcome truth table (9-row matrix) | Not produced |
| U | Diagnosis correctness (root cause detail) | Partial — failure injection confirmed exit code but not diagnosis depth |
| V | Platform Console truth (CLI vs API vs evidence vs console) | Not started |
| W | Repeatability (broader than doctor/plan) | Only doctor + plan verified |
| X | Real repository change (uncontrolled, real developer workflow) | Partial — only backend engine tested |
| Y | Full end-to-end audit (runtime + control-plane + architecture + cross-layer) | Not started |
| Z | Obligation completeness per scenario | Not quantified per scenario |
| AA | Execution completeness detail per scenario | Partial |
| AB | Evidence completeness detail per scenario | Not produced |
| AC | Outcome correctness detail per scenario | Not produced |
| AD | Console reconciliation detail per scenario | Not produced |

---

## Implementation Tasks

Execute in the order below. Each task produces specific artifacts.

### Task 1: Complete Phase I — Platform Console Change

**Objective:** Modify an actual Platform Console `.tsx` page and trace attribution through the framework.

**Steps:**
1. Identify a concrete Platform Console component from the architecture provider:
   - Target: `frontend/app/platform/framework/page.tsx` (already appears in E2E impact routes)
2. Add a one-line comment or harmless whitespace change to the file.
3. Run `verify plan` with the single-file input.
4. Record expected obligation set (should include `api-contracts` + any platform-related capability).
5. Classify result: PASS if obligations exist; FAIL with defect ID if zero.
6. Restore the original file content.

**Output:** Add entry to `scenario-matrix.json` with id `I-platform-console-change`.

---

### Task 2: Complete Phase J — Cross-Layer Change

**Objective:** Make simultaneous changes to a frontend hook AND its linked backend engine; verify cross-layer blast radius is computed once, not duplicated.

**Steps:**
1. Select paired files:
   - Frontend: `frontend/lib/capabilities/use-accounts-capability.ts` (linked to `account-engine` per provider)
   - Backend: `backend/src/engines/account_engine/lifecycle.py`
2. Add one-line comments to both files.
3. Run `verify plan` with both files.
4. Record obligation count and unique capability IDs.
5. Verify no duplicate obligations across the same capability (dedup should collapse identical commands).
6. Restore both files.

**Output:** Add entry to `scenario-matrix.json` with id `J-cross-layer-change`.

---

### Task 3: Complete Phase K — Configuration Fault

**Objective:** Temporarily modify `verification.yaml` to diverge from canonical consumer and verify the framework detects CONFIGURATION_DIVERGENCE.

**Steps:**
1. Back up current `runtime/foundation/verification/verification.yaml` to `audit-backup-verification.yaml`.
2. Introduce a single-key divergence: change `backend.coverage_threshold` from `40` to `999`.
3. Run `verify inspect mutation` or equivalent diagnostic to observe whether threshold divergence is flagged.
4. If the framework does not detect the divergence, classify as `CONFIGURATION_DIVERGENCE` defect.
5. Restore the original `verification.yaml`.
6. Verify restored state by re-running `verify doctor`.

**Output:** Add entry to `scenario-matrix.json` with id `K-config-fault`.

---

### Task 4: Complete Phase Q — Artifact Fault

**Objective:** Tamper with a generated artifact and verify the framework's freshness/integrity detector catches it.

**Steps:**
1. Identify a deterministic artifact: `runtime/generated/symbol-cache.json` (mtime-based, SHA-sensitive).
2. Back up the current file.
3. Introduce a minimal content change (e.g., modify one hash value).
4. Run `verify doctor` or the artifact freshness check and record the result.
5. Restore the original artifact.
6. Verify restoration by re-running the same check and confirming HEALTHY.

**Output:** Add entry to `scenario-matrix.json` with id `Q-artifact-fault`.

---

### Task 5: Complete Phase R — Function-to-Function Contract Audit (Full)

**Objective:** Document every transition in the canonical call chain with full INPUT, CONTRACT, TRANSFORMATION, IDENTITY, ERROR, NULL, MULTIPLICITY, ORDERING, PROVENANCE, PERSISTENCE fields.

**Steps:**
1. Read `canonical-call-chain.json` to identify all 13 steps.
2. For each step, write a detailed contract record including:
   - **INPUT:** exact type and schema of what flows in
   - **CONTRACT:** documented expectation from source code
   - **TRANSFORMATION:** what is changed between input and output
   - **IDENTITY:** can the object be correlated between steps
   - **ERROR BEHAVIOR:** what happens when the upstream fails
   - **NULL/EMPTY BEHAVIOR:** what happens when upstream returns nothing
   - **MULTIPLICITY:** can 1→0, 1→1, 1→N, N→1 occur
   - **ORDERING:** does ordering matter
   - **PROVENANCE:** can downstream identify origin
   - **PERSISTENCE:** is state actually persisted
3. Write to `transition-contracts.json` — append entries T07 through T13.
4. Mark each transition as PASS / FAIL / PARTIAL.

**Output:** Updated `transition-contracts.json` with 13 complete entries.

---

### Task 6: Complete Phase S — Negative Contract Testing

**Objective:** Deliberately provide invalid/incomplete inputs at each major transition and verify explicit diagnostic output.

**Test cases:**
| # | Invalid Input | Expected Behavior |
|---|---|---|
| S-1 | Empty list `[]` | 0 obligations, clean exit |
| S-2 | Nonexistent file path | UNMAPPED / 0 obligations |
| S-3 | Deleted file (remove from disk) | Framework handles gracefully |
| S-4 | Renamed file (different path) | Old path ignored, new path evaluated |
| S-5 | Ambiguous symbol (two functions same name in diff files) | Both symbols resolved or explicit ambiguity warning |
| S-6 | Missing capability in registry | Capability skipped with diagnostic |
| S-7 | Stale graph (outdated cross-layer-graph.json) | Framework rebuilds or warns |
| S-8 | Missing evidence for known task | Task still executed, evidence gap recorded |
| S-9 | Invalid final_decision string | Falls through to UNKNOWN outcome |

For each case: run `verify plan --json` or equivalent, capture output, classify as PASS/FAIL with evidence.

**Output:** New file `negative-contract-testing.json` with 9 entries.

---

### Task 7: Complete Phase T — Outcome Truth Table

**Objective:** Build the 9-row truth table specified in Section 28 of the task spec and verify each row through real execution.

**Rows to test:**

| Actual Execution | Expected Framework Outcome | Test Method |
|---|---|---|
| All required tasks pass | PASS | Backend engine change with passing tests |
| Required task fails | FAIL | Phase L: intentional failing test |
| Execution cannot complete due timeout | BLOCKED | Phase M: sleep(120) with timeout=5 |
| SIGINT/SIGTERM during run | INTERRUPTED | Phase N: send SIGINT |
| Evidence/artifact stale | STALE | Phase Q: tampered artifact |
| Framework authority/config divergence | DIVERGED | Phase O/P: authority drift + config fault |
| Insufficient information | UNKNOWN | Edge case: empty repo state |

**Output:** New file `outcome-truth-table.json` with 9 entries, each containing expected vs actual outcome.

---

### Task 8: Complete Phase U — Diagnosis Correctness

**Objective:** For each failure scenario, verify the framework's diagnosis identifies root-cause detail.

**Steps:**
1. Re-run Phase L failure scenario and capture the full `ExecutionReport`.
2. Extract `record.diagnostic` for the failed task.
3. Verify diagnosis contains: task_id, command, exit_code, stderr_tail, next_action.
4. Repeat for Phase M timeout scenario — verify diagnostic stage == `timeout`.
5. Compare CLI output (`_format_task_summary`) against stored record fields.
6. Classify any gap as `DIAGNOSTIC_DEFECT`.

**Output:** New file `diagnosis-correctness.json` with per-scenario diagnosis detail.

---

### Task 9: Complete Phase V — Platform Console Truth

**Objective:** For each tested scenario, compare four truth sources.

**Truth sources per scenario:**
1. **CLI truth:** raw stdout/stderr from `verify check`/`verify plan`
2. **API truth:** data returned by `ControlPlane.check()` / `cp.plan()` directly
3. **Stored evidence:** files written to `runtime/generated/m9-c49/logs/<plan_id>/`
4. **Console truth:** `verify inspect health` / `verify inspect evidence` outputs

**Steps:**
1. For each completed scenario (D–H, L–P), run `verify check` with explicit file inputs.
2. Capture CLI output to `pipeline-traces/<scenario>-cli.txt`.
3. Call `cp.check(changed_files=[...])` directly in Python and serialize to `pipeline-traces/<scenario>-api.json`.
4. Compare key fields: `final_decision`, `records[].completion_state`, `efficiency`.
5. Flag any discrepancy as `CONSOLE_TRUTH_VIOLATION`.

**Output:** New file `console-reconciliation.json` with per-scenario four-source comparison.

---

### Task 10: Complete Phase W — Broader Repeatability

**Objective:** Extend repeatability checks beyond doctor/plan to all observable commands.

**Commands to verify:**
| Command | Expected Invariant |
|---|---|
| `verify doctor` | Output identical except timestamp |
| `verify plan --json` | Same `set_id`, same obligation count |
| `verify inspect capabilities` | Same catalog count, same entries |
| `verify inspect evidence` | Same `set_id`, same obligation count |
| `verify inspect mutation` | Same measurement records, same scores |
| `verify inspect health` | Same `framework.integrity_status` |

Run each command twice within the session; compare structured fields (ignore timestamps).

**Output:** Append to `identity-continuity.json` or create `repeatability-broad.json`.

---

### Task 11: Complete Phase X — Real Repository Change

**Objective:** Make a real, non-trivial change to an existing ClariFin capability and trace the full pipeline.

**Steps:**
1. Pick a real backend capability with existing tests: `backend/src/engines/behaviour_engine/core.py`.
2. Make a small, reversible functional change (e.g., swap two operands in a pure calculation).
3. Run `verify check` and capture the full report.
4. Verify: obligations were generated, tasks were planned, execution ran, outcome was CLASSIFIED.
5. Check that the outcome matches expectations (should be PASS if change is benign; FAIL if change breaks a test).
6. If the change is benign, verify recovery: fix the change, rerun, confirm return to PASS.
7. Restore the original file.

**Output:** New file `real-repository-change.json` with full trace.

---

### Task 12: Complete Phase Y — Full End-to-End Audit

**Objective:** Run the complete framework validation across all layers.

**Sub-tasks:**
1. **Runtime tests:** `python -m pytest runtime/tests/ -q --timeout=120`
2. **Control-plane tests:** focus on `test_m9_c50_*`, `test_full_pipeline_integration.py`
3. **Architecture consistency:** verify `architecture-provider.json` counts match live computation
4. **Cross-layer consistency:** verify `cross-layer-graph.json` edges match actual imports
5. **C58/C60/C61/C62/C63 alignment:** run targeted tests for each certified milestone
6. **Static analysis:** ruff check + mypy check on runtime/ module
7. **Platform API smoke:** `verify inspect health` + `verify doctor`
8. **Compare expected architecture vs actual runtime behavior** and document deltas

**Output:** Append section to `final-reconciliation.md` with full validation results.

---

### Task 13: Complete Phase Z — Obligation Completeness Per Scenario

**Objective:** For each scenario, quantify: expected obligations, actual obligations, missing, unexpected, duplicates.

**Scenarios to audit:**
- D: backend unit change
- E: backend router change
- F: frontend component change
- G: unmapped file
- H: platform boundary
- J: cross-layer change
- X: real repository change

**Output:** Update `obligation-reconciliation.json` with per-scenario breakdown table.

---

### Task 14: Complete Phase AB — Evidence Completeness Per Scenario

**Objective:** For each executed task in each scenario, verify:
- execution started? (timestamp recorded)
- command recorded?
- stdout/stderr available?
- exit code recorded?
- duration recorded?
- result parsed?
- evidence persisted to disk?
- evidence linked to run?
- evidence linked to outcome?

Flag any task where evidence is missing after execution occurred.

**Output:** Create `evidence-reconciliation.json`.

---

### Task 15: Complete Phase AC — Outcome Correctness Detail

**Objective:** For each scenario, build a table:
| Scenario | Actual Execution Result | Framework Final Decision | Framework Outcome Status | Match? |
|---|---|---|---|---|
| D | ? | ? | ? | ? |
| ... | ... | ... | ... | ... |

Where "Actual Execution Result" is derived from direct subprocess observation, and "Framework Outcome Status" is from `report.final_decision` mapped via `decision_to_status()`.

**Output:** Create `outcome-reconciliation.json`.

---

### Task 16: Update progress.md

**Objective:** Bring the progress tracker to date reflecting all completed work.

**Updates needed:**
- Mark all completed phases with status and evidence references
- Add new sections for findings from Tasks 1–15
- List all new artifacts created
- Update the final classification to reflect current trustworthiness assessment

---

## Deliverable Checklist

After completing all 16 tasks, the following must exist:

```
runtime/generated/m9-c64-r-runtime-pipeline-forensic-validation/
├── progress.md                             [UPDATED]
├── canonical-call-chain.json               [EXISTS — no change needed]
├── scenario-matrix.json                    [UPDATED: add I, J, K, Q]
├── transition-contracts.json               [UPDATED: add T07–T13]
├── identity-continuity.json                [UPDATED: add repeatability data]
├── obligation-reconciliation.json          [UPDATED: add per-scenario table]
├── execution-reconciliation.json           [EXISTS — no change needed]
├── failure-injection-evidence.json         [EXISTS — no change needed]
├── fault-injection-summary.json            [EXISTS — no change needed]
├── residual-findings.json                  [EXISTS — append new findings]
├── final-reconciliation.md                 [UPDATED: add Y and AD sections]
├── negative-contract-testing.json          [NEW: Task 6]
├── outcome-truth-table.json                [NEW: Task 7]
├── diagnosis-correctness.json              [NEW: Task 8]
├── console-reconciliation.json             [NEW: Task 9]
├── repeatability-broad.json                [NEW: Task 10]
├── real-repository-change.json             [NEW: Task 11]
└── pipeline-traces/
    ├── baseline-*.json                     [EXISTS]
    ├── <scenario>-cli.txt                  [NEW: Task 9]
    └── <scenario>-api.json                 [NEW: Task 9]
```

---

## Risk & Dependency Notes

1. **Task 3 (Config Fault)** requires writing to `verification.yaml` — must restore exactly after test.
2. **Task 4 (Artifact Fault)** requires writing to `symbol-cache.json` — must restore exactly.
3. **Task 11 (Real Change)** must use a real, existing capability function with known test coverage to ensure meaningful attribution.
4. **Task 12 (Full E2E)** may take significant time due to running the full test suite — limit to targeted subsets if runtime exceeds 10 minutes.
5. **All file modifications** must be reverted before task completion; working tree must be clean at the end.
6. **Branch divergence** (C64R-F004) means all `verify check` runs on the working tree will see ~1127 changed files — always use explicit `changed_files=` parameter in Python API calls for controlled testing.
