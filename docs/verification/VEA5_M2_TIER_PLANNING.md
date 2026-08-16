# VEA-5 M2 — Tier Planning Implementation

**Milestone:** VEA-5 M2 — Planner Tier Eligibility + Explained Exclusions
**Status:** CERTIFIED (evidence-producing implementation milestone)
**Date:** 2026-08-12
**Branch:** recovery/program-r-forensic-reconstruction
**Prerequisite:** `VEA5_EXECUTION_MODEL.md` (M1, CERTIFIED); `VEA5_CI_FAILURE_FORENSICS.md` (M0, CERTIFIED)
**Constraint honored:** No `.github/workflows/` file, no production application code, and no test was modified. W4/W6/cache fixes were deliberately kept out of M2.

---

## 1. Objective

Implement and prove the three-tier planning model defined in M1, directly
attacking the architectural defect proven in M0: the change-scoped planner
computes blast radius against `origin/main` via merge-base, so this long-lived
branch's **967-file divergence** becomes "the change", selects a maximal blast
radius, and runs heavy units that fail.

Establish the critical invariant:

> A verification unit is never silently absent from a plan. It is either
> **selected**, or **excluded with a machine-readable reason**.

Tier semantics required by M2:

```
Tier 1 local  ≠ git merge-base HEAD origin/main
Tier 2 pr     = actual PR base/diff
Tier 3 deep   = explicit full-system execution
```

---

## 2. Implementation

New module `runtime/foundation/verification/tier.py` (no existing planner code
reimplemented; the existing intelligence planner is reused).

### 2.1 `VerificationTier` (LOCAL / PR / DEEP)

The tier, not just the changed files, decides base resolution.

### 2.2 Tier-aware base resolution

`resolve_base_ref_for_tier(tier, *, explicit_base=None, pr_base=None)`:

* **LOCAL** → `None`. Never consults `origin/main` / merge-base. This is the
  exact decoupling that closes the M0 967-file trap.
* **PR** → `explicit_base` or `pr_base` (`GITHUB_BASE_REF`).
* **DEEP** → `None` (not change-scoped).

`collect_working_tree_changes(repo_root)` (Tier 1) computes the change set as
**staged + unstaged + untracked vs `HEAD`** only, using
`orchestrator._filter_changed_files`. It never runs `git merge-base` and never
diffs `origin/main`. Proven by `test_local_never_invokes_merge_base_with_origin_main`.

### 2.3 Canonical unit catalog (completeness source of truth)

`UNIT_CATALOG` enumerates the 10 well-known verification units (ids/categories/
cost mirror `optimizer.py`): `unit-targeted`, `backend-unit`, `backend-integration`,
`contracts-schemathesis`, `frontend-unit`, `frontend-typecheck-build`, `playwright-e2e`,
`runtime-self-test`, `mutation-run`, `golden-regression`. The invariant checker
`TierPlan.is_complete()` asserts every catalog id is present as selected or excluded.

### 2.4 `plan_for_tier`

* **LOCAL / PR** → `analyze_changes` → `compute_blast_radius` →
  `optimize_verification` (the existing intelligence planner, which already emits
  `selected` + `SkippedSuite` with `reason` + `justification`). The result is
  **reconciled against `UNIT_CATALOG`** so every catalog unit appears in
  `selected` or `excluded`. Unit identity (`unit_id`) and provenance
  (`capabilities` / `impact_kinds` / `source`) are carried onto selected units.
* **DEEP** → builds the full unit set directly from `UNIT_CATALOG`, every unit
  `selected` with reason "deep tier: full-system verification (not change-scoped)".
  `changed_files` is empty; nothing is filtered by change scope.

### 2.5 Tier-2 selective mutation eligibility (M1 §8 policy)

A critical logic change in a backend engine (`backend/src/engines/...`) makes
`mutation-run` **SELECTED (targeted)** for PR only. LOCAL keeps the existing cost
gate (`mutation-run`/`golden-regression` excluded). This is the concrete,
deterministic proof that Tier 2 ≠ Tier 1.

### 2.6 `TierPlan` manifest

Machine-readable, inspectable artifact (`to_dict()`): `tier`, `base_ref`,
`head_ref`, `changed_files`, `selected[]`, `excluded[]`, `estimated_seconds`,
`planner_version`, `framework_version`, `unit_coverage.complete`. `fingerprint()`
excludes the timestamp for determinism comparison. `write()` persists to
`runtime/generated/vea5-tier-plan.json`.

### 2.7 CLI

`python runtime/verify.py plan --tier {local|pr|deep} [--base X] [--changed f…]`
emits and writes the manifest without executing any verification unit. This is
the inspectable evidence hook for CI/developers; it does not modify any workflow.

---

## 3. Acceptance Evidence

17 new tests in `runtime/tests/test_vea5_tier_plan.py` — **all passing**.

### Tier 1 (local)
- `test_local_resolves_no_base_and_ignores_branch_divergence` — LOCAL base is `None`; ignores explicit/PR base.
- `test_local_never_invokes_merge_base_with_origin_main` — monkeypatched `subprocess.run` asserts no `merge-base` / `origin/main` call for LOCAL.
- `test_local_working_tree_change_produces_nonzero_accurate_set` — engine change → 6 selected, complete plan.
- `test_local_clean_working_tree_has_defined_behavior` — clean tree: all units excluded with reasons, 0 selected.
- `test_local_heavy_units_not_selected_merely_because_branch_is_long_lived` — `mutation-run`/`golden-regression` excluded (cost gate), with reason.

### The critical regression test
- `test_repository_a_equals_repository_b_for_tier1` — Repository A (10 relevant files) vs Repository B (same HEAD, `origin/main` diverged 967 unrelated files via `explicit_base="origin/main"`). `plan_a.fingerprint() == plan_b.fingerprint()`; `plan_b.base_ref is None`. **The fundamental VEA-5 problem is closed for Tier 1.**

### Tier 2 (pr)
- `test_pr_base_is_explicitly_resolved` — `explicit_base`/`pr_base` honored.
- `test_pr_plan_uses_pr_base_and_reproduces_deterministically` — `base_ref == "main"`; identical plan on repeat.
- `test_pr_selects_engine_change_units_and_mutation_selectively` — backend-unit + targeted `mutation-run` selected; `golden-regression` excluded with reason+justification.
- `test_pr_plan_differs_from_local_for_engine_change` — `local.fingerprint() != pr.fingerprint()`; mutation-run in PR, not LOCAL.

### Tier 3 (deep)
- `test_deep_is_genuinely_full_system` — all 10 catalog units selected; mutation/golden/E2E/runtime included; 0 excluded.
- `test_deep_ignores_changed_files` — `changed_files == ()`; full set regardless of diff.

### Identity / determinism / evidence
- `test_every_selected_and_excluded_unit_retains_id_and_provenance` — `unit_id` + `source` + `reason`/`justification` present.
- `test_no_duplicate_unit_identities` — no duplicate ids; no positional `step-*` ids for all three tiers.
- `test_determinism_identical_state_identical_plan` — identical state → identical fingerprint.
- `test_manifest_records_required_fields_and_is_inspectable` — all required manifest fields present; `unit_coverage.complete == True`; round-trips write/read.
- `test_existing_optimizer_units_all_have_catalog_counterparts` — every unit the intelligence planner can emit is covered by `UNIT_CATALOG`.

### Regression
Existing planner/attribution/diagnostics suites: **139 passed** (no weakening,
no deletion). Files changed: only `runtime/verify.py` (CLI `plan` subcommand),
plus new `tier.py` and new test. No `.py` under `backend/`/`frontend/`, no
workflow, no production code modified.

---

## 4. What M2 deliberately did NOT do

Per the M2 scope contract, the following were **not** implemented (they belong to
their own milestones and would otherwise couple "is the planner correct?" to
"does an execution unit happen to fail?"):

* **W4** — 30s `pytest-timeout` wrapper around the backend-script subprocess.
* **W6** — `run_mutation_selective.sh` `python` → `python3`.
* **Cache exit-code integrity** (M1 §13 / M0 W3) — contract defined in M1; fix deferred to M3.
* Workflow topology changes, branch protection, CodeQL PR wiring.

---

## 5. M2 Verdict

CERTIFIED. The three-tier planning model is implemented and proven:
`plan(A) == plan(B)` for Tier 1 closes the 967-file divergence defect; every
unit is selected or excluded with a reason; the manifest is inspectable; existing
tests remain green. W4/W6/cache are correctly deferred.

*End of VEA-5 M2 Tier Planning Implementation.*
