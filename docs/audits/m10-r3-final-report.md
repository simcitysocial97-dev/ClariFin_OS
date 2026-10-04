# M10-R3 — Final Report

**Branch:** `m11/parallelism-correctness` · **Base:** `1c39736` · **Date:** 2026-10-04
**Scope of this document:** §17 of the mission.

---

## 1. The original architectural failure

Not an unmodelled "execution envelope".

> **Certification semantics existed in exactly one of six ways this repository executes
> a verification obligation.**

`verify check` / `verify run` produced a plan, bracketed execution with a repository
fingerprint, ran an authorization gate, and classified the result into a 7-value
`FinalDecision`. The other five — profile aliases, obligation legs, runtime shards,
Playwright legs, mutation — used **the same subprocess worker** and formed their verdict
as "the first non-zero exit code in plan order", writing a literal
`final_decision="certified"` into the event log. `_check_fingerprint_integrity` had
exactly **one call site**.

A green `verify backend` was therefore evidence that no shell exited non-zero. It was
not evidence that the repository was unchanged. Those are different claims, and only one
of them is a certification.

## 2. Evidence that established it

Full reconstruction: `docs/audits/m10-r3-checkpoint-a-forensic-report.md`.

| Claim in the supplied report | Verdict | Evidence |
|---|---|---|
| `ParallelExecutor` is dead | **False** | M10-R2 already promoted `parallel_executor.run_streaming_command` to the shared worker for every canonical path |
| `verify run --plan` discards plans | **False** | `control_plane_facade.py:662-663` executes it; `:631-636` refuses to regenerate |
| plan serialization must be built | **False** | `m9-c49-execution-plan/v1` already round-trips; CI already uses it |
| `required_environment` is inert | **True** | 2 reads, both in `to_dict()` — but on a class no execution path instantiates |
| the `timeout 85` unit bug is live | **False** | already fixed in `30042d6c` |
| 8 execution conditions | **Understated** | there are **12**; the omitted ones caused both failures |
| "409 s CI vs 30 s local" | **Misframed** | compares a *job* wall clock to a task number that is not reproducible |

Additional dead/duplicate surface found: `executor_pipeline.py` (2280 lines) on no live
path; `cli_surface.py` a second classification authority with different answers;
`verification/cli/cli.py` an orphan CLI with no timeout; `forensic_cli.py` and
`diagnostic_agent.py` unreachable; `verify status` literally *is* `verify doctor` across
18 CI call sites while three scripts expect `verify integrity` to be a scan.

## 3. Root causes of the two open failures

### Reconcile / `exec-0004` — **CPU oversubscription, not a timeout bug**

Reproduced with the CI environment. `exec-0004` **passes at 125.6 s**; its own pytest
self-reports 106.4 s of work, so the report's "30 s local" is not reproducible.

The shard planner estimates a **sum** (matrix: 1741 s — a serial machine); the executor
runs 4-wide; and two of the three concurrent tasks fork `-n auto`
(`run_contract_tests.sh:78`, `run_fast_checks.sh:89`). Nine CPU-bound processes on four
cores. Measured: `exec-0002` burned 180.3 s of a **360 s** budget; `exec-0003` burned
352.2 s of a task declared `estimated_duration=60`. Correct obligations were reclassified
`TIMED_OUT`.

The 409 s figure is a job wall clock: bootstrap 287 s + the (already-fixed) 85 s kill +
browser install. Comparing it to a task number is meaningless.

### Playwright — **not baseline drift**

Three stacked causes, none of which the report identified:

1. **Wrong database.** `transactions-page-chromium-linux.png` renders the three rows
   `global-setup.ts:274-282` writes — to a **hard-coded `backend/data/finance.db`** that
   `seedTestData()` writes while ignoring `FINANCE_DB_PATH`. CI seeds a different file
   via `tools/e2e_seed.py`. Two competing fixture authorities; the visual pass reads the
   one nobody re-seeds. This alone accounts for most of the 11.
2. **Three tests have no baseline** in the authoritative directory, while four commits
   regenerated into `frontend/tests/e2e/snapshots/` — a tree Playwright never reads,
   because no `snapshotPathTemplate` is configured.
3. **Non-deterministic independently of any change.** `timeline-rail.tsx:29-36` places a
   playhead by day-of-year on a bar rendered on every financial route (~600-900 px of
   drift against `MAX_DIFF_PIXELS = 500`, ~1100 px across a month boundary);
   `playwright.config.ts` sets no `expect.toHaveScreenshot`, so `animations` defaults to
   `'allow'`; neither Recharts chart disables `isAnimationActive`.

Regenerating baselines now would produce a set that passes once and rots.

**Also found:** `exec-0009`'s command is literally
`echo 'UNMAPPED capabilities require review (4): …' && exit 1` — a **mandatory,
always-failing registry-coverage sentinel**. It makes any plan containing it
uncertifiable regardless of code correctness. Reported, not changed: whether unmapped
capabilities *should* block certification is a policy decision, and relaxing a mandatory
gate is not this milestone's to take unilaterally.

## 4. Final execution architecture

```
verify local | verify check | verify run | CI legs
        │
        ▼
  canonical planner ──► ExecutionPlan (serialisable, m9-c49-execution-plan/v1)
        │                 · required_environment (PATH | TOOL | VARIABLE)
        │                 · timeout_seconds · cpu_demand · estimated_duration
        ▼
  preflight: verify_prerequisites ──► RequirementFailure (before ANY spawn)
        │
        ▼
  ExecutionOrchestrator.execute
        │   · fingerprint bracket  (capture → execute → capture → compare)
        │   · CPU-budget admission (CpuBudget, derived demand)
        │   · escalation barrier, authorization gate
        ▼
  parallel_executor.run_streaming_command   ◄── THE ONE process-spawn point
        │   tee-to-file · heartbeat · process-group kill · classify_termination
        ▼
  decide_final_outcome  ──►  FinalDecision (7 values) + distinct exit code
        │
        ▼
  m10r3-certification-run/v1 document  →  runtime/generated/certification/<topology>.json
```

**One execution authority** — `run_streaming_command`; all six topologies converge.
**One plan authority** — supplied plans are executed, never regenerated. **One
decision function** — `decide_final_outcome`, six producers.

## 5. What was consolidated / deleted

| Action | Detail |
|---|---|
| **Consolidated** | `prerequisites` + inert `required_environment` → **one** `required_environment` field with 3 enforced forms. Legacy plans fold in, never dropped. |
| **Consolidated** | `_finalize`'s private precedence table → module-level `decide_final_outcome`. The orchestrator is now the first consumer, not the only one. |
| **Consolidated** | two writers of `backend/pyproject.toml` (one non-atomic, one unaware of the backup) → one `restore_to()` |
| **Consolidated** | mutation's declared vs enforced budget: a bare `1200` literal at two sites → one greppable `DECLARED_MUTATION_TIMEOUT_SECONDS`, both values recorded |
| **Deleted** | the fail-open "first non-zero exit" verdict from profile aliases |
| **Deleted** | `final_decision="certified"` hard-coded literal |
| **Fixed** | `_verify_legs` / `verify_shards` / Playwright gate now refuse drift |
| **Fixed** | SIGKILL-during-mutation corruption (durable backup + atomic replace + self-heal) |

**Not deleted, and why — corrected after investigation.** This section originally claimed
`forensic_cli.py` and `diagnostic_agent.py` were "genuinely unreachable", which
over-stated the case. The *reachability* claim was right (zero Python importers) but the
implication was wrong:

* `forensic_cli` is named as the **declared implementation site** in provenance metadata
  for routes the canonical table marks `DEPRECATED` (`route_authority.py:120`,
  `certification.py:182`). Those strings are load-bearing — they are how this repository
  records where an implementation lives. Deleting the module would orphan them.
* `diagnostic_agent` supplies the `Uncertainty` / `Explainability` / `CERTIFIABLE`
  vocabulary those strings refer to, and is imported only by `forensic_cli`.

`cli_surface.py` was the exception and **was** consolidated (see L8a): its duplicate
classification table is gone and it re-exports the canonical one.

So the remaining surfaces — `executor.Executor`, `executor_pipeline.py`,
`verification/cli/cli.py`, `forensic_cli.py`, `diagnostic_agent.py` — are now **pinned by
test** (`test_m10r3_dead_code_pins.py`) rather than deleted on a belief. Each pin FAILS if
someone wires the module up, and the failure message says to delete the pin rather than
keep it. Converting "I believe this is dead" into a mechanically enforced claim is worth
more than a tidy file list, and `executor.Executor` in particular needs *consolidation*
onto the canonical worker, not deletion.

## 6. What remains intentionally separate

- **Profile aliases** (`quick`, `backend`, …) stay distinct from `verify check`: aliases
  are a fixed legacy task list with no plan; `check` derives one from the diff. Making
  them identical would discard the alias surface entirely, which is a product decision.
- **`MutationResult.to_dict` stays hand-written.** Converting it to `asdict` would change
  the evidence schema. The M10-R3 fields are added explicitly and the omission hazard is
  documented at the method.
- **Runner configuration** (SHA pins, `permissions`, cache keys) stays in YAML. It
  genuinely cannot belong to the runtime.

## 7. Canonical execution path

`parallel_executor.run_streaming_command:240` — one `Popen(shell=True,
start_new_session=True)`, tee-to-file, heartbeat, process-group kill, classification.
Callers: orchestrator, `profile_tasks`, `runtime_shards`, `playwright_shards`, facade
aliases.

Competing engines that bypass it and remain: `mutation_runner:761` (legitimate — mutmut
owns its child tree), `executor.Executor:204`, `MutmutAdapter:623`, and 11 ad-hoc
pytest/mutmut runners in the measurement and certification modules.

## 8. Local/CI equivalence

The local harness consumes the **same serialized execution description** CI does —
`verify local` is classified `CANONICAL_ALIAS`, a front-end over `plan` + `run --shard`,
never a distinct operation, so it cannot grow its own semantics.

Two irreducible runner differences, stated rather than hidden:
- **Concurrency.** CI runs 7 shards on separate runners; `verify local` runs them in
  sequence on one machine. Obligations are identical; only the schedule differs.
- **Wall clock.** A CI leg is faster per task for that reason. Compare task identity and
  outcome, never durations.

Verified live — `verify local` immediately surfaced `exec-0009`:

```
TASK       STATUS           DURATION  TERMINATION
exec-0009  failed               0.0s  command exit 1

RESULT: NOT CERTIFIED

FAILURE:
  exec-0009
  reproduce: .venv/bin/python -m runtime.verify run --plan <plan> --task exec-0009
```

## 9. Parallel topology

`CpuBudget` replaces the worker count. Demand is **derived**, not declared, preferring a
worker-count flag in the command, then inside the shell script the command invokes — the
script step is mandatory, because every heavy task here is `bash .github/scripts/*.sh`
with `-n auto` *inside*. Derivation cannot drift from the command; a declaration can.

Verified on the reproduced shard 6 (4 cores):

| | demand |
|---|---|
| `exec-0002` (`-n auto`) | 4 |
| `exec-0003` (`-n auto`) | 4 |
| `exec-0004` (no xdist) | 1 |

Schedule: `exec-0002` alone → `exec-0003` alone → `exec-0004`+`exec-0009`. Previously all
three at once: 9 CPU on 4 cores.

**Honest trade-off.** Bounding CPU *increases* wall clock — total CPU-seconds are
conserved, so preventing starvation means occupying more time. Shard 6's critical path
is now 540 s instead of three tasks contending to finish in ~352 s. The estimate moves to
reflect that, and a test asserts it does; an estimate that stayed constant while the
schedule changed would be the old bug in new clothing.

## 10. Matrix measurement: before → after

| shard | tasks | est_wall (new) | est_serial (old figure) | cpu_peak |
|---|---|---|---|---|
| 0 | 1 | 2700 s | 2700 s | 1 |
| 1 | 1 | 1800 s | 1800 s | 1 |
| 2 | 1 | 1800 s | 1800 s | 1 |
| 3 | 1 | 1800 s | 1800 s | 1 |
| 4 | 2 | 1200 s | 1800 s | 2 |
| 5 | 3 | 1200 s | 1800 s | 3 |
| 6 | 5 | 1440 s | 1741 s | 4 |

The two columns now differ exactly where concurrency applies. The old figure was the
serial sum, which described a machine that never ran; it is retained as
`estimated_seconds_serial` so the two can be compared rather than one silently replacing
the other.

## 11. Coverage duplication — **not resolved, reported**

The reproduced plan contains two coverage obligations: `exec-0010`
(`measurement coverage tests/unit/engines`) and `exec-0011` (`measurement coverage .`).
The report's "seven identical coverage tasks" were not observed in this plan.

Both are non-mandatory, share a `timeout 1800`, and write into one
`runtime/generated/m9-c49/measurements/` namespace. The narrower run is subsumed by the
whole-backend run. **Collapsing them at the planner level is the correct answer, and it
is not done** — it needs a measurement showing the narrow run contributes evidence the
broad one does not, and I did not have that evidence. Recording a guess as a
deduplication would be manufacturing evidence. Deferred to a checkpoint that measures.

## 12. Fingerprint / evidence integrity proof

The anti-tamper invariant is **preserved and extended**, not weakened.

- Baseline capture → execute → final capture → compare → `VALIDATION_BLOCKED` on drift.
  Verified live: mutating a hashed file inside the bracket produces
  `VALIDATION_BLOCKED` with **both** fingerprints in the reason.
- Called **once around fan-out**, asserted (`test_parallel_execution.py:401`).
- **Now all six topologies bracket**, and all three fan-out gates refuse drift.
- A bracket-less document (older producer) is read as **unstable**, never as a pass — so
  the new field cannot be opt-in.
- An unclosed bracket reports `fingerprint_stable = False`; a crashed runner cannot
  certify silently.
- Mutation rewrites the repo *by design*, so its bracket closes **after** restoration and
  its verdict keys off `toolchain_restored`. A healthy campaign is stable; an abandoned
  one is a hard `SCOPE` block naming the file that will fail the next capture.

Security and evidence rules untouched: CodeQL, SHA-pinned actions, untrusted-checkout
protections, plan identity, run identity, stale-evidence rejection, incomplete-shard
rejection, thresholds.

## 13. Validator / constitution changes — **not done**

No workflow file was modified in this milestone, so no new invariant was needed and none
was invented. `validate_actions.py` is unchanged. Recorded as remaining work, with the
invariants it should enforce once workflows migrate: required jobs invoke the canonical
runtime; fan-out workers execute runtime-generated units; no duplicated per-obligation
timeout or environment; no manually reconstructed evidence transport.

## 14. GitHub workflow results — **none**

No workflow was modified. These commits cannot have changed any CI result. Any claim
about workflow behaviour here would be unfounded.

## 15. Checkpoint SHAs

| Checkpoint | SHA | Subject |
|---|---|---|
| A | `178bba3d` | Forensic execution graph + both failure reproductions |
| B1+B2 | `67a9c9e2` | One certification authority, one environment contract |
| B3+C | `e7d77ae6` | Mutation crash-safety, budget provenance, sixth topology |
| D | `af0d2149` | The CPU budget — the execution condition that caused the failure |
| D2 | `e934154d` | Scoped execution + the local reference harness |
| G1 | `6a259b39` | The adversarial injection suite (§16) |

## 16. Tests

| Suite | Result |
|---|---|
| M10-R3 (6 files) | 330 passed, 1 strict xfail |
| Broad regression (95 files) | 2056 passed, 15 skipped, 0 failed |
| `test_platform_api_phase13::test_tool_schema_serialization` | **failed at `178bba3d`, pre-existing**, untouched |

`test_profile_alias_returns_the_real_profile_exit_code` was **passing for the wrong
reason** at HEAD: its stub pinned an exact keyword signature, did not match the real
call, so every task raised `TypeError`; the pool returns the *exception object*; the old
verdict read only dicts. **A profile in which every task raised returned exit 0 with
`final_decision="certified"`.** Now recorded as `INFRASTRUCTURE` and pinned.

## 17. Final working tree

Clean. Only the pre-existing plan-file edit remains, plus regenerable untracked output
(`runtime/generated/certification/`, `runtime/generated/local-harness/`).

`36 files changed, 8883 insertions(+), 249 deletions(-)` over 6 commits.

## 18. The adversarial acceptance test (§16)

| # | defect | outcome |
|---|---|---|
| 1 | missing env var | **detected, classified, refuses before spawn** |
| 2 | altered timeout | **NOT caught** — gap L2, `xfail(strict=True)` |
| 3 | evidence root | guarded statically; no configurable root exists yet — L1 |
| 4 | wrong plan | **refused**; corrupt plan refused, never regenerated |
| 5 | wrong shard | out-of-range/non-positive rejected; partition deterministic |
| 6 | mutation during run | **refused**, both fingerprints named |
| 7 | killed worker | bounded classified result; process group killed, not waited out |
| 8 | over timeout | `WRAPPER_TIMEOUT`, fires promptly |
| 9 | missing shard result | **refused**, missing id named |
| 10 | stale evidence replayed | **refused**; negative control at current sha certifies |

Tests assert **observed** behaviour. Two premises of mine were wrong and corrected in
place: `plan_fingerprint` is not the staleness signal (`repository_fingerprint` is), and
`population` is a `PopulationAccounting`, not an int.

## 19. Remaining limitations, explicitly classified

| # | Limitation | Class | Severity |
|---|---|---|---|
| **L1** | Workflows still hand-maintain env, timeouts, artifact paths, matrix projection. `verify local` and the certification documents now exist to consume, but no workflow has been migrated. | **Incomplete** | High — the duplication the mission targets is still in YAML |
| **L2** | `timeout_seconds` is not validated on plan load; a negative or absurd budget executes as written. | **Genuine defect** | Medium — an operator error, not attacker-controlled |
| **L3** | Mutation's declared (1200 s) and enforced (4200 s) budgets still differ. Now *recorded* and asserted-to-differ, not unified. | **Known divergence** | Medium |
| **L4** | `shell=True` makes a missing binary surface as exit 127 with `infra_error=None`, indistinguishable from a command that ran and asserted. Callers must special-case 127. | **Genuine defect** | Medium |
| **L5** | Coverage duplication unresolved (§11) — needs measurement, not a guess. | **Deferred** | Low — both tasks non-mandatory |
| **L6** | `exec-0009` is a mandatory always-failing sentinel. | **Policy question** | Medium — needs a human decision |
| **L7** | Playwright fixture authority, harness config and baselines unchanged (§3). | **Not started** | High — CI will still fail visually |
| **L8** | Dead/duplicate surfaces unpruned (§5). | **Deferred** | Low |

**L1 and L7 are why this milestone does not make CI green.** It was never going to: L7 is
three separate frontend/test fixes, and L1 is workflow migration that should not precede
a correct runtime. Reporting that plainly is more useful than a green board.

---

## 20. The closing question

> *If the next CI failure occurs in six months, will the runtime itself tell us exactly
> what failed, under what execution conditions, why it failed, where its evidence is, and
> how to reproduce that exact obligation locally?*

**Yes for six of the seven topologies, and no for the fourth sub-question of the sixth.**

| Question | Before | After |
|---|---|---|
| what failed | forensic investigation | named obligation, one classifier |
| under what execution conditions | not modelled at all | `required_environment`, `timeout_seconds`, `cpu_demand`, resolved and **enforced before spawn** |
| why it failed | first non-zero exit | `FinalDecision` + reason + both fingerprints |
| where its evidence is | 14 hand-maintained artifact path lists | each topology publishes `m10r3-certification-run/v1` |
| was the tree stable? | **not checked on 5 of 6 paths** | bracketed everywhere; drift refuses certification |
| reproduce it locally | reconstruct hidden YAML | `verify run --plan … --task <id>`, or `verify local` |
| *mutation budgets agree* | **no, and unknowable** | both recorded, still differ — **L3** |

**The milestone is not complete.** Not because the core work failed — the certification
model is now genuinely unified and the reconcile failure's mechanism is established and
bounded — but because L1 (no workflow migrated) and L7 (Playwright unfixed) mean the two
originally-open failures are **diagnosed and classified but not resolved**, and L2/L4
are genuine defects left standing.

The answer to the closing question is *yes* on the mechanism, which is what this
milestone was chartered to build, and *no* on completeness, which is what §15 requires
before "done" may be claimed.
---

# Addendum — resolution pass (2026-10-04, after `b7fd1e22`)

Eight limitations were recorded. Six are now closed, one is resolved as
*not-a-defect*, and one needs a human decision. This addendum supersedes §19 and §20.

## Closed

| # | Limitation | Resolution | Commit |
|---|---|---|---|
| **L2** | `timeout_seconds` recorded but never validated | `ExecutionPlan.validate()` rejects non-integer, non-positive and >24h budgets, plus invalid `cpu_demand`. The §16 strict xfail is now a real test. | `233b9558` |
| **L3** | mutation declared 1200 s vs enforced 4200 s | **One table.** `declared_mutation_timeout()` asks the runner; the orchestrator hands `spec.timeout_seconds` back. They agree by construction. | `fc065cf7` |
| **L4** | `shell=True` hid a missing binary as exit 127 | `_detect_shell_command_not_found` populates `infra_error` from the shell's own diagnostic — evidence-based, so a program that legitimately exits 127 stays `EXIT_NONZERO`. | `233b9558` |
| **L1a** | five workflows re-projected the matrix through field lists | Projections now select *shape*, not payload (`{include: .include}`). Measured: the old projection dropped `cpu_peak` and `estimated_seconds_serial`. **Rule 13** in `validate_actions.py` prevents regression, with positive and negative tests. | `60991a52` |
| **L1b** | **CI legs published no certification document** | Found while answering a design question. Only profile aliases wrote one; the reconcile legs — the ones that go red — wrote nothing. Every leg now publishes `runtime/generated/certification/<leg>.json`. | `3128b6c7` |
| **L8a** | two classification authorities disagreed on 12 entries | `cli_surface` now re-exports the canonical table. Three commands the facade routes (`mutation-plan`, `mutation-aggregate`, `mutation-trust`) were **missing from the canonical registry** and are now declared. | `d7cb74c5` |
| **L8b** | — | Removing the field-listing projection **exposed a live runtime bug**: `reasons` was a list in a matrix cell, which GitHub does not accept. The duplication had been masking it. Fixed; the invariant is now tested. | `d7cb74c5` |

## L5 — resolved as *not a defect*

The report's "seven identical coverage tasks" premise is false. The two coverage
obligations in the plan are **distinct per-capability evidence obligations**:

| task | capability | scope | output |
|---|---|---|---|
| `exec-0010` | `account-engine` | `tests/unit/engines` | `measurement-truth-account-engine-coverage.json` |
| `exec-0011` | `api-contracts` | `.` (whole backend) | `measurement-truth-api-contracts-coverage.json` |

Different capability, different scope, different destination. `certification_gate`
consumes records per capability, so collapsing them would **remove evidence** — i.e.
weaken certification, which is precisely what this milestone was chartered to prevent.
The cost is two coverage runs; the correct lever if that is too expensive is the
*certification requirement* (which capabilities require a coverage measurement), never
deduplication.

## L7 — causes fixed; baseline regeneration must happen in CI, and the repo already says so

Fixed: the wall-clock timeline (new pinnable `lib/runtime/clock.ts`), the competing
fixture authority (`global-setup.ts` now honours `FINANCE_DB_PATH` and *fails* rather
than falling back), the entirely unpinned rendering environment, the un-awaited
`document.fonts.ready`, the `setViewportSize` that made every `mobile-chrome` baseline a
desktop capture, and 87 baselines in a directory Playwright never reads.

**Not done: regenerating the 24×2 baselines — deliberately, and the reason is already in
the repository.** `.github/scripts/run_playwright_tests.sh` states it:

> `PLAYWRIGHT_UPDATE_SNAPSHOTS=1` regenerates the visual baselines. It must only ever be
> set on a GitHub runner: baselines are rasterisation-specific, so a workstation running
> with a different font stack produces images that look correct locally and fail in CI.

Regenerating them on this machine would therefore produce exactly the failure mode the
warning describes — 48 baselines that pass here and fail on the runner. Doing it anyway to
show progress would be manufacturing a green signal, which is the one thing this milestone
is not permitted to do.

The correct sequence is therefore: these fixes land → CI regenerates on its own runner →
the resulting diff is reviewed as *evidence that the causes are fixed*, not as a
mechanical PNG refresh. Four previous branch commits regenerated into a directory Playwright
never read, which is the failure mode that wasted them.

## L6 — still needs a human decision

`exec-0009` is a **mandatory, always-failing sentinel**:

    echo 'UNMAPPED capabilities require review (6): …' && exit 1

It makes any plan containing it uncertifiable regardless of code correctness. It was hit
again in the live shard-6 run above. Whether unmapped capabilities *should* block
certification is a policy question; relaxing a mandatory gate is not this milestone's to
take unilaterally.

## Measured: the CPU budget delivered

Same plan, same shard, budgeted vs the unbounded 4-wide contention measured in
Checkpoint A:

| task | contended | budgeted | delta |
|---|---|---|---|
| `exec-0002` | 180.3 s | **105.5 s** | −41% |
| `exec-0003` | 352.2 s | **215.1 s** | −39% |
| `exec-0004` | 125.6 s | **79.2 s** | −37% |

Every task got faster in absolute terms as well as in wall clock, because starved work
was spending most of its time runnable-but-not-running. Total shard wall clock *rose* to
1183.5 s — the honest trade: the CPU-seconds are real, and the previous figure was only
small because three tasks were fighting over four cores.

## Revised closing answer

The closing question is now **yes on mechanism and yes on the two original failures'
root causes, with one policy decision outstanding**:

- what failed — named obligation, one classifier, every topology
- under what execution conditions — `required_environment` (three forms, enforced before spawn), `timeout_seconds` (validated on load), `cpu_demand` (derived, not declared)
- why it failed — `FinalDecision` + reason + both fingerprints
- where its evidence is — **every leg now publishes its own certification document**
- was the tree stable — bracketed on all six topologies; drift refuses certification
- reproduce it locally — `verify run --plan … --task <id>`, or `verify local`
- is CI running what local runs — yes, from one serialized plan; runner-specific
  differences (concurrency, wall clock) stated rather than hidden

**Still not complete**: L1c (per-leg env duplication, hand-written timeout wrappers,
multi-path artifact lists, report parsing), L7 baselines, and the L6 policy decision.

---

# Addendum 2 — second resolution pass (`8844c688`)

Seven more items closed. One is a genuine latent defect the duplication had been hiding.

## L1c — the per-leg timeout was the runtime's, and it was **wrong**

Three workflows wrapped a matrix leg in a literal GNU `timeout` (`85m`, `1500`, `2400`),
each duplicating a budget the runtime already owned. Reconcile repeated its literal in
**three** places, so they could drift independently.

Derived from the plan, the literal was smaller than an obligation's own declared budget:

| shard | contractual | hard-coded | shortfall |
|---|---|---|---|
| 3 | **90 m** (a single task with `timeout_seconds=5400`) | 85 m | **5 m** |
| 6 | 96 m | 85 m | 11 m |

Shard 3 would have been killed five minutes before its contractual expiry — the runner
reporting a timeout for work still legitimately running.

The runtime now publishes `required_timeout_minutes` per shard (derived from task budgets
under the real CPU-budget schedule) and **refuses to start** when the backstop it is handed
expires too early. All three workflows read the published value and export it through
`VERIFY_INFRA_BACKSTOP_SECONDS` so the runtime can validate what it is actually running
under. **Rule 14** prevents regression and caught three real violations when added.

## L1c — per-leg environment is derived, not declared

Both fan-out workflows declared `FINANCE_DB_PATH` under *different* naming schemes
(`e2e-playwright-N` vs `e2e-<leg_id>`). That is per-leg mutable state in YAML, and it is
the value that determines correctness: two legs sharing a database is the cross-shard
mutation `run_playwright_tests.sh` itself documents as the cause of drifting screenshots.

`execution_shards.leg_environment()` derives both `FINANCE_DB_PATH` and `CLARIFIN_PYTHON`
from the runtime's own provenance, keyed on leg **and** plan id so isolation survives a
workflow restructure. Applied with `setdefault` semantics — a deliberate override still
wins.

Removed from `reconcile.yml` (no seeding step, so nothing needed it pre-runtime). **Kept
in `playwright.yml` for a real reason**: it runs `tools/e2e_seed.py --reset` in a step that
executes before any runtime code, so something must name the file first. That distinction
is asserted, because over-pruning would break seeding.

## L6 — a registry gap is a named condition, not `echo … && exit 1`

`exec-0009` was a `capability` task whose command was
`echo 'UNMAPPED capabilities require review (6): …' && exit 1`. The verdict read
*"mandatory obligation failed — run the diagnostic path"*, which is **wrong guidance**:
nothing was diagnostically broken, and the diagnostic path cannot resolve a missing mapping.

Now `CompletionState.REGISTRY_GAP` (distinct from `FAILED` and `CONFIGURATION`),
`ObligationKind.REGISTRY_MAPPING`, and `_execute_registry_mapping_task` — which consults the
live registry, re-checked at execution time so a plan authored while the gap existed cannot
certify after it closed.

    before: diagnostic — mandatory obligation(s) failed: exec-0009 — run the diagnostic path
    after:  not_certifiable — verification-registry mapping(s) missing for changed
            capabilities: exec-0009 (no verification-registry mapping for:
            unmapped:UNMAPPED[6]). This is a review obligation, not a test failure.

**Nothing weakened**: still `is_mandatory=True`, still non-zero exit. Only the report is now
accurate. And the policy question is now decidable in one line rather than by reading a
shell string.

## L8c — pinned, not deleted; and an over-claim corrected

Checkpoint A said `forensic_cli`/`diagnostic_agent` were "genuinely unreachable, and pruning
them is correct". Reachability was right; the conclusion was not. `forensic_cli` has zero
Python importers but is named as the **declared implementation site** in provenance
metadata for `DEPRECATED` routes (`route_authority.py:120`, `certification.py:182`), and
`diagnostic_agent` supplies the `Uncertainty`/`Explainability`/`CERTIFIABLE` vocabulary those
strings refer to. Deleting would orphan them.

They are now pinned by 8 tests that **fail if someone wires the module up**, with messages
saying to delete the pin rather than keep it. It was a third state: neither dead nor live —
documented as the implementation site for deprecated routes.

## Remaining

- **L7b — baseline regeneration must happen in CI.** `run_playwright_tests.sh` already says
  so: *"baselines are rasterisation-specific … must only ever be set on a GitHub runner"*.
  Regenerating here would produce 48 baselines that pass locally and fail in CI — the exact
  failure the warning describes. The frontend production build succeeds with the L7 changes,
  and the clock has 10 unit tests, but the pixels must be regenerated on the runner and the
  resulting diff reviewed as *evidence the causes are fixed*.
- **L1d — artifact path lists and report parsing** still duplicated in YAML.
- **L8d — `executor.Executor`** needs *consolidation* onto the canonical worker, not deletion.

---

# Addendum 3 — final status (`203813ac`)

## Verification

**2089 passed, 15 skipped, 0 failed** across the 97-file affected set (all M10-R3 suites
plus every file touching mutation, sharding, legs, profiles, planning, certification,
playwright, CLI governance, workflow topology and the mutation campaign).
`validate_actions.py`: **ALL CHECKS PASSED**.

The one failure seen in an intermediate run was **my own fault**: I edited
`control_plane_facade.py` while a 23-minute regression was in flight, so
`inspect.getsource(facade.main)` read a half-written file. It passes cleanly in isolation
and in the clean re-run. Worth recording because the symptom — a source-introspection
test failing on a file I had just touched — looks exactly like a real regression, and the
cheap way to tell the difference is to re-run the single test before believing it.

## Limitation ledger, final

| # | Item | Status |
|---|---|---|
| L1a | matrix projections named runtime fields | **Closed** — `{include: .include}` + Rule 13 |
| L1b | CI legs published no certification document | **Closed** — every leg publishes one |
| L1c | per-leg timeout hard-coded in YAML | **Closed** — runtime publishes it, validates it, Rule 14 |
| L1c | per-leg environment in YAML | **Closed** for reconcile; **justified** for playwright (seeds pre-runtime) |
| L1d | evidence-root reconstruction | **Manifest published**; the `upload-artifact` lists themselves unchanged (see below) |
| L2 | `timeout_seconds` unvalidated | **Closed** |
| L3 | mutation 1200 s vs 4200 s | **Closed** — one table |
| L4 | missing binary read as exit 127 | **Closed** — evidence-based detector |
| L5 | "7 identical coverage tasks" | **Not a defect** — distinct per-capability evidence |
| L6 | `echo 'UNMAPPED…' && exit 1` | **Closed** — `REGISTRY_GAP`, decided by the runtime |
| L7 | Playwright causes | **Closed** (clock, fixture authority, env pinning, emulation, 87 dead baselines) |
| L7b | baseline regeneration | **Must happen in CI** — the repository already forbids doing it here |
| L8a | two classification authorities | **Closed** — and 3 routed commands were missing from the canonical registry |
| L8b | runtime emitted a list in a matrix cell | **Closed** — exposed by removing the projection that hid it |
| L8c | dead surfaces | **Pinned, not deleted**; my "genuinely unreachable" claim corrected |
| L8d | `executor.Executor` competing engine | **Pinned**; needs consolidation, not deletion |

## The three things still open, and why

1. **L7b — baseline regeneration in CI.** `run_playwright_tests.sh`: *"baselines are
   rasterisation-specific … must only ever be set on a GitHub runner"*. Regenerating here
   would produce 48 baselines that pass locally and fail in CI. The frontend production
   build succeeds with the L7 changes and the clock has 10 unit tests, but the pixels must
   be regenerated on the runner, and the resulting diff reviewed as *evidence the causes
   are fixed* rather than as a mechanical PNG refresh.
2. **L1d — the `upload-artifact` path lists.** The runtime now publishes
   `evidence_roots` in every certification document, so the migration is a mechanical edit
   driven by the runtime's own answer. Changing the lists alters the artifact's internal
   layout (LCA behaviour), which a consumer may be pinned to, and it cannot be validated
   without a CI run. Trading a documented remaining item for an unverifiable one is a bad
   trade.
3. **L8d — `executor.Executor` consolidation.** Real, but a change with blast radius that
   belongs in a deliberate checkpoint. Pinned so nobody starts routing production through it
   unnoticed.

## Closing answer, final

The mission's question — *will the runtime tell us what failed, under what conditions,
why, where the evidence is, and how to reproduce it locally?* — is now **yes**, with three
exceptions stated above rather than smoothed over. The two originally-open failures have
established root causes and fixed causes; one of them (Playwright) additionally cannot be
*completed* outside CI, and the report says so instead of implying otherwise.
