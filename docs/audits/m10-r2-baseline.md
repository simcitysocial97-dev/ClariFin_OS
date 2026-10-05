# M10-R2 — Baseline (C0)

**Milestone:** M10-R2 Verification Execution Parallelization, milestone 1.
**Commit at measurement:** `f500f27f8692975f463722a4f9f124d937ea9a5c`
(`m11/parallelism-correctness`).

This file is the anti-regression oracle for every later phase. **No acceptance claim in
this milestone may cite any figure that is not recorded here.** In particular the
97-minute figure from `m9-c49/logs/execplan-d3fa20f767d7/` (2026-10-01, 4-core, loadavg
~9.6) is a *shape* datapoint only and is **not** used as a baseline.

## Machine

| Fact | Value |
|---|---|
| cores (`nproc`) | 4 |
| loadavg at measurement | 2.33 / 2.14 / 2.40 |
| Python | 3.12.3 (root `.venv`, the only sanctioned environment) |
| pytest | 9.1.1 |
| mutmut | 3.7.0 (pinned) |
| `pytest-xdist` | 3.8.0 (installed, **unused** on `runtime/tests`) |
| `pytest-randomly` | not installed ⇒ test ordering deterministic |

CI runners are 2-core. That caps any in-process fan-out at ≈1.5–1.8x; the large win comes
from runner-level matrix fan-out. Recorded so no phase overclaims.

## Environment verification

`.venv/bin/python -m runtime.verify env-check` ⇒ `ENVIRONMENT CONSISTENT — canonical
.venv is the only environment.` No forbidden `backend/venv` or `backend/.venv`.

## Serial loops (verified by reading, not comments)

| Location | Loop | Scope |
|---|---|---|
| `control_plane_facade.py:1332-1405` | `for task in profile.tasks: for cmd in task.commands: subprocess.run(...)` — serial, **fail-fast** | all 11 profile aliases (`quick`, `backend`, `frontend`, `runtime`, …) |
| `execution_orchestrator.py:1416` | `for spec in plan.tasks:` — serial, re-captures the fingerprint per task | `verify check` |

## `ParallelExecutor` disconnection

`runtime/foundation/verification/parallel_executor.py` exists, is internally consistent,
and is imported by **nothing** in the executor path. Only referents in the whole tree:

- `runtime/tests/test_e2e_smoke.py:243,273,295`
- `runtime/tests/test_regression_suite.py:104`

Four blockers to reusing it unchanged:

1. **No vocabulary.** Returns `dict`; has no `CompletionState`, `FailureStage`,
   `TaskExecutionRecord`, `measurement_truth`, `authorization_required`, or
   `FinalDecision`.
2. **Buffered output** (`capture_output=True`, `:154`) — regresses the deliberate
   2026-09-30 streaming-evidence stabilization documented at
   `execution_orchestrator.py:1598-1622`, which exists precisely because buffered output
   left 0-byte logs when a run was killed.
3. **No process-group kill** (`:153-161`) — a wrapper timeout orphans the
   shell → pytest → children tree; the orchestrator uses `start_new_session=True` +
   `_kill_process_group` for this.
4. **Wrong dependency model.** Reads `depends_on`/`dependencies`/`dependency_on`; the real
   model sets `depends_on` only for escalation tasks and gates on `is_escalation`.

## Measured plan shapes

### Narrow boundary — 2 `loan_engine` files

| Fact | Value |
|---|---|
| `plan_id` | `execplan-61ecf402e332` |
| `plan_fingerprint` | `61ecf402e3323d7a…` |
| capabilities | api-contracts, credit-card-engine, financial-intelligence, loan-engine |
| tasks | **8** |
| exact duplicate commands | 0 |
| certification requirements | `loan-engine` mutation ≥ 80.0 |

Tasks: `run_backend_verification.sh` (est 300), `run_contract_tests.sh` (180),
`run_frontend_verification.sh` (300), `run_fast_checks.sh` (60),
`run_property_tests.sh` (300), 2 coverage (1800 each), 1 mutation (1200).
Estimated serial total **5700 s**.

Note: on this boundary the two coverage tasks have **different** scopes (`.` for
api-contracts, `tests/unit/engines` for loan-engine), so there is nothing to collapse.

### Broad boundary — 40 files under `backend/src/engines/`

| Fact | Value |
|---|---|
| `plan_id` | `execplan-3074899e34db` |
| tasks | **11** |
| coverage tasks | **5** |
| **redundant coverage executions** | **3** |

The five coverage tasks resolve to only **two** distinct scopes:

| Resolved scope | Tasks | Capabilities | Distinct executions |
|---|---|---|---|
| `tests/unit/engines` | `exec-0007`, `exec-0009`, `exec-0010`, `exec-0011` | account-engine, behaviour-engine, credit-card-engine, financial-intelligence | 1 (3 redundant) |
| `.` | `exec-0008` | api-contracts | 1 |

This is the redundancy the milestone targets. Root cause: `_inject_revalidations`
(`execution_orchestrator.py:1044-1080`) has **no dedup**, and the `--out` path embeds the
capability name, so the *command string differs per capability even when the measured
scope is byte-identical*. A command-string dedup — the key already used at `:832` —
therefore cannot collapse them.

## Runtime pytest

`run_runtime_verification.sh:35` runs
`pytest runtime/tests/ -q --timeout=30` with **no `-n`**: 158 files, 2492 test functions,
fully serial. This is the single largest task in the runtime profile.

`-n auto` is used in only 2 of 15 CI scripts (`run_contract_tests.sh:78`,
`run_fast_checks.sh:89`), so the idiom is proven in-tree and `xdist` is already a pinned
dependency — the gap is that `runtime/tests` was never migrated.

Five verified xdist hazards, in three files:

| Location | Hazard |
|---|---|
| `runtime/tests/test_mutation_infra.py:315,359` | writes + restores real `backend/pyproject.toml` — the exact file `capture()` hashes (`execution_orchestrator.py:381`) |
| `runtime/tests/test_full_pipeline_integration.py:21-29,43` | writes + restores real `backend/src/engines/loan_engine/emi.py` — hashed by `_hash_tree` (`:379`) |
| `runtime/tests/test_m9_c55.py:566` `test_g20` | runs `pytest runtime/tests/test_m9_c54.py` **twice** and asserts both pass; the repetition *is* the certification claim, and concurrent execution of `test_m9_c54.py` elsewhere makes the two runs legitimately disagree |
| `runtime/tests/test_m9_c55.py:607` `test_g22` | nested `measure_coverage_cli` ⇒ shared `.coverage` write |
| `runtime/tests/test_m9_c55.py:628` `test_g23` | nested `run_mutation_cli(["--smoke"])` — a real mutation run |

`test_mutation_infra.py:303-313` already declares hermetic intent ("the test must be
hermetic"), so the fix direction — point at a `tmp_path` copy — is established in-tree.

**De-risked:** the backend test database is *already* xdist-safe.
`backend/tests/fixtures/database.py:10` states "Safe for pytest-xdist: each worker gets
its own session-scoped template", and `:105` uses `tmp_path_factory.mktemp`. No isolation
work is needed on the backend side.

## Per-task wall-clock

Per-task `duration_seconds` for a **live** `verify check` run is the authoritative
critical-path input (A2) and is measured at the C3 gate, once the fan-out exists, since a
serial run on this 4-core/loadavg-2.3 host is not comparable to CI. Until then the plan's
`estimated_duration_seconds` field is the only per-task cost signal available, and it is
used for shard balance only — never as a performance claim.

## Caching (audited, not redesigned)

| Cache | Location | Status |
|---|---|---|
| `~/.cache/pip` | `setup-python-runtime/action.yml:50` | exists |
| constructed `.venv` | `setup-python-runtime/action.yml:137` | exists; keyed OS+arch+**exact interpreter**, validated and self-repaired on restore (`:166-200`) |
| Playwright browsers | `setup-playwright` | exists |
| npm | `setup-node-runtime` | exists |
| `architecture-inventory.json`, `cross-layer-map.json`, `knowledge-index.json` | regenerated by `bootstrap-runtime` in all 15+ jobs | **not cached** — the one caching candidate |

Live cache hit/miss rate on recent CI runs (A4) is deferred; it does not gate any phase
and `pip install -e ".[all]` runs unconditionally on purpose (documented at
`setup-python-runtime/action.yml:78-90`) so upstream drift stays observable.

## Open items carried forward

| # | Open | Settled by |
|---|---|---|
| A2 | Reclaimable ≈ `max(single task)`, not `sum/N` | C3 gate, live per-task durations |
| A3 | Whether the other 153 `runtime/tests` files are xdist-safe | C2 pilot, 3 consecutive runs |
| A4 | Live CI cache hit rate | deferred; gates nothing |
| A5 | CI runner core count | 2-core known; caps in-process speedup |

## Verdict

The diagnosis holds and is now measured, not inferred:

1. Both canonical execution paths are serial, and the profile path is additionally
   fail-fast, so one failure erases the diagnosis of everything after it.
2. The parallel executor is present, tested, and unwired; reusing it verbatim would
   regress evidence streaming, so the proven worker must be promoted into it.
3. `runtime/tests` is fully serial despite a pinned, working `xdist`.
4. Coverage revalidation emits 3 redundant executions on a 40-file boundary because
   dedup is absent and the `--out` path defeats command-string dedup.
5. `capture()` runs once per task and re-walks all of `backend/src` each time.