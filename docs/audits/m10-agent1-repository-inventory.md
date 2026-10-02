# M10 Agent 1 — Repository Inventory

**Baseline:** `main` @ `bfcf336b5b7f46e759c7486f3eb02d0f8d92e14b`
**Scope:** whole-repository classification, with adjudications for the items named in the
M10 brief. Deletions are listed in `m10-agent1-cleanup-ledger.md`.

## Environment caveat (binding on every number in this document)

This worktree has **no `.venv`**. `bash scripts/bootstrap.sh` was not run, so per the M10
brief fallback I used the main worktree interpreter:

```
/home/vasantha/AI-Projects/ClariFin_OS/.venv/bin/python
```

invoked with `-m` module execution from this worktree root, per `AGENTS.md`.

This is safe for *correctness of the code under test*, and I verified it rather than assuming
it. The venv installs the project as an editable install whose finder maps `runtime` →
`/home/vasantha/AI-Projects/ClariFin_OS/runtime` (the **main** worktree). setuptools appends
that finder to `sys.meta_path`, so `sys.path` — and therefore the CWD — is consulted first.
Verified empirically:

```
$ .venv/bin/python -c "import runtime; print(runtime.__file__)"
.../m10-agent1-repo-tests-1287161cee8c69ee/runtime/__init__.py     # this worktree, not main
```

So the code exercised is this worktree's. `pytest`, `ruff`, `mypy`, `mutmut` and `coverage`
all resolve from the sanctioned venv's `site-packages` when invoked as `python -m <tool>`.

**Caveat that does matter:** `python -m runtime.verify env-check` reports
`pytest_source: "path"` and `venv_bin: <this worktree>/.venv/bin` — the latter path does not
exist. The check still returns `consistent: true`, but a local `.venv` should be created
before any mutation- or CI-sensitive work in this worktree.

## Top-level classification

4,808 tracked files. `git ls-files` count, not working-tree count.

| Path | Tracked | Class | Basis |
|---|---:|---|---|
| `runtime/foundation/` | 326 | SOURCE | verification/platform core; the repo's primary authority |
| `runtime/platform/` | 70 | SOURCE | platform API services, contracts, AI control layer |
| `runtime/system/` | 59 | SOURCE | context/workspace/selection runtime |
| `runtime/tests/` | 173 | TEST | 154 `test_*.py`, flat, plus conftest/fixtures/snapshots |
| `runtime/generated/` | 2,149 | GENERATED (mixed) | milestone evidence + scripts; see "mixed" note below |
| `runtime/archive/` | 30 | GENERATED | archived execplan stdout/stderr logs |
| `backend/src/` | 310 | SOURCE | FastAPI app, engines, services |
| `backend/tests/` | 347 | TEST | 203 `test_*.py` in 13 category directories |
| `backend/migrations/` | 0 | UNKNOWN | directory absent from this commit |
| `frontend/app/` | 54 | SOURCE | Next.js App Router (Agent 3) |
| `frontend/tests/` | 162 | TEST | frontend test suite (Agent 3) |
| `frontend/src/` | 0 | UNKNOWN | directory absent; app lives in `frontend/app` |
| `tools/` | 21 | TOOLING | dev/diagnostic/generator scripts |
| `testing/` | 8 | TEST | TS vitest mirror of runtime contracts |
| `docs/` | 203 | DOCUMENTATION | incl. 4 `docs/audits` entries |
| `scripts/` | 6 | TOOLING | bootstrap, env-doctor, freeze-env, launch, verify, verify-fast |
| `.github/` | 43 | CONFIGURATION | CI workflows (Agent 2) |
| `.husky/`, `.pre-commit-config.yaml` | 2 | TOOLING | local pre-commit gates |
| `.clinerules`, `.cgcignore`, `.repomixignore` | 3 | CONFIGURATION | tool-specific ignore/rule files |
| `servers/` | 1 (gitlink) | SOURCE | **submodule**, mode `160000`, not vendored |
| `pyproject.toml`, `requirements.lock`, `conftest.py` | 3 | CONFIGURATION | dependency + test authority |
| `package.json`, `package-lock.json`, `vitest.setup.ts` | 3 | CONFIGURATION | frontend toolchain (Agent 3) |

### `runtime/generated/` is GENERATED *and* evidence — deliberately mixed

`.gitignore` states the policy explicitly and unusually well: the subtree is never excluded,
because git does not descend into an excluded directory, so a `!`-allowlist would make every
exception unreachable. The line is drawn by *file signature* instead (`*.diff`, `*.log`,
`__pycache__`, `runtime/generated/execution/`, …). 2,149 files are tracked because runtime
tests read m9-c55 certification artifacts, m9-c42.28–.31 baselines, and m9-c48 governance
records as **inputs**, and no bootstrap regenerates them.

Consequence for this audit: **`runtime/generated/` is not safely cleanable.** It contains both
regenerable bulk and irreplaceable evidence, and 2,149 tracked files is the *intended* state,
not drift. I removed nothing from it.

## Adjudication of the items named in the brief

| Item | Exists? | Class | Verdict | Evidence |
|---|---|---|---|---|
| `_probe_emi_up.py` | yes, tracked, 32 lines | TOOLING (misplaced) | **KEEP — route to owner** | Imports `src.engines.loan_engine.*` and runs a 4-level nested loop printing "EMI UP" cases. No `test_` prefix, no `main()`, no callers → not a test, not a module. A one-off investigation scratchpad committed at repo root. Outside my ownership (repo root, not `runtime/tests`/`backend/tests`), so **not deleted**; flagged for `main`. |
| `repomix-output.xml` | yes, tracked, 8.0 MB / 244,584 lines | GENERATED | **KEEP — route to owner** | Self-describes as "a merged representation of the entire codebase, combined into a single document by Repomix". A build artifact of the `repomix` tool. `.repomixignore` excludes `*.xml`, so the artifact is not even fed back into its own tool. Not mine; flagged for `main`. |
| `clarinfin_verification.egg-info/` | **absent** | — | Already resolved | `.gitignore` has `clarinfin_verification.egg-info/`; nothing on disk, nothing tracked. |
| `servers/` | gitlink only | SOURCE | **KEEP — gitignore contradiction** | `git ls-files -s` → mode `160000` = submodule at `ada8803d`. It has no content in this worktree. **But `.gitignore` lists `servers/`** — so it is tracked *and* declared ignorable. `.gitignore` only affects untracked paths, so this is inert, not broken; it is a contradiction to clean up. `AGENTS.md`/`mypy` already reference `servers/src/fetch/tests/`. Agent 4 owns `servers/`. |
| `unrelated/` | **absent** | — | Already resolved | `.gitignore` has `unrelated/`; nothing on disk, 0 tracked. |
| `tools/` | yes, 21 files | TOOLING | **KEEP** | Genuine developer tooling: `development/`, `diagnostics/`, `generators/`, `e2e_seed.py`. Not a framework layered over an existing one. |
| `memory-bank/` | yes, **3 files tracked, and `.gitignore` lists `memory-bank/`** | DOCUMENTATION | **KEEP — contradiction** | `activeContext.md`, `architecture.md`, `projectbrief.md` are tracked; `.gitignore` declares the whole dir ignored. Tracked files ignore `.gitignore`, so this is inert. Frozen at checkout; flagged. |
| `.next/` | **absent** | — | Already resolved | `.gitignore` has `.next/`. |
| `.hypothesis/` | **present, 386 files / 1.6 MB, untracked** | GENERATED | **KEEP on disk, never commit** | Hypothesis example database. `.gitignore` has `.hypothesis/`; correctly untracked. |
| `test-results/` | yes, **1 tracked file: `.last-run.json`** | GENERATED | **KEEP — contradiction** | Playwright last-run state. `.gitignore` lists `test-results/`, yet the file is tracked. 96 bytes. Inert contradiction; flagged for `main`. |
| `frontend/dist` | **absent** | — | Already resolved | `.gitignore` has `dist/`. |
| `backend/mutants` | **absent** | — | Already resolved | `.gitignore` has `backend/mutants/`, `mutants/`, `.mutmut-cache/`; `pyproject` `norecursedirs` also excludes it. |
| `backend/.mutmut-cache` | **absent** | — | Already resolved | As above. |
| `__pycache__` dirs | 131 on disk, 0 tracked | GENERATED | **KEEP on disk, never commit** | `**/__pycache__/` + `**/*.pyc` in `.gitignore`; `norecursedirs` excludes `__pycache__`. Correctly untracked. |
| `BASELINE.md` | yes | DOCUMENTATION | **KEEP — route to owner** | A dated snapshot of a specific failing run (5 failed / 3,826 passed). Restates repo state at a point in time and is already contradicted by current numbers. Not mine. |
| `CAPABILITY_AUDIT.md` | yes | DOCUMENTATION | **KEEP — route to owner** | Point-in-time audit. Not mine. |
| `M13_COMPLETION_REPORT.md` | yes | DOCUMENTATION | **KEEP — route to owner** | Completion report for M13. Not mine. |
| `activeContext.md` (root) | yes | DOCUMENTATION | **KEEP — route to owner** | 1 tracked file at root; `.gitignore` lists `activeContext.md` under "Memory and progress tracking" in `.repomixignore`. Contradiction again. Not mine. |
| `progress.md` | yes, 7,786+ lines | DOCUMENTATION | **KEEP — high value** | Contains the prior four-audit backlog (see below). Not mine, but I used it as evidence. |

`dependency-reports/` (4 tracked files) is the same contradiction class: `.gitignore` lists
`dependency-reports/`, the files are tracked.

## Finding: 83 tracked files are also matched by `.gitignore`

`git ls-files -z | git check-ignore --stdin --no-index` yields 83 tracked paths that the
ignore rules also match. They can never be updated by a normal workflow, because git ignores
the ignore-rules for paths it already tracks.

| Area | Count | What it is |
|---|---:|---|
| `runtime/generated/**` | 30 | `*.log`/`*.stdout`/`*.stderr` command output from one milestone run (`m9-c64-final-runtime-command-ci-convergence/command-output/`, 15 command pairs) and `runtime/archive/execplan-1218b76aa610/` (14 logs) |
| `.kilo/plans` | 24 | agent plan documents (expected; `.kilo/plans/` is intentionally ignored) |
| `dependency-reports/` | 4 | pinned dependency reports |
| `memory-bank/` | 3 | `activeContext.md`, `architecture.md`, `projectbrief.md` |
| `backend/tests/mutation_infra/mutants/` | 6 | mutmut-generated mutants of a test probe — **in my ownership, addressed in the cleanup ledger** |
| `test-results/` | 1 | Playwright `.last-run.json` |
| `servers/` | 1 | the submodule gitlink |

The 30 under `runtime/generated/` are the interesting ones: they are per-run command logs
committed once and then frozen, which is the exact class `.gitignore` already declares
regenerable. Removing them is not mine to authorise, but they are a sound cleanup candidate.

## Finding: a test run dirties the working tree

Running the runtime suite rewrote **5 tracked files** (restored before committing):

| Tracked path | Change | Written by |
|---|---|---|
| `runtime/generated/m9-c47/coverage/.coverage` | binary, 192,512 → 221,184 B | a coverage test writing into the real m9-c47 evidence dir |
| `runtime/generated/m9-c47/coverage/raw-coverage.json` | 1 line | same |
| `runtime/generated/m9-c55/c56-readiness.json` | 1 line | same class |
| `runtime/generated/metrics/test/.index.json` | +4 lines | metrics writer |
| `backend/tests/mutation_infra/mutants/mutmut-stats.json` | 2 lines | `runtime.verify mutation --smoke` |

This matters beyond tidiness: `.coverage` is a binary SQLite coverage database that should
never be version-controlled, and a careless `git add -A` after a test run commits one run's
artifacts. 28 files under `runtime/tests/` write into `runtime/generated/`. Two of the worst
offenders were making that materially dangerous and are fixed — see
`m10-agent1-test-taxonomy.md`, "Hermeticity defects".

## Finding: the `servers` submodule cannot be audited from here

`servers/` is a gitlink at `ada8803d`. It is outside the repository tree, so no inventory,
coverage, dead-code or naming statement in this document covers its contents.

## Not classified: UNKNOWN

`backend/migrations/` and `frontend/src/` are referenced by config (`mypy` `mypy_path`,
`ruff` `per-file-ignores`, and the `modules` map in `runtime/tests/conftest.py`) but do not
exist in this commit. Harmless stale configuration; noted, not changed.
