# VEA-5 M1 — Execution Model Specification

**Milestone:** VEA-5 M1 — Execution Model Definition
**Status:** COMPLETE (specification only; no code, workflow, or production changes)
**Date:** 2026-08-12
**Branch:** recovery/program-r-forensic-reconstruction
**Prerequisite:** `docs/verification/VEA5_BASELINE.md`, `docs/verification/VEA5_CI_FAILURE_FORENSICS.md` (M0, CERTIFIED)
**Constraint honored:** No `.github/workflows/` file, no production application code, and no test was modified in M1. M1 defines semantics only.

---

## 1. Purpose

Define the **execution model** that lets the existing ClariFin_OS verification
framework operate correctly across three tiers:

1. **Tier 1 — Local Developer Loop**
2. **Tier 2 — Pull Request Gate**
3. **Tier 3 — Deep / Scheduled / Release Verification**

M1 is a **specification milestone**. It fixes the *semantics* the planner,
evidence system, cache, and CI topology will later implement. It does not
redesign the planner, CI topology, workflows, mutation system, or application.

The central problem it solves is structural (established in M0): a long-lived
branch that diverges from `origin/main` by **967 files** causes the
change-scoped planner to treat the entire divergence as the change, select a
maximal blast radius, run heavy units that fail for concrete reasons, and turn
CI red while the raw full-suite scripts are green.

> **Branch divergence ≠ developer change must never become
> branch divergence = blast radius.**

---

## 2. Current VEA-5 M0 problem statement

M0 measured three distinct behaviors, not two (see
`VEA5_CI_FAILURE_FORENSICS.md` §1):

| # | Behavior | Changed files | Result |
|---|----------|---------------|--------|
| A | Raw full-suite scripts (`run_*_verification.sh`) | n/a (full) | GREEN (backend 468, frontend known lint RED-but-pre-existing) |
| B | `verify.py <profile>` **in CI** (push → merge-base → 967) | 967 | FAILS on runtime / mutation / frontend-lint units |
| C | `verify.py <profile>` **locally** (no `GITHUB_*` → `base_ref=None` → `git diff HEAD`) | 0 | refuses to run (exit 1) |
| C' | `verify.py <profile>` locally **with `VERIFICATION_BASE_REF`** | 967 | reproduces CI failures (B) |

The **architectural finding** (M0 §5): the change-scoped planner computes blast
radius against `origin/main` via merge-base. Because this branch has 967
unmerged files, every push looks "all changed", so the planner selects the
maximal unit set and runs expensive units (`mutation`, `runtime` self-test) that
fail. Tier 1 should scope to the *actual* change, Tier 2 should explain every
exclusion, and Tier 3 should own mutation/golden/E2E explicitly.

Concrete M0 evidence reused throughout this document:

* **967-file branch divergence** → maximal blast radius → heavy-unit over-selection.
* **Runtime timeout** → `test_backend_exit_contract_holds_both_directions` exceeds the 30s `pytest-timeout` wrapper (W4).
* **Mutation `python`/`python3`** → `run_mutation_selective.sh` hardcodes `python`; `ubuntu-latest` only ships `python3` (W6).
* **Cache exit-code anomaly** → `verify.py quick` printed `Verification FAILED / Failed: 3` yet exited `0` on a cache hit (W3).
* **Stale `main` workflows** → W5/W6/W8 fail on `main` designs not present on this branch.
* **Playwright missing build** → `main`'s playwright path omits `next build` (W8 / VEA4-3).
* **Pre-existing frontend lint (34 errors)** → `PRE_EXISTING`, unrelated to any backend push (W2 / VEA-2 Phase 1.5 BL-001).

---

## 3. Three-tier execution model

The framework already possesses two complementary planning pipelines. M1 does
not replace them; it assigns them tier semantics.

* **Registry planner** — `runtime/foundation/verification/planner/planner.py`
  (`VerificationPlanner`) produces a `VerificationPlan` of `VerificationStep`s.
  Each step carries `unit_id` (stable identity spine) and `provenance`
  (`capabilities`, `impact_kinds`, `source`).
* **Intelligence optimizer** — `runtime/foundation/intelligence/platform/optimizer.py`
  (`optimize_verification`) produces `VerificationPlanIntel` with `selected`
  (`VerificationUnit[]`) and `skipped` (`SkippedSuite[]`). **`SkippedSuite` already
  implements "exclusion with reason"** (fields: `id`, `category`, `reason`,
  `justification`), and `mutation-run` / `golden-regression` are already
  classified as `explicit request (cost >= 600s)` — i.e. deep-tier candidates by
  default. This is the existing architectural basis M1 extends, not invents.

### Tier 1 — Local Developer Loop

* **Purpose:** fast feedback on the developer's *actual local change*.
* **Trigger:** git commit / pre-commit integration where appropriate, or an
  explicit CLI invocation.
* **Scope source:** the **working tree change** — staged + unstaged edits, OR the
  developer's current commit range against the branch's own recent history — **NOT**
  `git merge-base HEAD origin/main`. This is the single most important M1 rule.
  The M0 "behavior C" (0 changed files → refuse) and "behavior C'" (967 files →
  maximal plan) are both wrong for Tier 1; the correct input is the developer's
  own delta.
* **Default objective:** seconds to a few minutes, not tens of minutes.
* **Must NOT automatically execute** (unless the planner proves the change
  genuinely requires it, or the developer explicitly requests a deep run): full
  mutation, massive golden datasets, complete E2E matrix, expensive stress
  testing, entire-project deep regression.

Local flow (reusing existing stages):

```
working change
    ↓ change understanding (analyze_changes)
    ↓ unit identity (VerificationUnit)
    ↓ capability mapping (registry / architecture provider)
    ↓ dependency / impact graph (compute_blast_radius)
    ↓ local blast radius (working-tree-scoped)
    ↓ targeted verification plan (optimize_verification → selected)
    ↓ fast execution (Executor)
    ↓ machine evidence
    ↓ normalized result
    ↓ developer verdict
```

### Tier 2 — Pull Request Gate

* **Purpose:** prevent unverified changes from merging while remaining practical.
* **Trigger:** PR opened / synchronized / pushed / relevant PR events.
* **Scope source:** the **actual PR diff against the PR base** (the branch the PR
  targets), computed with PR semantics, **not** the branch's historical divergence
  from `origin/main`.
* **Must NOT inherit the local plan blindly.** It independently re-establishes:
  what changed, what is affected, what is required, what is intentionally
  excluded, why each exclusion is safe, and which deep checks remain deferred.

```
PR diff
   ↓ change understanding
   ↓ unit identity
   ↓ capability / impact graph
   ↓ blast radius (PR-scoped)
   ↓ tier eligibility
   ↓ verification plan (selected + skipped[SkippedSuite])
   ↓ execution
   ↓ machine evidence
   ↓ failure normalization
   ↓ failure clustering
   ↓ change attribution (attribution.py)
   ↓ pre-existence determination
   ↓ diagnostic verdict
   ↓ merge recommendation
```

### Tier 3 — Deep Verification

* **Purpose:** periodically prove that the entire verification architecture and
  application remain healthy **beyond the scope of any individual PR**.
* **Trigger:** nightly schedule, manual `workflow_dispatch`, pre-release, release
  candidate, major architectural change.
* **Explicitly full-system, not accidentally over-selected.** Deep verification is
  intentionally **not change-scoped**; it validates the system as a whole.
* **May execute:** full backend, full frontend, complete runtime, golden datasets,
  mutation testing, large property datasets, Playwright/E2E, performance
  regression, build verification, dependency/security verification, CodeQL/SAST,
  cross-layer contract verification, full evidence-integrity verification.

---

## 4. Trigger model

| Tier | Trigger | Base / scope source | Default unit set |
|------|---------|--------------------|-----------------|
| 1 | git commit / pre-commit / explicit CLI | working tree delta (NOT merge-base vs origin/main) | fast checks, direct unit tests, immediate dependents, in-blast-radius contracts |
| 2 | PR open / sync / push / PR event | PR diff vs PR base | gated selection with every exclusion justified |
| 3 | nightly / dispatch / pre-release / RC / arch-change | none (whole system) | everything |

The trigger determines the **scope source**, which is what prevents the
967-file divergence from becoming the blast radius. Tier 1 and Tier 2 are
*change-scoped but with different bases*; Tier 3 is unbounded by design.

---

## 5. Scope model

Three explicit scopes, each with a distinct "what changed" definition:

* **Working-tree scope** — Tier 1. The developer's actual local edit: staged +
  unstaged working-tree changes, or the developer's last commit(s) relative to a
  recent local ancestor. Must never be expanded to "everything that differs from
  `origin/main`".
* **PR scope** — Tier 2. The PR diff computed against the PR's target base using
  GitHub PR semantics (`GITHUB_BASE_REF` / PR diff). Independent of how far the
  branch has diverged from `origin/main`.
* **Deep scope** — Tier 3. Not change-scoped. Validates the entire repository and
  stack.

The `verify.py` planner's `_resolve_base_ref` currently collapses local and CI
into merge-base resolution. M1 mandates that the **tier determines the base
resolution**, so the same planner can serve all three tiers without treating
branch divergence as the change.

---

## 6. Branch-vs-change distinction

The 967-file divergence is **branch topology, not the developer's change**. M1
codifies the policy that:

* `changed_files` for Tier 1 = the developer's working-tree delta.
* `changed_files` for Tier 2 = the PR diff vs the PR base.
* Neither uses `git merge-base HEAD origin/main` as the change definition.
* Tier 3 ignores `changed_files` entirely.

M1 explicitly forbids altering branch history, merging/rebasing the branch,
deleting commits, or modifying workflows merely to make the current branch green.
The purpose is to define correct semantics first (per M0 §5 and the §22
constraint).

---

## 7. Planner responsibilities

The planner is the **intelligence layer** that decides scope. CI is the
execution environment, not the place where verification policy is duplicated.
Responsibilities:

1. Resolve the **tier** from the trigger.
2. Resolve the **base / scope source** from the tier (§5).
3. Compute **change understanding** (paths → capabilities → impact graph → blast radius).
4. Determine **unit identity** for every selected unit (`unit_id` + `provenance`).
5. Apply **tier eligibility** (§8) to decide which unit classes may run.
6. Emit a **plan** with `selected` units (each with `reason` + `evidence`) **and**
   `skipped` units (`SkippedSuite` with `reason` + `justification`).
7. Represent **execution cost** (`estimated_seconds`) and **environment
   requirements** for every selected unit.
8. Preserve **plan identity** and **execution identity** for reconciliation (§11).
9. Hand the plan to the executor; never execute inside the planner.

The existing `VerificationPlanner.plan()` and `optimize_verification()` already
implement most of this. M1 extends them with explicit tier eligibility and a
mandatory exclusion-reasons contract; it does not replace them.

---

## 8. Tier eligibility policy

Every verification **unit class** has a default tier eligibility. The M1 policy
matrix reuses the existing unit-cost metadata (`VerificationUnit.estimated_seconds`,
and the already-skipped `mutation-run` / `golden-regression` "cost >= 600s"
classification) rather than inventing new risk scores.

| Unit Property              | Local (T1) | PR (T2) | Deep (T3) |
| -------------------------- | :--------: | :-----: | :-------: |
| Fast checks                | YES        | YES     | YES       |
| Direct unit tests          | YES        | YES     | YES       |
| Immediate dependents       | YES        | YES     | YES       |
| Cross-layer contract tests | CONDITIONAL| YES     | YES       |
| Runtime self-test          | CONDITIONAL| CONDITIONAL / YES | YES |
| Mutation                   | NO / CONDITIONAL | SELECTIVE / CONDITIONAL | YES |
| Golden datasets            | NO         | CONDITIONAL | YES   |
| Full E2E                   | NO         | SELECTIVE / CONDITIONAL | YES |
| Performance regression     | NO         | CONDITIONAL | YES    |
| Large datasets             | NO         | NO / CONDITIONAL | YES |
| Full project regression    | NO         | NO      | YES       |

"CONDITIONAL" means eligibility is decided by the planner from the change (e.g.
runtime self-test runs in T1/T2 only when a `runtime/` path changed — already the
rule in `optimizer.py`). "SELECTIVE" means a *targeted* subset keyed to the
changed capability, not the full campaign.

**Selective mutation policy (future PR execution), keyed to existing metadata:**

```
small low-risk change          → no mutation
critical logic change         → targeted mutation
high-risk financial calc       → targeted mutation
architecture / runtime change → targeted mutation
nightly / deep                → complete mutation campaign
```

**Dataset-class policy:**

```
small representative dataset → local / PR
medium regression dataset    → PR where relevant
large / full dataset         → deep / nightly / release
```

These reuse the `estimated_seconds` cost signal already present on
`VerificationUnit`; no arbitrary risk scoring is introduced without repository
evidence.

---

## 9. Verification plan contract

Every plan emitted by the planner must contain, at minimum:

```
execution_id
tier
trigger
base_ref
head_ref
changed_files
changed_units
affected_capabilities
affected_dependencies
blast_radius
selected_units
excluded_units
exclusion_reasons
execution_cost
environment_requirements
verification_profile
planner_version
framework_version
```

If the plan already carries some of these (e.g. `VerificationPlanIntel` has
`selected`, `skipped`, `generated_at`; `VerificationPlan` has `metadata` with
`changed_files`, `impacted_capabilities`, `impacted_modules`, `estimated_duration_seconds`),
**extend rather than duplicate**. The `excluded_units` / `exclusion_reasons`
fields are satisfied by the existing `SkippedSuite` structure (`id`, `category`,
`reason`, `justification`) and the M0 taxonomy vocabulary in §13.

The manifest must be sufficient to answer: *Why did this verification run these
units and not the others?*

---

## 10. Manifest contract

The manifest is the persistent record of one verification run. It must preserve:

* **Plan identity** (`execution_id`, `planner_version`, `framework_version`, `tier`, `trigger`).
* **Scope identity** (`base_ref`, `head_ref`, `changed_files`).
* **Selection identity** (`selected_units` with `unit_id`, `provenance`,
  `reason`, `estimated_seconds`).
* **Exclusion identity** (`excluded_units` with `SkippedSuite.reason` +
  `justification`).
* **Execution identity** (per-unit `ExecutionResult`: `exit_code`,
  `duration_seconds`, `stdout_path`, `stderr_path`, `unit_id`, `provenance`).
* **Evidence identity** (per-unit `VerificationEvidence`: `status`, `metadata`).

This is an extension of the existing evidence models in
`runtime/foundation/verification/models/model.py` (`VerificationPlan`,
`VerificationStep`, `ExecutionResult`, `VerificationEvidence`) plus the existing
intelligence provenance shape (`provenance: {capabilities, impact_kinds, source}`).
No new identity abstraction is required; the `unit_id` spine already joins
planning → execution → evidence (see `model.py` identity note on
`VerificationStep` and `ExecutionResult`).

---

## 11. Evidence contract

Evidence must preserve, per unit and per run:

```
unit identity (unit_id)
execution identity (execution_id / run id)
commit identity (head_ref / commit sha)
plan identity (execution_id / planner_version)
environment identity (OS, python, node, GITHUB_* or "local", mutmut present?)
command
start / end time
exit code
stdout / stderr references
test counts (passed / failed / skipped)
failure records
status
classification
attribution
```

### Status vocabulary

The framework already defines `VerificationStatus`
(`runtime/foundation/verification/models/model.py`):

```
PENDING, PLANNED, IN_PROGRESS, PASSED, FAILED, SKIPPED, BLOCKED, UNKNOWN
```

M1 **reuses** this enum and layers the M0-required distinctions on top rather
than inventing conflicting terms:

| M1-required status | Mapping to existing model |
|--------------------|---------------------------|
| `NOT_EXECUTED` | `PLANNED` / `PENDING` (planned but not run this tier) |
| `PASSED` | `PASSED` (unchanged) |
| `FAILED` | `FAILED` (unchanged) |
| `BLOCKED` | `BLOCKED` (unchanged) |
| `SKIPPED` | `SKIPPED` (unchanged; tier-ineligible) |
| `PRE_EXISTING` | attribution-derived classification over `FAILED` (reuses `attribution.PRE_EXISTING`) |
| `ENVIRONMENT_FAILURE` | classification over `FAILED` (e.g. `dependency/environment`, `workflow command divergence`) |
| `INFRASTRUCTURE_FAILURE` | classification over `FAILED` (e.g. transient checkout / runner state) |

`NOT_EXECUTED`, `PRE_EXISTING`, `ENVIRONMENT_FAILURE`, `INFRASTRUCTURE_FAILURE`
are **classifications of a unit's outcome**, surfaced via the existing
attribution taxonomy, not a replacement of `VerificationStatus`. The system MUST
distinguish these; it must not collapse everything into a generic "test failed".

---

## 12. Exit-code contract

M1 explicitly specifies:

```
PASS  → process exit 0
FAIL  → process exit != 0
BLOCKED → process exit != 0 unless explicitly classified as non-gating
```

Most importantly:

> **Cache MUST NOT mask failures.**
> If cached evidence represents `FAILED`, replaying it MUST still produce a
> failing verification verdict and an appropriate non-zero exit code.

The forbidden state (observed in M0 W3):

```
output: Verification FAILED
exit code: 0
```

This directly addresses the VEA-5 M0 cache anomaly. The cache may short-circuit
*execution*, but it must never short-circuit the *verdict*: a cached `FAILED`
replays as `FAILED` with `exit != 0`; only a cached `PASSED` (with a matching
fingerprint across `last_commit` + `changed_files` + `executed_profiles`) may
replay as `PASSED` with `exit 0`.

---

## 13. Cache semantics

The existing cache (`runtime/verify.py` → `runtime/generated/verification-cache.json`,
`_is_cache_valid`, `_update_cache`) keys on `last_commit`, `changed_files`, and
`executed_profiles`. M1 defines its contract:

1. **Validity** requires a fingerprint match on `commit` + `changed_files` +
   `profile`. A change to any input invalidates the cache (already the rule in
   `_is_cache_valid`).
2. **Verdict integrity** (new contract): the cached record MUST store the
   `overall_status` / per-unit status. On a cache hit, the replayed exit code is
   derived from the **stored status**, never from a default of 0. A stored
   `FAILED` → `exit != 0`.
3. **No silent PASS**: if the stored status is `FAILED`/`BLOCKED`, the run is
   reported FAILED/BLOCKED and exits non-zero, even when the fingerprint matches.
4. **Local vs CI fingerprints differ** by environment identity; a CI cache hit
   and a local cache hit are not interchangeable verdicts (supports §11
   reconciliation).

This closes the W3 anomaly without modifying the cache implementation in M1 — M1
defines the contract; the fix is a later milestone.

---

## 14. Local / CI reconciliation

The system must distinguish:

### Case A — same plan, different result
```
LOCAL PLAN == CI PLAN
LOCAL RESULT == PASS
CI RESULT == FAIL
```
Interpretation: **environment / toolchain / runtime difference**
(e.g. local Python 3.12.3 vs CI 3.12.13; `mutmut` present locally but absent in
CI; `python` vs `python3`).

### Case B — different plan
```
LOCAL PLAN != CI PLAN
```
Interpretation: **planning / scope divergence** (the 967-file vs working-tree
delta split documented in M0 §1). The tier/scope source differs, so the selected
unit set legitimately differs.

### Case C — same plan, same environment, different result
```
SAME PLAN
SAME ENVIRONMENT
DIFFERENT RESULT
```
Interpretation: **non-determinism / flaky execution / external state**.

The reconciliation layer must record `plan_id` + `environment_identity` for every
run so these three cases are mechanically distinguishable. The existing
`plan_verification()` determinism audit (planner audit) and the `unit_id` spine
make this possible without new abstractions. The framework must not report all
local-vs-CI differences simply as "CI failure".

---

## 15. Failure classification

Use the existing VEA taxonomy where available. The M0 forensic vocabulary
(`VEA5_CI_FAILURE_FORENSICS.md` §4) is the established classification set and MUST
be reused:

| Classification | Example (M0) |
|----------------|-------------|
| genuine application failure | none observed in branch-triggered runs — backend app suite GREEN |
| verification-runtime failure | runtime self-test timeout (W4) |
| planner divergence | over-selection from 967-file divergence (W1–W3) |
| dependency/environment failure | mutation `python` not found on `ubuntu-latest` (W6) |
| workflow command divergence | stale `main` golden/mutation/playwright designs (W5/W6/W8) |
| frontend toolchain failure | pre-existing 34 lint errors (W2, BL-001) |
| timing/concurrency failure | 30s `pytest-timeout` wrapper too tight (W4) |
| pre-existing failure | frontend lint (PRE_EXISTING) |
| infrastructure failure | transient checkout / runner-workspace state (W7) |
| generated-artifact failure | cross-run artifact dependency in stale `main` golden (W5) |

Do **not** collapse these into a generic "test failed". The attribution layer
(`attribution.py`) already separates `IN_BLAST_RADIUS`, `OUTSIDE_BLAST_RADIUS`,
`PRE_EXISTING`, `ATTRIBUTION_UNKNOWN`, `UNMAPPED_UNIT`; failure classification is
the coarser layer that explains *what kind* of failure occurred, attribution
explains *whether the change caused it*.

---

## 16. Attribution integration

Preserve the VEA identity spine (`attribution.py`):

```
failure
   ↓ ObservedFailure(unit_id, phase, path, diagnostic, pre_existing)
   ↓ unit_id → plan (VerificationUnit / VerificationStep)
   ↓ capability / impact graph (BlastRadius)
   ↓ graph traversal
   ↓ causal dependency chain
   ↓ attribution ∈ {IN_BLAST_RADIUS, OUTSIDE_BLAST_RADIUS, PRE_EXISTING, ATTRIBUTION_UNKNOWN, UNMAPPED_UNIT}
   ↓ verdict (change_is_implicated)
```

The execution model integrates with this existing architecture rather than
replacing it. For every failure, the final diagnostic must answer:

* What failed?
* Which verification unit failed? (`unit_id`)
* Why was that unit selected? (`reason` + `provenance`)
* Which changed capability caused selection? (`provenance.capabilities`)
* Is the failure attributable to this change? (`IN_BLAST_RADIUS` vs `OUTSIDE_BLAST_RADIUS`)
* Was it pre-existing? (`PRE_EXISTING` — strictly stronger than `OUTSIDE_BLAST_RADIUS`)
* Is it an environment/infrastructure failure? (§15 classification)
* What should happen next? (repair plan / merge recommendation)

The existing `test_failure_attribution.py` already guards these invariants; M1
extends the *contract* so Tier 2 plans emit attribution-ready evidence
(`phase`, `path`, `unit_id`) for every failure.

---

## 17. Coverage strategy

Coverage is **one signal**, not the sole correctness metric. M1 defines its
architectural role without implementing the full coverage system.

### Code coverage
* line, branch, function (where useful).

### Behavioral coverage
* capability coverage (which capabilities have verification evidence)
* workflow coverage (which registry workflows executed)
* contract coverage (cross-layer contract tests)

### Verification coverage
```
changed capability
    ↓
verification units covering capability
```

The eventual objective is not "90% lines covered" but "important capabilities have
meaningful verification evidence". The `affected_capabilities` field in the plan
manifest (§9) is the hook the coverage layer will consume; no coverage engine is
built in M1.

---

## 18. Automatic test-generation strategy

M1 does **NOT** implement automatic test generation. It defines where it belongs:

```
change
 ↓ capability
 ↓ risk
 ↓ coverage gap
 ↓ test-generation recommendation
 ↓ generated candidate tests
 ↓ human / machine validation
 ↓ test admission
```

Generated tests require **provenance and validation**; they must never silently
modify production tests and declare success. Recorded as a future VEA phase
(beyond M1). The `UNIT_TO_WORKFLOW` enumerated mapping discipline (never guess,
`UNMAPPED` over guessed) is the same discipline the generation layer must follow
for provenance.

---

## 19. Mutation strategy

Mutation belongs **primarily to Tier 3** (deep). The framework already encodes
this: in `optimizer.py`, `mutation-run` is skipped by default with reason
`explicit request (cost >= 600s)`.

Selective mutation eligibility for future PR execution (reusing existing
unit-cost metadata, not arbitrary risk scoring):

```
small low-risk change          → no mutation
critical logic change         → targeted mutation
high-risk financial calc       → targeted mutation
architecture / runtime change → targeted mutation
nightly / deep                → complete mutation campaign
```

The genuine mutation *defect* (W6: `python` → `python3`) is a tooling fix for a
later milestone; M1 only places mutation in the correct tier.

---

## 20. Dataset strategy

Large datasets are a **deep-tier** concern. The planner should know the dataset
class and execution cost (`estimated_seconds`):

```
small representative dataset → local / PR
medium regression dataset    → PR where relevant
large / full dataset         → deep / nightly / release
```

`golden-regression` is already skipped by default in `optimizer.py` with reason
`explicit request (cost >= 600s)`, consistent with this placement.

---

## 21. UI / E2E strategy

The future verification architecture must include UI behavior, not only backend
correctness. Defined eventual layers:

```
Type safety
   ↓ component tests
   ↓ interaction tests
   ↓ route / page verification
   ↓ API contract verification
   ↓ Playwright E2E
   ↓ visual regression (where justified)
   ↓ performance metrics
```

Tier placement:

* Type safety / component / interaction / route — Tier 1 (fast) and Tier 2 (gated).
* Playwright E2E — Tier 2 (selective, when workspace/UI entities in blast radius)
  and Tier 3 (full).
* Visual regression / performance — Tier 3 (deep), not implemented in M1.

The `playwright-e2e` unit is already conditionally selected only when a `workspace`
entity is in the blast radius (`optimizer.py`), so the UI/E2E tier placement
already exists; M1 makes the policy explicit.

---

## 22. Performance strategy

Performance verification is a **first-class evidence category**, distinct from
functional correctness. Eventually measured:

* verification runtime (per-unit `estimated_seconds` vs actual)
* application build time
* page load / route performance
* API latency where meaningful
* E2E execution time
* dataset processing time
* mutation execution cost

The framework must eventually distinguish `functional correctness` from
`performance regression`. The `VerificationCategory.PERFORMANCE` enum already
exists (`model.py`); M1 records that performance is a future evidence category and
that no arbitrary thresholds are introduced in M1 without repository evidence.

---

## 23. CodeQL placement

Audited directly against the repository's GitHub configuration:

```
gh api repos/.../code-scanning/default-setup
→ {
    "state": "configured",
    "languages": ["actions","javascript","javascript-typescript","python","typescript"],
    "query_suite": "default",
    "threat_model": "remote",
    "schedule": "weekly",
    "runner_type": "standard"
  }
```

Findings:

* **Active:** yes — GitHub CodeQL **default setup** is enabled.
* **Languages analyzed:** Python, JavaScript/TypeScript (incl. `javascript-typescript`), and `actions` (workflows).
* **Trigger:** weekly schedule (default setup) — runs on `main`/default branch cadence, not wired into the per-PR `verify.py <profile>` gate.
* **Visibility to verification architecture:** CodeQL results live in GitHub code-scanning alerts, **not** in the `runtime/verify.py` evidence model. There is no existing bridge that folds CodeQL findings into the VEA evidence/attribution spine.
* **Conflict / duplication:** none observed. The repo has no custom `codeql.yml` workflow; default setup is independent of the `run_*_verification.sh` scripts. No overlap with existing SAST/security checks was found.
* **Tier placement:** security scanning is a **Tier 2 (PR) + Tier 3 (deep)** concern. Default setup's weekly schedule already approximates Tier 3; it should additionally be considered for PR eligibility on `backend/**`, `frontend/**`, `runtime/**` paths in a later milestone. It does **not** belong in Tier 1 (local loop).

Per the §20 constraint: **do NOT disable, replace, or change CodeQL configuration.** The current configuration is adequate.

```
AUDITED — NO CHANGE REQUIRED
```

---

## 24. CI integration philosophy

```
                  ┌────────────────────┐
                  │      CHANGE        │
                  └─────────┬──────────┘
                            │
                     CHANGE UNDERSTANDING
                            │
                 CAPABILITY / IMPACT GRAPH
                            │
                      BLAST RADIUS
                            │
              ┌─────────────┼─────────────┐
              │             │             │
           LOCAL            PR           DEEP
           Tier 1         Tier 2         Tier 3
              │             │             │
           TARGETED       GATED          FULL
              │             │             │
              └─────────────┼─────────────┘
                            │
                     MACHINE EVIDENCE
                            │
                 FAILURE NORMALIZATION
                            │
                    FAILURE CLUSTERS
                            │
                    CHANGE ATTRIBUTION
                            │
                     PRE-EXISTENCE
                            │
                     DIAGNOSTIC VERDICT
                            │
                   ACTION RECOMMENDATION
```

The **planner is the intelligence layer** deciding scope. **CI is the execution
environment**, not the place where verification policy is duplicated. Every
`.github/workflows/*.yml` should invoke `python runtime/verify.py <profile>`
with the correct tier/scope inputs and then report machine evidence + attribution;
it should not re-implement scope policy in YAML.

---

## 25. Deferred implementation phases

M1 defines semantics only. Deferred (with prerequisites, from M0 §8):

* **M2** — Extend the planner for `unit_id` / `capability` / `impact_kinds` /
  `dependencies` / scope policy / `execution cost` / `environment` / tier
  eligibility; emit explained exclusions (directly addresses W1–W3 over-selection).
* **M3 / M5** — Fix two genuine CI-tooling defects before PR gating:
  * W4: raise/remove the 30s `pytest-timeout` wrapper around the backend-script subprocess.
  * W6: change `run_mutation_selective.sh` `python` → `python3`.
* **M3 (cache)** — Enforce the §12/§13 cache exit-code integrity contract (W3).
* **M4 / M6** — Build local/CI plan equivalence + reconciliation (§14 Case A/B/C).
* **M7 / M8** — Re-audit workflow topology; resolve VEA4-1 with planner evidence;
  record branch-protection status (VEA4-2). **Do not** consolidate/delete workflows
  without evidence.
* **M9** — CodeQL PR-eligibility wiring (§23) — configuration itself unchanged.
* **M10** — Define the deep profile contract (golden / mutation / E2E home).
* Future VEA — automatic test generation (§18), full coverage engine (§17),
  performance evidence (§22), visual regression (§21).

---

## 26. Acceptance criteria

### Architecture
- [x] Tier 1 / Tier 2 / Tier 3 are explicitly defined (§3).
- [x] Trigger semantics are explicit (§4).
- [x] Scope semantics are explicit (§5).
- [x] Branch divergence cannot automatically equal developer change (§6).
- [x] Deep verification is explicitly full-system rather than accidental over-selection (§3 T3).

### Planner
- [x] Planner responsibilities are defined (§7).
- [x] Tier eligibility is defined (§8).
- [x] Execution cost is represented (`estimated_seconds`, §8/§9).
- [x] Environment requirements are represented (§9/§11).
- [x] Exclusion reasons are mandatory (`SkippedSuite.reason` + `justification`, §9).

### Evidence
- [x] Every selected unit has provenance (`unit_id` + `provenance`, §9/§10).
- [x] Every excluded unit has a reason (`SkippedSuite`, §9).
- [x] Plan identity is preserved (§10).
- [x] Execution identity is preserved (`ExecutionResult`, §10).
- [x] Exit-code semantics are explicit (§12).
- [x] Cache semantics cannot permit failure → exit 0 (§13).

### Diagnostics
- [x] Same-plan/different-result is distinguishable from different-plan (§14).
- [x] Pre-existing failures are distinguishable from change-attributable failures (`PRE_EXISTING` vs `IN_BLAST_RADIUS`, §15/§16).
- [x] Environment failures are distinguishable from product failures (§15 vocabulary).
- [x] Failure attribution integrates with the existing identity spine (`attribution.py`, §16).

### Future capability
- [x] Coverage has a defined architectural role (§17).
- [x] Automatic test generation has a defined future role (§18).
- [x] Mutation has a defined tier policy (§19).
- [x] Large datasets have a defined tier policy (§20).
- [x] UI/E2E has a defined tier policy (§21).
- [x] Performance has a defined evidence category (§22).
- [x] CodeQL placement has been audited (§23 — `AUDITED — NO CHANGE REQUIRED`).

### Safety
- [x] No production functionality removed.
- [x] No existing tests weakened.
- [x] No verification units deleted.
- [x] No workflow modified.
- [x] No speculative planner implementation introduced.

---

*End of VEA-5 M1 Execution Model Specification.*
