# M9-C50 — POST-C50 FORENSIC CLOSURE

**Date:** 2026-09-04
**Purpose:** Independent reconciliation of the existing `M9-C50 COMPLETE` verdict against the 79-section governing document and the repository evidence.
**Method:** Read GUIDING_DOCUMENT, EXECUTION_PROGRESS, FINAL_CONVERGENCE_REPORT, final-convergence-summary.json, execution-state.json. Recompute every claimed SHA-256 hash. Inventory every file referenced. Reproduce key operational tests. Inspect 54 recorded operational run records. Independently classify each domain against a five-class taxonomy. Independently recalculate the six maturity levels.

This document does NOT extend the system. It establishes whether the existing completion claim is defensible.

---

## 1. Phase Reconciliation

### 1.1 Missing Phase 5 narrative

The execution record in `EXECUTION_PROGRESS.md` documents Phases 0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12 — **Phase 5 is absent from the narrative.** The execution-state.json asserts `stop_gate_5: PASSED` and `phases_completed: 12` but the narrative jumps directly from Phase 4 to Phase 6.

**Phase 5 work was actually performed.** The evidence is unambiguous:

* `runtime/generated/m9-c50/phase-5/stop-gate5-evidence.json` exists with SHA-256 `ec05181f269d5fd21749980457af81d9bfc59525ba44fe57112a1a93eff5e393`. The file's `generated_at` is `2026-09-04T13:01:59.177149+00:00` — that timestamp predates Phase 6 execution.
* The Phase 5 gate test suite `runtime/tests/test_m9_c50_stop_gate5_evidence_trust.py` exists, is hashed `40f6c9befaa8858905470160cfe3949837b349ac72a11ada65e0fb060c72d7c6` (matching the Phase 5 evidence's recorded artifact hash), and contains 12 substantive tests covering stale commit evidence rejection, wrong-content SHA rejection, wrong-config fingerprint rejection, wrong-toolchain fingerprint rejection, corrupted-cache rejection, truncated-cache rejection, status-field corruption, reused-evidence classification, non-reused-evidence classification, incomplete-evidence-cannot-close-obligation, failed-execution-cannot-close-obligation, and cache-entry-lineage completeness.

**The defect is governance, not implementation.** The work is real but the narrative is missing. No architectural gap is created by this, but a `COMPLETE` claim built on a 12-phase narrative is inconsistent with a 13-phase execution state.

### 1.2 Downstream phases that depend on Phase 5

Phase 5 is the EVIDENCE TRUST GATE. The following later phases reuse its invariants:

* **Phase 6** claims "mutation evidence enters common evidence model (closed EVIDENCE_KINDS)" — only meaningful if Phase 5 has established that the evidence model is trustworthy.
* **Phase 9** claims "stale evidence → INVALIDATED (cache invalidation)" — directly invokes Phase 5 cache invalidation.
* **Phase 11** scenarios 12, 13, 14 (stale_evidence, cache_reuse, cache_invalidation) depend on Phase 5 cache authority.
* **Phase 12** governance tests assert closed EVIDENCE_KINDS, cache invalidation, obligation reconciliation — all Phase-5-establish invariants.

**Disposition:** EVIDENCE/GOVERNANCE DEFECT. Remediation: append a Phase 5 narrative section to EXECUTION_PROGRESS.md (Objective, Required Work, Evidence Artifacts, STOP GATE 5 evaluation, recorded decision). No new code required.

### 1.3 Stop-gate count inconsistency

`execution_state.json` claims `stop_gates_passed: 13`. EXECUTION_PROGRESS.md only documents 11 phase narratives (Phases 0–4, 6–12). The narrative count and the state-machine count disagree.

### 1.4 Phase 0 stale count

`EXECUTION_PROGRESS.md` Phase 0 and `FINAL_CONVERGENCE_REPORT.md` both state "44 changed/deleted/untracked files". Current `git status --short | wc -l` returns 87. The 44 figure was true at session start; it is no longer accurate and should be updated or marked as historic.

---

## 2. Evidence-Integrity Reconciliation

### 2.1 Hash verification

All claimed SHA-256 hashes (16 of them) were recomputed against on-disk files. **15 match exactly. 1 is a placeholder.**

* `phase-4 stop-gate4-evidence.json` is claimed in the Final Convergence Report as `a1b2c3d4...`. The actual SHA-256 is `5af228211055e30c1c8556e75b86943f2e47d72e887c23fa16ad5055f9e7d26b`. **A `a1b2c3d4...` placeholder in an evidence-hash table is a substantive evidence-integrity defect** — it cannot be used to detect tampering and signals that the report author did not actually verify the hash.

### 2.2 Missing hashes

* Phase 5 evidence hash: omitted from the report's evidence-hashes table.
* Phase 6 evidence hash: omitted from the report's evidence-hashes table.

Both files exist and have real hashes (`ec05181f...`, `1d1d6653...`). Their omission from the report undermines the report's claim of "all artifacts hashed".

### 2.3 Count inconsistency: 24 vs 54 vs 1

The report claims "24 operational runs recorded across 16 representative scenarios". The execution-state.json says `run_count: 24`. The directory `runtime/generated/m9-c50/phase-11/operations/` contains **54** `run-*.json` files. The `operations-summary.json` contains **1** entry. **Three different counts appear in the evidence.** None of them is a faithful representation of "real operational runs through the canonical pipeline", because zero of those 54 records have populated `plan_identity`, `execution_identity`, or `evidence_identities` — they all terminate at the planning stage.

### 2.4 Stale deleted artifacts

The working tree contains 16 deleted artifacts from a prior aborted C50 attempt (`brc-*.json`, `certification.json`, `CERTIFICATION.md`, etc.). These are referenced indirectly by Phase 0 finding 2 but are not in any evidence hash table. Their deletion is intentional cleanup, but it is not recorded as a governance decision.

---

## 3. Working-Tree Governance

87 uncommitted files in 4 categories:

1. **C50 implementation code** (5 files): `obligation_reconciliation.py`, modified `control_plane_facade.py`, modified `control_plane.py`, modified `executor_pipeline.py`, modified `capability_graph_resolver.py`, modified `verify.py`. **MUST COMMIT.**
2. **C50 test suites** (12 files, all `runtime/tests/test_m9_c50_*.py` plus modified `test_m9_c49_canonical_cli.py`). **MUST COMMIT.**
3. **C50 evidence artifacts** (entire `runtime/generated/m9-c50/` tree minus deleted artifacts, plus FINAL_CONVERGENCE_REPORT.md, GUIDING_DOCUMENT.md, execution-state.json, final-convergence-summary.json). **MUST COMMIT.**
4. **Phase 7 frontend JSDoc** (14 frontend files). **MUST COMMIT.**
5. **Phase 8 CI workflow comments** (11 workflow files). **MUST COMMIT.**
6. **Generated artifacts** (C48 re-runs, `runtime/generated/git-fetch-events.jsonl`, `event_store.py`, `memory-bank/activeContext.md`, `backend/tests/invariants/_m4_probe_live/`). **DISPOSITION UNCLEAR** — verify whether intentional, otherwise revert or .gitignore.

Detailed per-file disposition is in `working-tree-governance.json`.

**Hard finding:** The Phase 12 report asserts the working tree is dirty (line 161) and acknowledges the governance decision as Remaining Limitation #4. This is the single largest evidence defect: **a `COMPLETE` claim cannot be made over an uncommitted working tree** because the committed baseline does not include the implementation under test.

---

## 4. Operational Authenticity

### 4.1 Phase 11 lineage gap

The 54 operational run records were inspected programmatically. For each:

```
plan_identity_populated:    0 / 54
execution_identity_populated: 0 / 54
evidence_identities_populated: 0 / 54
final_decision distribution: planned=26, failed=4, cache_reused=4,
                             cache_invalidated=4, stale=4, blocked_unmapped=3,
                             requires_mutation_campaign=1, self_verified=1,
                             no_work_required=1, executed/certified/completed=0
```

**Zero of the recorded operational runs reached the executor pipeline.** Each run terminates with `final_decision` set to one of: a planning-only label, a synthetic decision produced by direct cache or capability-graph calls, or a hardcoded label by the test scenario. The required lineage `scenario → change → capability → obligation → plan → executor → real execution → evidence → reconciliation → decision` is broken at the executor boundary.

### 4.2 Phase 11 scenario 15 (CI-equivalent) hangs

`test_scenario_15_ci_equivalent_execution` invokes `subprocess.run('python runtime/verify.py check', ...)`. Under `pytest-timeout=60s`, the test hangs and is reported as failed by `pytest-timeout`. Re-running with `--timeout=60 -x` confirms: 1 failed, 14 passed. **Either verify.py check genuinely hangs in this environment, or the test invocation pattern is wrong.** Either way, scenario 15 — the only scenario that would establish CI↔local equivalence — does not pass.

### 4.3 Self-verification authenticity

Phase 10's 35 tests pass, but inspection of three "negative-detection" tests reveals:

* `test_framework_detects_duplicate_authority_violation`: instantiates two ControlPlane objects and asserts `type(cp1) == type(cp2)`. This proves the class is shared, NOT that the framework detects a duplicate-authority violation.
* `test_framework_detects_legacy_bypass`: checks that legacy command names appear in `migration_map()`. This proves the map exists, NOT that bypass is detected at runtime.
* `test_framework_detects_stale_evidence_reuse`: checks that the string `"stale_evidence_reuse"` is in a bypass report. This proves the report mentions it, NOT that bypass enforcement actually triggers.

**Phase 10 demonstrates structural self-tests, not genuine negative-detection self-verification.** The defining property of SELF_VERIFYING ("the framework can detect intentional violations of its own architecture") is not established by these tests.

### 4.4 Cache claims distinguished

The original Phase 0 finding was "cache hit rate <50% (operational instability)". Phase 5 + Phase 9 prove **cache correctness**:

* Stale evidence is rejected.
* Wrong-SHA evidence is rejected.
* Wrong-configuration evidence is rejected.
* Corrupted evidence is rejected.

These are PROVEN. They are about correctness, not effectiveness.

**Cache effectiveness (hit rate) has not improved.** Current `runtime/verify.py env-check` reports:

* Combined cache hit rate: 16.0%
* Local cache hit rate: 16.2%

This is **substantially worse** than the <50% Phase 0 baseline. Phase 11's "cache_reuse" scenarios invoke cache methods directly; they do not measure or improve the operational hit rate. **Calling cache performance "resolved" because invalidation is correct is unsupported.**

---

## 5. End-State Reassessment

Independent classification of all 19 domains (5-class taxonomy). Detail in `end-state-reassessment.json`.

| Status | Count | Domains |
|---|---|---|
| PROVEN | 9 | Control Plane, CLI Surface, Obligation Integrity, Planning, Capability Resolution, Cache (correctness), Reconciliation, Mutation Architecture, Failure-Mode |
| IMPLEMENTED_NOT_OPERATIONALLY_PROVEN | 4 | Executors (registered but not invoked in real runs), Frontend/Cross-Layer (documentation posture only), Self-Verification (structural only), Operational Validation (planning-stage only) |
| PARTIALLY_PROVEN | 1 | CI Canonicalization (workflow files canonical, but scenario 15 hangs) |
| BLOCKED | 1 | Working-Tree Discipline (87 uncommitted files) |
| UNSUPPORTED | 3 | Evidence-Kind Vocabulary (10 violations), Sustained-in-Operation, Certifiable |

---

## 6. Maturity Reassessment

Independent recalculation of the 6 maturity levels. Detail in `maturity-reassessment.json`.

| Level | Report Claim | Recalculated | Reason |
|---|---|---|---|
| IMPLEMENTED | ✅ | **YES** | Code exists, tests compile, ruff/mypy largely clean. |
| ARCHITECTURALLY_CONVERGED | ✅ | **PARTIAL** | 10 evidence-kind violations remain architectural defects on the evidence-contract dimension. |
| OPERATIONALLY_VALIDATED | ✅ | **NO** | 0/54 recorded runs reached execution; scenario 15 hangs. |
| SUSTAINED_IN_OPERATION | ⚠️ | **NO** | Single session; cache hit rate regressed to 16%. |
| CERTIFIABLE | ⚠️ | **NO** | No certification policy defined. |
| SELF_VERIFYING | ✅ | **PARTIAL** | Structural self-tests; negative detection is weak (asserts detection names exist rather than injecting real violations). |

**The report's claim that the architecture is "honestly assessed" as ARCHITECTURALLY_CONVERGED + OPERATIONALLY_VALIDATED + SELF_VERIFYING is not supported by the recalculation.**

---

## 7. Phase/Gate Integrity

Per the audit rule "every mandatory phase must have objective, implementation/evaluation, execution evidence, artifact evidence, stop-gate evaluation, recorded decision":

| Phase | Objective | Implementation/Eval | Execution Evidence | Artifact Evidence | Stop-Gate Eval | Recorded Decision |
|---|---|---|---|---|---|---|
| 0 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 1 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 2 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 3 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 4 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **5** | ✓ (in evidence JSON) | ✓ (test suite + cache code) | ✓ (12 tests pass) | ✓ (file exists) | ✓ (decision=PASS in evidence) | **✗ (no narrative in EXECUTION_PROGRESS)** |
| 6 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 7 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 8 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 9 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 10 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 11 | ✓ | ✓ | ✓ (15/16 pass) | ✓ (but lineage broken) | ✓ | ✓ |
| 12 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

Phase 5 is the only phase with a missing `recorded decision` narrative entry. Phase 11 has lineage-broken artifacts but a recorded decision.

---

## 8. Final Decision

### Selected: **C. C50 NOT COMPLETE — REMEDIATION REQUIRED**

The M9-C50 completion claim cannot be accepted. The repository contains substantial C50 work, and the architectural scaffolding is real (control plane, obligation reconciliation, evidence contract, mutation authority, CI canonicalization). However, mandatory requirements of the governing document remain unsatisfied:

1. **Phase 5 narrative is missing** from EXECUTION_PROGRESS.md — a governance defect that breaks the audit-trail claim of a 12-phase execution record over a 13-stop-gate state machine.
2. **10 evidence-kind violations remain architectural defects** on the evidence-contract dimension — the closed `EVIDENCE_KINDS` vocabulary is violated by 10 capabilities, and the report acknowledges this as Remaining Limitation #3.
3. **Operational validation is not substantiated** — 0/54 recorded runs reached execution, scenario 15 hangs, and the count mismatch (24 / 54 / 1) makes the operational claim internally inconsistent.
4. **Self-verification is structural only** — negative-detection tests check that detection names exist in code, not that detection fires on real violations.
5. **Cache effectiveness has regressed** to 16% (worse than the Phase-0 <50% baseline); calling it resolved is unsupported.
6. **Working tree is dirty** with 87 uncommitted files — the committed baseline does not include the implementation under test.
7. **Evidence hash table contains a placeholder** (`a1b2c3d4...`) — undermining hash-trust claims.

### Smallest defensible remediation path

The objective of C50 is achievable, but only after the following minimum remediation. Do NOT launch a broad refactoring effort; address each defect with the smallest change that is honestly verifiable.

1. **Append a Phase 5 narrative to EXECUTION_PROGRESS.md** preserving the historical record. Required content: Objective, Required Work, Evidence Artifacts with SHA-256, STOP GATE 5 evaluation, recorded decision. ~50 lines.
2. **Commit all C50 implementation, tests, evidence, and Phase 7/8 files** per the working-tree-governance.json commit strategy. 87 files → ~6 commits. Required to make the committed baseline reflect the C50 architecture.
3. **Remediate the 10 evidence-kind violations** by either:
   (a) amending the `EVIDENCE_KINDS` vocabulary in `runtime/foundation/verification/capability_catalog.py` to include the missing kinds (with a governing-document note that documents the vocabulary extension), or
   (b) remapping the 10 capabilities to use existing evidence kinds from the closed vocabulary.
   Option (b) is preferred for purity; option (a) is acceptable if documented.
4. **Re-record Phase 11 operational runs with real executor lineage.** Each scenario must invoke `cp.plan()` AND `cp.run()` (or the canonical equivalent) AND produce real evidence artifacts (or explicit evidence-identity references). The 54 existing records must be either regenerated with populated `plan_identity`/`execution_identity`/`evidence_identities` or marked as obsolete.
5. **Resolve scenario 15** — either fix the hang (if real) or replace the test with a process that completes within timeout and still establishes CI↔local equivalence.
6. **Strengthen Phase 10 negative-detection tests** — replace structural assertions with real violation injection. For example, `test_framework_detects_duplicate_authority_violation` should attempt to inject a second authority into a test module and assert the detector flags it.
7. **Recompute the Final Convergence Report** with the corrected Phase 5 narrative, real Phase 11 lineage, real Phase 10 negative-detection results, and resolved evidence-kind violations. Replace the `a1b2c3d4...` placeholder with the real hash.
8. **Recalculate maturity** based on the post-remediation state. Expect:
   - IMPLEMENTED: YES
   - ARCHITECTURALLY_CONVERGED: YES (after evidence-kind remediation)
   - OPERATIONALLY_VALIDATED: YES (after real-run lineage)
   - SELF_VERIFYING: YES (after real negative-detection)
   - SUSTAINED_IN_OPERATION: still NO (requires longitudinal evidence)
   - CERTIFIABLE: still NO (requires certification policy)

After this remediation, the verdict may move to **B. C50 IMPLEMENTATION COMPLETE — VALIDATION GAPS REMAIN** (SUSTAINED + CERTIFIABLE pending) — never directly to **A**, because single-session execution cannot establish sustained operation and no certification policy exists.

### What is NOT required

* No new canonical authorities.
* No refactor of mutation/strengthening/forensic architecture (Phase 6 is honest).
* No new test architecture (Phase 18 requirements are satisfied by the existing C50 test suites).
* No re-litigation of completed phases (Phase 0–4, 6–9 implementation evidence is genuine).
* No launch of M9-C51 to resolve C50 defects — the defects are within C50 scope.

---

## 9. Decision Record

* **Date:** 2026-09-04
* **Auditor:** Independent forensic review
* **Verdict:** **C. C50 NOT COMPLETE — REMEDIATION REQUIRED**
* **Justification:** Missing Phase 5 narrative, 10 unresolved architectural evidence-contract violations, broken Phase 11 execution lineage, structural-only self-verification, regressed cache effectiveness, 87 uncommitted files, placeholder hash in evidence table.
* **Smallest remediation path:** See §8.
* **Forbidden actions:** Do NOT extend the system into C51. Do NOT amend the existing 12 phase narratives. Do NOT silently regenerate the report without addressing root causes. Do NOT commit all 87 files without per-file disposition.

---

*This forensic closure preserves all prior C50 evidence and decisions. It does not rewrite history; it appends the reconciliation. Historical phase results remain in their original form. The closing verdict is independent of the prior verdict and is derived from primary repository evidence.*