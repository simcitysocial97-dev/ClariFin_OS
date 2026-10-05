# M10-R3 — Checkpoint A: Forensic Execution Graph & Failure Reproduction

**Date:** 2026-10-04
**Branch:** `m11/parallelism-correctness` @ `1c39736`
**Status:** Phase 1 + Phase 2 complete. No runtime or workflow behaviour changed.
**Host used for reproduction:** 4 vCPU / 7 GiB RAM, `.venv` per `AGENTS.md`.

---

## 0. Executive summary

The supplied M10-R3 report identifies a real seam but **four of its load-bearing
premises are false against this repository**, and the two failures it asks us to
diagnose have **different root causes than reported**.

| Plan premise | Verdict | Evidence |
|---|---|---|
| "`ParallelExecutor` is genuinely dead" | **False** | `parallel_executor.run_streaming_command` was promoted in M10-R2 and is the shared worker for *every* canonical path. Only the `ParallelExecutor` *class façade* is legacy. |
| "`verify run --plan` genuinely discards supplied plans" | **False** | `control_plane_facade.py:662-663` executes the supplied plan; `:631-636` explicitly refuses to regenerate. |
| "plan serialization must be implemented" | **False** | `m9-c49-execution-plan/v1` already round-trips (`to_dict`/`from_dict`) and is used in CI today. |
| "`required_environment` is inert" | **True** | Confirmed: 2 reads, both in `to_dict()`. `verify_prerequisites` reads `t.prerequisites` only. |
| "six of eight execution conditions are unowned" | **Understated** | There are **twelve**, and the worst one is not in the report: **five of six verification topologies never construct a plan, never fingerprint, and never certify.** |
| "reconcile failure: 409 s CI vs 30 s local" | **Misframed** | 409 s is a *job* wall-clock (bootstrap 287 s + a killed run). 30 s is not reproducible; isolated `exec-0004` costs **106 s** of pytest. |

**The actual architectural failure is not an unmodelled "execution envelope".**
It is that **certification semantics exist in exactly one of six execution
topologies.** `verify check` / `verify run` have a plan, a fingerprint
anti-tamper invariant, an authorization gate and a 7-value `FinalDecision`.
The other five — every profile alias, every obligation leg, every runtime
shard, every Playwright leg, and mutation — run the *same* subprocess worker
with **no plan, no fingerprint, no gate, and a verdict of "first non-zero exit
code"**, then hard-code `final_decision="certified"` into the event log.

An execution envelope would not fix that. Consuming CI topology from a
runtime-generated plan would *entrench* it.

---

## 1. Canonical entry points (§1.A of the mission)

`python -m runtime.verify` → `control_plane_facade.main` (`:2175`). One dispatcher.

Legend: **RS** = `parallel_executor.run_streaming_command`; **SR** = bare
`subprocess.run`; **INPROC** = no subprocess.

| command | handler | planner | executor | spawn | fingerprint | certification |
|---|---|---|---|---|---|---|
| `check` | `facade:2738` → `ControlPlane.check:179` | `ControlPlanePlanner.plan` ×**2** (`:238` dead, `:246` live) | `ExecutionOrchestrator.execute` | RS | **YES** | **YES** (`_finalize:2381`) |
| `run` | `facade:2837` → `ControlPlane.run:568` | supplied plan, else `build_execution_plan` | `ExecutionOrchestrator.execute` | RS | **YES** | **YES** |
| `run --aggregate` | `facade:2850` → `_aggregate_shard_reports:1225` | none (reads `plan.json`) | none | none | no | inherited |
| `run --profile P --task/--verify-legs` | `facade:2917` → `run_profile_fanout:1072` | `profiles` static list | `profile_tasks.run_obligation_leg:289` | RS | **NO** | own gate |
| `run --profile runtime --shard` | `facade:2900` → `run_test_shards:922` | `runtime_shards` | `runtime_shards.run_test_shard:358` | RS | **NO** | own gate |
| `plan` (default) | `facade:447` | `ControlPlanePlanner.plan` | **none** | none | no | no |
| `plan --shard-matrix/--shard-plan` | `facade:526-556` | `build_execution_plan` | none | none | no | no |
| **aliases** `quick\|backend\|frontend\|contracts\|graph\|full\|runtime\|golden\|playwright\|api-contracts` | `facade:2446` `_run_profile_alias` | **none** | **none** (direct loop `:2586`) | RS | **NO** | **NO — first non-zero exit** |
| `runtime-shard` | `facade:2343` | `build_test_shards` | `run_test_shard` | RS | **NO** | no |
| `runtime-aggregate` | `facade:2390` | none | none | RS (gate integrity `:3183`) | no | no |
| `backend-task` / `backend-aggregate` | `facade:2396/2394` | none | `run_obligation_leg` | RS | **NO** | no |
| `playwright-plan` / `playwright-aggregate` | `facade:2318/2386` | `playwright_shards` | legs via `run --profile playwright --task` | RS | **NO** | no |
| `strengthen` (`mutation`) | `facade:1395` → `mutation_runner` | mutation_runner | mutation_runner | **SR** (own engine `mutation_runner.py:761`) | own `_MutationSafety` | separate `mutation-trust` |
| `certify` | `facade:1563` → `certification.main:425` | none | none | INPROC | no | **the gate** |
| `ci` | `facade:1571` → `_run_reconcile_cli:1723` | reads manifest | none | none | no | reconciliation |
| `doctor`, `diagnose`, `inspect *`, `mutation-plan/-aggregate/-trust`, `measurement coverage`, `env-check` | various | none/bypass | none | INPROC/SR | no | no |

### Dead and misrouted surfaces found

| Finding | Evidence |
|---|---|
| `verify status` **is literally `verify doctor`** — `args` discarded. 18 CI call sites rely on this. | `canonical_control_plane.py` `migration_map` → `facade:2268` → `:1871` |
| `verify integrity` → `doctor`, but `.github/scripts/run_runtime_verification.sh:44` and `facade:3183` both expect an **integrity scan**. | same |
| `forensic_cli.py` (8 entry points) and `diagnostic_agent.py` (the whole `Uncertainty`/`Explainability`/`CERTIFIABLE` vocabulary) are **unreachable from the CLI**. Legacy `forensic-diagnose`/`forensic-report` are rewritten to `diagnose`. | zero importers in the facade |
| `verification/cli/cli.py` is an orphan click CLI, not wired to `python -m runtime.verify`, no console script, and calls bare `python3` with **no timeout** (`:462,473,490`). | — |
| `cli_surface.py` is a near-duplicate `canonical_control_plane.py` with a **materially different** `_CLASSIFICATION`; imported only by 2 tests. | — |
| `help_resolver.py` has zero importers; `verify help-resolve` routes to `plan`. | — |
| `executor_pipeline.py` (2280 lines) — named in the facade docstring as part of the execution stack — is **not on any live execution path**. Its only subprocess boundary is reached solely from the unreachable `forensic_cli`. | `executor_pipeline.py:1692` |
| `ExecutionOrchestrator.build_execution_plan` is **not a separate planner** — it calls the same `ControlPlanePlanner.plan` (`:824-832`). So `verify check` resolves capabilities **twice per run**, and the first result (`_obligations`, `facade:241-243`) is **never read**. | — |
| The `ControlPlanePlan` (C48) is a **dead output on every executing path**. | — |

---

## 2. Process-spawn inventory (§1.B of the mission)

**137 production spawn sites** in `runtime/` (excluding `generated/`, `tests/`).
Full table: this audit's working notes; the material partition:

### 2.1 The canonical worker (1 site)

`parallel_executor.py:297` — `subprocess.Popen(shell=True, start_new_session=True,
stdout/stderr=PIPE)` inside `run_streaming_command` (`:240`). Provides
preflight-free spawn, tee-to-file evidence, heartbeat, process-group kill,
`classify_termination`, `CommandResult`.

Callers: `execution_orchestrator.py:1974` (check/run), `profile_tasks.py:331`
(obligation legs), `runtime_shards.py:422` (runtime shards),
`control_plane_facade.py:2525` (profile aliases), `:3183` (runtime integrity),
`parallel_executor.py:758` (legacy façade).

### 2.2 Competing engines that execute verification obligations

| engine | site | verdict |
|---|---|---|
| `Executor._execute_once` | `executor.py:204` | Full duplicate: own `Popen`, own `_tee`, own `_kill_process_group`, own result dir, own retry loop, **no `ProgressContext`**. Reached from `orchestrator.py:1137`, `execution/dispatcher.py:111`, `executor_pipeline.py:1692` — **none reachable from the CLI**. |
| `archive/orchestration/orchestrator.py:980` | buffered twin of the canonical worker | archived |
| `mutation_runner.execute_mutation` | `mutation_runner.py:761` | **Distinct by necessity** — mutmut manages its own child tree and source restoration. But it has **no heartbeat, no progress, no `--result-out`**, and its budget table (`DEFAULT_RUNTIME`, `:259-264`) **disagrees with `mutation_execution/orchestrator.py:60-64` by 5× (`smoke`) and 7× (`target`)**. |
| `MutmutAdapter._run_with_isolation` | `mutation_execution/mutmut_adapter.py:623` | second mutmut engine, no progress |
| `coverage_truth.py:144`, `coverage_measurement.py:159` | two coverage runners |
| `certification.py:61`, `c53_certification.py:85`, `regression.py:34`, `candidate_validation.py:173,256`, `convergence_pipeline.py:1193`, `symbol_resolver.py:360`, `typescript_symbol_resolver.py:241,527`, `test_strengthening_pipeline.py:126` | 11 further pytest/mutmut runners with bare `python`/`python3`, no cwd, no env, `shell=True` in one case |

### 2.3 Infrastructure sites

~100 `git rev-parse` / `git status` / `git diff` / tool-version probes. **Legitimate**
meta-operations. Note: **8 of them have no timeout** (`env_contract.py:210`,
`verification_contract.py:100,114`, `execution_enforcer.py:166,178`,
`certification.py:415`, `blast_radius.py:515`, `cli/cli.py:516+`).

### 2.4 Answer to "where is the one authoritative spawn point?"

> **`parallel_executor.run_streaming_command` is the one authoritative spawn
> point for every canonical path, and it already is one.** The report's
> proposal to make it so is already implemented.
>
> The real defect is the **six** engines that bypass it (`executor.py:204`,
> `mutation_runner.py:761`, `mutmut_adapter.py:623`, the 11 ad-hoc runners), and
> — far more seriously — the **six topologies that use the canonical worker
> while holding none of its callers' semantics**.

---

## 3. Execution-condition inventory (§1.C of the mission)

The report lists eight. There are **twelve**, and the three it omits are the
expensive ones.

| # | condition | owner | modelled? | status |
|---|---|---|---|---|
| 1 | what must run | runtime plan | yes | correct |
| 2 | command + cwd | runtime | yes | correct |
| 3 | repository paths (prereqs) | `verify_prerequisites:1479` | yes | **partial** — `:1495-1501` *skips* `.venv/git/mutmut/pytest/coverage` outright |
| 4 | **required env vars** | shell / YAML | **NO** | `required_environment` inert (2 reads, both `to_dict()`); no variable axis exists anywhere |
| 5 | **time budget** | YAML `timeout` | **NO** | three unrelated authorities (below) |
| 6 | **evidence transport** | YAML path lists | **NO** | 14 multi-path `upload-artifact` sites; `mutation.yml:513-517` hard-codes the reconstructed path `backend/tests/generated/mutation` |
| 7 | **liveness** | — | partly | heartbeat exists in `run_streaming_command` but **only when `progress_prefix` is set**; `verify check` never sets it (see §3.2) |
| 8 | evidence → verdict | runtime | yes | correct |
| 9 | **concurrency budget** | **nowhere** | **NO** | **omitted by the report; root cause of the reconcile failure (§4.1)** |
| 10 | **plan/leg identity + plan fingerprint binding** | partial | partly | `plan_fingerprint` preserved across shard narrowing (`facade:337`) — good; but **no runtime check that a leg's plan matches the aggregate's plan** beyond the shard JSON |
| 11 | **per-leg mutable state** | workflow env | **NO** | `FINANCE_DB_PATH` is per-leg, declared only in YAML (reconcile `:200`, playwright `:146`) — and is the *one* env var that silently determines correctness |
| 12 | **fixture authority** | **nowhere** | **NO** | **omitted by the report; root cause of the Playwright failure (§4.2)** — two competing seeders, one hard-coded |

### 3.1 Timeout model — three authorities, no runner coupling

| scope | value | source |
|---|---|---|
| `ExecutionTaskSpec.timeout_seconds` | `max(60, 2×estimated)`, else 900 | `_timeout_for:1452-1460` |
| revalidation literals | 1200 / 1800 | `:1105, :1143, :1217` |
| profile alias + **every obligation leg** | **flat 3600** | `control_plane_facade.py:2443` |
| runtime shard | 2400 | `runtime_shards.py:365` |
| mutation (declared) | 1200 | `:1105` |
| mutation (enforced) | `DEFAULT_RUNTIME["target"] = 4200` | `mutation_runner.py:725` |

- `facade:2434` docstring claims `max(600, 2 × task.estimated_duration)`. **`:2443` returns a constant `3600`.** The per-task estimate is never consulted — so every leg gets a 3600 s ceiling regardless of whether it needs 5 s or 40 min.
- **No code anywhere reads a CI job `timeout-minutes`.** `infrastructure_timeout` exists only as a mutation vocabulary label (`mutation_execution/domain_model.py:55`) with no executable path. The backstop-vs-budget relationship exists solely as `assert backstop > 60` in two tests.
- `timeout_seconds` is `str()`-ed into `plan_fingerprint` (`:1394`) with **no unit validation and no upper bound**.

### 3.2 The observability asymmetry (found during reproduction)

`run` sets `progress_prefix` (`facade:754-772`); **`check` does not**. So on every
`verify check` task `ProgressContext` is `None` and the runtime emits **no
start/heartbeat/exit lines at all**. The live-log capability added in M10-R2
exists on the shard path and not on the main path.

### 3.3 The timeout unit bug — **already fixed**

`verification-reconcile.yml:274` reads `timeout "${SHARD_TIMEOUT_MINUTES:-85}m"`.
The `m` suffix and the explanatory comment (`:270-273`) are on disk, added by
`30042d6c`. The plan's "Stage 2" (§3.3) describes a defect that no longer exists.
Three bare-number GNU `timeout` calls remain (`runtime.yml:191`, `backend.yml:167`,
`playwright.yml:194`) — correct only because the variable names end `_SECONDS`.

---

## 4. Failure reproduction (§2 of the mission)

### 4.1 Reconcile / `exec-0004` — **NOT a timeout-unit failure**

Method: `verify plan --shard-matrix --shard-count 7` → `plan --shard-plan` →
`verify run --plan … --shard 6 --shard-count 7 --result-out …`, exact CI env.

Plan `execplan-2c8aa6c390d3`, 14 tasks, `repository_sha 1c39736`, shard 6 =
`exec-0002, exec-0003, exec-0004, exec-0009, exec-0021`.

| task | kind | declared `timeout` | declared `est` | **actual** | term | verdict |
|---|---|---|---|---|---|---|
| exec-0009 | capability | 900 | **0** | 0.0 s | EXIT_NONZERO | **an `echo` string is a mandatory obligation** |
| exec-0004 | property | 600 | 300 | **125.6 s** | EXIT_ZERO | **PASS** |
| exec-0002 | contract | 360 | 180 | **180.3 s** | EXIT_NONZERO | 4 real contract-test ERRORs |
| exec-0003 | unit | 3600 | **60** | **352.2 s** | EXIT_NONZERO | **`black` formatting gate** |

**Causal mechanism, established by measurement:**

1. `exec-0004`'s pytest self-reports `78.47 + 5.12 + 22.81 = 106.4 s`
   (`exec-0004-stdout.log`). **The report's "30 s local" is not reproducible —
   the true isolated cost is ~106 s.** The 30 s figure is unfounded.
2. The executor ran `exec-0002`, `exec-0003`, `exec-0004`, `exec-0009`
   **concurrently** (`DEFAULT_MAX_WORKERS = 4`), but the shard planner
   estimated `1741 s` — a **sum**, i.e. it assumed serial execution.
3. **Two of those three concurrent tasks fork their own worker pools:**
   `run_contract_tests.sh:78` passes `-n auto`, `run_fast_checks.sh:89` passes
   `-n auto`. So shard 6 runs ~7 CPU-bound Python processes against 4 cores.
4. `exec-0002` consumed 180.3 s of a **360 s** budget while `exec-0003` — declared
   `est=60 s`, budget 3600 s — consumed 352.2 s. **The estimator is wrong by ~6×,
   and the budget is `2 ×` a wrong estimate.**
5. On a 2-vCPU GitHub runner the contention factor exceeds the 2× safety margin,
   so legitimate work is reclassified `TIMED_OUT`. That is the mechanism by
   which correct obligations become opaque CI failures.

**What the old `timeout 85` bug actually caused:** the *job* wall clock was
`bootstrap (287 s, measured at `setup-python-runtime/action.yml:64-68`) +
85 s kill + browser install + upload ≈ 409 s`. The report compares that
**job-level** number against a **task-level** number. The comparison is
meaningless; the underlying defect (85 s instead of 85 min) was real and is
already fixed.

**Additional defect proven by this run:** I killed the leg at 900 s while
`exec-0021` (mutation) was still running. **No `--result-out` file was written
and no terminal result was recorded** — the aggregate would classify this as a
missing-result infrastructure failure with no way to distinguish "killed" from
"never ran". `LEG_RESULT_SCHEMA` (`facade:3013`) is only written on handled exit
paths (`facade:783, 807`); SIGKILL bypasses all of them.

### 4.2 Playwright visual — **NOT baseline drift alone**

Three stacked causes plus three latent harness defects. The dominant one is
proven by reading the baseline pixels.

1. **Baselines were captured against the wrong database (class 1, high confidence).**
   `transactions-page-chromium-linux.png` renders *"Test Transaction 1/2/3 —
   1 Jan/1 Feb/1 Mar 2025 — ₹1,000/₹500/₹1,500"*. Those are literally the three
   rows written by `frontend/tests/global-setup.ts:274-282`, which
   **`seedTestData()` writes to a hard-coded `backend/data/finance.db` and
   ignores `FINANCE_DB_PATH` entirely.** CI seeds a *different* file
   (`backend/data/e2e-<leg_id>.db`) via `tools/e2e_seed.py` — 27 rows, 6 months.
   Two competing fixture authorities; the visual pass reads the one nobody re-seeds.
   This alone accounts for the bulk of the 11.
2. **Three tests have no baseline at all (class 8).** `mode-toggle`,
   `empty-state`, `upload-modal` are absent for **both** projects in
   `frontend/tests/e2e/specs/visual-regression.spec.ts-snapshots/`.
   `mode-toggle-*.png` exists only in `frontend/tests/e2e/snapshots/` — a
   directory Playwright **never reads**, because no `snapshotPathTemplate` is
   configured. Four branch commits (`f5d49d04`, `d2f6cd46`, `512a400a`,
   `dee94146`) regenerated baselines into that dead tree and could not have
   affected CI.
3. **The suite is non-deterministic independently of any change (classes 4/5/6).**
   `frontend/components/os-shell/timeline-rail.tsx:29-36` places a playhead at
   `(dayOfYear/365)%` of a **fixed footer bar rendered on every financial route**.
   Day drift ≈ 600-900 differing px against `MAX_DIFF_PIXELS = 500`; month
   rollover ≈ 1100 px. `playwright.config.ts` sets **no `expect.toHaveScreenshot`**
   → `animations` defaults to `'allow'`, and neither Recharts chart disables
   `isAnimationActive` (1500 ms default). `locale`, `timezoneId`, `colorScheme`,
   `reducedMotion` are all unpinned; no `await document.fonts.ready`.
   `retries: CI ? 2 : 0` then re-diffs against moving pixels.
4. `visual-regression.spec.ts:105-107` calls `setViewportSize({1280,720})` in
   `beforeEach`, **destroying `mobile-chrome`'s Pixel 5 emulation** for 19 of 24 tests.
5. 4 of the 10 snapshotted "pages" (`/analytics`, `/categories`, `/import`, `/`)
   are **redirect aliases**; `analytics-page-*.png` is pixel-identical to
   `dashboard-page-*.png` (85107 B each) and `categories-page` to `settings-page`.
   The spec asserts dead deep links.

**Consequence:** regenerating baselines *now* would produce a set that passes once
and rots on the next day boundary. Items 1-4 must land first.

---

## 5. Challenge to the proposed architecture (§3 of the mission)

| # | Question | Answer |
|---|---|---|
| 1 | Is an "execution envelope" the smallest correct missing abstraction? | **No.** The smallest correct missing abstraction is **`FinalDecision` + `RepositoryFingerprint` applied uniformly**. An envelope is a *transport* concern; the defect is a *certification* concern. An envelope delivered first would produce runtime-generated CI topology that still reports "certified" for work that was never fingerprinted. |
| 2 | Can `required_environment` be repaired cleanly? | **Yes**, and cheaply. It has exactly **2 readers** and **25 assignments**, all on two near-identical `ExecutableVerificationTask` copies. Add a variable axis to `verify_prerequisites` and the field becomes real. But note: **the field is on a class that no execution path uses** — `verify_prerequisites` operates on `ExecutionTaskSpec`. Repairing it on the wrong class would create a *third* inert abstraction. It must move to `ExecutionTaskSpec` (which has `prerequisites`) or be deleted. |
| 3 | Can `ParallelExecutor` become the canonical executor? | **Already is** (`run_streaming_command`). But `ParallelExecutor` the *class* and `executor.Executor` are two competing façades with no CLI route → **delete**, keep the module. |
| 4 | Can local and CI execute the same serialized description? | **Yes for `check`/`run` today** — `m9-c49-execution-plan/v1` + `--shard`/`--shard-count` + `--result-out` already does exactly this, and `run --aggregate` reads it back. **No for the other five topologies**, which have no plan at all. |
| 5 | Does the workflow still need to know env/artifact paths/timeouts/report parsing/commands? | **It should not**, and today it does: 5 hand-written `timeout` wrappers, **5 distinct per-leg budget variable names, 0 declared**, 14 multi-path artifact uploads, ~28 jq/grep parse sites, 5 copies of the matrix-projection jq, 6 copies of the transport-diagnostic step. |
| 6 | Can the runtime emit the matrix the CI consumes? | **Yes, and it already does** for all five topologies. The remaining YAML duplication is the *jq projection* and the *heredoc emission*, which are pure copies of one another. |

### The load-bearing reframe

The plan's §3.5 target shape is:

```
plan → runtime-generated execution units → matrix → execute one unit → aggregate → certification
```

That is architecturally right, and it is **already 80% built** for the reconcile
topology and **0% built** for the other four. The genuine gap is that
`finalize`/`certify` sits in exactly one of six places.

---

## 6. Evidence integrity: what is real and what is theatre

| invariant | status | evidence |
|---|---|---|
| repository fingerprint | **real but narrow** | `RepositoryFingerprint.capture:244-271` covers HEAD + `backend/src/**/*.py` + 2 pyproject files + 3 tool versions. **No dirty flag, no untracked notion, no `backend/tests`, no `frontend`, no workflows, no `verification.yaml`.** |
| mismatch ⇒ fatal | **YES** | `:1889` `CompletionState.SCOPE` → `:2399-2403` `VALIDATION_BLOCKED`. No warn branch. |
| once around fan-out | **YES, asserted** | `:1470` + `:1868`; `test_parallel_execution.py:401` `capture() called 2 times for 5 tasks`. Correct design. |
| **coverage of topologies** | **1 of 6** | single call site `:1760`. Aliases, obligation legs, runtime shards, Playwright legs, mutation and all aggregates have none. |
| mutation safety | real but SIGKILL-vulnerable | `mutation_runner.py:202-251` restores via `atexit` + SIGTERM/SIGINT only. **SIGKILL bypasses both**, leaving `backend/pyproject.toml` changed → next capture mismatches → `VALIDATION_BLOCKED` on an all-green run. Observed live, recorded at `runtime/tests/conftest.py:52-55`. |
| `prerequisites_satisfied` | **hard-coded `True`** | `execution_orchestrator.py:2522` |
| terminal result on death | **absent** | SIGKILL writes nothing (§4.1) |
| CodeQL / SHA pins / artifact integrity | intact | `validate_actions.py:264-286`; all 26 checkouts SHA-pinned; `security-codeql.yml` `permissions` justified `:27-33` |

---

## 7. Coverage duplication (§8 of the mission)

In the reproduced plan there are **two** coverage obligations:
`exec-0010` = `measurement coverage tests/unit/engines`,
`exec-0011` = `measurement coverage .`, both `timeout 1800`, `est 1800`,
`is_mandatory=False`. The report's "seven identical coverage tasks" were not
observed in this plan; the duplication to investigate is **the whole-backend
run subsuming every narrower run**. Both write into the same
`runtime/generated/m9-c49/measurements/` namespace. This is a planner-level
collapse candidate, deferred to Checkpoint D pending measurement.

---

## 8. Answer to the mission's closing question, as of Checkpoint A

> *If the next CI failure occurs in six months, will the runtime itself tell us
> exactly what failed, under what execution conditions, why it failed, where its
> evidence is, and how to reproduce that exact obligation locally?*

**No.** And the reason is now precisely located:

- "under what execution conditions" — **no**; env vars are not modelled at all
  (`required_environment` inert, `:1479` reads a different field);
- "why it failed" — **partly**; termination classification is good
  (`EXIT_ZERO`/`EXIT_NONZERO`/`TIMED_OUT`) but `verify check` emits no live
  progress (`:3.2`), so the first 200 s of a 400 s failure are invisible;
- "where its evidence is" — **no**; the runtime does not know its own artifact
  root, so 14 workflows each hand-maintain the LCA contract, and
  `mutation.yml:513-517` hard-codes a path that only exists because of an
  unrelated upload's shape;
- "how to reproduce locally" — **yes for `check`/`run`**, no for the other five
  topologies;
- and, underlying all four: **five of six topologies can report "certified"
  without ever capturing a fingerprint.**

---

## 9. Evidence produced by this checkpoint

| artefact | path |
|---|---|
| execution plan | `/tmp/m10r3/plan.json` |
| shard matrix | `/tmp/m10r3/plan-matrix.out` |
| per-task evidence | `runtime/generated/m9-c49/logs/execplan-2c8aa6c390d3/exec-000{2,3,4,9}-{stdout,stderr}.log` |
| reproduction stderr (live heartbeat lines) | `/tmp/m10r3/shard6.err` |

Host: 4 vCPU / 7 GiB. Reproduce with the commands in §4.1.

---

## 10. ADDENDUM — a predicted defect, reproduced live during this checkpoint

§6 predicted: *"SIGKILL bypasses both [`atexit` and the SIGTERM/SIGINT handlers],
leaving `backend/pyproject.toml` changed → the next capture mismatches →
`VALIDATION_BLOCKED` on an all-green run."*

**This happened, in this session, on this working tree.**

`verify run --plan … --shard 6` was executing `exec-0021`
(`verify mutation --target reconciliation_engine`). The leg was killed by an
external 900 s bound while mutmut held the tree. After the run:

```
$ git diff backend/pyproject.toml
-# Scope: credit_card_engine
-source_paths = ["src/engines/credit_card_engine"]
-also_copy = ["src"]
+# Scope: reconciliation_engine
+source_paths = ["src/engines/reconciliation_engine.py"]
+also_copy = ["src", "tests"]
     "tests/unit/engines/reconciliation",
     "tests/properties/reconciliation",
     "tests/capabilities/reconciliation"
```

`backend/pyproject.toml` is one of the **two files** in `config_hash`
(`execution_orchestrator.py:252-253`). So:

1. The mutation task was killed → restoration never ran.
2. `backend/pyproject.toml` is left rewritten.
3. Any subsequent `RepositoryFingerprint.capture()` mismatches `config_hash`.
4. `_check_fingerprint_integrity:1889` raises `CompletionState.SCOPE`.
5. `_finalize:2399-2403` returns **`VALIDATION_BLOCKED`** with the diagnostic
   *"scope or fingerprint mismatch detected — cannot certify"*.

**The verdict would name the wrong cause.** The real cause is *"a mutation task
was killed mid-flight and did not restore its toolchain config"*. The runtime
would instead report a repository-integrity failure — which is exactly the
opaque, misattributed CI failure class this milestone exists to eliminate.

Note the compounding factor: `exec-0021` declares `timeout_seconds=1200`
(`execution_orchestrator.py:1105`) but is executed by `mutation_runner`, whose
enforced budget is `DEFAULT_RUNTIME["target"] = 4200` (`mutation_runner.py:725`).
**The declared budget is not the enforced budget**, so the runtime cannot even
tell whether the task was killed by its own timeout or by something external.

Restored with `git checkout -- backend/pyproject.toml`. Working tree clean.

This is classified as a **genuine defect**, not runner-specific behaviour, and
it is now a Checkpoint B/C target: mutation toolchain restoration must be made
crash-safe (write-to-temp + atomic rename, or a pre/post toolchain-hash
comparison recorded in the task result), and the declared-vs-enforced budget
must be reconciled.
