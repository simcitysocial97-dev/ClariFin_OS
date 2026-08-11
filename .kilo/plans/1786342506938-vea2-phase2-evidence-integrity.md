# VEA-2 Phase 2 — Evidence Integrity (Execution Specification)

**Status:** EXECUTION DOCUMENT — authoritative for VEA-2 Phase 2
**Predecessors:** `docs/verification/VEA2_PHASE1_CERTIFICATION.md`, `docs/verification/VEA2_PHASE1_5_REAL_WORLD_DIAGNOSIS.md`
**Execution ledger:** `docs/progress.md`
**Deferred-item register:** `docs/verification/VEA_BACKLOG.md` (created by M0)

---

## 0. Why this phase exists (the reframing)

Phase 1.5 proved the diagnosis concept on a real failure. Planning this phase surfaced a
structural fact that the Phase 1.5 handoff did not capture, and it changes the objective.

**The repository contains two entirely disjoint verification pipelines.**

| | Intelligence pipeline | Orchestrator pipeline |
|---|---|---|
| Produces | `VerificationUnit` (`id`, `capabilities`, `impact_kinds`, `source`) | `VerificationStep` → `ExecutionResult` (`task_id`, `command`, `exit_code`) |
| Command vocabulary | `python3 -m pytest backend/tests/unit/ -q`, `cd frontend && npx tsc --noEmit && npm run build` | `bash .github/scripts/run_*.sh` |
| Carries C11 provenance | **Yes** | **No** |
| Executes a subprocess | **Never** (0 call sites) | **Yes**, via `Executor` |
| Invoked by CI | **No** | **Yes** — every workflow runs `python runtime/verify.py <profile>` |

Verified during planning:

```bash
grep -rn "optimize_verification\|VerificationUnit" runtime/foundation/verification/   # → empty
grep -cE "subprocess|Executor|\.execute\(" runtime/foundation/intelligence/platform/pipeline.py  # → 0
grep -rn "verify.py" .github/workflows/*.yml   # → verify.py <profile> only (orchestrator)
```

**Consequence:** the layer that knows *why* a check runs never runs it, and the layer that
runs checks does not know why. Phase 1.5's attribution worked **only because failures were
hand-fed from manually parsed log files**.

So E-3 is not "attach a unit ID to evidence". **There is no join key between planning and
execution at all.** Emitting JUnit (E-1) or adding a frontend evidence model (E-2) into a
pipeline with no unit identity would simply recreate E-3 in a new format.

**Phase 2 objective: establish one durable identity spine from plan → execution → evidence,
then make Phase 1.5's attribution run automatically on real pipeline output.**

```
VerificationUnit.id ──► VerificationStep.unit_id ──► ExecutionResult.unit_id ──► Evidence.unit_id
        │                                                                              │
        └────────────── provenance (capabilities, impact_kinds, source) ───────────────┘
```

### Non-goals

Phase 2 does **not** change what CI executes. The orchestrator keeps its `run_*.sh`
vocabulary and the Phase 1 C1–C12 certified paths stay behaviourally identical. Identity and
evidence are threaded **through** the existing execution, additively.

---

## 1. Execution contract

The implementing agent MUST:

1. Execute milestones **sequentially**. M0 first; M7 last.
2. Update `docs/progress.md` after every milestone, using the template in §5.
3. Never mark a milestone `DONE` without its acceptance evidence existing on disk.
   **A milestone is not DONE because the agent says so.**
4. Stop and document a blocker when a criterion cannot be proven.
5. Prefer extending existing components over creating new ones.
6. Preserve all existing functionality and tests. Baseline is **291 runtime tests passing**.
7. Never weaken tests, thresholds, coverage, mutation requirements, or lint rules to get green.
8. Never delete orphaned/dead-looking project code merely because it is unused.
9. Never enter an uncontrolled TypeScript/build-fix loop.
10. Treat `UNKNOWN`/`UNMAPPED` as legitimate, visible outcomes — never inferred away.

### Hard invariant (carried from Phase 1.5, now binding)

```
PROVEN   over  PROBABLE
UNKNOWN  over  GUESSED
```

Any code path that would attribute, classify, or join by keyword match, substring match, or
"first entry wins" is **prohibited**. This is the defect class that produced E-4
(`_find_chain_for_failure()` returning the first chain-map entry regardless of the failure).

### STOP conditions

Halt and record in `docs/progress.md` rather than proceeding, if:

- A change would alter which commands CI executes.
- A change would modify Phase 1 C1–C12 certified behaviour.
- A change would modify any file under `.github/workflows/` (Group E is deferred; see §2.1).
- The work drifts into any item in `docs/verification/VEA_BACKLOG.md`.
- A required acceptance artifact cannot be produced.

---

## 2. Prohibited scope

These are **out of scope for all of VEA-2 Phase 2**. Touching them is a STOP condition.
They are tracked in `docs/verification/VEA_BACKLOG.md` (M0).

| Item | Group | Owner phase |
|------|-------|-------------|
| 31 pre-existing React-hooks / Next lint errors | D | Independent remediation |
| Credit-card over-prediction hop (loan change → credit-card view models) | C | After diagnosis reliability |
| E-4: replace keyword attribution with graph traversal | B | **Phase 3** |
| **CI workflow topology audit and consolidation** | **E** | **Post-Phase-2** |
| GAP-003: `verification.yaml` capability-module path sync | — | Later |
| Schemathesis expansion, Pynguin, automated test generation | — | Later |
| Mutation campaigns, golden redesign, large regression redesign | — | Later |
| Broad frontend/backend refactoring; verification architecture rewrite | — | Never as a side effect |

Rationale for Group C specifically: over-prediction fails in the **safe direction**
(extra verification = cost) rather than the unsafe one (missed verification = undetected
defect). Correctness and evidence integrity precede optimization.

Rationale for Group E: Phase 2 is explicitly scoped to **preserve the existing CI execution
topology** (§0 non-goals, M3 acceptance diffs the executed command list). Auditing or
consolidating workflows during Phase 2 would invalidate that invariant and remove the
control that proves Phase 2 changed nothing behaviourally. The audit is therefore only
meaningful **after** Phase 2 certification, when the identity spine and per-unit evidence
exist to prove execution equivalence. See §2.1.

### 2.1 Deferred: CI workflow topology audit and consolidation (Group E)

**Deferred to:** post-Phase-2 (Phase 3 or a dedicated phase).
**Status in Phase 2:** `DO NOT TOUCH`. Modifying any file under `.github/workflows/` is a
STOP condition, except where a milestone explicitly authorizes it.

**Objective (when it runs):** Audit every GitHub Actions workflow and profile against the
unified verification runtime. Identify duplicate executions, redundant gates, duplicated
evidence generation, and workflows whose responsibilities can be collapsed **without
changing verification semantics**.

**Grounding evidence gathered during Phase 2 planning** (recorded here so the future audit
starts from fact, not suspicion):

- 9 workflows exist; 7 invoke a distinct `runtime/verify.py <profile>`:
  `backend`, `frontend`, `golden`, `mutation`, `playwright`, `quick`, `runtime`.
- Each declares itself "the ONLY verification command" in its header comment, yet
  **trigger paths overlap substantially**:
  - `runtime/**` triggers `backend-verify`, `frontend-verify`, `playwright`, and
    `verification-runtime`.
  - `backend/src/routers/**` triggers `backend-verify`, `frontend-verify`, and
    `verification-runtime`.
  - `quality.yml` has **no path filter** — it runs on every push to every branch.
  - Net effect: a single `backend/src/routers/**` change can fan out to ~5 workflows, each
    independently re-running changed-file detection, capability mapping and blast-radius
    computation.
- All 9 workflows upload artifacts and all emit `GITHUB_STEP_SUMMARY`, so evidence
  generation is also duplicated per workflow.

**Hard constraints for the future audit:**

1. **Consolidate only after execution equivalence is proven.** Equivalence must be
   demonstrated with evidence (the Phase 2 run manifest and per-unit evidence make this
   possible for the first time), not argued from workflow YAML alone.
2. **Do not remove a workflow merely because it appears redundant.** Apparent redundancy is
   a hypothesis. Overlapping triggers may encode intentional defence-in-depth, differing
   runner images, differing permissions, or required-status-check contracts on protected
   branches.
3. Distinguish *duplicate execution of the same work* (waste) from *the same profile run
   under different conditions* (possibly intentional).
4. Check branch-protection required status checks before proposing removal; deleting a
   workflow that is a required check silently blocks merges.
5. Preserve the separation of heavy workloads (`golden`, `mutation`) from ordinary
   verification — they are schedule-triggered by design, not redundancy.
6. Any consolidation must keep local/CI parity intact (Phase 1 C10).

**Prerequisite:** Phase 2 certification. The audit needs `unit_id`-keyed execution manifests
to prove that two workflows do or do not perform the same verification work.


---

## 3. Milestones

### M0 — Baseline and backlog register

**Objective:** Freeze the starting state and create the deferred-item register.

**Allowed:** `docs/verification/VEA_BACKLOG.md` (new), `docs/progress.md`.
**Prohibited:** any source file.

**Requirements**

1. Record HEAD, branch, working-tree status.
2. Run and record, without modifying anything:
   - `python3 -m pytest runtime/tests -q` (expect 291 passed)
   - `bash .github/scripts/run_backend_verification.sh` (expect exit 0)
   - `bash .github/scripts/run_frontend_verification.sh` (expect exit 1; lint-only failure,
     31 pre-existing errors; typecheck/build/test pass)
3. Create `docs/verification/VEA_BACKLOG.md`. Each entry records: ID, description,
   classification, evidence reference, why deferred, owning phase, and explicit
   `DO NOT FIX DURING VEA-2`. Seed it with every row from §2.
4. Record the **CI workflow topology baseline** in the backlog entry for Group E, so the
   future audit has a fixed reference point:
   - `ls .github/workflows/*.yml | wc -l` (expect 9)
   - the workflow → `verify.py <profile>` map (7 profile-invoking workflows)
   - the trigger-overlap observations captured in §2.1
   This is **observation only** — no workflow file may be modified.

**Acceptance**

- [ ] Baseline numbers recorded in `docs/progress.md`
- [ ] `VEA_BACKLOG.md` exists with all §2 rows, including the Group E entry
- [ ] CI workflow topology baseline recorded (9 workflows, profile map, overlaps)
- [ ] No source file modified; **no `.github/workflows/` file modified**

---

### M1 — Stable verification-unit identity in the models

**Objective:** Give the execution layer a place to carry identity and provenance.

**Allowed:** `runtime/foundation/verification/models/model.py`, new tests.
**Prohibited:** executor, orchestrator, planner logic, registry.

**Context:** Step IDs are positional (`step-0001`) and are **reassigned during command
dedup** (`planner.py` ~line 650). They are unstable across runs and MUST NOT be used as the
join key. They remain valid as an internal ordering handle.

**Requirements**

1. Add to `VerificationStep`, both optional and defaulted so all existing construction sites
   keep working:
   - `unit_id: str | None = None`
   - `provenance: dict[str, Any] = field(default_factory=dict)`
2. Add the identical two fields to `ExecutionResult` (5 construction sites repo-wide).
3. Both dataclasses are `frozen=True, slots=True` — preserve that.
4. `provenance` mirrors the C11 shape already emitted by
   `VerificationUnit.to_dict()["provenance"]`: `capabilities`, `impact_kinds`, `source`.

**Tests required**

- Defaults are `None` / `{}` so pre-existing construction is unaffected.
- Round-trip: a step/result constructed with `unit_id` + `provenance` retains them.

**Negative test required**

- Constructing without the new fields must not raise (backwards compatibility).

**Acceptance**

- [ ] 291 existing runtime tests still pass, unmodified
- [ ] New model tests pass
- [ ] `ruff check` clean on changed files

---

### M2 — Explicit unit ↔ registry mapping, with UNMAPPED visible

**Objective:** Establish the join between the 10 optimizer unit IDs and the registry's
workflow/script IDs, explicitly and machine-checked.

**Allowed:** `runtime/foundation/verification/registry/registry.py`, new tests.
**Prohibited:** heuristic/category/substring inference (violates the §1 hard invariant).

**Context — the closed unit set (verified during planning):**

```
unit-targeted            contracts-schemathesis   backend-integration   backend-unit
frontend-unit            frontend-typecheck-build playwright-e2e        runtime-self-test
mutation-run             golden-regression
```

Registry workflow IDs include `backend`, `frontend`, `contracts`, `property`, `golden`,
`mutation`, `playwright`, `runtime`. The sets are **not 1:1** — several units legitimately
map to one script, and cost-gated units may have no executed counterpart.

**Requirements**

1. Add an explicit, enumerated mapping table `UNIT_TO_WORKFLOW` in the registry, with a
   comment justifying each non-obvious row (e.g. why both `unit-targeted` and `backend-unit`
   resolve to the backend script).
2. Provide a lookup returning the registry ID **or an explicit `UNMAPPED` sentinel**.
   Never guess, never fall back to "first match".
3. `UNMAPPED` is a reportable outcome, surfaced in the M3 run manifest — never silently dropped.
4. Many-to-one is permitted and must be explicit.

**Tests required**

- **Coverage test:** every one of the 10 optimizer unit IDs appears in the table (as a
  mapping *or* an intentional `UNMAPPED`). This test fails CI when a new unit is added
  without a mapping decision — that is its purpose.
- Cost-gated units (`mutation-run`, `golden-regression`) resolve without error.
- Lookup of an unknown ID returns `UNMAPPED`, does not raise, does not guess.

**Acceptance**

- [ ] Mapping is enumerated, not inferred
- [ ] Coverage test present and passing
- [ ] `UNMAPPED` reachable and asserted

---

### M3 — Thread identity through execution

**Objective:** Make `unit_id` + provenance survive plan → execute → result.

**Allowed:** `runtime/foundation/verification/orchestrator.py`,
`runtime/foundation/verification/planner/planner.py` (population only), new tests.
**Prohibited:** changing any executed command; changing step ordering or dedup semantics.

**Requirements**

1. Where the planner builds a `VerificationStep` and already knows the owning
   workflow/script, populate `unit_id` via the M2 mapping and attach available provenance.
2. `Orchestrator.execute()` copies `unit_id` and `provenance` from the step onto the
   `ExecutionResult` it constructs (~line 506).
3. Emit a per-run **manifest** at `runtime/generated/evidence/run-manifest.json`:
   - schema key, commit, branch, timestamp
   - one entry per step: `unit_id` (or `UNMAPPED`), `command`, `exit_code`, `status`,
     `duration_seconds`, `stdout_path`, `stderr_path`, `provenance`
   - a top-level `unmapped` list
4. The manifest is the durable join key artifact consumed by M5/M6.
5. Command dedup must not lose unit identity: if two units collapse to one command, the
   surviving step records **all** contributing `unit_id`s. Do not silently drop the second.

**Tests required**

- A planned step for a known unit carries the expected `unit_id`.
- `ExecutionResult` carries the same `unit_id` as its step.
- Manifest round-trips and contains provenance.
- Dedup case: two units → one command → both IDs retained.

**Negative test required**

- A step with no mapped unit produces `UNMAPPED` in the manifest and **does not** crash the run.

**Acceptance**

- [ ] Manifest generated on a real `verify.py` run
- [ ] Executed commands byte-identical to pre-M3 (diff the command list, record in ledger)
- [ ] 291 + new tests pass
- [ ] Snapshots `runtime/tests/snapshots/verification-{plan,report}.json` regenerated
      **only if** the diff is additive; any semantic change is a STOP condition

---

### M4 — Per-phase structured evidence, keyed by unit

**Objective:** Generalize the Phase 1.5 frontend phase decomposition to the backend, and key
all of it by `unit_id`. This is where E-1 (JUnit) lands — as one artifact among several,
**not** as the objective.

**Allowed:** `.github/scripts/run_backend_verification.sh`,
`.github/scripts/run_frontend_verification.sh`, new tests.
**Prohibited:** changing pass/fail semantics or the exit-code contract of either script.

**Requirements**

1. `run_backend_verification.sh` gains per-phase structure equivalent to the frontend script
   (which already emits `frontend-verification/v1`): per-directory/suite phase, status, exit
   code, duration, log path, plus a JSON summary.
2. Add `--junitxml` to pytest invocations, written under
   `runtime/generated/evidence/backend/`. This satisfies **E-1** and finally gives
   `EvidenceAggregator._collect_test_results()` the `junit.xml` it has always looked for.
3. Both scripts accept a `VERIFICATION_UNIT_ID` env var and record it in their JSON summary,
   so evidence self-identifies.
4. **Exit-code contract unchanged:** 0 when all phases pass, 1 when any fails. The backend
   script currently parallelizes suites — preserve that; do not serialize for convenience.

**Tests required**

- Backend JSON summary validates against its schema and lists every phase.
- JUnit XML is produced and parses with the existing `TestResultCollector`.
- Exit code 0 on all-pass, 1 on any-fail (assert both directions).

**Acceptance**

- [ ] Backend evidence JSON + JUnit XML exist after a real run
- [ ] Frontend evidence unchanged in shape (already `frontend-verification/v1`)
- [ ] Backend verification still exits 0 on the current tree
- [ ] Backend suite still runs in parallel

---

### M5 — Evidence model carries frontend and unit identity

**Objective:** Close E-2 and E-3 in `EvidenceAggregator`.

**Allowed:** `runtime/system/evidence/aggregator.py`,
`runtime/system/evidence/models/evidence.py`, collectors, new tests.
**Prohibited:** `_find_chain_for_failure()` / `_find_dependency_chain()` **rewrite** — that
is E-4 and belongs to Phase 3.

**Requirements**

1. **E-2:** add a `frontend` section to `EvidenceSummary` alongside `backend`, populated from
   the M4 frontend JSON: per-phase `typecheck` / `build` / `lint` / `test` status, exit code,
   duration. Today the sole occurrence of "frontend" in the aggregator is a synthesized
   `suggested_layer` string; the frontend failure is structurally unrepresentable.
2. **E-3:** add a unit-keyed failure list, joined via the M3 manifest, each entry carrying
   `unit_id`, `phase`, `path`, `diagnostic`, and `provenance`.
3. `overall_status` must account for frontend phases; a red frontend build cannot report
   `pass`.
4. Leave the existing E-4 keyword functions **in place and untouched**. Do not extend them.
   Record in the ledger that they remain a known defect owned by Phase 3.

**Tests required**

- A frontend build failure appears in `EvidenceSummary.frontend` and forces a non-pass overall.
- Unit-keyed failures carry provenance end-to-end.
- Backend-only runs still aggregate exactly as before (no regression).

**Negative test required**

- Missing frontend evidence yields `not_run`, **not** `pass`.

**Acceptance**

- [ ] Frontend representable in the evidence model
- [ ] Failures joinable to units and provenance
- [ ] Existing `test_evidence_aggregator.py` passes unmodified

---

### M6 — Attribution consumes real pipeline evidence

**Objective:** Remove the hand-fed-log dependency. This is the milestone that makes Phase 1.5
real rather than demonstrated.

**Allowed:** `runtime/foundation/intelligence/platform/attribution.py` (additive adapter),
`runtime/verify.py` (new subcommand), new tests.
**Prohibited:** changing `ObservedFailure`/`FailureAttribution`/`AttributionReport` verdict
semantics; introducing any inference (§1 invariant).

**Requirements**

1. Add an adapter that constructs `ObservedFailure` records from the M3 manifest + M4/M5
   evidence, replacing the ad-hoc regex log parsing used in Phase 1.5.
2. `unit_id` comes from the manifest, **not** from string matching.
3. Populate `pre_existing` only from real evidence (e.g. a recorded baseline comparison).
   If unknown, leave it `None` → the failure classifies as `OUTSIDE_BLAST_RADIUS`, never
   `PRE_EXISTING`. Do not infer pre-existence.
4. Expose `python runtime/verify.py diagnose-failures` rendering
   `format_cross_layer_failure()` from real artifacts.
5. Failures that cannot be joined to a unit are `ATTRIBUTION_UNKNOWN` and are **reported**.

**Tests required**

- Adapter produces the Phase 1.5 verdict from artifacts alone: `in_blast_radius=0`,
  `change_is_implicated=False`.
- A synthetic in-radius failure still yields `IN_BLAST_RADIUS` (guards over-correction).
- Unjoinable failure → `ATTRIBUTION_UNKNOWN`, surfaced not swallowed.

**Negative test required**

- No evidence present → explicit "no evidence" state, **not** a false green and not a
  fabricated verdict.

**Acceptance**

- [ ] Attribution runs with **zero manual log parsing**
- [ ] All 10 Phase 1.5 attribution tests still pass unmodified
- [ ] Mutation check: forcing the join to always match kills ≥1 test

---

### M7 — Re-run the Phase 1.5 specimen end-to-end

**Objective:** Prove the durable data path on the same real specimen. No synthetic substitute.

**Allowed:** documentation, `docs/progress.md`, final report.
**Prohibited:** application changes; any fix that makes the specimen green artificially.

**Requirements**

1. Against the same specimen (loan-engine change at `b9074020`), run the **real** pipeline
   and produce the §18 CROSS-LAYER FAILURE diagnostic with **no manual steps**.
2. Compare against the Phase 1.5 manual result. The verdict must match:
   `in_blast_radius=0`, `change_is_implicated=False`.
3. Record the manual-step count: Phase 1.5 ≈ 15 forensic steps → Phase 2 target **0**.
4. Write `docs/verification/VEA2_PHASE2_CERTIFICATION.md` covering: identity spine, mapping
   coverage + UNMAPPED inventory, evidence artifacts produced, attribution reproduced
   automatically, regression status, and the Phase 3 handoff.

**Acceptance**

- [ ] Diagnostic reproduced automatically, verdict identical to Phase 1.5
- [ ] Zero manual parsing steps
- [ ] Backend green; runtime green; frontend build/typecheck/test green; lint still the
      31 known pre-existing errors (unchanged count — a *change* here means scope leaked)
- [ ] Certification document written

---

## 4. Completion gate

Phase 2 is complete only when **all** hold:

**Identity** — `unit_id` flows plan → step → result → evidence; mapping enumerated and
coverage-tested; `UNMAPPED` visible.

**Evidence** — backend and frontend both emit per-phase structured evidence; JUnit produced
and consumed; `EvidenceSummary` represents the frontend; failures joinable to units and
provenance.

**Attribution** — runs on real artifacts with zero manual parsing; `UNKNOWN` preserved; no
inference introduced.

**Regression** — 291 baseline runtime tests pass unmodified; new tests mutation-checked;
nothing weakened; executed CI commands byte-identical to pre-Phase-2.

**Restraint** — no item from `VEA_BACKLOG.md` touched; the 31 lint errors remain exactly 31;
backend application code unchanged; **no `.github/workflows/` file modified**; the 9-workflow
topology recorded in M0 is unchanged.

**Ledger** — every milestone in `docs/progress.md` with evidence paths; no `IN_PROGRESS` →
`DONE` without artifacts.

---

## 5. `docs/progress.md` entry template

```
## M# — <name>
Status:      NOT_STARTED | IN_PROGRESS | BLOCKED | DONE
Started / Completed
Objective
Commands executed
Files inspected / Files changed
Tests executed (counts before → after)
Evidence (paths)
Findings
Blockers
Decision
Next milestone
```

Statuses: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `DONE`.
A milestone may not move `IN_PROGRESS` → `DONE` without its acceptance artifacts on disk.

---

## 6. Phase roadmap context

```
Phase 1    Integration backbone      change → capability → impact → verification      DONE
Phase 1.5  Real-world attribution    failure → blast radius → attribution             DONE
Phase 2    Evidence integrity        unit → execution → evidence → provenance         THIS
Phase 3    Graph-based diagnosis     failure → cluster → graph → causality verdict    NEXT
Phase 4    Agent-safe autonomy       diagnose → classify → recommend → then remediate

Deferred, post-Phase-2 (not yet sequenced):
  Group E  CI topology audit        workflow → profile → execution equivalence → consolidation
```

Phase 3 inherits: E-4 graph traversal, the credit-card over-prediction hop, and any
`UNMAPPED` inventory M2/M3 surface.

**Group E (CI workflow topology audit, §2.1)** is deliberately left unsequenced. It becomes
actionable once Phase 2 certification provides `unit_id`-keyed execution manifests, which are
the only artifact capable of proving execution equivalence between two workflows. It may run
alongside or after Phase 3; it must not run before Phase 2 certification, because Phase 2's
central control is that CI execution remains byte-identical.

---

## 7. Risk register

| Risk | Mitigation |
|------|-----------|
| Model changes ripple | Only 5 `ExecutionResult` sites; fields optional + defaulted; M1 is isolated |
| Snapshot churn | 2 snapshot files; regenerate only if additive — semantic change is a STOP |
| Scope creep into lint debt | M0 backlog register + §2 prohibition + M7 asserts the count is still 31 |
| Mapping becomes a heuristic | §1 invariant + M2 enumerated table + coverage test |
| CI behaviour drift | M3 acceptance diffs the executed command list; exit-code contracts fixed in M4 |
| Rebuilding E-4 by accident | M5 explicitly forbids touching the keyword functions |
| Agent "tidies up" overlapping workflows while adding evidence steps | `.github/workflows/` edits are a §1 STOP condition; M0 records the 9-workflow baseline; M7 asserts it is unchanged |
