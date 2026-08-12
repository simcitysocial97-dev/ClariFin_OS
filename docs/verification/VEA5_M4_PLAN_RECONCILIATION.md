# VEA-5 M4 — Plan Reconciliation

**Status:** DONE — 2026-08-12
**Module:** `runtime/foundation/verification/reconciliation.py`
**CLI:** `python runtime/verify.py reconcile ...`
**Tests:** `runtime/tests/test_vea5_plan_reconciliation.py` (14 passed)
**Verdict:** CERTIFIED

---

## Problem this milestone closes

VEA-5 M0 proved the local-green / CI-red split was caused by the change-scoped
planner treating the 967-file branch divergence as the developer's change. M2 made
the *tier* decide the base/scope, so LOCAL can never over-select. But a new risk
remained open: when a developer's LOCAL plan is compared against the CI/PR plan,
**how do we tell a legitimate tier difference from a planning defect?**

The naive invariant — "local plan must equal PR plan" — is wrong and would reject
correct, by-design behavior. The execution model (§3–§6, §14) explicitly allows
LOCAL and PR to select different unit sets (e.g. PR selects targeted mutation for a
critical engine change; LOCAL keeps it behind the cost gate).

## Invariant (corrected)

```
equivalent normalized inputs
    + equivalent tier policy
    -> deterministic equivalent plans (fingerprint-stable)
```

and **any** divergence between two plans must be *explainable* by exactly one
classified cause:

| Status | Meaning | CLI exit |
|--------|---------|----------|
| `same-plan` | identical normalized plan fingerprints | 0 |
| `expected-tier-difference` | only tier-eligible units (mutation/golden) differ; both plans individually complete + valid | 0 |
| `environment-divergence` | same plan, but recorded execution/evidence diverged | 0 |
| `planning-divergence` | an unexplained change in selected/excluded units — a real defect | 2 |

`planning-divergence` is the **only** status indicating a defect. Everything else
is a validated, explainable outcome.

## Components

### Change-set normalization (`reconciliation.py:normalize_change_set`, `change_set_fingerprint`)
- Order- and duplicate-insensitive normalization.
- Deterministic 12-char SHA-256 fingerprint.
- `change_set_diff` returns symmetric difference for forensics.

### Plan fingerprint (`PlanFingerprint`, `plan_fingerprint`)
- Compact deterministic identity: `tier`, normalized change-set fingerprint,
  `selected`, `excluded`, `estimated_seconds`, `policy_version`.
- `base_ref` is deliberately **excluded** — a change-set-equal plan must fingerprint
  identically regardless of an unrelated base ref the tier ignored. (Carries the M2
  LOCAL guarantee into reconciliation.)
- Digest is a 16-char SHA-256 over the order-stable JSON of the above.

### Execution / evidence reconciliation (`UnitExecution`, `_compare_execution`)
- Compares recorded per-unit `status` + `exit_code`.
- Never assumes a cached PASS; relies on the M3 cache integrity contract for what was
  recorded.

### Classification (`reconcile`)
Priority order:
1. Identical fingerprints → same-plan (or `environment-divergence` if execution
   diverged for the same plan).
2. Same tier + same change-set + identical unit sets, but execution differs →
   `environment-divergence`.
3. Different tier, and the *only* differing units are tier-eligible
   (mutation/golden) → `expected-tier-difference`.
4. Otherwise → `planning-divergence` (unexplained unit change — real defect).

### Evidence identity spine (`build_evidence_identity`)
```
commit -> change-set fingerprint -> tier -> plan fingerprint -> unit_id
       -> provenance -> execution -> evidence -> failure -> attribution -> verdict
```

### CLI (`verify.py reconcile`)
- Generate both plans from tiers/changed-files, or load from plan manifests
  (`--local`, `--ci`).
- Emits a machine-readable `vea5-reconciliation/v1` report.
- Exits 2 on `planning-divergence` so CI can fail on a genuine planning defect
  without failing on legitimate tier/environment differences.

## Acceptance gates — all met

- [x] Change-set normalization order/dup-insensitive; fingerprint deterministic.
- [x] Plan fingerprint ignores irrelevant `base_ref`.
- [x] Local vs PR for engine change → `EXPECTED_TIER_DIFFERENCE` (PR selects
      `mutation-run`, local keeps it excluded) — NOT planning divergence.
- [x] Same plan, diverged execution → `ENVIRONMENT_DIVERGENCE`.
- [x] Different change sets / unexplained unit drop → `PLANNING_DIVERGENCE`.
- [x] Repository A (10 relevant files) reconciles as `SAME_PLAN` against Repository B
      (same HEAD, origin/main diverged 967 files).
- [x] Evidence identity spine emission verified.

## Verification

```
python3 -m pytest runtime/tests/test_vea5_plan_reconciliation.py -q   → 14 passed
python3 -m pytest runtime/tests/ -q                                   → 502 passed, 0 failed
```

Runtime suite grew from 488 → 502 (M4 added 14 tests); zero regressions.

## Files changed

```
runtime/foundation/verification/reconciliation.py   (new)
runtime/tests/test_vea5_plan_reconciliation.py      (new, 14 tests)
runtime/verify.py                                   (cmd_reconcile + dispatch + usage list)
docs/verification/VEA5_M4_PLAN_RECONCILIATION.md    (this file)
docs/progress.md                                    (M1–M4 summaries inserted)
```

No `.github/workflows/` modified. No backend/frontend production changes.

## Next (deferred)

- M5: CI integration of `verify.py reconcile` + tier-gated workflows.
- M6–M10: evidence correlation, scheduler/deep tier, dashboard, audit, release gating.
- VEA-6 … VEA-11: subsequent phases of the verification ecosystem audit.
