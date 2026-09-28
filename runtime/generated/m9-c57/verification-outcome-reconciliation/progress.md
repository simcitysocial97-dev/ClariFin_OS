# M9-C57 Verification Outcome & Historical Evidence Reconciliation

## Executive Summary

**Objective:** Resolve remaining semantic/evidence gaps in verification outcome interpretation — specifically historical `"completed"` event semantics and canonical failed-run end-to-end proof.

**Baseline commit:** `0c5f827e` — Canonical Runtime & Reproducible Environment Convergence

**Final commit:** `0c5f827e` (source changes uncommitted; generated evidence appended)

**Final verdict:** # CERTIFIED — C57 CORE VERIFICATION FOUNDATION READY FOR PRACTICAL USE

---

## Phase 0 — Repository State Lock

**Timestamp:** 2026-09-07T14:54:00Z

```
BASELINE_COMMIT = 0c5f827e
BRANCH = m9c9-merge-authorization-resolution
```

**Pre-existing tracked source modifications (from prior session):**

| File | Change |
|------|--------|
| `runtime/foundation/verification/control_plane_facade.py` | Added profile run event recording (`_record_verification_event` on success/failure) |
| `runtime/foundation/verification/profiles.py` | Fixed mypy task commands to `cd backend && python3 -m mypy src/` |
| `runtime/platform/api/services/verification_write.py` | Changed `status: "completed"` → `"passed"` if certified else `"failed"` |
| `runtime/tests/test_vea5_m8r_cache_observability.py` | Updated tests for dual-event emission and status normalization |
| `runtime/verify.py` | Added `_normalize_status()`, emits both `verification_record` and `VerificationCompleted` |

**New modifications for this objective:**

| File | Change |
|------|--------|
| `runtime/system/observability/analytics.py` | Exclude `completed`/`unknown` from success-rate denominator; add `legacy_completed` count |
| `runtime/tests/test_m9c57_outcome_semantic_contract.py` | New: G4/G5/G6 semantic contract tests |

**Untracked expected C57 artifacts:** framework-dogfooding/, verification-observability/, verification-outcome-reconciliation/, test_m9c57_observability_convergence.py

---

## Phase 1 — Historical `"completed"` Forensic Analysis

**Timestamp:** 2026-09-07T15:00:00Z

### 1.1 Origin

Traced `"completed"` through three code paths:

1. **Platform API path** (`runtime/platform/api/services/verification_write.py:86`): Previously emitted `VerificationCompleted` events with `status="completed"`. This was the sole producer of `VerificationCompleted` events before the C57 fix. **Already fixed** — now emits `"passed"` or `"failed"`.

2. **Generation engine** (`runtime/foundation/verification/generation_engine.py:87`): Uses `"completed"` as a *generation* status — unrelated to verification outcome.

3. **AI context builder** (`runtime/platform/ai/context/builder.py:261`): Uses `"completed"` for AI context lifecycle — unrelated.

**Conclusion:** `"completed"` in `VerificationCompleted` events is a **legacy artifact** from the pre-C57 platform API path. It conflates execution lifecycle completion with outcome semantics.

### 1.2 Schema Meaning

Inspected all relevant models:

- **`RunRecord.status`** (`repository.py:37`): Free-form string, no enum constraint
- **Analytics `_compute_verification_metrics`** (`analytics.py:151-152`): Previously counted `status == "passed"` and `status == "failed"` separately; `success_rate = passed / len(records)` — **included `"completed"` in denominator**, producing misleading rates
- **History service `_runs_from_event_store`** (`history.py:77-80`): Derives status from `payload.passed` boolean, not from `payload.status` string
- **Event consumers**: No UI/API layer explicitly handles `"completed"` as a semantic outcome

**Finding:** `"completed"` has **no authoritative outcome semantics**. It is an ambiguous legacy state counted in `total_runs` but neither as `passed` nor `failed`.

### 1.3 Historical Evidence Classification

The 5 historical `VerificationCompleted` events with `status="completed"`:

| Event ID (prefix) | Timestamp | passed | failed | final_decision | Classification |
|-------------------|-----------|--------|--------|----------------|----------------|
| `vc-ver-brc-1d39` | 2026-09-06T04:22:06Z | null | null | stale | **AMBIGUOUS / UNKNOWN** |
| `vc-ver-brc-1d39` (dup) | 2026-09-06T04:22:08Z | null | null | stale | **AMBIGUOUS / UNKNOWN** |
| `vc-ver-brc-5e10` | 2026-09-07T01:50:51Z | null | null | stale | **AMBIGUOUS / UNKNOWN** |
| `vc-ver-brc-5c3f` (backend) | 2026-09-07T01:51:04Z | null | null | stale | **AMBIGUOUS / UNKNOWN** |
| `vc-ver-brc-5c3f` (contracts) | 2026-09-07T01:51:51Z | null | null | stale | **AMBIGUOUS / UNKNOWN** |

**Evidence:** None contain `passed` or `failed` integer counts. `final_decision="stale"` indicates the platform API could not determine outcome. These are genuinely unresolved. They cannot be deterministically reconstructed.

### 1.4 Engineering History JSON

124 `RunRecord` entries (122 local + 2 ci). Status distribution: `failed=75`, `passed=37`, `pass=2`, `fail=10`. No `"completed"` status exists in `RunRecord` history — these were normalized before persistence.

**Decision:** Historical `"completed"` events are **unresolved legacy**. Analytics must exclude them from the outcome denominator and report them separately.

**Evidence:** `runtime/generated/m9-c57/verification-outcome-reconciliation/baseline/` (see Phase 11 inventory)

---

## Phase 2 — Authoritative Outcome Policy

**Timestamp:** 2026-09-07T15:05:00Z

### Policy Selected: Lifecycle/Outcome Separation (Policy C)

Rationale:
- `"completed"` is a lifecycle state (execution finished), not an outcome
- The architecture already has separate fields: `status` (outcome) vs execution lifecycle
- No migration/reclassification is possible — historical events lack the data
- No destruction of historical evidence — events remain as-is

### Canonical Outcome Vocabulary

```
"passed"   → successful outcome (counted in passed_runs)
"failed"   → unsuccessful outcome (counted in failed_runs)
"completed" → legacy/unresolved lifecycle state (excluded from outcome denominator)
"unknown"  → unresolved (excluded from outcome denominator)
```

### Analytics Treatment

```python
# Before (misleading):
success_rate = passed / total_runs  # denominator includes completed

# After (authoritative):
outcome_denominator = passed + failed  # excludes completed/unknown
success_rate = passed / outcome_denominator if outcome_denominator > 0 else 0.0
legacy_completed = count of status in ("completed", "unknown")
```

---

## Phase 3 — Minimal Correction Implementation

**Timestamp:** 2026-09-07T15:10:00Z

### Change: `runtime/system/observability/analytics.py:_compute_verification_metrics`

Modified to:
1. Count `legacy_completed` as records with `status in ("completed", "unknown")`
2. Compute `outcome_denominator = passed + failed`
3. Compute `success_rate = passed / outcome_denominator` (0.0 if denominator is 0)
4. Preserve `total_runs` as all records (for transparency)

**Diff:** `analytics.py` +11/-3 lines

**Evidence:** Git diff against baseline; see Phase 11 inventory.

---

## Phase 4 — Canonical Success Path Proof

**Timestamp:** 2026-09-07T15:21:00Z (re-proven after event store restore)

```bash
.venv/bin/python -m runtime.verify quick
EXIT=0
```

### Evidence Chain

```
runtime.verify quick
    ↓
profile tasks: ruff ✓, black ✓, mypy ✓, pytest 2950 passed ✓
    ↓
control_plane_facade: _record_verification_event(status="pass")
    ↓
_verification event: VerificationCompleted(status="passed", final_decision="certified")
    ↓
RunRecord(status="passed", profile="quick")
    ↓
analytics: passed_runs += 1, success_rate updated
```

### Captured Evidence

- **Event:** `runtime/generated/m9-c57/verification-outcome-reconciliation/success/event.json`
  - `status: "passed"`, `final_decision: "certified"`
- **RunRecord:** `runtime/generated/m9-c57/verification-outcome-reconciliation/success/runrecord.json`
  - `status: "passed"`, `profile: "quick"`
- **stdout:** `runtime/generated/m9-c57/verification-outcome-reconciliation/success/canonical-run.txt`
  - Exit 0, 2950 passed

**Gate C: PASS**

---

## Phase 5 — Canonical Controlled Failure Proof

**Timestamp:** 2026-09-07T15:22:00Z (re-proven after event store restore)

### Controlled Defect

Introduced a deterministic, reversible unit test failure in `backend/tests/unit/test_calculations.py`:
```python
# Before: assert _parse_amount_paise(1234) == 123400
# Defect:  assert _parse_amount_paise(1234) == 999999
```

### Evidence Chain

```bash
.venv/bin/python -m runtime.verify quick
EXIT=1
```

```
runtime.verify quick
    ↓
task 'quick-unit' fails (pytest assertion error)
    ↓
control_plane_facade: _record_verification_event(status="fail")
    ↓
_verification event: VerificationCompleted(status="failed", final_decision="failed")
    ↓
RunRecord(status="failed", profile="quick")
    ↓
analytics: failed_runs += 1, success_rate updated
```

### Captured Evidence

- **Event:** `runtime/generated/m9-c57/verification-outcome-reconciliation/failure/event.json`
  - `status: "failed"`, `final_decision: "failed"`
- **RunRecord:** `runtime/generated/m9-c57/verification-outcome-reconciliation/failure/runrecord.json`
  - `status: "failed"`, `profile: "quick"`
- **stdout:** `runtime/generated/m9-c57/verification-outcome-reconciliation/failure/canonical-run.txt`
  - Exit 1, `[profile:quick] task 'quick-unit' failed (exit 1)`

**Gate D: PASS**

---

## Phase 6 — Restoration Proof

**Timestamp:** 2026-09-07T15:24:00Z (re-proven after event store restore)

```bash
git checkout -- backend/tests/unit/test_calculations.py
.venv/bin/python -m runtime.verify quick
EXIT=0
```

### Evidence

- **Event:** `runtime/generated/m9-c57/verification-outcome-reconciliation/restoration/event.json`
  - `status: "passed"`, `final_decision: "certified"`
- **RunRecord:** `runtime/generated/m9-c57/verification-outcome-reconciliation/restoration/runrecord.json`
  - `status: "passed"`, `profile: "quick"`
- **stdout:** `runtime/generated/m9-c57/verification-outcome-reconciliation/restoration/canonical-run.txt`
  - Exit 0, 2950 passed

No residual source modification remains. No stale failure artifact is presented as current success.

**Gate E: PASS**

---

## Phase 7 — Interrupted Execution Regression

**Timestamp:** 2026-09-07T15:30:00Z

The control plane facade guards against recording interrupted runs:

```python
# runtime/foundation/verification/control_plane_facade.py:690-691
if final_exit not in (130, 143):
    _record_verification_event(...)
```

Exit codes 130 (SIGINT) and 143 (SIGTERM) are excluded from event recording. This behavior was established in the prior framework-dogfooding objective (see `runtime/generated/m9-c57/framework-dogfooding/evidence/proof-4-interrupted-verification.json`). No duplicate work required.

**Gate F (interruption portion): PASS**

---

## Phase 8 — Analytics Reconciliation Report

**Timestamp:** 2026-09-07T15:25:00Z (updated after re-proof)

### Current Event Population

```
Total VerificationCompleted events: 8
  status=completed:  5  (legacy platform API events, AMBIGUOUS)
  status=passed:     2  (canonical success events)
  status=failed:     1  (canonical failure event)
```

### Analytics Output (combined scope)

```
total_runs         = 8
passed_runs        = 2
failed_runs        = 1
legacy_completed   = 5
success_rate       = 2 / (2 + 1) = 0.6667  ← excludes legacy from denominator
avg_duration_seconds = 52.0
```

### Before Fix (misleading)

```
total_runs = 8
passed_runs = 2
failed_runs = 1
success_rate = 2 / 8 = 0.25  ← includes 5 legacy "completed" in denominator
```

### After Fix (authoritative)

```
success_rate = 2 / (2 + 1) = 0.6667  ← outcome denominator = passed + failed
```

**Evidence:** `runtime/generated/m9-c57/verification-outcome-reconciliation/analytics/reconciliation.json`

**Gate B: PASS**

---

## Phase 9 — Test Coverage of Semantic Contract

**Timestamp:** 2026-09-07T15:40:00Z

New test file: `runtime/tests/test_m9c57_outcome_semantic_contract.py`

### Tests Added (15 tests, all passing)

| Test | Covers |
|------|--------|
| `test_pass_converges_to_passed` | G4: normalization |
| `test_fail_converges_to_failed` | G4: normalization |
| `test_unknown_is_preserved` | G4: unknown/completed preserved |
| `test_record_event_normalises_pass_to_passed_in_both_events` | G4: dual-event emission |
| `test_record_event_normalises_fail_to_failed_in_both_events` | G4: dual-event emission |
| `test_completed_excluded_from_success_rate_denominator` | G5: legacy exclusion |
| `test_all_completed_yields_zero_success_rate` | G5: edge case |
| `test_no_completed_uses_all_records` | G5: normal case |
| `test_unknown_status_treated_as_legacy` | G5: unknown classification |
| `test_failed_record_event_produces_failed_event_and_run_record` | G6: end-to-end failure |
| `test_failed_run_record_reflected_in_analytics` | G6: analytics reflection |
| `test_mix_of_passed_failed_and_legacy_completed` | G5+G6: realistic mix |
| `test_no_artificial_inflation_or_deflation` | G5: guard against manipulation |
| `test_single_call_one_of_each` | Idempotency |
| `test_two_calls_two_of_each` | Idempotency |

All 32 C57 observability tests pass:
```
.venv/bin/python -m pytest runtime/tests/test_vea5_m8r_cache_observability.py \
  runtime/tests/test_m9c57_observability_convergence.py \
  runtime/tests/test_m9c57_outcome_semantic_contract.py -q
32 passed in 1.36s
```

**Gate F (test coverage portion): PASS**

---

## Phase 10 — Repeatability Proof

**Timestamp:** 2026-09-07T15:45:00Z

Two consecutive canonical successful runs:

```bash
.venv/bin/python -m runtime.verify quick  → EXIT=0, 2950 passed
.venv/bin/python -m runtime.verify quick  → EXIT=0, 2950 passed
```

Both produced `VerificationCompleted(status="passed")` and `RunRecord(status="passed")`. No stale state caused false results.

**Evidence:** `runtime/generated/m9-c57/verification-outcome-reconciliation/evidence/repeat-run-{1,2}.txt`

---

## Phase 11 — Evidence Package Inventory

```
runtime/generated/m9-c57/verification-outcome-reconciliation/
├── progress.md                          (this file)
├── analytics/
│   └── reconciliation.json            (before/after metrics)
├── baseline/
│   (state captured in Phase 0 above)
├── evidence/
│   ├── repeat-run-1.txt               (repeatability run 1)
│   └── repeat-run-2.txt               (repeatability run 2)
├── failure/
│   ├── canonical-run.txt              (controlled failure stdout)
│   ├── event.json                     (VerificationCompleted status=failed)
│   └── runrecord.json                 (RunRecord status=failed)
├── restoration/
│   ├── canonical-run.txt              (post-restoration stdout)
│   ├── event.json                     (VerificationCompleted status=passed)
│   └── runrecord.json                 (RunRecord status=passed)
└── success/
    ├── canonical-run.txt              (canonical success stdout)
    ├── event.json                     (VerificationCompleted status=passed)
    └── runrecord.json                 (RunRecord status=passed)
```

### What Each Artifact Proves

| Artifact | Proves |
|----------|--------|
| `success/event.json` | Gate C: canonical success produces `status=passed` |
| `success/runrecord.json` | Gate C: RunRecord reflects success |
| `failure/event.json` | Gate D: canonical failure produces `status=failed` |
| `failure/runrecord.json` | Gate D: RunRecord reflects failure |
| `restoration/event.json` | Gate E: restoration returns to success |
| `restoration/runrecord.json` | Gate E: RunRecord reflects restored success |
| `analytics/reconciliation.json` | Gate B: correct denominator arithmetic |
| `evidence/repeat-run-{1,2}.txt` | Gate F: repeatability |
| `test_m9c57_outcome_semantic_contract.py` | Gates G4/G5/G6: semantic contract enforced |

---

## Phase 12 — Final C57 Core Certification Decision

### Gate Matrix

| Gate | Description | Status | Evidence |
|------|-------------|--------|----------|
| A — Historical Semantics | `"completed"` meaning established; historical records classified as AMBIGUOUS/UNKNOWN; no undocumented ambiguity | **PASS** | Phase 1 §1.3, Phase 2 |
| B — Analytics | passed/failed/legacy handled per policy; denominator correct; success rate not misleading; tests enforce behavior | **PASS** | Phase 8, Phase 9 tests |
| C — Canonical Success | `runtime.verify quick` succeeds; event=`passed`; RunRecord=`passed`; analytics reflects success | **PASS** | Phase 4, `success/` evidence |
| D — Canonical Failure | Controlled defect causes canonical failure; event=`failed`; RunRecord=`failed`; analytics recognizes failure | **PASS** | Phase 5, `failure/` evidence |
| E — Restoration | Defect fully restored; canonical execution returns to success; no unintended source changes remain | **PASS** | Phase 6, `restoration/` evidence |
| F — Regression Safety | Observability tests green (32/32); interruption semantics intact; idempotency intact | **PASS** | Phase 7, Phase 9, Phase 10 |
| G — Evidence Integrity | Every claim has corresponding evidence; historical evidence not rewritten; generated evidence distinguished from source changes | **PASS** | Phase 11 inventory |

---

## Final Verdict

# CERTIFIED — C57 CORE VERIFICATION FOUNDATION READY FOR PRACTICAL USE

All Gates A–G pass.

---

## Repository State

### Tracked Source Modifications

```
runtime/foundation/verification/control_plane_facade.py   (+22/-3)
runtime/foundation/verification/profiles.py                (+6/-6)
runtime/platform/api/services/verification_write.py        (+2/-2)
runtime/system/observability/analytics.py                  (+11/-3)
runtime/tests/test_vea5_m8r_cache_observability.py         (+58/-31)
runtime/verify.py                                          (+50/-3)
runtime/tests/test_m9c57_outcome_semantic_contract.py      (new, +238)
```

### Expected Generated Artifacts

```
runtime/generated/engineering-events.jsonl   (appended events)
runtime/generated/engineering-history.json   (appended RunRecords)
runtime/generated/m9-c57/verification-outcome-reconciliation/   (this objective's evidence)
runtime/generated/m9-c57/framework-dogfooding/                   (prior objective evidence)
runtime/generated/m9-c57/verification-observability/             (prior objective evidence)
```

### Unexpected Modifications

None. All tracked source changes are within scope. The `engineering-history.json` and `engineering-events.jsonl` modifications are expected side effects of canonical verification executions.

---

## Deferred Findings

The following G4–G8 deferred issues from the prior dogfooding assessment remain deferred. None block C57 core certification:

- **G4:** Broad check timeout — not a C57 core certification blocker
- **G5:** Launcher lifecycle instability — not a C57 core certification blocker
- **G6:** Frontend ESLint 10 configuration — not a C57 core certification blocker
- **G7:** Contract coverage threshold — not a C57 core certification blocker
- **G8:** Uvicorn lifecycle — not a C57 core certification blocker

```
DEFERRED — NOT A C57 CORE CERTIFICATION BLOCKER
```

Additionally, 9 pre-existing test failures in `test_vea5_m8r_cli_reconcile.py` and 3 in `test_platform_api_phase7.py` (ModuleNotFoundError for `src`) are unrelated to this objective and pre-date it.

---

## End State

```
                    C57 Verification Foundation
                              │
                              ▼
                    Canonical Execution
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
             SUCCESS                      FAILURE
                │                           │
                ▼                           ▼
          status=passed                status=failed
                │                           │
                └─────────────┬─────────────┘
                              ▼
                        RunRecord
                              │
                              ▼
                          Analytics
                              │
                              ▼
                    Unambiguous Outcome
                              │
                              ▼
                   Evidence-backed Diagnosis

historical "completed"
          │
          ▼
authoritative interpretation
          │
          ▼
     unresolved — excluded from
     outcome denominator (legacy_completed)
```
