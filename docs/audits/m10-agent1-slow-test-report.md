# M10 Agent 1 — Slow-Test Report

## How these numbers were obtained, and what limits them

`pytest --durations` only prints at the end of a run, so a run that is killed yields nothing.
The repository already solves this: `runtime/foundation/verification/pytest_progress.py`
(`TestProgressTracker`) appends one JSON event per test start and per phase report to
`runtime/generated/verification-progress/pytest-progress-<pid>.jsonl`, each carrying `ts` and a
per-phase `duration`. That is the same information `--durations` prints, available
incrementally.

All runtime per-test timings below were reconstructed from that evidence
(`/tmp/kilo/m10a1/BEFORE-progress.jsonl`, 459 events, pid 1265429) rather than from a completed
summary. Backend timings come from a completed `--durations=20` run.

### The binding limitation: this host cannot produce trustworthy wall times

| Fact | Value |
|---|---|
| Cores (`nproc`) | **4** |
| IDE background load during measurement | `cursor` at 39.9% + 24.6% + 13.5% + 3.0% + 0.9% + 1.1% |
| Concurrent test load | Agent 2 running `pytest tests/contract/ -n auto` (4 xdist workers) from its own worktree |
| Other | a `next-server` at ~24% CPU |
| Observed `loadavg_1m` during the first attempt | **15.54 – 18.17 on 4 cores** |

Consequence, stated plainly: **absolute wall times in this document are not comparable to any
other machine, and BEFORE/AFTER wall-time deltas across agents are meaningless.** A full
`runtime/tests` run reached 190/2,564 tests in ~16 min and was projected at ~3.6 h, versus the
~29 min the suite documents for itself (`runtime/tests/conftest.py:19`, "This suite takes ~29
minutes") — a 7.5× inflation attributable to ~4× CPU oversubscription.

What *is* reliable and what I relied on:
- **Counts** (collected / passed / failed) — deterministic.
- **Per-test call durations** — the ranking and the order of magnitude of the offenders.
- **Relative structure** (which module dominates, how many subprocesses, how many scans).

A full clean BEFORE/AFTER wall-time pair for `runtime/tests` is **not** in this report, and I
am not going to present a contaminated number as if it were one. I asked the board to
serialize heavy runs; that request is logged as `board_97bffef5`.

## Runtime: where the ~29 minutes go

The five cost-dominant modules measured are **99.5% of the measured cost**
(1,242.5 s of 1,249.4 s call time across 114 tests).

| Module | Call time | Tests | Failed | Share |
|---|---:|---:|---:|---:|
| `test_m9_c55.py` | 686.40 s | 72 | 9 | 54.9% |
| `test_mutation_infra.py` | 242.69 s | 21 | 0 | 19.4% |
| `test_coverage_path_authority.py` | 230.32 s | 10 | 5 | 18.4% |
| `test_regression_suite.py` | 83.09 s | 7 | 0 | 6.7% |
| `test_mutation_edge_cases.py` | 6.85 s | 4 | 1 | 0.5% |

## Top 20 runtime tests by call phase

Setup/teardown are excluded — they are fixture cost, reported separately below.

| # | call (s) | total (s) | test | outcome |
|---:|---:|---:|---|---|
| 1 | 300.11 | 300.12 | `test_m9_c55.py::TestC55ReproducibilityExperiments::test_g22_coverage_measurement_structure` | failed\* |
| 2 | 299.98 | 299.98 | `test_m9_c55.py::TestC55ScenarioHarness::test_scenario_c_reproducible_coverage` | failed\* |
| 3 | 213.19 | 213.19 | `test_mutation_infra.py::test_r2_evidence_collected_with_target_config_active` | passed |
| 4 | 72.69 | 72.74 | `test_regression_suite.py::TestRegressionSuite::test_mutation_smoke_runs` | passed |
| 5 | 60.07 | 60.07 | `test_coverage_path_authority.py::…::test_coverage_run_from_subdirectory` | failed |
| 6 | 60.07 | 60.07 | `test_coverage_path_authority.py::…::test_coverage_clean_environment` | failed |
| 7 | 60.07 | 60.07 | `test_coverage_path_authority.py::…::test_coverage_run_resolves_from_backend_cwd` | failed |
| 8 | 30.07 | 30.07 | `test_coverage_path_authority.py::…::test_coverage_nonzero_pytest_exit` | passed |
| 9 | 29.30 | 29.30 | `test_mutation_infra.py::test_smoke_end_to_end_distinguishes_classifications` | passed |
| 10 | 18.88 | 18.89 | `test_m9_c55.py::…::test_scenario_a_same_env_same_backend_evidence` | passed |
| 11 | 14.79 | 14.82 | `test_m9_c55.py::TestC55EnvironmentContract::test_g5_all_python_tools_match_pins` | failed |
| 12 | 10.38 | 10.50 | `test_m9_c55.py::TestC55DriftExperiments::test_experiment_e_config_drift_detected` | passed |
| 13 | 10.02 | 10.03 | `test_coverage_path_authority.py::…::test_coverage_artifact_missing_no_crash` | passed |
| 14 | 10.02 | 10.04 | `test_coverage_path_authority.py::…::test_coverage_malformed_scope` | failed |
| 15 | 7.60 | 7.60 | `test_m9_c55.py::TestC55DriftExperiments::test_experiment_f_dependency_drift_detected` | passed |
| 16 | 4.70 | 4.70 | `test_mutation_edge_cases.py::test_incremental_mutation_with_no_coverage` | passed |
| 17 | 4.13 | 4.14 | `test_m9_c55.py::TestC55ControlPlaneEnforcement::test_control_plane_refuses_incompatible_env` | passed |
| 18 | 4.08 | 4.09 | `test_regression_suite.py::TestRegressionSuite::test_verify_plan_backend` | passed |
| 19 | 3.87 | 3.88 | `test_m9_c55.py::TestC55EnvironmentContract::test_g5_npm_matches_pin` | passed |
| 20 | 3.63 | 3.64 | `test_m9_c55.py::TestC55ControlPlaneEnforcement::test_control_plane_allows_consistent_env` | passed |

### Read the two 300 s rows correctly

\* **These two are my measurement artifact, not a baseline defect.** Both terminate at
~300.0 s because *I* passed `--timeout=300`; the suite's own budget is lower
(`run_runtime_verification.sh` uses `--timeout=30`, and `test_m9c66_repeatability.py:70-85`
documents raising one test to 180 s "to the same 180 s bound the rest of the suite already
uses"). They are also the *nested-pytest* tests, so their true cost is the full re-execution of
the modules they spawn. Their `failed` outcome is my cap firing, and I do not count them as
genuine failures.

The 60 s rows, by contrast, are genuine: `test_coverage_path_authority.py` passes
`max_runtime=60` to `_coverage_run` itself, and three tests hit it exactly.

## Backend: top 20 by call phase

From a completed run of `unit/ + properties/ + invariants/`: **3,556 passed, 1 xpassed,
0 failed, 200.65 s** (wall 204.67 s).

| # | phase | seconds | test |
|---:|---|---:|---|
| 1 | call | 8.37 | `unit/orchestration/test_statement_orchestrator_persistence.py::test_migration_004_idempotent` |
| 2 | call | 7.60 | `…test_statement_orchestrator_persistence.py::test_has_errors_true_when_stage_fails` |
| 3 | call | 7.16 | `…test_statement_orchestrator_persistence.py::test_has_errors_false_on_full_success` |
| 4 | call | 6.61 | `invariants/test_reconciliation_properties.py::test_deterministic_matching_property` |
| 5 | call | 6.45 | `invariants/test_reconciliation_properties.py::test_no_cycles_property` |
| 6 | call | 6.12 | `invariants/test_reconciliation_properties.py::test_bipartite_matching_property` |
| 7 | call | 5.17 | `unit/core/db/test_migration_registry.py::test_m001_idempotent_same_connection` |
| 8 | call | 4.88 | `…test_migration_registry.py::test_unapplied_migration_runs_exactly_once` |
| 9 | **setup** | 4.69 | `unit/engines/ledger/test_ledger_engine.py::TestValidateLedgerIntegrity::test_passes_clean_ledger` |
| 10 | call | 4.51 | `properties/credit_cards/test_engine_properties.py::…::test_emi_detection_returns_none_for_random` |
| 11 | call | 3.55 | `invariants/test_reconciliation_determinism.py::test_edge_cases_property` |
| 12 | call | 3.42 | `invariants/test_reconciliation_properties.py::test_match_uniqueness_property` |
| 13 | call | 3.38 | `…test_migration_registry.py::test_m003_backfill_populates_v2_without_touching_content` |
| 14 | call | 2.76 | `invariants/test_reconciliation_determinism.py::test_match_uniqueness_property` |
| 15 | call | 2.35 | `…test_reconciliation_determinism.py::test_deterministic_matching_property` |
| 16 | call | 2.02 | `…test_reconciliation_determinism.py::test_no_cycles_property` |
| 17 | call | 2.02 | `…test_reconciliation_determinism.py::test_bipartite_matching_property` |
| 18 | call | 1.41 | `invariants/test_reconciliation_properties.py::test_edge_cases_property` |
| 19 | **setup** | 1.18 | `invariants/test_reconciliation_determinism.py::test_deterministic_matching` |
| 20 | call | 1.16 | `unit/repositories/test_account_balance_repository.py::test_get_balance_history` |

### Backend is well behaved — and the reason matters

Only **2 of 3,557** backend tests exceed 5 s, and the tail is flat. The cause is a deliberate
prior refactor recorded in `backend/tests/fixtures/MIGRATION_NOTES.md`: autouse per-test
seeding was removed, the schema is built **once per session** into
`_pristine_db_template` (`fixtures/database.py:94-120`) and each test `shutil.copy2`s that file
(~0.001 s) instead of re-running `create_all()` + migrations (~4.4 s). Documented as
~4.4 s → ~0.15 s per test.

`MIGRATION_NOTES.md` also records that optimisation *worked*: reconciliation engine went
76.78 s and service tests 109.29 s **before**, and today the whole
`unit + properties + invariants` slice is 200.65 s. The two slow groups that remain are both
**property/integration** work, not fixture overhead.

## Fixture cost is already well managed — do not "optimise" it

| Fixture | Scope | Assessment |
|---|---|---|
| `_pristine_db_template` | session | Correct. Single DDL+migration pass, copied per test. |
| `finance_db` / `temp_db` / `db_path` | function | Correct. `copy2` of the template, cleanup in `finally`. |
| `seeded_db` | function, **not** autouse | Correct. Opt-in, canonical connection, no PRAGMA. |
| `reset_global_registry` (`runtime/tests/conftest.py`) | function, autouse | Called twice per test (pre + post) for 2,564 tests = ~5,128 calls. `reset_registry()` is cheap; measured cost is not in the top 20. Leave it — the autouse reset is what keeps the global registry from leaking across tests. |
| `isolated_registry` | function | Builds a full YAML config + `VerificationRegistry` per test, including a redundant `config_path.write_text(json…)` immediately followed by `config_path.write_text(yaml.dump(config))` (conftest.py:246-252). The JSON write is dead. Minor, and only for tests requesting the fixture. |

## Remaining slow groups, ranked by value

1. **`test_m9_c55.py` — 686 s, 55% of measured cost.** Dominated by recursive nested pytest:
   `test_g30_regression_green` (line 951) re-runs `test_m9_c52.py`, `test_m9_c53.py` and
   `test_m9_c54.py` wholesale, and lines 129/503/517 do more. `progress.md` item A measured this
   class at 386.66 s — 34% of a ~1,800 s run. **The fix is a behavioural rewrite of
   certification-gate assertions, which the standing constraints forbid me to do blind.
   Highest-value item for an owner who can authorise it.**
2. **The four identical coverage runs — 240 s, 18% of measured cost.**
   `test_coverage_path_authority.py` calls `_coverage_run(scope="tests/unit/engines/credit_card",
   max_runtime=60)` four times (lines 53, 64, 132, 140) and asserts identical properties each
   time, while the test *names* promise four different invocation contexts
   (`…from_backend_cwd`, `…from_subdirectory`, `…clean_environment`, `…ci_like_environment`)
   that **no body establishes** — none chdirs or patches `os.environ`. So it is either 240 s of
   pure duplication or a real coverage gap. A cache fixture would entrench whichever it is;
   adding the missing context variation costs more time. **Needs an intent decision, not a
   unilateral fix.**
3. **Duplicated reconciliation property coverage — ~36 s, 18% of the backend slice.**
   `invariants/test_reconciliation_properties.py` and
   `invariants/test_reconciliation_determinism.py` share 311 identical lines and both define
   the same 5 properties. **Not a deletion** (see below) — they differ in `max_examples`
   (10 vs 5) and one is the pre-fix variant.
4. **`test_mutation_infra.py::test_r2_evidence_collected_with_target_config_active` — 213 s,
   one test.** A single test worth 19% of measured runtime. Uninvestigated in depth; it is the
   largest single-test outlier in the suite and the obvious next profiling target.
5. **`test_regression_suite.py::test_mutation_smoke_runs` — 72.7 s.** Runs a real
   `runtime.verify mutation --smoke` campaign. The test's own `timeout=60` is *below* the 600 s
   smoke budget in `mutation_runner.py:252`, so this test is close to a latent flake on a slow
   host.

### Why the two reconciliation invariant files were NOT merged or deleted

Byte-comparison of the 5 shared property tests found them **not** identical:

| Property | `max_examples` | Isolation fix |
|---|---|---|
| `test_match_uniqueness_property` | 10 vs 5 | both present |
| `test_deterministic_matching_property` | 10 vs 5 | both present |
| `test_no_cycles_property` | 10 vs 5 | both present |
| `test_bipartite_matching_property` | 10 vs 5 | both present |
| `test_edge_cases_property` | 5 vs 10 | **only in the determinism file** |

`test_reconciliation_determinism.py` additionally defines `populated_db` and a sixth test,
`test_deterministic_matching`, so it is a superset *in file count* — but
`test_reconciliation_properties.py` runs **twice as many examples** on four of the five
properties. Deleting either file would change the statistical strength of a money-representation
property test. That is a reduction in meaningful coverage, so neither was removed.

What *was* fixed, and it is a genuine defect: inside
`test_reconciliation_properties.py`, four of the five property tests call
`reconciliation_db = _fresh_reconciliation_db(_pristine_db_template)` (lines 112, 155, 208, 249)
and `test_edge_cases_property` did not. `_fresh_reconciliation_db`'s own docstring explains why
this matters — Hypothesis reuses one function-scoped fixture for every example, so rows
accumulate in an append-only `transactions` table (whose `StatementRepository` trigger refuses
`DELETE`, correctly, for a financial ledger) and a later example collides on
`UNIQUE (statement_id, date, description, amount_paise, sequence_num)`. The sibling file already
had the fix. Applied the same pattern to the one test missing it, keeping `max_examples`
unchanged. **Strictly additive: same examples, same assertions, isolation per example.** Both
files: 11 passed.
