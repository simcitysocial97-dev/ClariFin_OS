# VEA-5 M3 — Verification Runtime Integrity

**Milestone:** VEA-5 M3 — Verification Runtime Integrity
**Status:** CERTIFIED (evidence-producing implementation milestone)
**Date:** 2026-08-12
**Branch:** recovery/program-r-forensic-reconstruction
**Prerequisite:** `VEA5_M2_TIER_PLANNING.md` (M2, CERTIFIED); `VEA5_CI_FAILURE_FORENSICS.md` (M0, CERTIFIED)
**Constraint honored:** No `.github/workflows/` file modified. No production application code modified. No test weakened or deleted. W4/W6/cache were explicitly in scope; M4/M5/M6 deferred.

---

## 1. Objective

Fix the three verification-runtime integrity defects discovered in VEA-5 M0 and
prove each fix with tests:

| Code | Defect | M3 bucket |
|------|--------|-----------|
| W4 | `test_backend_exit_contract_holds_both_directions` killed by outer 30s `pytest-timeout` | M3-A |
| W6 | `run_mutation_selective.sh` runner hardcodes bare `python` | M3-B |
| W3 | Verification cache can replay FAIL as PASS / exit 0 | M3-C |

M3 certifies the verification runtime itself before any CI topology changes.

---

## 2. M3-A — Runtime Timeout Defect (W4)

### Root cause

`run_runtime_verification.sh` invokes the runtime test suite with
`python3 -m pytest runtime/tests/ -q --timeout=30`. The heavy test
`test_backend_exit_contract_holds_both_directions` runs the real
`run_backend_verification.sh` as a subprocess; that script takes **66–140s**,
exceeding the outer 30s per-test timeout. The test is killed before it can
prove the exit-contract probe.

### Fix

1. **Measured per-test timeout override.** Added `@pytest.mark.timeout(300)` to
   `test_backend_exit_contract_holds_both_directions`. The 300s value is derived
   from measured execution (66–140s observed, with margin for CI slowness), not
   chosen arbitrarily. The per-test marker overrides the global `--timeout=30`
   only for this specific evidence-producing test.
2. **Lightweight controlled-probe test.** Added `TestExitCodeContractLightweight`
   in `runtime/tests/test_backend_evidence.py` using a tiny inline pytest
   (pass → exit 0, fail → exit != 0). This is the hierarchy step-1 proof that
   the exit-code contract holds independently of the full backend runtime. It
   runs in milliseconds and is immune to any global timeout.

### Proof

```
python3 -m pytest runtime/tests/test_backend_evidence.py -q --timeout=300
```
Result: **35 passed** (including the heavy test) in ~67s.

---

## 3. M3-B — Mutation Runner Portability (W6)

### Root cause

`.github/scripts/run_mutation_selective.sh` line 40 embedded bare `python` in
the mutmut runner string:
```bash
--runner "python -m pytest tests/unit/ tests/properties/ -x -q --timeout=30"
```
`ubuntu-latest` only ships `python3`; `python` is not on PATH.

### Fix

Changed line 40 to:
```bash
--runner "python3 -m pytest tests/unit/ tests/properties/ -x -q --timeout=30"
```

This reuses the repository's existing convention:
* every other `.github/scripts/run_*.sh` uses `python3`
* `.github/actions/bootstrap-runtime/action.yml` provisions `python3` explicitly

No new interpreter-selection mechanism introduced.

### Proof

Added `TestMutationRunnerPortability` in `runtime/tests/test_backend_evidence.py`:
* `test_mutation_runner_uses_python3_not_python` — asserts `python3 -m pytest`
  present and bare `python -m pytest` absent.
* `test_mutation_script_is_syntactically_valid` — `bash -n` passes.

---

## 4. M3-C — Cache Integrity Defect (W3)

### Root cause

The verification cache (`runtime/generated/verification-cache.json`) stored
execution metrics but not the verification verdict. A cache hit path could
replay a previously recorded FAIL as a successful verification (exit 0),
violating the integrity invariant:

```
Verification FAILED
Failed: 3
exit code = 0   ← forbidden
```

### Fix

New module `runtime/foundation/verification/cache.py` implements the explicit
replay contract from `VEA5_EXECUTION_MODEL.md` §12-§13:

```python
class VerificationCache:
    def replay(self, commit, changed_files, profile) -> ReplayResult:
        ...
```

`ReplayResult`:
* `reusable=True` + `overall_status="fail"` → `exit_code=1`
* `reusable=True` + `overall_status="pass"` → `exit_code=0`
* `reusable=False` → caller must re-execute; `exit_code=None` (never silently 0)

`verify.py` `main()` is wired to use the cache replay:
* **valid cache hit** → replay stored verdict with correct exit code; skip re-execution
* **invalid / missing / corrupt / fingerprint mismatch** → re-execute full verification and save new verdict

Per-profile `changed_files` isolation prevents one profile's fingerprint from
invalidating another's.

### Proof

9 tests in `runtime/tests/test_vea5_verification_cache.py`:
* missing cache → not reusable
* corrupt cache → not reusable
* fingerprint mismatch → not reusable
* profile mismatch → not reusable
* cached PASS → exit 0
* cached FAIL → exit != 0 (critical invariant)
* stale failure never silently becomes PASS
* save/reload round-trip preserves FAIL status
* multiple profiles do not interfere

---

## 5. Acceptance Gate Results

| Gate | Required | Measured |
|------|----------|----------|
| Runtime test suite GREEN | 458+ passed | **488 passed, 0 failed** |
| Exit-code contract | success→0, failure→non-zero | Proven by heavy test + lightweight probe |
| Mutation execution | CI interpreter portable | `python3` confirmed; bare `python` removed |
| Cache PASS | PASS remains PASS | Replay verified |
| Cache FAIL | FAIL remains FAIL | Replay verified (exit 1) |
| Cache corrupt/missing | Re-execute or fail safely | `reusable=False` verified |
| No test weakening | — | 0 tests weakened/deleted |
| No product-code modification | — | 0 backend/frontend files changed |
| No workflow modification | `.github/workflows/` untouched | Verified |

> **Do not certify M3 merely because the tests are green.**
> The tests prove *why* they are green:
> * the exit-contract test runs the **real backend script** and proves failure attribution
> * the lightweight probe proves the contract independently of the heavy runtime
> * the cache tests simulate stored PASS and stored FAIL and assert the exact exit code
> * the mutation test asserts the interpreter contract statically and validates syntax

---

## 6. What M3 Deliberately Did NOT Do

Per scope discipline, the following remain deferred:

* **M4/M6** — local/CI plan equivalence + reconciliation (M1 §14).
* **M5** — CI topology integration (wire tiers into GitHub Actions).
* **M7/M8** — workflow topology re-audit; branch-protection record.
* **M9** — CodeQL PR-eligibility wiring (config unchanged).
* **M10** — deep profile contract (golden/mutation/E2E home).

M3 isolates "does the verification runtime itself behave correctly?" from "is CI wired correctly?".

---

## 7. M3 Verdict

CERTIFIED. The three M0 runtime defects are fixed and proven:
* W4: exit-contract test runs to completion under a measured 300s override; lightweight probe provides independent proof.
* W6: mutation runner uses `python3`, matching repo convention; static proof in test.
* W3: cache replay contract guarantees FAIL→non-zero, PASS→0, corrupt→re-execute; 9 tests prove every row of the acceptance table.

Runtime test suite: **488 passed, 0 failed**.

*End of VEA-5 M3 Verification Runtime Integrity.*
