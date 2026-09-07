# M9-C57 Verification Integrity & Diagnostic Hardening — Implementation Plan

## Context

M9-C57 Phases 15–20 have been certified (commit 6be3f46e). The post-implementation convergence pass (Phase 3) produced real verification evidence but exposed 20 critical gaps in evidence integrity, verification control plane, and validation rigor. The framework **runs and produces evidence**, but it has NOT been hardened against messy realities: stale evidence, interrupted runs, tampered artifacts, ambiguous PASS semantics, and uncontrolled failure classification.

The M9-C57 Phase 3 progress report (`runtime/generated/m9-c57/post-implementation-convergence/progress.md`) defines the next objective: **M9-C57 — Verification Integrity & Diagnostic Hardening** via seven proof experiments.

Additionally, the working tree contains uncommitted changes from Phase 3 convergence fixes that must be committed before proceeding:
- Frontend test fixes (8 `__tests__/` files — React.createElement JSX syntax)
- Platform route fixes (`errors/page.tsx`, `capabilities/page.tsx`, `verification/run/[capability]/page.tsx`)
- `use-live-execution.ts` setState-in-effect fix
- `runtime/verify.py` `from typing import Any` import fix
- `scripts/launch.sh` (new operational entry points)
- Generated artifacts (`git-fetch-events.jsonl`, `platform/snapshot.json`, `engineering-events.jsonl`)
- Deleted `backend/tests/invariants/_m4_probe_live/test_m4_exit_probe.py`

## Current State Assessment

### M9-C57 Phase 3 — Completed (Pending Commit)
| Item | Status |
|------|--------|
| Frontend lint/build/test fixes | ✅ Fixed, pending commit |
| Backend verification executed | ✅ 3,058/3,059 pass, 1 real failure (floating-rate) |
| Quick checks pass | ✅ ruff, black, mypy, unit tests, architecture |
| Platform API endpoints verified | ✅ 5 endpoints working |
| Launcher script created | ✅ `scripts/launch.sh` |
| C50 freeze preserved | ✅ No frozen modules modified |
| Floating-rate failure classified | ✅ Pre-existing, not caused by C57 |

### M9-C57 Phase 3 — Gaps Identified (NOT CERTIFIED)
The 20 gaps are categorized into:
1. **Evidence integrity**: lineage traceability, stale-evidence protection, tampering resistance, idempotency
2. **Verification control plane**: PASS semantics, partial execution policy, workflow validation matrix
3. **Diagnostic capability**: controlled-failure test, pre-existing vs introduced classification, false-positive/negative resistance
4. **Infrastructure**: snapshot/cache lifecycle, interruption/recovery, clean-session launcher proof
5. **Classification**: C50 mypy provenance, schema/versioning, security boundaries

### M9-C45 Balance Work — Status
- M45.0–M45.4: DONE
- M45.14 (L-ARCH-001): DONE — mutmut 3.7.0 handles all Python 3.10+ syntax used in production
- M45.6 (interrupt/resume): NOT STARTED — M44.32 explicit requirement
- M45.5, M45.9, M45.10, M45.11, M45.12, M45.13, M45.15–M45.21, M45.23, M45.24: PENDING

## Objective

Execute the seven proof experiments from the M9-C57 Phase 3 report to harden the verification framework against evidence integrity failures, and complete the M9-C45 balance work milestones (starting with M45.6 interrupt/resume).

## Important Details

- **All seven proof experiments must pass without modifying frozen C50 or "fixing" evidence by manipulating tests**
- **M45.6 is an explicit M44.32 requirement** — must complete before M45.24
- **The uncommitted working tree changes are Phase 3 convergence fixes** — commit these first before new work
- **No `not_checked` results may be unexplained**
- **Cache validation must prevent stale evidence**
- **CI uses canonical path exclusively** (verify.py mutation → mutation_runner.py → mutmut 3.7.0)

## Work State

### Completed
- M9-C57 Phases 1–20 certified and committed
- M9-C57 Phase 3 convergence fixes applied (pending commit)
- M9-C45 M45.0–M45.4 and M45.14 artifacts created
- `mutation-population-completeness.json` confirms mutmut 3.7.0 handles all production syntax
- `mutation_contract.py` has `execution_path` field (M45.12 done)
- `verify.py` uses canonical control plane (M9-C49 consolidation)

### Active
- M9-C57 Phase 4: Verification Integrity & Diagnostic Hardening (7 proof experiments)
- M9-C45 balance work completion (M45.6 first)
- Working tree has pending changes awaiting commit

### Blocked
- None — all prerequisites are in place

## Next Move

### Step 1: Commit Phase 3 Convergence Fixes
Commit the uncommitted working tree changes to establish a clean baseline for the proof experiments:

```bash
git add -A
git commit -m "M9-C57 Phase 3: post-implementation convergence fixes

- Fix frontend test JSX syntax (8 test files)
- Fix platform route setState-in-effect anti-patterns
- Fix verify.py typing import
- Add scripts/launch.sh operational entry points
- Remove obsolete m4 exit probe test
- Generated platform/engineering event artifacts"
```

### Step 2: Run Clean Baseline (Proof Experiment 1)
Execute `bash .github/scripts/run_backend_verification.sh` on clean repo state:
- Record: exit code, duration, evidence files
- Verify: PASS verdict on clean baseline
- Artifact: `runtime/generated/m9-c57/proof-experiments/proof-1-clean-baseline.json`

### Step 3: Controlled Code Failure (Proof Experiment 2)
Introduce a deliberate, reversible bug into `src/engines/loan_engine/` floating rate calculation:
- Run verification: must produce FAIL with correct diagnosis
- Verify: failure is correctly classified (not INFRASTRUCTURE_FAILURE)
- Verify: diagnostic output identifies the specific function
- Artifact: `runtime/generated/m9-c57/proof-experiments/proof-2-controlled-failure.json`

### Step 4: Controlled Environment Failure (Proof Experiment 3)
Remove a required dependency (e.g., temporarily rename a test fixture):
- Run verification: must produce ENVIRONMENT_FAILURE
- Verify: failure is correctly classified as environment issue, not code defect
- Artifact: `runtime/generated/m9-c57/proof-experiments/proof-3-environment-failure.json`

### Step 5: Interrupted Verification (Proof Experiment 4)
Start backend verification, send SIGTERM to the process mid-execution:
- Verify: workspace state preserved
- Verify: evidence files exist but marked INCOMPLETE
- Verify: never produces PASS from interrupted run
- Resume: re-run with same parameters
- Verify: completed mutants not re-executed, final counts consistent
- Artifact: `runtime/generated/m9-c57/proof-experiments/proof-4-interrupted-verification.json`

### Step 6: Stale Evidence Scenario (Proof Experiment 5)
Take a previous PASS evidence file, modify a source file, then attempt to consume the stale evidence:
- Verify: stale evidence is rejected (not used for current verdict)
- Verify: system detects evidence is from different repository state
- Artifact: `runtime/generated/m9-c57/proof-experiments/proof-5-stale-evidence.json`

### Step 7: Evidence Tampering Scenario (Proof Experiment 6)
Take a real FAIL evidence file, manually change JSON status to PASS, then feed to framework:
- Verify: tampered evidence is detected and rejected
- Verify: system does not produce PASS from manipulated artifacts
- Artifact: `runtime/generated/m9-c57/proof-experiments/proof-6-evidence-tampering.json`

### Step 8: Repeated Baseline Runs (Proof Experiment 7)
Run the clean baseline verification 3 times consecutively:
- Verify: all 3 runs produce equivalent conclusions
- Verify: reproducible results (same mutant counts, same verdict)
- Verify: no silent state leakage between runs
- Artifact: `runtime/generated/m9-c57/proof-experiments/proof-7-idempotency.json`

### Step 9: Classification of Real Existing Failures
Document the three real failure types found during convergence:
1. C50 frozen mypy failure → correctly classified as C50 frozen
2. Floating-rate property failure → correctly diagnosed as pre-existing code bug
3. Frontend Vitest failure → correctly classified as pre-existing React rendering issue
- Artifact: `runtime/generated/m9-c57/proof-experiments/proof-8-failure-classification.json`

### Step 10: Commit Proof Experiment Results
Commit all proof experiment artifacts and update the convergence progress report.

### Step 11: M9-C45 M45.6 — Interrupt/Resume Qualification
Create `runtime/generated/m9-c45/campaign-recovery-report.json`:
- Start account_engine campaign with `--max-runtime 300`
- After 10 seconds, send SIGTERM to mutmut subprocess
- Verify: workspace state preserved, evidence files exist
- Resume: re-run with same parameters
- Verify: completed mutants not re-executed, final counts consistent
- Verify: no orphaned processes, no silent environment mixing

### Step 12: M9-C45 Remaining Milestones
Complete M45.5 (full campaign qualification), M45.9/M45.10 (CI qualification), M45.11 (evidence certification), M45.15–M45.21 (supporting), M45.23 (architecture doc), M45.24 (final certification).

### Step 13: Update M9-C57 Progress Report
Update `runtime/generated/m9-c57/post-implementation-convergence/progress.md` with proof experiment results and certification status.

### Step 14: Final Certification Decision
- M9-C57: Issue formal certification based on proof experiment results
- M9-C45: Issue M45.24 final certification decision

## Acceptance Criteria

After completion:
1. All 7 proof experiments pass (clean baseline, controlled failure, environment failure, interrupted, stale evidence, tampering, idempotency)
2. Real existing failures correctly classified (C50 frozen, pre-existing code bug, pre-existing frontend issue)
3. No PASS from interrupted/stale/tampered evidence
4. M45.6 interrupt/resume campaign works correctly
5. All M9-C57 Phase 4 artifacts present in `runtime/generated/m9-c57/proof-experiments/`
6. M9-C45 M45.6 artifact present in `runtime/generated/m9-c45/`
7. Working tree is clean after all commits
8. No C50 freeze violation
9. No duplicate architecture introduced
10. All exclusions explicitly documented

## Risks

1. **Proof experiments may reveal new bugs** — the framework might not correctly classify some failure modes; be prepared to adjust diagnostic logic
2. **Interrupt/resume complexity** — SIGTERM handling may leave orphaned processes; implement cleanup logic
3. **Stale evidence detection** — requires robust repository state fingerprinting; may need to enhance `MutationResult` with timestamp + git tree hash
4. **Tampering detection** — requires evidence file integrity checks (hashing); may need to add `evidence_hash` field to `MutationResult`
5. **M9-C45 M45.6 depends on M9-C57 proof experiment infrastructure** — may need shared utilities for process management and state verification

## Validation Plan

1. `python runtime/verify.py check` passes on clean baseline
2. `bash .github/scripts/run_backend_verification.sh` produces correct verdicts for each proof experiment
3. `python runtime/verify.py mutation --smoke` passes (bounded mutation infra smoke)
4. All proof experiment artifacts are valid JSON with required fields
5. `git status --short` shows clean working tree after commits
6. `python runtime/verify.py verify-status` shows all phases certified
7. `runtime/verify.py integrity` confirms no stale evidence
8. M45.6 campaign recovery works: `python runtime/verify.py mutation --target account_engine` survives interrupt

## Open Questions

1. For proof experiment 2 (controlled failure), should the bug be in `loan_engine` floating rate (real known failure) or a new deliberate injection? Using the existing known failure avoids introducing new test code but provides less control over the failure mode.
2. For proof experiment 4 (interrupt), should we use `verify.py check` or `verify.py mutation`? Mutation campaigns are longer and more likely to be interruptible, but `verify.py check` is more representative of typical usage.
3. For stale evidence detection (proof experiment 5), should we add a new field to `MutationResult` or rely on existing `repository_sha` + `tree_sha` fields? The existing fields may be sufficient if the framework properly compares them.
4. For tampering detection (proof experiment 6), should we implement file-level hashing or structural validation? Hashing is simpler but requires a hash store; structural validation is more robust but more complex.
5. Should proof experiment artifacts go to `runtime/generated/m9-c57/proof-experiments/` or `runtime/generated/m9-c57/verification-integrity/`? The naming should align with the milestone convention.

## Out of Scope

- Implementing new mutation backends (cosmic-ray, mutpy)
- Modifying production code to improve mutation scores
- Running full repository mutation campaign locally (deferred to CI)
- Automated test generation for mutation gaps (next phase after M9-C45)
- New feature development for the platform
- Fixing the pre-existing floating-rate bug (not caused by C57)
- Modifying frozen C50 modules

## Relevant Files

- `runtime/generated/m9-c57/post-implementation-convergence/progress.md` — current convergence state, 20 gaps defined
- `runtime/foundation/verification/mutation_contract.py` — canonical mutation result contract with `execution_path` field
- `runtime/verify.py` — thin compatibility shim routing through canonical control plane
- `runtime/foundation/verification/control_plane_facade.py` — single canonical control plane dispatcher
- `backend/tests/invariants/_m4_probe_live/test_m4_exit_probe.py` — deleted file (already removed from working tree)
- `scripts/launch.sh` — new operational entry points (pending commit)
- `.github/scripts/run_backend_verification.sh` — backend verification script
- `.github/scripts/run_fast_checks.sh` — quick verification script
- `runtime/generated/m9-c45/mutation-population-completeness.json` — L-ARCH-001 investigation results
- `runtime/generated/m9-c45/m9-c45-baseline.json` — M9-C45 baseline frozen
- `runtime/generated/m9-c57/phase-21/SKIPPED.md` — Phase 21 skip documentation
- `runtime/generated/m9-c57/phases-15-21/SUPERSEDED.md` — phases 15-21 superseded documentation
