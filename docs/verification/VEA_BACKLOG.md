# VEA Deferred-Item Register

**Status:** AUTHORITATIVE deferred-work register for VEA-2
**Created by:** VEA-2 Phase 2, M0
**Governing document:** `.kilo/plans/1786342506938-vea2-phase2-evidence-integrity.md` §2

---

## Purpose

Every item in this register is **known, diagnosed or observed, and deliberately not fixed**
during VEA-2 Phase 2. The register exists so that deferral is an explicit, evidenced decision
rather than an omission, and so that a later agent does not "helpfully" repair something that
Phase 2 depends on holding still.

**Global rule for all entries below:**

> ### DO NOT FIX DURING VEA-2
>
> Touching any item in this register during VEA-2 Phase 2 is a **STOP condition**
> (plan §1 STOP conditions, §2 prohibited scope). Halt and record in `docs/progress.md`
> instead of proceeding.

Rationale for the register as a whole: Phase 2's central control is that **CI execution
remains byte-identical**. Phase 2 threads identity and evidence *through* existing execution,
additively. Any repair to the items below would change either executed behaviour or the
failure population that Phase 2 measures itself against, destroying the control.

---

## Entry index

| ID | Item | Group | Owning phase |
|----|------|-------|--------------|
| [BL-001](#bl-001) | Pre-existing React-hooks / Next lint errors | D | Independent remediation |
| [BL-002](#bl-002) | Credit-card over-prediction hop | C | After diagnosis reliability |
| [BL-003](#bl-003) | E-4: keyword attribution → graph traversal | B | Phase 3 |
| [BL-004](#bl-004) | CI workflow topology audit and consolidation | E | Post-Phase-2 |
| [BL-005](#bl-005) | GAP-003: `verification.yaml` capability-module path sync | — | Later |
| [BL-006](#bl-006) | Schemathesis expansion, Pynguin, automated test generation | — | Later |
| [BL-007](#bl-007) | Mutation campaigns, golden redesign, regression redesign | — | Later |
| [BL-008](#bl-008) | Broad frontend/backend refactoring; verification rewrite | — | Never as a side effect |
| [BL-009](#bl-009) | Planner step-ordering non-determinism (set iteration) | — | Post-Phase-2 |

---

<a id="bl-001"></a>
## BL-001 — Pre-existing React-hooks / Next lint errors

**Group:** D
**Classification:** `FRONTEND_IMPLEMENTATION` (application defect, pre-existing)
**Owning phase:** Independent remediation workstream
**Status:** DO NOT FIX DURING VEA-2

### Description

`npx eslint .` in `frontend/` exits 1 with genuine React-correctness findings across
~20 components. These are real defects, not false positives, but they are unrelated to the
verification-architecture work and unrelated to the change under test.

### Measured baseline (M0, this phase)

**Total: 34 errors, 0 warnings.**

| Rule | Count |
|------|-------|
| `react-hooks/set-state-in-effect` | 15 |
| `react-hooks/exhaustive-deps` | 8 |
| `react/no-children-prop` | 3 |
| `react-hooks/static-components` | 2 |
| `react-hooks/purity` | 2 |
| `react-hooks/immutability` | 2 |
| `@next/next/no-sync-scripts` | 1 |
| `@next/next/no-assign-module-variable` | 1 |
| **Total** | **34** |

### Reconciliation with the Phase 1.5 figure of 31 — IMPORTANT

The Phase 2 plan and `docs/progress.md` M13 both refer to **31** pre-existing lint errors.
The measured M0 baseline is **34**. This is a **documentation gap in Phase 1.5, not a
regression**, and it is reconciled here so the Phase 2 completion gate asserts against a
true number.

- The 31 errors enumerated in the Phase 1.5 M13 table are **all still present, unchanged**,
  rule-for-rule and count-for-count.
- The difference is **exactly 3 `react/no-children-prop` errors**, a rule that does not
  appear anywhere in the Phase 1.5 M13 table. It was omitted from that table.
- Affected files:
  - `frontend/components/dashboard/cashflow-chart.tsx:53:72`
  - `frontend/components/dashboard/category-spend-chart.tsx:39:72`
  - `frontend/components/graph/graph-overlay.tsx:160:9`

**Pre-existence PROVEN, not assumed** (plan §1: `PROVEN over PROBABLE`):

```bash
git diff --quiet HEAD      -- <each of the 3 files>   # → unmodified
git diff --quiet bacc1fe2  -- <each of the 3 files>   # → unmodified
```

All three files are **byte-identical both to `HEAD` and to `bacc1fe2`** — the last commit
touching `frontend/`, five commits before the change under test. They were not introduced by
Phase 1.5 remediation and are not caused by the backend change.

Phase 1.5's own M13 narrative separately recorded lint dropping "44 → 35" after excluding
vendored `public/` and generated `dist/` output, which is inconsistent with its own
31-row table. The measured value supersedes both.

### Binding baseline for the Phase 2 completion gate

> The Phase 2 gate criterion "the lint errors remain exactly 31" is **corrected to
> **exactly 34**, with the per-rule distribution above.** Any deviation from 34, in either
> direction, means scope leaked and is a STOP condition.

### Why deferred

1. Every affected file is pre-existing and unrelated to the change under test
   (`in-blast-radius=0`, Phase 1.5 M5/M12).
2. Repairing ~20 components is a substantial independent workstream requiring its own
   diagnosis, not a side effect of an evidence-integrity phase.
3. Phase 2 uses the lint failure population as a **fixed control**. Changing it invalidates
   the proof that Phase 2 altered nothing behaviourally.

### Evidence

- `runtime/generated/evidence/frontend/lint.log`
- `runtime/generated/evidence/frontend/frontend-verification.json`
- `docs/progress.md` → VEA-2 Phase 1.5 M13 "Deliberate stop"

### Explicitly prohibited

No suppression, `eslint-disable`, rule downgrade, severity change, rule removal, threshold
change, or file exclusion may be used to reduce this count (plan §1.7).

---

<a id="bl-002"></a>
## BL-002 — Credit-card over-prediction hop

**Group:** C
**Classification:** `VERIFICATION_FRAMEWORK` (precision, not correctness)
**Owning phase:** After diagnosis reliability is established
**Status:** DO NOT FIX DURING VEA-2

### Description

A loan-engine change pulls credit-card entities into the blast radius through a shared
`endpoint:GET /report` / `credit_card_engine` hop:

- `capability:useCreditCardsCapability` (ownership graph)
- `mapper:frontend/lib/mappers/credit-cards-mapper.ts` (chain map)
- `view_model:StatementHistoryViewModel` (chain map)

A loan amortization change reaching credit-card view models is a wide hop.

### Why deferred

**It fails in the safe direction.** Over-prediction costs extra verification; under-prediction
misses defects. Plan §2 is explicit: correctness and evidence integrity precede optimization.
Tightening the graph before attribution is trustworthy risks trading a cheap, safe error for
an expensive, unsafe one.

Phase 3 inherits this once graph-based diagnosis exists to prove a narrowed radius is still
sound.

### Evidence

`docs/progress.md` → Phase 1.5 M5 "Over-prediction assessment (restraint)"

---

<a id="bl-003"></a>
## BL-003 — E-4: replace keyword attribution with graph traversal

**Group:** B
**Classification:** `VERIFICATION_FRAMEWORK` (known defect, contained)
**Owning phase:** **Phase 3**
**Status:** DO NOT FIX DURING VEA-2 — and specifically **do not extend**

### Description

In `runtime/system/evidence/aggregator.py`:

- `_find_chain_for_failure()` returns the **first** entry of the chain map irrespective of
  which test actually failed (`aggregator.py:474` — `for engine_file, chain in
  cross_map.items(): ... return` on the first iteration).
- `_find_dependency_chain()` joins by **substring match**.

This is attribution by guessing, and is the exact defect class the Phase 2 hard invariant
prohibits (`PROVEN over PROBABLE`, `UNKNOWN over GUESSED`).

### Phase 2 handling — leave in place, untouched

Plan M5 explicitly forbids rewriting these functions. They must be:

- **left in place** (no deletion — plan §1.8 forbids removing unused-looking code),
- **not extended**,
- **not called** by any new Phase 2 code path.

New Phase 2 attribution joins via the `unit_id` spine and the M3 run manifest instead, so the
defective functions are bypassed rather than built upon.

### Why deferred

Replacing keyword matching with real graph traversal is Phase 3's stated objective
(`failure → cluster → graph → causality verdict`). Doing it inside Phase 2 would conflate
"establish the identity spine" with "change attribution semantics", and Phase 2's tests would
no longer prove the spine works.

### Risk if ignored

Rebuilding E-4 by accident in a new format is listed in the plan's risk register. Any new
join keyed on names, substrings, categories or "first match" recreates it.

---

<a id="bl-004"></a>
## BL-004 — CI workflow topology audit and consolidation

**Group:** E
**Classification:** Infrastructure / CI architecture
**Owning phase:** Post-Phase-2 (Phase 3 or a dedicated phase); deliberately unsequenced
**Status:** **DO NOT TOUCH.** Modifying any file under `.github/workflows/` during Phase 2 is
a STOP condition.

### Objective when it eventually runs

Audit every GitHub Actions workflow and profile against the unified verification runtime.
Identify duplicate executions, redundant gates, duplicated evidence generation, and workflows
whose responsibilities can be collapsed **without changing verification semantics**.

### CI workflow topology baseline — recorded at M0, observation only

Frozen reference point so the future audit starts from fact, not suspicion. No workflow file
was modified to produce this.

```bash
ls .github/workflows/*.yml | wc -l    # → 9
```

**All 9 workflows:**

```
backend-verify.yml        frontend-verify.yml       golden.yml
mutation.yml              playwright.yml            quality.yml
verification-runtime.yml  dependency-update.yml     release.yml
```

**Workflow → `verify.py <profile>` map (7 profile-invoking workflows):**

| Workflow | Command | Line |
|----------|---------|------|
| `backend-verify.yml` | `python runtime/verify.py backend` | 51 |
| `frontend-verify.yml` | `python runtime/verify.py frontend` | 61 |
| `golden.yml` | `python runtime/verify.py golden` | 45 |
| `mutation.yml` | `python runtime/verify.py mutation` | 52 |
| `playwright.yml` | `python runtime/verify.py playwright` | 71 |
| `quality.yml` | `python runtime/verify.py quick` | 46 |
| `verification-runtime.yml` | `python runtime/verify.py runtime` | 54 |

The remaining 2 (`dependency-update.yml`, `release.yml`) do **not** invoke a verification
profile. `dependency-update.yml` appends `verify.py status` to its summary only;
`release.yml` explicitly documents that the delegation rule applies to verification workflows.

Each of the 7 declares in its header comment that it runs
"the ONLY verification command" — yet **trigger paths overlap substantially**.

**Trigger-overlap observations (verified at M0):**

| Path pattern | Workflows triggered |
|--------------|---------------------|
| `runtime/**` | `backend-verify`, `frontend-verify`, `playwright`, `verification-runtime` |
| `backend/src/routers/**` | `backend-verify` (via `backend/**`), `frontend-verify`, `verification-runtime` |
| `backend/src/mappers/**` | `backend-verify` (via `backend/**`), `frontend-verify`, `verification-runtime` |
| `backend/src/engines/**` | `backend-verify` (via `backend/**`), `verification-runtime` |
| `frontend/**` | `frontend-verify`, `playwright` |
| *(any path)* | `quality.yml` — **no path filter**, runs on every push to every branch |

Additional confirmed detail:

- `quality.yml` triggers on `push: branches: ["**"]` with **no `paths:` filter** at all.
- `playwright.yml` is branch-restricted (`main`, `master`, `develop`) unlike
  `backend-verify`/`frontend-verify`/`verification-runtime`, which run on `"**"`.
- `golden.yml` and `mutation.yml` are **schedule-triggered** (`cron` 03:00 and 02:00 daily)
  plus `workflow_dispatch` — they are not push-triggered and are **by design**, not redundancy.
- Net effect: a single `backend/src/routers/**` change can fan out to ~5 workflows
  (`backend-verify`, `frontend-verify`, `verification-runtime`, `quality`, and `playwright`
  if the branch matches and frontend paths are touched), each independently re-running
  changed-file detection, capability mapping and blast-radius computation.
- All 9 workflows upload artifacts and all emit `GITHUB_STEP_SUMMARY`, so **evidence
  generation is also duplicated per workflow**.

### Hard constraints for the future audit

1. **Consolidate only after execution equivalence is proven** — with evidence (the Phase 2
   run manifest and per-unit evidence make this possible for the first time), not argued from
   workflow YAML alone.
2. **Do not remove a workflow merely because it appears redundant.** Apparent redundancy is a
   hypothesis. Overlapping triggers may encode intentional defence-in-depth, differing runner
   images, differing permissions, or required-status-check contracts on protected branches.
3. Distinguish *duplicate execution of the same work* (waste) from *the same profile run under
   different conditions* (possibly intentional).
4. **Check branch-protection required status checks before proposing removal** — deleting a
   workflow that is a required check silently blocks merges.
5. Preserve the separation of heavy workloads (`golden`, `mutation`) from ordinary
   verification — they are schedule-triggered by design.
6. Any consolidation must keep local/CI parity intact (Phase 1 C10).

### Why deferred

Phase 2 is scoped to **preserve the existing CI execution topology**; M3 acceptance diffs the
executed command list to prove it. Auditing or consolidating workflows during Phase 2 would
invalidate that invariant and remove the very control proving Phase 2 changed nothing
behaviourally.

### Prerequisite

Phase 2 certification. The audit needs `unit_id`-keyed execution manifests to prove that two
workflows do or do not perform the same verification work.

### Gate assertion

Phase 2 M7 must re-assert that this 9-workflow topology is **unchanged**.

---

<a id="bl-005"></a>
## BL-005 — GAP-003: `verification.yaml` capability-module path sync

**Group:** —
**Classification:** Configuration drift
**Owning phase:** Later
**Status:** DO NOT FIX DURING VEA-2

### Description

The `verification.yaml` registry carries stale module paths; the canonical authority for
capabilities and chains is the `runtime.foundation.architecture` provider. Registry capability
`modules` entries (e.g. `backend/src/loan_engine`) do not all correspond to current source
layout (e.g. `backend/src/engines/loan_engine`).

### Why deferred

Phase 2 M2 joins units to registry **workflow/script IDs**, which are accurate and stable. It
does not depend on capability `modules` paths, so the drift does not block the identity spine.
Correcting registry paths changes capability resolution and therefore risks changing which
verification gets selected — a behavioural change Phase 2 forbids.

### Evidence

`docs/verification/VEA1_AUDIT_REPORT.md`; `docs/progress.md` VEA-1 summary ("`verification.yaml`
registry has stale module paths").

---

<a id="bl-006"></a>
## BL-006 — Schemathesis expansion, Pynguin, automated test generation

**Group:** —
**Classification:** Test-capability expansion
**Owning phase:** Later
**Status:** DO NOT FIX DURING VEA-2

### Description

Broader Schemathesis coverage, Pynguin-based generation, and other automated test-generation
initiatives.

### Why deferred

Phase 2 is about making **existing** verification evidence trustworthy and joinable. Adding
new test generators increases the failure population and the evidence surface at exactly the
moment Phase 2 needs both held constant. Generation is only valuable once its output can be
attributed, which is what Phase 2 and Phase 3 establish.

---

<a id="bl-007"></a>
## BL-007 — Mutation campaigns, golden redesign, large regression redesign

**Group:** —
**Classification:** Verification-strategy expansion
**Owning phase:** Later
**Status:** DO NOT FIX DURING VEA-2

### Description

Large-scale mutation-testing campaigns, redesign of the golden-dataset regression approach,
and broad regression-suite redesign.

### Why deferred

These are cost-gated, long-running workloads (`mutation-run` and `golden-regression` both
carry `estimated_duration_seconds >= 600` and require explicit request). Redesigning them
changes both executed commands and CI topology — two Phase 2 STOP conditions.

Note: Phase 2 **does** use targeted mutation checks as a *test-strength verification technique*
(M6 acceptance: "forcing the join to always match kills ≥1 test"). That is a local, temporary,
reverted probe — categorically different from a mutation campaign, and not covered by this
deferral.

---

<a id="bl-008"></a>
## BL-008 — Broad frontend/backend refactoring; verification architecture rewrite

**Group:** —
**Classification:** Architectural change
**Owning phase:** **Never as a side effect**
**Status:** DO NOT FIX DURING VEA-2

### Description

Any broad refactor of frontend or backend application code, or any rewrite of the verification
architecture, undertaken opportunistically while performing other work.

### Why deferred — permanently, as a side effect

Plan §1.5 requires preferring extension over creation; §1.6 requires preserving all existing
functionality and tests. The two disjoint pipelines (intelligence vs orchestrator) described
in plan §0 are a real architectural problem, but Phase 2's answer is to **thread an identity
spine through them additively**, not to merge or rewrite them.

A rewrite would make it impossible to demonstrate that executed commands are byte-identical,
which is the single control that makes Phase 2 verifiable.

### Specifically prohibited during Phase 2

- Merging the intelligence and orchestrator pipelines.
- Deleting orphaned or dead-looking project code merely because it is unused (§1.8).
- Any uncontrolled TypeScript/build-fix loop (§1.9).
- Backend application code changes (Phase 1.5 established backend is innocent and green).

---

<a id="bl-009"></a>
## BL-009 — Planner step-ordering non-determinism

**Group:** —
**Classification:** `VERIFICATION_FRAMEWORK` (determinism defect, pre-existing)
**Owning phase:** Post-Phase-2
**Status:** DO NOT FIX DURING VEA-2
**Discovered:** VEA-2 Phase 2, M3 (while establishing the executed-command control)

### Description

`VerificationPlanner` emits verification steps in a **different order on different runs of
the same input**. The command *set* is stable; only the order varies.

Observed on pristine `HEAD` code (change-independent), profile `mutation`, 3 consecutive runs:

```
run_fast_checks | run_backend_verification | run_runtime_verification | run_mutation_selective
run_runtime_verification | run_fast_checks | run_backend_verification | run_mutation_selective
run_fast_checks | run_backend_verification | run_runtime_verification | run_mutation_selective
```

### Root cause — located and proven

In `runtime/foundation/verification/planner/planner.py::_determine_workflows_scripts`
(~lines 528-556):

- `workflows` and `scripts` are built as unordered `set()`s.
- `capabilities` is an unordered `set` iterated directly (`for cap_id in capabilities:`),
  so `workflows.update(cap.workflows)` inserts in a run-dependent order.
- The function does return `sorted(...)`, but the variance has already influenced which
  workflow `_build_steps` selects first for a given target, and that selection determines
  step order.

**Proof (not inference):** with `PYTHONHASHSEED=0` the ordering is perfectly stable across
repeated runs; without it, it varies. Python string-hash randomisation is the driver.

### Pre-existence PROVEN

Demonstrated by `git stash`-ing all Phase 2 changes and re-running the capture against
pristine `HEAD` code, which reproduced the variance. It is **not** introduced by the
Phase 2 identity spine.

### Why deferred

Fixing it changes **the order in which CI executes verification scripts**. Plan §M3
explicitly prohibits "changing step ordering or dedup semantics", and the Phase 2 central
control is that executed behaviour is byte-identical. Repairing this during Phase 2 would
destroy the control that proves Phase 2 changed nothing.

Phase 2 instead established its command-equivalence control under a pinned
`PYTHONHASHSEED`, which isolates this variable while still proving M3 neutral.

### Impact assessment

- **Not currently a correctness bug.** All planned steps execute regardless of order, and
  the steps have no order-dependent side effects on each other today.
- It does undermine reproducibility, snapshot stability, and any future attempt to prove
  two runs did the same work by comparing ordered output.

### Consequence for BL-004 (Group E CI topology audit)

The future audit **must not** use step order to prove execution equivalence between
workflows. It must compare the command *set keyed by `unit_id`*, which the Phase 2
`run-manifest.json` now makes possible.

### Suggested fix when it runs

Iterate `capabilities` and the category set in sorted order, so insertion order into
`workflows`/`scripts` is deterministic. Then re-baseline any order-sensitive snapshot.

---

## Amendment log

| Date | Entry | Change |
|------|-------|--------|
| 2026-08-11 | BL-001 | Created. Baseline corrected **31 → 34** with proof of pre-existence for the 3 previously-unrecorded `react/no-children-prop` errors. |
| 2026-08-11 | BL-004 | Created with the M0 CI topology baseline: 9 workflows, 7-profile map, trigger overlaps. |
| 2026-08-11 | all | Register created by VEA-2 Phase 2 M0, seeded from plan §2. |
| 2026-08-11 | BL-009 | Added. Planner step-ordering non-determinism discovered at M3, proven pre-existing via `git stash` + `PYTHONHASHSEED` isolation. |
