# BASELINE.md — ClariFin_OS Pre-Remediation Baseline

**Milestone**: M00 — Baseline & Verification Harness
**Captured**: 2026-09-23 (agent: Cline, session started 17:33 local)
**Purpose**: Record the pre-change test/lint/type/build/schema status of the repository so
later milestones can distinguish a pre-existing failure from a regression introduced by this
program. Nothing in this file was fixed — M00 is read-only by design.

## Captured repository state

| Item | Value |
|---|---|
| Branch | `m9c9-merge-authorization-resolution` |
| HEAD commit | `5e519592d7f79cc0a5463cd2967f463cf03bef75` (`M9-C69: Final certification — all phases complete, all metrics met`) |
| Working tree at capture | **Dirty — pre-existing, not caused by M00** (see below) |
| Python | `.venv/bin/python` → Python 3.12.3 (repository-root venv, per `AGENTS.md`) |
| SQLite library | 3.45.1 |
| Node / npm | v24.20.0 / 11.19.0 |
| Cores | 4 |

### Pre-existing working-tree changes (present before M00 began)

Recorded so that M00's "zero other files changed" gate is objectively checkable: these were
already modified/untracked when M00 started, and M00 neither created nor altered them.

```
 M backend/runtime/generated/platform/snapshot.json
 M frontend/__tests__/utils/createMockResponse.ts
 M frontend/vitest.config.ts
 M package-lock.json
 M package.json
 M runtime/generated/git-fetch-events.jsonl
 M runtime/generated/platform/snapshot.json
?? .repomixignore
?? IMPLEMENTATION_PLAN.md
?? backend/runtime/generated/git-fetch-events.jsonl
?? frontend/__tests__/simple.test.ts
?? frontend/app/api/
?? frontend/tsconfig.test.json
?? repomix-output.xml
?? vitest.setup.ts
```

Note: `frontend/__tests__/simple.test.ts`, `frontend/tsconfig.test.json` and `vitest.setup.ts`
are untracked-but-present pre-existing files, and `frontend/vitest.config.ts` was modified before
M00 began — the frontend test/type results below therefore reflect that pre-existing, uncommitted
state.

---

## M00-T1 — Backend test status

Command (exactly as specified): `.venv/bin/python -m pytest backend/tests`
(duration: **1633.91s ≈ 27 min 13 s**, 4-core machine, `timeout = 60` per test from
`backend/pyproject.toml`, `pytest-timeout` active, no `-n` parallelism)

### Summary line (verbatim)

```
====== 5 failed, 3826 passed, 1 xpassed, 3 warnings in 1633.91s (0:27:13) ======
```

`ERROR` count: **0**.

### Full pass/fail list — failing node IDs (verbatim from the short test summary)

```
FAILED backend/tests/integration/test_platform_api_phase3.py::TestTasks::test_detail_for_known_task
FAILED backend/tests/integration/test_platform_api_phase3.py::TestErrors::test_error_endpoints_return_valid_envelopes[/platform/v1/errors/recurring]
FAILED backend/tests/integration/test_platform_api_phase4.py::TestCacheTiming::test_cached_response_is_faster_than_uncached[/platform/v1/change/intelligence-change]
FAILED backend/tests/integration/test_platform_api_phase4.py::TestGate4ProgrammaticAnswers::test_what_was_last_verified
FAILED backend/tests/integration/test_platform_api_phase4.py::TestGate4ProgrammaticAnswers::test_what_obligations_are_open
```

The other 3826 tests **passed**; 1 test is `xpassed`. All 5 failures are confined to two
pre-existing platform-API integration files (`test_platform_api_phase3.py`,
`test_platform_api_phase4.py`) that exercise the `/platform/v1/*` runtime — no test under
`backend/tests/unit/`, `contract/`, `invariants/`, `golden/` or `properties/` failed.

### Failure detail (verbatim evidence)

Three failures carry explicit assertion messages:

```
backend/tests/integration/test_platform_api_phase3.py:174: in test_detail_for_known_task
E   AssertionError: Expected 200, got 404:
E     {"kind":"platform.error",...,"error":{"code":"NOT_FOUND","layer":"platform.tasks",
E      "message":"Task/obligation 'obl-e237087aa33a-0' not found in live set",...}}
E   assert 404 == 200

backend/tests/integration/test_platform_api_phase4.py:214: in test_what_was_last_verified
    assert total == 75
E   assert 20 == 75

backend/tests/integration/test_platform_api_phase4.py:227: in test_what_obligations_are_open
    assert open_count == 13, f"Expected 13 open obligations, got {open_count}"
E   AssertionError: Expected 13 open obligations, got 64
E   assert 64 == 13
```

Two further failures were terminated by the per-test timeout (evidence — two occurrences in
the run output):

```
E   Failed: Timeout (>60.0s) from pytest-timeout.
```

whose stack dumps show a `starlette.testclient` request blocked inside
`anyio.from_thread` → `portal.call(self.app, ...)` as the tail frames that were captured before Kill
(one dump additionally logs
`WARNING runtime.foundation.verification.symbol_resolver:symbol_resolver.py:89 File not found: backend/src/engines/credit_card_engine/core.py`).

**Attribution note (stated precisely, not glossed):** the summary lists 5 failed node IDs, while the
`FAILURES` section printed only 3 section headers. The two timeout reports appear inside the
`TestTasks.test_detail_for_known_task` section without their own headers, so the exact pairing of
each 60 s timeout to a node ID is **inferred** (the two non-assertion failures:
`TestErrors::test_error_endpoints_return_valid_envelopes[/platform/v1/errors/recurring]` and
`TestCacheTiming::test_cached_response_is_faster_than_uncached[/platform/v1/change/intelligence-change]`),
not directly stated by pytest's output.

Because both 60 s timeouts ran while the machine was heavily loaded by M00's own concurrent
static checks (load average peaked at 9.4 on 4 cores), their timeout status is **load-sensitive**
and a quiet re-run is recorded under "Addendum A" below.

### Captured noise during the run (observed, pre-existing)

* `E2E IMPACT: 23 route(s) changed / 4 E2E test(s) required ...` is emitted to stderr by the
  runtime on several platform paths.
* Slow platform endpoints: single requests took up to the 60 s timeout — a pre-existing
  performance characteristic of the `/platform/v1/*` runtime in this environment (see
  "Discovered issues").


## M00-T2 — Backend lint / format / type

Commands (run from `backend/`, exactly as specified in `IMPLEMENTATION_PLAN.md` §4 M00-T2):

| Command | Result | Exit |
|---|---|---|
| `../.venv/bin/python -m ruff check src/` | **FAIL — 3 errors**, all in `src/routers/platform.py` | 1 |
| `../.venv/bin/python -m black --check src/` | **FAIL — 1 file would be reformatted**: `src/routers/platform.py` (243 files unchanged) | 1 |
| `../.venv/bin/python -m mypy src/` | **FAIL — 6 errors in 1 file (292 source files checked)**, all in `src/routers/platform.py` | 1 |

### ruff violation list (verbatim)

```
F401 [*] `runtime.platform.api.contracts._primitives.Status` imported but unused
   --> src/routers/platform.py:948:60

I001 [*] Import block is un-sorted or un-formatted
    --> src/routers/platform.py:1023:5

F401 [*] `runtime.platform.diagnostics.engine.build_diagnostic_recommendation` imported but unused
    --> src/routers/platform.py:1024:9

Found 3 errors.
[*] 3 fixable with the `--fix` option.
```

### black output (verbatim)

```
would reformat /home/vasantha/AI-Projects/ClariFin_OS/backend/src/routers/platform.py

Oh no! 💥 💔 💥
1 file would be reformatted, 243 files would be left unchanged.
```

### mypy output (verbatim)

```
src/routers/platform.py:180: error: Module "runtime.platform.api.services" has no attribute "status"  [attr-defined]
src/routers/platform.py:296: error: Module "runtime.platform.api.contracts" has no attribute "verification"  [attr-defined]
src/routers/platform.py:310: error: Cannot find implementation or library stub for module named "runtime.foundation.verification.capability_catalog"  [import-not-found]
src/routers/platform.py:320: error: Cannot find implementation or library stub for module named "runtime.foundation.verification.workflow_inspection"  [import-not-found]
src/routers/platform.py:948: error: Cannot find implementation or library stub for module named "runtime.platform.api.contracts._primitives"  [import-not-found]
src/routers/platform.py:948: note: See https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports
src/routers/platform.py:1054: error: Item "None" of "dict[str, Any] | None" has no attribute "get"  [union-attr]
Found 6 errors in 1 file (checked 292 source files)
```

**Interpretation (recorded, not fixed):** all three backend static checks currently FAIL, and
every failure is confined to one file, `backend/src/routers/platform.py`. This is the
pre-existing state against which M06b's "hook matches `verify-fast.sh`" comparison and every
later milestone's "no new violation" claim must be measured. Note `scripts/verify-fast.sh` runs
exactly these three commands (with `ruff --fix`), so `verify-fast.sh` also fails today.

---

## M00-T3 — Frontend test / type-check / lint

Run from `frontend/`, exactly as specified.

| Command | Result | Exit |
|---|---|---|
| `npm run test` (`vitest run`) | **FAIL — 18 failed \| 1349 passed (1367 tests)**; `Test Files 1 failed \| 106 passed (107)`; duration 131.91s | 1 |
| `npm run type-check` (`tsc --noEmit`) | **FAIL — 3 TS errors** | 1 |
| `npm run lint` (`eslint`) | **PASS (exit 0) — 173 warnings, 0 errors** | 0 |

### `npm run test` — failing file and root cause (verbatim)

All 18 failures are in a single file, and every test in it fails:

```
 ❯ __tests__/api-contracts/platform-c67.2.contract.test.ts (18 tests | 18 failed) 250ms
     × returns 200 with valid envelope 88ms
     × data has required top-level fields 18ms
     ... (18 total: /platform/v1/status, /health, /workflows, /runs, /verification)
```

```
TypeError: fetch failed
Caused by: Error: connect ECONNREFUSED 127.0.0.1:8000
⎯⎯ Serialized Error: { errno: -111, code: 'ECONNREFUSED', syscall: 'connect', address: '127.0.0.1', port: 8000 }
```

**Interpretation:** this contract file performs real HTTP calls to a live backend on
`127.0.0.1:8000` and is **environment-dependent** — with no backend running, all 18 fail with
`ECONNREFUSED`. This is a pre-existing baseline condition (and a notable one for M13-T9/T10,
which must account for it). The other 106 test files (1349 tests) pass.

### `npm run type-check` — errors (verbatim)

```
__tests__/utils/createMockResponse.ts(1,1): error TS6133: 'MockResponse' is declared but its value is never read.
__tests__/utils/createMockResponse.ts(16,36): error TS2693: 'MockResponse' only refers to a type, but is being used as a value here.
lib/hooks/__tests__/use-platform-status.test.ts(11,1): error TS6133: 'usePlatformStatus' is declared but its value is never read.
```

All 3 errors are in test-only files; note `frontend/__tests__/utils/createMockResponse.ts` was
already modified in the working tree before M00 began (pre-existing change), so this result
reflects a pre-existing, uncommitted state.

### `npm run lint` — summary (verbatim)

```
✖ 173 problems (0 errors, 173 warnings)
  0 errors and 2 warnings potentially fixable with the `--fix` option.
```

Warning rules by frequency (parsed from the report): `no-console` 97,
`@typescript-eslint/no-explicit-any` 54, `@typescript-eslint/consistent-type-imports` 12,
`@typescript-eslint/no-unused-vars` 7, plus 1 each of `react-hooks/set-state-in-effect`,
`jsx-a11y/role-has-required-aria-props`. Lint exits **0** (warnings only; the repo's
`lint-staged` config uses `--max-warnings 0`, which is a stricter gate — see M06b's context).

---

## M00-T4 — Frontend build

Command (from `frontend/`): `npm run build` (`next build`, Next.js 16.1.6 / Turbopack).

**Result: PASS (exit 0).** Verbatim key lines:

```
✓ Compiled successfully in 32.4s
  Running TypeScript ...
  Collecting page data using 3 workers ...
```

Warnings emitted (pre-existing, non-fatal):

```
⚠ Warning: Next.js inferred your workspace root, but it may not be correct.
 We detected multiple lockfiles and selected the directory of
 /home/vasantha/AI-Projects/ClariFin_OS/package-lock.json as the root directory.
 Detected additional lockfiles:
   * /home/vasantha/AI-Projects/ClariFin_OS/frontend/package-lock.json
⚠ The "middleware" file convention is deprecated. Please use "proxy" instead.
```

The build emitted the full route table (39 route lines, e.g. `├ ○ /transactions`,
`├ ƒ /platform/verification/run/[capability]`) and completed with `ƒ Proxy (Middleware)` /
`○ (Static)` / `ƒ (Dynamic)` legend output, i.e. a normal successful production build.

Note: the build's TypeScript step succeeded even though `npm run type-check` fails — the build's
`tsconfig.json` include set differs from the standalone `tsc --noEmit` run's (the 3 failing
files are test-only files not covered by the build's type pass). Recorded as observed.


## M00-T5 — Schema / migration baseline

Method (the plan's instruction is "start the backend against a scratch DB path and record
`verify_schema()` counts"):

```bash
cd backend && FINANCE_DB_PATH=/tmp/m00/scratch/finance.db UPLOAD_DIR=/tmp/m00/scratch/uploads \
  ../.venv/bin/python -c "from src.startup import run_startup_validation; assert run_startup_validation() is True"
```

`FINANCE_DB_PATH` / `UPLOAD_DIR` are the repository's own documented configuration env vars
(`backend/src/core/db/config.py` resolution order, `.env.example`); they were set only so the
scratch database and uploads land outside the repository. No source file was changed.

Result — startup validation PASSED (exit 0):

```
2026-09-23 17:37:54,159 - clarifin - INFO - Starting ClariFin_OS startup validation...
2026-09-23 17:37:54,159 - clarifin - INFO - Configuration validation passed
2026-09-23 17:38:05,197 - clarifin - INFO - Database schema initialized and verified
2026-09-23 17:38:05,200 - clarifin - INFO - Database connectivity verified
2026-09-23 17:38:05,200 - clarifin - INFO - Startup validation complete - all systems ready
```

### `verify_schema()` counts on a fresh scratch DB

Counts measured against the required sets in `backend/src/core/db/schema.py`
(`_REQUIRED_TABLES` / `_REQUIRED_INDEXES` / `_REQUIRED_TRIGGERS`):

| Object class | Required | Present | Missing |
|---|---|---|---|
| Tables | 29 | **29** | none |
| Indexes | 25 | **25** | none |
| Triggers | 2 | **2** | none |

Additional facts about the fresh DB:

| Probe | Value |
|---|---|
| Total tables in DB (incl. `sqlite_sequence`) | 30 |
| `PRAGMA foreign_key_check` | `[]` (no violations) |
| `PRAGMA user_version` | `0` |
| `schema_migrations` table exists | **False** |
| `SELECT COUNT(*) FROM transactions` | 0 |
| `SELECT SUM(amount_paise) FROM transactions` | `None` (empty table) |

**Interpretation:** the pre-M03 schema exactly meets the required baseline (29/25/2, nothing
missing, FK enforcement clean) and has **no version tracking at all**
(`schema_migrations` absent, `user_version = 0`) — precisely the gap M03 exists to close.

### Live database state at baseline (for M13-T19's comparison)

The canonical launcher starts the backend with `cd backend` (`scripts/launch.sh`), so the DB the
running application uses by default is `backend/data/finance.db`. Both candidate DB files were
read read-only (`file:...?mode=ro`, so no write/lock side effects):

| DB path | transactions | SUM(amount_paise) | statements | tables | `schema_migrations` |
|---|---|---|---|---|---|
| `backend/data/finance.db` (canonical launcher target) | **3** | **225000** | 1 | 31 | False |
| `data/finance.db` (CWD-dependent default) | 0 | `None` | 0 | 30 | False |

These are the numbers M13-T19's `SELECT COUNT(*)` / `SELECT SUM(amount_paise)` check must still
match at the end of the program (no historical financial data altered anywhere in the program).

---

## M00-T6 — `runtime.verify` harness (`./scripts/verify.sh quick`)

The `runtime/` package **is present** in the working repository (the plan flagged this as
`UNKNOWN — REQUIRES VERIFICATION`), so the harness was executed:

| Command | Result | Exit |
|---|---|---|
| `./scripts/verify.sh quick` | **FAIL** — aborted on its first task | 1 |

Verbatim end of output:

```
Found 3 errors.
[*] 3 fixable with the `--fix` option.
[profile:quick] task 'quick-ruff' failed (exit 1)
```

**Interpretation:** the `quick` profile's first task (`quick-ruff`, i.e. `ruff check .` over the
backend) fails on exactly the same 3 pre-existing violations already recorded in T2
(`src/routers/platform.py` lines 948/1023/1024), and the profile **aborts** instead of running its
remaining tasks (black, mypy, unit tests, architecture tests, meta tests). The harness is
therefore available and correctly wired; its failure is fully explained by the pre-existing lint
state — no new defect. (For reference, the profile's underlying script
`.github/scripts/run_fast_checks.sh` runs ruff, black, a non-blocking mypy, then
`pytest tests/unit -x -n auto`, architecture and meta suites.)

---

## Addendum A — Characterization re-run of M00-T1's 5 failures

Because the 60 s timeouts in T1 occurred while M00's own static checks were loading the 4-core
machine, the **same 5 node IDs** were re-run afterwards on a quiet machine (no competing jobs) to
determine whether they are load artifacts or deterministic:

```
.venv/bin/python -m pytest \
  "backend/tests/integration/test_platform_api_phase3.py::TestTasks::test_detail_for_known_task" \
  "backend/tests/integration/test_platform_api_phase3.py::TestErrors::test_error_endpoints_return_valid_envelopes[/platform/v1/errors/recurring]" \
  "backend/tests/integration/test_platform_api_phase4.py::TestCacheTiming::test_cached_response_is_faster_than_uncached[/platform/v1/change/intelligence-change]" \
  "backend/tests/integration/test_platform_api_phase4.py::TestGate4ProgrammaticAnswers::test_what_was_last_verified" \
  "backend/tests/integration/test_platform_api_phase4.py::TestGate4ProgrammaticAnswers::test_what_obligations_are_open" \
  -v
```

Result: `collected 5 items` → `================== 5 failed, 2 warnings in 196.63s (0:03:16) ===================`

| Node ID | Addendum-A failure mode |
|---|---|
| `TestTasks::test_detail_for_known_task` | `Failed: Timeout (>60.0s) from pytest-timeout` |
| `TestErrors::test_error_endpoints_return_valid_envelopes[/platform/v1/errors/recurring]` | `Failed: Timeout (>60.0s) from pytest-timeout` |
| `TestCacheTiming::test_cached_response_is_faster_than_uncached[/platform/v1/change/intelligence-change]` | `Failed: Timeout (>60.0s) from pytest-timeout` |
| `TestGate4ProgrammaticAnswers::test_what_was_last_verified` | AssertionFailure — `assert 23 == 75` |
| `TestGate4ProgrammaticAnswers::test_what_obligations_are_open` | AssertionFailure — `Expected 13 open obligations, got 64` (`assert 64 == 13`) |

Three timeout failures + two assertion failures = 5, exactly T1's failure set — so **all 5 are
deterministic/reproducible, not load-induced** (196.63 s ≈ three 60 s timeouts + fast assertions).

**Non-determinism observed:** the same assertion produced `assert 20 == 75` in T1's full run and
`assert 23 == 75` in Addendum A — the *actual* value varies with accumulated runtime telemetry
while the expected constant (75) matches neither observation. Recorded as a pre-existing,
state-dependent failure.



---

## Addendum B — Files written by M00's own mandated commands (disclosure + restoration)

M00 is declared read-only and its only intended artifact is `BASELINE.md`. However, the
**mandated** commands themselves (`pytest backend/tests`, `./scripts/verify.sh quick`) drive the
repository's verification runtime, which rewrites tracked telemetry under `runtime/generated/`.
Evidence — the `git status --porcelain` / `git diff --stat` delta caused by executing T1/T6:

```
 M runtime/generated/engineering-events.jsonl        (+7 lines)        [clean before M00]
 M runtime/generated/engineering-history.json        (+50 lines)       [clean before M00]
 M runtime/generated/frontend-backend-map.json       (978 lines)       [clean before M00]
 M runtime/generated/git-fetch-events.jsonl          (42 → 88 insertions; already dirty pre-M00)
 M runtime/generated/platform/snapshot.json          (already dirty pre-M00; content changed further)
```

* The first three files were **clean at HEAD before M00**. Their post-run content was archived to
  `/tmp/m00/written_by_m00/` and they were then **restored to their pre-M00 (HEAD) content** with
  `git checkout -- <paths>` — a restoration of the pre-task state, not a source change. sha256
  verification showed the restored files are byte-identical to `HEAD`.
* The last two were **already modified before M00 began** (uncommitted telemetry from earlier
  verification runs), so their pre-M00 content could not be recovered; they were deliberately
  **left untouched** rather than being reset to HEAD, which would have destroyed pre-existing,
  unrelated uncommitted state.
* **No source file, test file, configuration file or script was created, modified or deleted by
  M00, and no fix of any kind was applied.**

Post-M00 verification of that claim (pre-M00 snapshot vs. final state):

```
$ diff /tmp/m00/git_status_pre.txt  <(git status --porcelain)
8a9
> ?? BASELINE.md
```

i.e. the working tree is the pre-M00 state plus the single new file `BASELINE.md`.

---

## Known expected failures (introduced by M01, resolved by M04/M05)

Per `IMPLEMENTATION_PLAN.md` M01-T3. These two tests are *supposed* to fail
against current production code; their failure characterizes the defect each
later milestone fixes. They must not be confused with regressions:

| Test file | Task | Expected state today | Resolved by |
|---|---|---|---|
| `backend/tests/unit/repositories/test_transaction_hash_dedup.py` | M01-T1 | **FAILS** — characterizes `BE-001` (verified: `AssertionError`, second row swallowed by hash dedup; runs in ~5s, not a fixture/collection error) | M05 |
| `backend/tests/architecture/test_household_sentinel_cross_group_consistency.py` | M01-T2b | **FAILS** — characterizes `DB-002` (verified: `assert 'default' == 'primary'`; `behaviour_snapshots` defaults to `'default'`, `financial_goals` to `'primary'`) | M04 |

Companion guard `backend/tests/architecture/test_household_sentinel_internal_consistency.py`
(M01-T2a) **passes** today, as required — it is a regression guard for the
four-table group, not a characterization of `DB-002`.

---

## Pre-existing failure summary (what later milestones must not regress)

| # | Check | Pre-existing state at M00 |
|---|---|---|
| 1 | `pytest backend/tests` | 5 failed / 3826 passed / 1 xpassed — all failures in `integration/test_platform_api_phase3.py` + `test_platform_api_phase4.py` |
| 2 | `ruff check src/` (backend) | FAIL — 3 errors, all in `src/routers/platform.py` |
| 3 | `black --check src/` (backend) | FAIL — 1 file (`src/routers/platform.py`) |
| 4 | `mypy src/` (backend) | FAIL — 6 errors, all in `src/routers/platform.py` |
| 5 | `npm run test` (frontend) | FAIL — 18 failed / 1349 passed (one live-backend-dependent contract file) |
| 6 | `npm run type-check` (frontend) | FAIL — 3 test-file TS errors |
| 7 | `npm run lint` (frontend) | PASS — 0 errors / 173 warnings |
| 8 | `npm run build` (frontend) | PASS (exit 0) |
| 9 | `./scripts/verify.sh quick` | FAIL — aborts on `quick-ruff` (same 3 ruff errors) |
| 10 | Fresh-DB schema | PASS — 29/29 tables, 25/25 indexes, 2/2 triggers, no FK violations, `schema_migrations` absent, `user_version = 0` |
| 11 | Live data | `backend/data/finance.db`: 3 transactions, `SUM(amount_paise)` = 225000, 1 statement — unchanged by every M00 command |



---

## Discovered issues (recorded, NOT fixed — M00 is read-only)

1. **Tracked telemetry under `runtime/generated/` is rewritten by every verification run**, so the
   repository cannot execute its own mandated verification commands without dirtying tracked
   files. Suggested owner: new issue, unassigned (needs a `.gitignore`/artifact-policy decision);
   it directly affects the wording of any "read-only milestone" gate. (See Addendum B.)
2. **`/platform/v1/*` endpoints can exceed the 60 s per-test timeout** in this environment. The
   captured timeout stacks implicate
   `runtime/foundation/verification/planner/planner.py::_find_chain` (reached while serving a
   request) and a repo-scanning loop
   `runtime/foundation/architecture/sources.py::_iter_python_files` (`root.rglob("*.py")` over the
   configured scan roots). Suggested owner: new issue, unassigned (§13 already defers
   "N+1/cache-invalidation audit" to a dedicated future audit).
3. **`verify_schema()`'s "Schema verified: N tables, N indexes, N triggers" line is invisible**:
   it logs through the module logger `src.core.db.schema`, which has no handler configured (only
   the `clarifin` logger is configured in `src/logger.py`), so the counts never reach stdout at
   startup. Suggested owner: **M07** (centralized logging).
4. **`frontend/__tests__/api-contracts/platform-c67.2.contract.test.ts` requires a live backend**
   at `127.0.0.1:8000` and fails 18/18 without one; whether `npm run test` is meant to be
   self-contained is unclear. Suggested owner: **M13** (T9/T10 must account for it).
5. **`DATABASE_PATH` resolution is CWD-dependent** and this checkout holds two DB files
   (`data/finance.db` empty; `backend/data/finance.db` live with 3 transactions) with no `.env`
   present; the canonical launcher (`cd backend` + uvicorn) uses the latter. Suggested owner: new
   issue, unassigned (operational clarity; not a data-integrity defect).
6. **`npm run type-check` and `npm run build` disagree on the same tree** — the build's TypeScript
   step passes while standalone `tsc --noEmit` fails on 3 test-only files. Suggested owner: new
   issue, unassigned.
7. **`package.json`, `package-lock.json` and several frontend test-config files were already
   modified before M00 began**, so all frontend results above reflect an uncommitted state.
   Suggested owner: the in-flight branch work (pre-existing; not introduced by this program).

---

## Addendum C — M00 gate self-assessment

| Gate criterion | Objective assessment |
|---|---|
| `BASELINE.md` exists with concrete results (or explicit `UNKNOWN`) for all six task categories T1–T6 | **MET** — T1, T2, T3, T4, T5, T6 each recorded with real command output. No `UNKNOWN` was needed for T6 because the `runtime/` package proved available. |
| Zero other files changed | **MET for the final repository state**: `git status --porcelain` differs from the pre-M00 snapshot only by `?? BASELINE.md`. Disclosed caveat (Rule 7 disclosure): the mandated commands wrote 5 tracked telemetry files during the run; 3 were archived and restored to HEAD, and 2 were already dirty before M00 so they could not be reset without destroying pre-existing uncommitted state. No source / test / config / script file was touched. |
| Nothing fixed (baseline capture only) | **MET** — zero fixes applied; all pre-existing failures recorded above. |


