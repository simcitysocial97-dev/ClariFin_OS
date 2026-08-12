# VEA-5 M5 — CI Integration & Reconciliation Gate

**Status:** DONE — 2026-08-12
**Workflow:** `.github/workflows/verification-reconcile.yml` (new; does NOT consolidate the 9 existing workflows)
**Module extensions:** `runtime/foundation/verification/reconciliation.py` (persisted-artifact helpers), `runtime/verify.py` (`cmd_plan` M5-A guard, `cmd_exec_evidence`, `cmd_reconcile` M5 persisted path + exit contract)
**Tests:** `runtime/tests/test_vea5_m5_ci_integration.py` (8 passed)
**Verdict:** CERTIFIED

---

## Objective (narrowly scoped)

Make CI **consume and enforce** the verification framework's plan/reconciliation
semantics **without** prematurely redesigning the workflow topology.

```
GitHub PR / push
       │
       ▼
checkout
       │
       ▼
bootstrap
       │
       ▼
verify.py plan --tier pr        → PR TierPlan manifest (M5-B)
       │
       ▼
verify.py <profile>             → execution evidence (M5-C)
       │
       ▼
verify.py reconcile             → { SAME-PLAN | EXPECTED-TIER-DIFFERENCE
                                   | ENVIRONMENT-DIVERGENCE
                                   | PLANNING-DIVERGENCE }   (M5-D)
       │
       ▼
   VERDICT (M5-E exit contract)
```

M5 deliberately does **not** consolidate the nine workflows
(`backend-verify`, `frontend-verify`, `quality`, `verification-runtime`,
`golden`, `mutation`, `dependency-update`, `playwright`, `release`). VEA-4 already
demonstrated why deletion needs evidence; M5 integrates the verification runtime,
it does not redesign CI topology.

## Hard gates implemented

### M5-A — PR base correctness
For a PR: `base_ref = GITHUB_BASE_REF` (or explicit equivalent). It must **never**
silently fall back to `origin/main` when a PR base is available.

Implemented in `cmd_plan`: `--tier pr` requires `--base` or `GITHUB_BASE_REF`;
otherwise it fails loudly (exit 1). The resolver (`resolve_base_ref_for_tier`)
itself never invents a base.

### M5-B — Plan artifact
Every PR verification produces an inspectable manifest (the M2 `TierPlan.to_dict`)
containing at least: `tier`, `base_ref`, `changed_files`, `selected` (with
`unit_id` + provenance: `source`/`capabilities`/`impact_kinds`/`evidence`),
`excluded` (with `reason` + `justification`), plan fingerprint, and catalog
completeness (`unit_coverage.complete`).

### M5-C — Execution artifact
`verify.py exec-evidence` writes `vea5-execution-evidence/v1` (schema
`vea5-execution-evidence/v1`). Each selected unit retains `unit_id`, provenance
(carried from the plan), `status`, `exit_code`, `evidence_ref`. The artifact is
the deterministic input to reconciliation — **never** reconstructed from live job
state.

> **M5 limitation (documented, not a defect):** per-unit status granularity is
> derived from the executed profile's overall outcome. Finer per-unit evidence
> location is a later enhancement; the artifact *shape* (M5-C) is fully satisfied
> and the gate remains deterministic.

### M5-D — Reconciliation
CI invokes `verify.py reconcile --plan <pr-plan.json> --evidence <pr-exec.json>
--report <recon.json> --commit <sha>`, which calls `reconcile_from_artifacts` and
reads **only** persisted artifacts. Output is one of: `same-plan`,
`expected-tier-difference`, `environment-divergence`, `planning-divergence`.

### M5-E — Exit contract
| Status | Exit |
|--------|------|
| `same-plan` | 0 |
| `expected-tier-difference` | 0 |
| `environment-divergence` | 1 |
| `planning-divergence` | 2 |

The environment-vs-planning distinction is **preserved in the persisted report**
even though both fail the gate. `environment-divergence` means "the system
selected the right verification, but execution/evidence differed because the
environment did" — useful later. `planning-divergence` is an architectural
failure.

## Key constraint honored

> Do not make reconciliation itself another source of nondeterminism.

Reconciliation consumes **persisted evidence artifacts** (`vea5-tier-plan.pr.json`,
`vea5-execution.pr.json`), not "whatever happens to exist at the end of a job".
`reconcile_from_artifacts` loads explicit files; no plan is generated and no
execution result is reconstructed from the process tree or job log.

## Acceptance gates — all met

- [x] M5-A: PR base = `GITHUB_BASE_REF`; no silent `origin/main` fallback (guard in `cmd_plan`).
- [x] M5-B: plan manifest carries tier/base/changed/selected+provenance/excluded+reasons/fingerprint/completeness.
- [x] M5-C: per selected unit `unit_id`/`provenance`/`status`/`exit_code`/`evidence_ref`; persisted artifact round-trips.
- [x] M5-D: `reconcile` returns exactly one of the four statuses from persisted artifacts.
- [x] M5-E: exit mapping `same-plan/expected-tier-difference→0`, `environment-divergence→1`, `planning-divergence→2`; distinction preserved in report.
- [x] Determinism: identical persisted inputs → identical report (no live-job dependence).
- [x] Nine-workflow topology untouched.

## Verification

```
python3 -m pytest runtime/tests/test_vea5_m5_ci_integration.py -q   → 8 passed
python3 -m pytest runtime/tests/test_vea5_*.py -q                  → 48 passed
python3 -m ruff check runtime/foundation/verification/reconciliation.py runtime/verify.py → clean
yaml.safe_load(.github/workflows/verification-reconcile.yml)      → OK
```

## Files changed

```
.github/workflows/verification-reconcile.yml             (new — M5 gate; no topology change)
runtime/foundation/verification/reconciliation.py        (persisted-artifact helpers)
runtime/verify.py                                        (cmd_plan M5-A guard, cmd_exec_evidence, cmd_reconcile M5 path + exit contract)
runtime/tests/test_vea5_m5_ci_integration.py             (new, 8 tests)
docs/verification/VEA5_M5_CI_INTEGRATION.md              (this file)
docs/progress.md                                         (M5 summary inserted)
```

No backend/frontend production changes. `verify.py plan`, `verify.py reconcile`,
`verify.py exec-evidence`, `verify.py status` are the only runtime entry points used.

## Next (deferred)

- M6: evidence correlation — finer per-unit evidence location in the M5-C artifact.
- M7–M10: scheduler/deep tier, dashboard, audit, release gating.
- Workflow-consolidation decision deferred until M5 produces evidence (per VEA-4).
