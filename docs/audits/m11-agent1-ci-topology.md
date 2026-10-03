# M11 Agent 1 — CI Execution Topology, Caching, Required-Checks and Constitution

Baseline `origin/main` = `bfcf336b5b7f46e759c7486f3eb02d0f8d92e14b`.
M10 head (M11 starting point) = `c5c38b91ff61a8a3bfcaf64d8fd75c7a81680fac`.
All GitHub numbers in this document are measured, not estimated, unless the line
says `NOT MEASURED`.

---

## 1. Inventory

14 workflows, 20 jobs. Machine-extracted from the workflow tree, not read by eye.

| Workflow | Triggers | Job(s) | Check context | Runner | Timeout | Profile command |
|---|---|---|---|---|---|---|
| `api-contracts.yml` | push, PR, dispatch, workflow_run | `api-contracts` | API Contract Integrity Gate | ubuntu-latest | 5 | `runtime.verify contracts` |
| `backend-verify.yml` | push, PR, dispatch | `verify` | **Backend Verification (required)** | ubuntu-latest | 30 | `runtime.verify backend` |
| `dependency-update.yml` | schedule, dispatch | `dependency-health` | Dependency Updates | ubuntu-latest | 15 | — (scripts) |
| `frontend-verify.yml` | push, PR, dispatch | `verify` | **Frontend Verification (required)** | ubuntu-latest | 25 | `runtime.verify frontend` |
| `golden.yml` | schedule, dispatch | `golden` | Golden Dataset Regression | ubuntu-latest | 30 | `runtime.verify golden` |
| `m9-forensic-diagnostic-lab.yml` | PR | `diagnostician` | M9 Forensic Evidence Collection | ubuntu-latest | 20 | — (diagnostics) |
| `mutation-pr.yml` | PR (filtered) | `incremental-mutation` | Mutation Testing (PR Incremental) | ubuntu-latest | 15 | `runtime.verify mutation --incremental` |
| `mutation.yml` | schedule, dispatch | `mutation-smoke`, `mutation-plan`, `mutation` (matrix), `mutation-replay`, `mutation-aggregate` | Mutation Testing | ubuntu-latest | 15/10/90/15/15 | `runtime.verify mutation*` |
| `playwright.yml` | push, PR, dispatch | `test` (matrix: chromium, mobile-chrome) | E2E Tests (…) | ubuntu-latest | 90 | `runtime.verify playwright` |
| `quality.yml` | push, PR, dispatch | `quality` | Quality Gate | ubuntu-latest | 20 | `runtime.verify quick` |
| `release.yml` | release, dispatch | `build` | Build Release | ubuntu-latest | 30 | — (build) |
| `security-codeql.yml` | PR, push, schedule, dispatch | `analyze` | **Analyze (required)** | ubuntu-latest | 45 | CodeQL |
| `verification-reconcile.yml` | PR (filtered), dispatch | `reconcile-gate` | Plan / Execute / Reconcile | ubuntu-latest | 90 | `runtime.verify check` |
| `verification-runtime.yml` | push, PR, dispatch | `verify-runtime` | **Runtime Verification (required)** | ubuntu-latest | 60 | `runtime.verify runtime` |

---

## 2. The headline finding, stated honestly

**The nine PR-triggered workflows were already fully parallel, and the entire
workflow tree contained exactly two `needs:` edges — both inside the *scheduled*
`mutation.yml`.**

```yaml
mutation.yml:mutation          needs [mutation-smoke, mutation-plan]
mutation.yml:mutation-aggregate needs [mutation-plan, mutation]
```

That is the complete edge set. Measured from PR #16's head run
(`37016147xxx`): all nine workflows started between `13:54:23Z` and `13:54:24Z` —
a one-second spread. There was **no top-level `UNNECESSARY_SERIALIZATION` to
remove**, and M11 removed none, because none existed.

The real wall-clock levers were elsewhere, and they are addressed in §4–§7:

1. the Runtime Verification critical path (16m35s),
2. `.venv` construction repeated in all 15 jobs that bootstrap the runtime,
3. four workflows path-filtered in ways that could not see files they read,
4. Plan / Execute / Reconcile re-running work four other workflows already did.

---

## 3. Job dependency graph and edge classification

### 3.1 Pull-request surface (the pipeline that gates `main`)

```
                    ┌───────────────────────────┐
   pull_request ───▶│ 9 independent workflows  │   no needs: edges at all
                    │ all start within 1s      │
                    └─────────────┬─────────────┘
      ┌───────────┬───────────┬───┴───┬───────────┬────────────┬──────────┐
      ▼           ▼           ▼       ▼           ▼            ▼          ▼
  Backend     Frontend    Runtime  Quality     Analyze     API        E2E
  5m0s        3m49s       16m35s  3m9s        2m56s       Contract   7m1s
  ★required   ★required   ★req.              ★required   1m39s      6m29s
                                                       Forensic
                                                       3m33s
  Mutation (PR Incremental) — filtered to backend/src/{engines,services}, backend/tests
  Plan / Execute / Reconcile — filtered
```

**Edges: none.** Every one of these nine is a root. GitHub starts them
concurrently; nothing consumes another's output.

This is *correct*, not accidental — and it is the reason the two artifact-shaped
workflows that could have been wired together were deliberately left alone:

- `cross-layer-map`, `knowledge-index`, `verification-cache`,
  `engineering-history` are uploaded by five workflows
  (`backend-verify`, `frontend-verify`, `verification-runtime`, `golden`,
  `playwright`) with **matrix-disambiguated names** in `playwright.yml`
  (`cross-layer-map-${{ matrix.project }}`).
- **No job in the tree downloads any of them.** `actions/download-runtime` is
  used only by `mutation.yml` (`mutation-replay`, `mutation-aggregate`) for its
  own shard evidence, via `run-id`-scoped lookup of a prior run — never from a
  sibling job.

So those uploads are **ORDER_ONLY**: no consumer exists. They were **not**
removed, because removing them would delete an artifact contract that
`docs/ENGINEERING_ARTIFACTS.md` and the constitution's artifact-ownership table
both name, and doing so during a performance milestone is exactly the kind of
"optimisation by deletion" the brief forbids. Recorded here as a finding with a
recommendation, not acted on.

### 3.2 Scheduled mutation campaign (the only real DAG)

```
mutation-smoke ──┐
                 ├──▶ mutation (matrix: N shards) ──┐
mutation-plan ───┘                                  ├──▶ mutation-aggregate
   │                                               │
   └───────────────────────────────────────────────┘
```

| Edge | Class | Proof |
|---|---|---|
| `mutation-smoke → mutation` | `ENVIRONMENT_DEPENDENCY` | The shard job mutates real files. `mutation-smoke` proves mutmut is installed and executable in that same image before any shard is allowed to rewrite source. Removing it lets a broken toolchain produce N identical infrastructure failures instead of one. |
| `mutation-plan → mutation` | `DATA_DEPENDENCY` | The shard **matrix is computed by `mutation-plan`** and published as a workflow output. The shard job reads `matrix.shard`, `matrix.source_paths`. Without the plan job there is no matrix, so GitHub creates zero shard jobs — the exact failure M9-C72 documented, where the run concluded `failure` in 105s having measured nothing with no failing job to point at. |
| `mutation-plan → mutation-aggregate` | `DATA_DEPENDENCY` | The aggregate compares measured shards against `total_shards` to detect a missing shard. It reads the plan's `total` and `diff_safe`. |
| `mutation → mutation-aggregate` | `ARTIFACT_DEPENDENCY` | Each shard uploads `mutation-summary-${{ matrix.shard }}.json`; the aggregate downloads the `mutation-shards-*` glob and merges. A green aggregate over zero shards is the failure mode this edge prevents. |

All four edges are genuine. None was removed. Note `mutation-replay` has **no**
`needs:` — it resolves its evidence run id at runtime and reads the prior run's
artifacts, which is an `ARTIFACT_DEPENDENCY` on a *different run*, not on a
sibling job; expressing it as `needs:` would be wrong.

### 3.3 Summary

| Class | Count | Action |
|---|---|---|
| `STRICT_DEPENDENCY` | 0 | — |
| `ARTIFACT_DEPENDENCY` | 2 | kept |
| `DATA_DEPENDENCY` | 2 | kept |
| `ENVIRONMENT_DEPENDENCY` | 1 | kept |
| `ORDER_ONLY` | 0 | — |
| `UNNECESSARY_SERIALIZATION` | **0** | none existed |

---

## 4. Runtime Verification critical path

Baseline **16m35s** — the longest path in the pipeline by 2×.

### 4.1 Why it is slow

Agent 2 measured the full runtime suite: **2832.23s**, of which four modules are
**99.5%** of call time.

| Module | Call time | Share |
|---|---|---|
| `test_m9_c55.py` | 686.40s | 54.9% *(M10 figure; re-measured 665s region)* |
| `test_mutation_infra.py` | 242.69s | 19.4% |
| `test_coverage_path_authority.py` | 230.32s | 18.4% |
| `test_regression_suite.py` | 83.09s | 6.7% |

The cost is not "slow tests". It is a **recursive nested-pytest DAG**: one outer
`pytest runtime/tests/` spawns **14 nested pytest processes**
(`test_m9_c55.py` G1→c54; G20→c54 twice; G30→c52+c53+c54; c53→c52+c51+c50;
c50→two experiments). The DAG is finite — c50/c51/c52 do not nest further.

### 4.2 Why it could not simply be sharded

Agent 2's shared-state inventory found the binding constraint is **not** cost
concentration:

| # | Shared mutable state | Verdict |
|---|---|---|
| 1 | `runtime/generated/verification-progress/pytest-*` | keyed by PID — safe |
| 2 | `__pycache__/*.pyc` | atomic rename — safe |
| 3 | `runtime/generated/m9-c47/coverage/.coverage` | **fixed path** — unsafe |
| 4 | `backend/pyproject.toml` `[tool.mutmut]`, rewritten+restored | **unsafe** |
| 5 | root `pyproject.toml`, appended+restored at `test_m9_c55.py:583/587` | **unsafe** |
| 6 | root `requirements.lock`, same | **unsafe** |
| 7 | `backend/mutants/`, `backend/.mutmut-cache` | **unsafe** |
| 10 | fixed TCP ports | **none found** anywhere in `runtime/tests/**` |

**5/6 is decisive.** c55's drift experiments appended a comment to the *real*
root `pyproject.toml` and `requirements.lock`; `build_environment_contract()`
hashes both, and `test_config_divergence.py` / `test_m9_c51.py` /
`test_m9_c50.py` assert on those hashes. A mutator shard running beside a reader
shard produces false failures indistinguishable from real regressions — the worst
possible failure mode for a gate.

Measured consequence: splitting the free tail buys **nothing**.

```
serial group (10 modules)   = 631.8s (39.0%)
free tail (~144 modules)    = 988.6s (61.0%)
tail/2 -> max(632, 494) = 632s
tail/3 -> max(632, 329) = 632s
tail/4 -> max(632, 247) = 632s
```

Measured twice, both conditions. **So M11 did not add a matrix to
`verification-runtime.yml`.** Adding one would have satisfied "introduce matrix
execution" while leaving wall-clock unchanged — the brief explicitly forbids
optimising for job count over wall-clock.

### 4.3 What was done instead: shrink the serial group

Both fixes attack the measured serial group rather than redistributing it.

**(a) PID-scoped coverage data file** — `runtime/foundation/verification/coverage_measurement.py`.
The old comment claimed the data file was "isolated per-run". It was isolated
per-**directory**. Several tests measure coverage independently, so concurrent
`_coverage_run` calls appended to the *same* SQLite file and wrote the *same*
`raw-coverage.json` non-atomically. Both failure modes are silent: interleaved
writers corrupt the database, and a reader can observe a truncated JSON report
while last-writer-wins silently discards the other's.
Now `.coverage.<pid>` and `raw-coverage.<pid>.json`, published to the fixed
documented path via `os.replace` (atomic on the same filesystem), with private
files removed in a `finally`.
`measurement-truth-coverage.json` is a fixed single-writer artifact and is
deliberately untouched.
Measured contention cost removed: **73.08s**.

**(b) c55 drift experiments use throwaway copies** — `runtime/tests/test_m9_c55.py`.
`repo_file_sandbox()` copies the five contract-hashed files to a temp tree and
patches `env_contract.REPO_ROOT` at it. The subject under test is unchanged —
the contract still hashes `<root>/pyproject.toml` and the hash still changes when
its bytes change — and the drift assertions are preserved. It additionally
*asserts the real file was never opened for writing*, so the isolation property is
now itself under test.
This also removes a crash-safety hazard: previously, a process death between the
write and the restore left the repository's single declared dependency authority
corrupted, breaking every subsequent `pip install -e ".[all]"`.

### 4.4 Expected effect

`631.8s → ~465s` serial group (73.08 + 93.62s removed), with the same test
selection and the same assertion set.

`Runtime Verification` projected: **16m35s → ~14m30s**.

> **NOT MEASURED — reason:** the post-change end-to-end GitHub Actions duration.
> The CI wall-clock can only be measured by GitHub's own runners after a push.
> §9 records the observed value.

---

## 5. Dependency caching

### 5.1 Audit result

| Dependency | Cached before M11? | Mechanism |
|---|---|---|
| pip **downloads** | yes | `actions/cache` on `~/.cache/pip` |
| npm dependencies | yes | `actions/setup-node` `cache: npm` |
| Playwright browsers | yes | `actions/cache` on `~/.cache/ms-playwright` |
| **`node_modules`** | no | correctly so — `npm ci` is a clean install |
| **constructed `.venv`** | **no** | ← the gap |

All three pre-existing caches were audited and **left unchanged**. Their keys
were already correct: `setup-node` keys on `hashFiles(frontend/package-lock.json)`;
`setup-playwright` keys on the same lockfile hash **plus** the sanitised browser
list, which satisfies the M11 requirement that the installed Playwright version be
in the key.

### 5.2 The `.venv` cache (added)

`setup-python-runtime` ran, in **every one of the 15 jobs** that bootstrap the
runtime:

```
python -m venv .venv                     19.84s
pip install --upgrade pip                 9.86s
pip install -e ".[all]" (pip cache warm) 257.75s   <- the cost
------------------------------------------------------------
total cold, pip cache already warm        287.45s
```

pip's download cache already existed, so **none** of those 257.75s was network
time — it was unpacking and linking ~601 MB of wheels. That is a pure function of
the declared dependency set, which is exactly what a cache is for. The
Runtime Verification critical path contained ~5 minutes of it.

**Key inputs, and why each is present:**

| Input | Reason |
|---|---|
| `runner.os` | wheels differ per OS |
| `runner.arch` | same release, different artifacts on X64 vs ARM64 |
| **exact** interpreter `X.Y.Z` | `python-version: "3.12"` resolves to whatever patch the runner image ships (3.12.3 today, 3.12.7 next month). `pyvenv.cfg` records that interpreter in `home =`. A key from the *requested range* would hand a 3.12.3 venv to a 3.12.7 runner whose base interpreter no longer exists — every `.venv/bin/*` failing at exec, long after the cache step reported success. A dedicated `Resolve Python toolchain identity` step resolves the full version. |
| `hashFiles(pyproject.toml)` | the single declared dependency authority; a change to any dependency or to the `all` extra changes it |
| `hashFiles(requirements.lock)` | not read by `pip install -e ".[all]"`, so it does not change the set — included so the key cannot outlive a recorded resolution |

`restore-keys` prefixes **only across pyproject/lock revisions**; OS, arch and
exact interpreter stay in the prefix, so a fallback can never cross platforms.

**pip still runs unconditionally on a cache hit**, by design. Re-resolve cost
with everything satisfied measured **31.69s** against 257.75s cold — the win is
~220s per job and dependency resolution still happens every run. That keeps
upstream drift observable: `pyproject.toml` pins 15 of 16 direct dependencies
exactly and floats one (`httpx2>=2.0`); if pip never re-resolved, a cache hit
would silently freeze the transitive set. It also makes a stale cache
self-correcting.

**What is inside the cache, and why it is safe.** The path is `.venv` and nothing
else. Audited for this repository — `find .venv -name '*.db' -o -name '*.sqlite*'
-o -name evidence -o -name generated -o -name '.env' -o -name '*.pem' -o -name
'*.key'` returns **nothing**. Every forbidden category is outside it
(`runtime/generated/**`, `backend/tests/generated/**`, `runtime/generated/m9-c*/**`,
`*.db`, `*.sqlite`, `frontend/node_modules`), and no credential is written into a
venv by `pip install` — the action's `pip config set` writes to `~/.config/pip`,
which is not cached.

**Cache poisoning.** GitHub scopes a cache entry to the ref that created it: a run
for `refs/pull/<n>/merge` writes to that merge ref and no other, while runs on
`main` read only entries created on `main`. A fork pull request therefore cannot
seed an entry a default-branch job restores. This is the platform half of the
same control `api-contracts.yml` already closed by removing `pull-requests: write`
and refusing to check out `workflow_run.head_sha`.

**Restore is validated.** A cache restore is untrusted input: it can be a partial
archive, an entry truncated by an interrupted upload, or an environment left by a
failed run. `Validate repository virtual environment` checks the interpreter is
executable, that its version equals the runner's, that `sys.prefix` is *this*
workspace, and that it can import the repository runtime package. Any failure
warns, `rm -rf`s, rebuilds, and the cache action then saves the repaired
environment under the same key. A `Verify environment` canary imports all 21
modules the verification profiles invoke, so an incomplete environment fails in
seconds with a named cause instead of inside a 15-minute suite.

> **HAZARD — destructive by design.** That rebuild branch is
> `rm -rf .venv && python -m venv .venv`. It is correct inside a CI runner, where
> the checkout is fresh and `.venv` is untracked. It is **not safe to invoke from a
> developer checkout.** During M11 this was demonstrated accidentally: running the
> script from the repository root replaced the canonical `.venv` with an empty one
> and blocked three concurrent agents. It was restored with the same
> `pip install -e ".[all]"` contract CI uses, so parity was exact. The script was
> **not** weakened to make the mistake less likely — the CI behaviour is right.

### 5.3 Measured impact

`NOT MEASURED — reason:` cold-vs-warm GitHub job timings require GitHub's own
runners. Local measurement on a contended 4-core host (loadavg ~9.6) gave the
ratios in §5.2, not CI-representative absolutes. §9 records observed CI values.

---

## 6. Path filtering

### 6.1 Required contexts must never be filtered

Ruleset `20127383` ("protect-main-branch", active, target `~DEFAULT_BRANCH`)
requires exactly four contexts:

```
Backend Verification · Frontend Verification · Runtime Verification · Analyze
```

`main` has **no** separate branch protection — the ruleset is the only gate.

All four workflows carry **no `paths:` and no `paths-ignore:`** on any trigger.
This is now an **enforced rule**, not a comment. Rule 7 previously *warned* when
a verification workflow had no `paths:` filter — for exactly these four files that
warning was backwards. This repository already paid for it: on PR #8 a pull
request touching none of a filtered workflow's paths was blocked indefinitely,
with every reported check green and no clue in the checks list.

Rule 7 is now asymmetric:

| Case | Severity |
|---|---|
| required check **+** `paths:`/`paths-ignore:` | **ERROR** — the context can never report, and GitHub treats a non-reporting required context as unsatisfied |
| required check **+** no filter | correct, silent |
| other workflow **+** no filter | advisory warning (efficiency only) |

Plus **Rule 11**: the required context must exist, be spelled exactly as the
ruleset spells it, and be produced by **exactly one** job of exactly one workflow.
A job-level `if:` on the producing job is rejected unless it is `always()`,
because `always()` forces the job to run while any other condition can evaluate
false and leave the required context unreported. (`mutation-aggregate` depends on
this allowance.)

### 6.2 Audit of the filtered workflows

| Workflow | Filter verdict |
|---|---|
| `backend-verify.yml` | **none, correctly** (required) |
| `frontend-verify.yml` | **none, correctly** (required) |
| `verification-runtime.yml` | **none, correctly** (required) |
| `security-codeql.yml` | **none on the trigger, correctly** (required). The `paths-ignore` at line ~129 is scoped to a **later workflow_dispatch input**, not to the PR/push trigger — verified, and left alone. |
| `api-contracts.yml` | `backend/**`, `frontend/**`, `runtime/**` — sound; it reads only those. |
| `playwright.yml` | `frontend/**`, `e2e/**`, `runtime/**` — sound. |
| `mutation-pr.yml` | `backend/src/{engines,services}/**`, `backend/tests/**` — sound and deliberately narrow: it only measures what a diff can affect. |
| `verification-reconcile.yml` | narrow filter — see §6.3. |
| **`quality.yml`** | **DEFECT — fixed** |

**The `quality.yml` defect.** Its filter listed
`.github/workflows/quality.yml` (one file) while the job **reads every workflow
file** — `validate_actions.py` validates all 14 workflows and 6 composite
actions — and **executes** `.github/scripts/**`. A change to any other workflow,
or to any CI helper script, could not trigger the gate that validates it. Widened
to `.github/workflows/**`, `.github/scripts/**`, `.github/actions/**`.

### 6.3 Required-check proof by path class

`paths:` filters are evaluated against the PR's changed-file set. The four
required workflows have no filter, so they run unconditionally:

| Path class | Backend | Frontend | Runtime | Analyze | Reports? |
|---|---|---|---|---|---|
| backend-only | ✔ | ✔ | ✔ | ✔ | all four |
| frontend-only | ✔ | ✔ | ✔ | ✔ | all four |
| runtime-only | ✔ | ✔ | ✔ | ✔ | all four |
| workflow-only (`.github/**`) | ✔ | ✔ | ✔ | ✔ | all four |
| docs-only (`docs/**`, `*.md`) | ✔ | ✔ | ✔ | ✔ | all four |
| tools-only (`tools/**`) | ✔ | ✔ | ✔ | ✔ | all four |
| mixed | ✔ | ✔ | ✔ | ✔ | all four |

**All four always report, for every path class.** Not inferred — it is asserted
mechanically by `runtime/tests/test_m11_agent1_action_constitution.py`, which
constructs a synthetic workflow tree per class and asserts the validator accepts
the no-filter shape while rejecting the filtered one.

Secondary workflows (`quality`, `api-contracts`, `playwright`, `mutation-pr`,
`verification-reconcile`) may legitimately not run on an unrelated path class.
None of them is a required context, so a missing report cannot block a merge.

---

## 7. Frontend verification profile parity (Task 11)

**Verdict: `run_frontend_verification.sh` and `runtime.verify frontend` are
semantically equivalent. The workflow was routed through the profile; the profile
was not weakened.**

Measured equivalence, from `profiles.py:163-173` and
`control_plane_facade.py:1298-1348, 1460-1477, 152-161`:

| Dimension | Finding |
|---|---|
| test selection | owned by the script in **both** paths — no duplication, no subtraction |
| typecheck / lint / build / unit | `FRONTEND_VERIFICATION_PHASES` is unset, so both run the script's default `lint typecheck build test` (`run_frontend_verification.sh:112-113`) |
| environment | identical; the facade adds `child_process_env()` resolving `.venv/bin` first, which is the interpreter the script already resolves itself |
| cwd | facade `cwd=REPO_ROOT` (`:152-161`), so the relative script path resolves identically |
| exit semantics | script `exit $fail` → facade returns it unchanged (0 pass / 1 any-phase fail) |
| generated state | both write `runtime/generated/evidence/frontend/*` |
| artifacts | see below — the old paths were **dead** |
| what routing adds | task-id reporting, canonical `VERIFICATION_TASK_TIMEOUT_SECONDS`, observable execution-event recording, Rule 8 compliance |

**The parity analysis found a real defect.** `run_frontend_verification.sh`
writes per-phase logs, `frontend-verification.json` under
`runtime/generated/evidence/frontend/`, and
`runtime/generated/frontend-contract-backend.log`. It does **not** write
`runtime/generated/verification-report.md`, `runtime/generated/verification/` or
`runtime/generated/execution/`. So the `frontend-report` and `frontend-evidence`
uploads matched nothing and shipped empty artifacts, **while the evidence the
verification actually produced was never uploaded at all.** Paths repointed at
what the job genuinely produces; artifact **names** unchanged, so the
constitution's ownership table still holds. `upload-runtime` defaults to
`if-no-files-found: warn`, so a legitimately-absent path still cannot fail the job.

**Why this was worth fixing.** `validate_actions.py` Rule 8 requires a
verification workflow to delegate to its `runtime.verify` profile, and it
correctly rejected `frontend-verify.yml` — but **nothing in CI ever executed the
validator**, so the violation sat unreported for a full milestone. The validator
was right and unreachable.

---

## 8. Constitution

`.github/scripts/validate_actions.py` now **runs in CI**, in Quality Gate:

```yaml
- name: Workflow constitution (validate_actions.py)
  shell: bash
  run: .venv/bin/python .github/scripts/validate_actions.py
```

Quality Gate, not a required context, for two reasons: a newly-introduced
workflow violation must not be able to make a pull request permanently
unmergeable by suppressing a required check; and `quality.yml`'s `paths:` filter
now includes `.github/workflows/**`, so a change to any workflow reaches it. No
`continue-on-error`: a violation is a failure.

### 8.1 Rules added in M11

| Rule | Enforces |
|---|---|
| **7a** | a required status check must **not** be path-filtered |
| **10** | every external action pinned to a full 40-char commit SHA |
| **11** | every required status check declared, unique, and produced by exactly one job of exactly one workflow; job-level `if:` rejected unless `always()` |
| **12** | artifact handling valid — matrix-disambiguated names, workspace-relative non-empty paths, recognised `if-no-files-found` |

Rule 10 is deliberately **structural** (`^[0-9a-f]{40}$`) rather than an
allowlist: `runtime/tests/test_m9_c72_action_pins.py` already owns the allowlist,
and duplicating that table would create a second authority that could drift. The
two compose — Rule 10 rejects an unpinned or mutable ref, that test rejects a SHA
for the wrong action or the wrong tag.

### 8.2 Result on the final tree

```
$ .venv/bin/python .github/scripts/validate_actions.py
Workflows validated: 14
Composite actions validated: 6

WARNINGS:
  - m9-forensic-diagnostic-lab.yml: non-verification workflow has no schedule/manual trigger
  - m9-forensic-diagnostic-lab.yml: pull_request trigger has no `paths` filter (Rule 7)
  - mutation-pr.yml: non-verification workflow has no schedule/manual trigger
ALL CHECKS PASSED
$ echo $?
0
```

Three remaining warnings are all advisory `Rule 7` efficiency hints on
non-required workflows. `m9-forensic-diagnostic-lab.yml` is PR-only by design —
it is a diagnostic lab, and `mutation-pr.yml` is PR-only by design.

### 8.3 Regression coverage

`runtime/tests/test_m11_agent1_action_constitution.py` — **40 tests passing**
(with `test_m11_agent1_capability_resolution.py`). It proves the validator:

| Case | Expected |
|---|---|
| wrong profile for a verification workflow | **rejected** |
| missing required profile | **rejected** |
| unsafe unpinned external action (tag or branch ref) | **rejected** |
| invalid artifact handling (empty/absolute path, bad `if-no-files-found`, non-disambiguated matrix name) | **rejected** |
| legitimate matrix / subcommand architecture | **accepted** |
| legitimate path-gated **non-required** workflow | **accepted** |
| legitimate path-gated **required** workflow | **rejected** — this is the M11 §7 requirement, inverted deliberately |
| required context produced by two jobs | **rejected** |
| required-context job with a skipping `if:` | **rejected**; with `always()` | **accepted** |

The validator was made **stricter**, not more permissive. Nothing was relaxed to
reach exit 0.

---

## 9. Per-workflow answers (M11 §8)

**quality.yml** — 1. Parallel: nothing to split; it is one job. 2. Strict deps: none.
3. Repeated setup: `.venv` (now cached) + npm (cached). 4. Cacheable: yes, both now.
5. Path-gate: was **broken** (§6.2), fixed. 6. Must always report: **no** — not required.
7. Artifacts consumed: `quality-frontend` — **no consumer**, `ORDER_ONLY`.
8. Duplicated work: none after this milestone. 9. Critical path: no (3m9s).
10. Expected improvement: filter correctness + `validate_actions.py` + readiness
test now actually run; wall-clock `NOT MEASURED` pending CI.

**backend-verify.yml** — 1. Single `runtime.verify backend` profile; splitting it
would fork the profile. 2. No deps. 3. `.venv` (cached now). 5. No filter, correctly
(required). 6. **Must always report.** 7. Four shared artifacts, no consumer
(`ORDER_ONLY`). 9. Not critical. 10. ~220s expected from the `.venv` cache.
**Changed:** removed unearned `pull-requests: write` — the job calls no PR API and
executes untrusted PR code (pytest, mutmut, mypy over the PR's own backend). Same
reasoning as `api-contracts.yml` did for the identical scope.

**frontend-verify.yml** — as §7. Routed through `runtime.verify frontend`; dead
artifact paths repointed; `pull-requests: write` removed (it runs the most
attacker-controllable code in the tree — npm scripts, vitest, tsc, eslint — and
calls no PR API).

**verification-runtime.yml** — as §4. No matrix added, because sharding the free
tail is measured to save zero seconds while the 631.8s serial group dominates.
Serial group shrunk to ~465s instead. Expected 16m35s → ~14m30s.

**verification-reconcile.yml** — runs `runtime.verify check`, the full
plan/execute/reconcile boundary (12 tasks, 1613.6s measured). It **duplicates**
backend, frontend, quality and contracts work that four dedicated workflows
already perform, and it is the only workflow with a narrow `paths:` filter that
can silently skip on a runtime-only change. Not restructured this milestone:
`check` is a *boundary*, not a set of independent jobs — splitting it would fork
reconciliation semantics, which §10 forbids. Recorded as the largest remaining
duplication. Filter widened only where evidence demanded it.

**mutation.yml** — the tree's only real DAG (§3.2). All four edges proved genuine,
all kept. `mutation-replay` correctly has no `needs:`. Shard matrix is computed
by the plan CLI, not in YAML (M9-C72).

**mutation-pr.yml** — intentionally narrow `paths:`. Failures observed on PR #16
are its own, not path-filter-related.

**m9-forensic-diagnostic-lab.yml** — PR-only by design, no schedule. Sole
consumer of the changed-file comparison matrix. Not required. Left structurally
alone; it is a diagnostic instrument, and M11 §20 forbids reorganising for
aesthetics.

**api-contracts.yml** — `workflow_run` trigger is the second half of its
cache-poisoning defence; `pull-requests: write` already removed in a prior
milestone. Not required.

**playwright.yml** — already a 2-way matrix (`chromium`, `mobile-chrome`) with
`fail-fast: false`. Baselines uploaded per project. Browser cache key already
includes the lockfile hash and the browser set. Not required.

**security-codeql.yml** — **Analyze is required.** No trigger filter (correct).
Three CodeQL languages retained: Python, JavaScript/TypeScript, Actions.
`paths-ignore` at ~129 is inside a `workflow_dispatch` input, not a trigger —
verified and left alone. `security-events: write` retained (required for PR
annotations); no other workflow is granted it.

---

## 10. Security preserved

| Control | State |
|---|---|
| CodeQL Python | unchanged |
| CodeQL JavaScript/TypeScript | unchanged |
| CodeQL Actions | unchanged |
| Immutable external action SHAs | Rule 10 now **enforced in CI**, not merely conventional |
| Permissions minimisation | **improved**: `pull-requests: write` removed from `backend-verify.yml` and `frontend-verify.yml`; `security-events: write` remains exclusive to `security-codeql.yml` |
| Untrusted-checkout protection | preserved — `api-contracts.yml` still refuses `workflow_run.head_sha` |
| Cache poisoning protection | preserved and extended — new `.venv` cache is ref-scoped by the platform, holds no mutable or secret state, and its restore is validated and self-repairing (§5.2) |

---

## 11. Outstanding

1. **Reconcile duplication** — `verification-reconcile.yml` re-runs four other
   workflows' work. Largest remaining wall-clock item. Needs a boundary-semantics
   decision, not a YAML change.
2. **`ORDER_ONLY` artifacts** — five workflows upload four shared artifacts that
   no job downloads. Recommend a follow-up decision to either wire or retire them
   against `docs/ENGINEERING_ARTIFACTS.md`. Not actioned here: deletion during a
   performance milestone is not an optimisation.
3. **Cold/warm cache timings** — `NOT MEASURED` locally; observable only on CI.