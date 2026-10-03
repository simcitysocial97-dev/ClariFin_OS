# M10-R2 — Verification Execution Parallelization: Final Report

**Baseline commit:** `f500f27f8692975f463722a4f9f124d937ea9a5c` (`m11/parallelism-correctness`)
**Milestone commits:** `d6bd5b79` (C0+C1), `0d29e22e` (C3), `c6dc733f` (C4), `90e8e6de` (C2)
**Diff:** 50 files, +5226 / −1150

---

## 1. Architecture

### 1.1 Old topology

Both canonical execution paths were serial loops:

| Path | Loop | Location |
|---|---|---|
| Profile aliases (`quick`, `backend`, `frontend`, `runtime`, …) | `for task: for cmd: subprocess.run(...)`, **fail-fast** | `control_plane_facade.py:1332-1405` |
| `verify check` | `for spec in plan.tasks:`, re-capturing the fingerprint per task | `execution_orchestrator.py:1416` |

`parallel_executor.py` existed, was internally consistent, and was imported by nothing
in the executor path. `runtime/tests` ran 158 files / 2492 tests with no `-n` despite a
pinned `pytest-xdist`.

### 1.2 New topology

```
CLI
 └─ runtime.verify
     ├─ profile alias ─► _run_profile_alias
     │                     └─ parallel_executor.execute_tasks_in_parallel (bounded pool)
     │                          └─ run_streaming_command  ◄── THE ONE WORKER
     └─ check ─────────► ControlPlane.check
                           ├─ build_execution_plan  (serialization, dedup)
                           ├─ [sharded] ExecutionOrchestrator.execute
                           │     ├─ concurrent independent tasks (non-escalation)
                           │     ├─ main-thread tasks (mutation, authorization-gated)
                           │     ├─ escalation barrier (plan order)
                           │     └─ fingerprint capture-after ─► _finalize
                           └─ run --aggregate ─► merge_shard_reports ─► single verdict

Verification Reconcile (CI):  plan ─► matrix (≤7 shards) ─► aggregate
```

### 1.3 Why parallelism is safe

- **Evidence paths are unique per task.** Logs are `m9-c49/logs/{plan_id}/{task_id}-{stream}.log`.
  `evidence_path_conflicts()` asserts no two concurrently-scheduled tasks share a
  destination; a collision is a hard failure, never resolved by discarding evidence.
- **Records merge in plan order, never completion order**, so output cannot depend on
  scheduling.
- **A dependency is only honoured when it exists.** `depends_on` is populated *only* for
  escalation tasks (`:1219-1227`), so the non-escalation set is provably a free set.
- **Escalation tasks are a barrier, not a fan-out unit.** Every shard and the in-process
  path run them after the mandatory set completes, because stop-on-sufficiency is only
  decidable then.

### 1.4 Fingerprint semantics — changed, and strictly stronger

| | Before | After |
|---|---|---|
| When | once per task, between tasks | once before, once after the fan-out |
| Coverage | a change during the **final** task went undetected | cannot miss a change anywhere |
| Verdict | `SCOPE` → `VALIDATION_BLOCKED` | identical |
| New decision values | — | none |
| Threshold changes | — | none |
| Cost | re-walked all of `backend/src` per task | exactly 2 captures per execution (asserted) |

Lost behaviour: the early `break`. That is recorded explicitly in `decisions` as
`repository-integrity-check-failed` so the evidence does not claim work was abandoned
when it completed and was then rejected for provenance.

---

## 2. Executor

`parallel_executor.py` is now the single execution core; both call paths use it.

**The dead executor was not reused verbatim — four blockers were fixed:**

1. **Buffered output** (`capture_output=True`) would have regressed the 2026-09-30
   stabilization whose comment records that all 20 task logs stayed 0 bytes on a killed
   run. The streaming worker was promoted instead.
2. **No process-group kill** → a wrapper timeout orphaned shell → pytest → children.
3. **Wrong dependency field** (`dependency_on`; the model uses `depends_on`).
4. **No result vocabulary** (returned dicts, so no completion state or termination kind).

**Single implementation, verified by identity** (not by inspection):

```python
eo._summarise_pytest_outcome is pe.summarise_pytest_outcome   # True
eo._classify_termination    is pe.classify_termination        # True
eo._tee                    is pe._tee                          # True
eo._kill_process_group     is pe._kill_process_group           # True
```

Fidelity preserved: `TEST_ASSERTION_FAILURE` / `TEST_TIMEOUT` /
`COLLECTION_OR_INTERNAL_ERROR` are still distinguished, and termination still resolves
signal names (`143` → `SIGTERM`).

**Concurrency primitive: threads, not processes.** The work is waiting on a subprocess,
and the spec/plan/orchestrator are unpicklable. Threads also keep `on_record` in-process,
so partial progress stays observable. A deliberate divergence from the original
`ProcessPoolExecutor` implementation.

**Bounds:** `min(cpu, 4)` default, `VERIFY_MAX_WORKERS` override, never unbounded, never
exceeds available work.

**Failure semantics changed to collect-all** in `_run_profile_alias`. The verdict is
unchanged (any required task failing fails the profile); what changed is that one failure
no longer erases unrelated results. Exit codes, the timeout/interruption vocabulary and
the event records are byte-identical.

---

## 3. Plan

**Serialization.** `ExecutionTaskSpec.from_dict` / `ExecutionPlan.from_dict` added,
schema-asserted, unknown-key tolerant. Four existing call sites already rebuilt a spec via
`ExecutionTaskSpec(**spec.to_dict())`, which silently turned the eight `tuple[str, ...]`
fields into lists; they now route through `from_dict`, and the field-for-field round-trip
test is what pins that.

**A supplied plan is authoritative.** Previously `ControlPlane.run` loaded the plan file,
found no `ControlPlanePlan.from_dict` via `hasattr`, discarded the payload it had just
parsed, and rebuilt the whole plan from the changed files — and a corrupt plan exited 0.
All four failure modes are now hard errors.

**Sharding.** Deterministic duration-weighted LPT over `estimated_duration_seconds`;
`task_id` is the total-order tiebreak. `partition_fingerprint` lets every shard assert it
agrees with the plan job.

**The honest ceiling:** a task cannot be split across runners, so the critical path floors
at the slowest single task. On a 40-file boundary that is the ~1800 s coverage measurement
of a ~4741 s total, so 7 shards reach ~1800 s — **~2.6x, not 7x**. Asserted in
`test_critical_path_cannot_beat_the_heaviest_single_task`. An earlier version of the
balance test asserted `sum/N`, which no partitioner can deliver for indivisible tasks.

**The split-brain guard.** `set(record.task_id) == set(t.task_id for t in plan.tasks)`; a
short set yields `NOT_CERTIFIABLE` naming the missing ids. There is no configuration in
which a shard that silently failed to report leaves the run certifiable. A shard that died
mid-flight leaves an unreadable report → decided `NOT_CERTIFIABLE` naming the file, not an
opaque exit 2.

**Deduplication.** Measured on a 40-file boundary: **11 tasks → 8, coverage 5 → 2,
redundant coverage executions 3 → 0.**

The mechanism mattered: `_inject_revalidations` had no dedup *and* the `--out` path embeds
the capability name, so identical scopes produced byte-different command strings. A
command-string dedup — the key already used at `:832` — **cannot** fix this. Grouping is on
resolved scope, and `fan_out_shared_measurement_records` materialises a per-capability
record before the decision so `_finalize` and `_find_measurement_record` are untouched.
`revalidation_sources` keeps one entry per capability: no obligation deleted, only
redundant executions removed.

---

## 4. Runtime — xdist on `runtime/tests`: piloted and rejected

| Run | Result | Wall |
|---|---|---|
| serial | 2685 passed, 16 skipped | 1601 s (26m41s) |
| `-n 4` | 2584 passed, 16 skipped, **6 failed** | 1344 s (22m24s) |

**1.19x is not worth a gate that fails intermittently.** All 6 failures are budget
exhaustion under contention, not logic errors: `runtime.verify doctor`/`status` timed out at
30 s having ~2 s of headroom serially; nested `test_m9_c50.py`/`test_m9_c51.py` timed out at
120 s; two `test_m9_c49` scenarios asserted `diagnostic`/`awaiting_authorization` but saw
`validation_blocked` because the run exceeded its budget and the fingerprint check correctly
refused to certify a drifted tree.

The cost profile explains the ceiling: time is dominated by a few very long tests, so there
is little short-test parallelism to win. **The headroom is not in pytest distribution — it
is the reconcile matrix**, which shards whole verification *tasks* across runners.

Three files are additionally non-parallelisable, identified by reading source, not inferred:

| File | Hazard |
|---|---|
| `test_mutation_infra.py` | writes/restores the **real** `backend/pyproject.toml`, which `capture()` hashes. Observed live: an interrupted run left `source_paths` at `loan_engine` in the working tree |
| `test_full_pipeline_integration.py` | writes/restores the **real** `backend/src/engines/loan_engine/emi.py`, inside the tree `_hash_tree` walks |
| `test_m9_c55.py` | `test_g20` runs `test_m9_c54.py` twice and asserts both agree — **the repetition is the certification claim**; `test_g22` writes a shared `.coverage`; `test_g23` runs a nested mutation campaign |

`conftest.py` encodes this as a **live guard**: if `-n` is ever enabled, those files skip
under xdist only. Serial collection is untouched — 2701 tests, same as before.

Measurement worth recording: `config.option.numprocesses` **cannot** detect xdist from a
conftest — pytest-xdist strips it in the worker (reads back `None`, `dist='no'`, even under
`-n 2`). `config.workerinput` is the real signal.

---

## 5. GitHub

**Verification Reconcile only.** It is *not* one of the four required contexts
(`validate_actions.py:75-80` pins Backend Verification, Frontend Verification, Runtime
Verification, Analyze), so its topology was free to change. The reported check identity is
unchanged — the gate job is still `Verification Reconcile`.

| Job | `needs` | `fail-fast` | `max-parallel` | `if` |
|---|---|---|---|---|
| `reconcile-plan` | — | — | — | — |
| `reconcile-shard` | `[reconcile-plan]` | `false` | 7 (literal) | `shard_count != '0'` |
| `reconcile-gate` | `[reconcile-plan, reconcile-shard]` | — | — | `always()` |

Three traps learned in `mutation.yml` are load-bearing and commented at the point of use:

1. **A matrix job whose own properties are dynamic is never created.** `timeout-minutes` and
   `max-parallel` are therefore **literal**; the real per-shard budget is enforced inside the
   step with GNU `timeout`.
2. **`fail-fast: false` is required** — with `true` the first red shard cancels the rest,
   their evidence is lost, and the gate reports "incomplete" instead of the real failure.
3. **`always()` on the gate** — otherwise one red shard leaves the run with no conclusion.

`if: always()` is also used for shard artifact upload (evidence matters most when red) but
**not** for the shard's informational status print: making that unconditional was genuine
failure masking and certification gate **G12** caught it.

### 5.1 Validator compliance

| Rule | How satisfied |
|---|---|
| 7a / 15 | Reconcile is not required; no `paths:` added to any required context |
| 8 | Reconcile is not a profile workflow; shard legs run the *same* operation as the gate; `diagnose` is a non-profile subcommand |
| 9 | `runtime.verify status` retained on the gate |
| 3 / 4 | All uploads via `upload-runtime`; downloads via the repo's own `download-runtime` composite (an inline `actions/download-artifact` with a guessed SHA was rejected by Rule 10 — the repo's composite carries the correct pin) |
| 12 | Every matrix artifact name interpolates `matrix.` |
| 13 / 14 | `concurrency` unchanged; external actions pinned |

`validate_actions.py`: **ALL CHECKS PASSED** (3 pre-existing warnings in unrelated
workflows remain).

---

## 6. Performance

All values **measured on this host** (4 cores), not derived from CPU capacity.

| Workload | Before | After | Speedup |
|---|---:|---:|---:|
| `verify backend` (required gate's canonical command) | 498.3 s | 252.6 s | **1.97x** |
| `verify quick` | 144.3 s | 140.7 s | **1.02x** |
| `verify check` coverage expansion (40-file boundary) | 11 tasks / 5 coverage / 3 redundant | 8 tasks / 2 coverage / 0 redundant | 3 redundant executions removed |
| `verify check` reconcile, 7 shards | — | critical path ≈ heaviest single task | ≈2.6x projected (see §3) |
| `runtime/tests` under `-n 4` | 1601 s, 0 failed | 1344 s, **6 failed** | **rejected** |
| Backend / Frontend / Runtime Verification | unchanged topology | unchanged topology | see below |

**The required gates were not restructured, per the milestone scope.** They receive only
runtime-internal optimizations, so their job topology, delegation and check identities are
untouched. `verify backend` — the canonical command behind the Backend Verification gate —
measured 1.97x with identical exit codes and no workflow change.

**`verify quick` gained 1.02x and that is the correct result**, not a defect: its longest
single task (`mypy`) dominates, so there is nothing to overlap. This is the same
indivisibility floor as the shard ceiling, and reporting it as such is more useful than
hiding it.

**Not yet measured:** CI elapsed time. That requires a real run of the restructured
workflow and is the remaining acceptance item.

### 6.1 Bugs found by running, not by reading

| Bug | Symptom | Cause |
|---|---|---|
| Mutation off-thread | `ValueError: signal only works in main thread` | mutmut installs a signal handler; pool workers cannot |
| `run --json` unparseable | aggregate could not read a shard report | `to_json()` returns a JSON **string**; `json.dumps` on it emits an escaped string literal |
| State downgrade | every task → INFRASTRUCTURE, whole reconciliation failed | `CompletionState` is a str-mixin enum, so `str(member)` is `"CompletionState.PASS"` |
| Gate exit 2, no verdict | unreadable shard report killed the gate | gate must always decide |

---

## 7. Correctness

**New tests:** 17 serialization · 12 dedup · 24 parallel/fingerprint · 36 sharding/aggregation.

**Full suite:** **2685 passed, 16 skipped, 0 failed** (~26 min).

**Race and integrity coverage:** independent tasks overlap in wall time; results return in
input order regardless of completion order; one failure does not erase unrelated results;
`capture()` called exactly twice per execution; a change inside the *final* task still
yields `VALIDATION_BLOCKED` (strictly stronger than before); mutation runs on the calling
thread; shard union == plan and shards are pairwise disjoint for `M ∈ 1..7`; partition is
deterministic across builds; a dropped task → `NOT_CERTIFIABLE` naming it; a duplicate report
→ rejected; unreadable shard report → decided, not skipped; evidence paths collide-detected.

**Pre-existing contracts followed their own documented maintenance path, not weakened:**

- `test_backend_evidence`'s workflow guard carries an explicit allowlist whose comment reads
  *"a milestone that legitimately changes CI must add its files here"*.
  `verification-reconcile.yml` added.
- `test_vea5_m8` asserted `len(jobs) == 1` as a proxy for *"stable check name for branch
  protection"*. With a fan-out there are legitimately several jobs, so the invariant was
  **restated** in the terms that matter: exactly one job may claim the identity, the gate
  keeps the name, and it is reachable via `needs` + `always()`.

**Pre-existing debt cleared rather than carried forward:** `profiles.py` failed
`black --check` (a slip in the previous commit's playwright delegation) — the
`verify quick` / Backend Verification gate was **red before this work**. Also: 85 ruff
errors across `runtime/`, dead test fixtures, C401/SIM103/B018.

---

## 8. Remaining issues

1. **CI elapsed time is unmeasured.** The reconcile topology is validated end-to-end locally
   (plan → 3 shards → aggregate, each shard executing exactly its assigned tasks, gate
   merging all records and deciding correctly) and the validator passes, but the real
   GitHub Actions critical-path reduction needs a live run. **This is the one outstanding
   acceptance item.**
2. **Required gates are not migrated to matrix topology.** Deliberate — a later milestone,
   under their existing check identities. They currently get ~2x on `verify backend` from
   the in-process fan-out.
3. **`runtime/tests` remains serial.** Justified by measurement (§4), with a live guard
   preventing a naive re-enable.
4. **`_run_profile_alias` still uses one runner per profile task.** A profile whose tasks
   contend for CPU (`run_contract_tests.sh` passes `-n auto` internally) will oversubscribe.
   Correctness is unaffected; only the speedup is.
5. **Three certification tests still write real repo files.** Making them hermetic means
   changing `execute_mutation`'s contract — a larger change than the problem warrants, but
   it is the reason `backend/pyproject.toml` can be left seeded after an interrupted run.
6. **Two `SIM102` clusters remain** in `runtime/foundation/verification/` (13 findings). Not
   auto-fixed: collapsing them is mechanical but each sits in planner/config logic where a
   shape change is better reviewed deliberately than applied by `--unsafe-fixes`.

### Not in this milestone, by design
`/forecast` fabricated projections, Recharts `NaN`, wellness-score scaling, Platform Console
cold-start, unconsumed backend capabilities, Investments HTTP 500, E2E seed limits — all
pre-existing product defects, untouched.

---

## 9. Definition of done

| # | Criterion | Status |
|---|---|---|
| 1 | Canonical executor no longer unnecessarily serializes independent tasks | met |
| 2 | `ParallelExecutor` wired as the single execution core | met |
| 3 | `verify check` executes independent obligations concurrently | met |
| 4 | Fingerprint integrity still enforced | met — stricter |
| 5 | Plan serialization real and tested | met |
| 6 | A shard executes only its assigned plan | met |
| 7 | Duplicate coverage executions eliminated, no obligation deleted | met |
| 8 | `runtime/tests` uses safe parallelism where proven | **not applicable — rejected by measurement** |
| 9 | Required checks retain identity, authority, topology | met — untouched |
| 10 | Independent CI jobs run concurrently in reconcile | met |
| 11 | Matrix aggregation preserves failures | met |
| 12 | Existing caching preserved | met — audited, not redesigned |
| 13 | `validate_actions.py` passes with zero errors | met |
| 14 | No verification/security/quality threshold weakened | met |
| 15 | No unrelated product defects mixed in | met |
| 16 | Real GitHub runs show a critical-path reduction | **outstanding — needs a live run** |
| 17 | All relevant tests green | met — 2685 passed |
| 18 | Final report has measured before/after | this document |
| 19 | Every stage checkpointed; tree clean | met — 4 commits |