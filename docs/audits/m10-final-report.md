# M10 — Repository, Runtime Console & Application Consolidation

**Consolidated completion report**

| | |
|---|---|
| **Baseline** | `main` @ `bfcf336b5b7f46e759c7486f3eb02d0f8d92e14b` |
| **Head** | `f2f04557` on `m10/consolidation` |
| **Pull request** | [#16](https://github.com/simcitysocial97-dev/ClariFin_OS/pull/16) |
| **Repository** | `simcitysocial97-dev/ClariFin_OS` (the brief named `vasantha/ClariFin_OS`; verified via `gh repo view`) |
| **Scope** | 4 parallel agents with strict file ownership, plus integration |
| **Delta** | 57 commits · 170 files · +8,200 / −12,750 |

This document consolidates all four agent audits and the integration phase into
one record. Per-agent evidence remains in `docs/audits/m10-agent{1,2,3,4}-*`
and `m10-ci-constitution-reconciliation.md`.

---

## 1. Final health

### 1.1 Real GitHub Actions results on #16

| Workflow | Result | Duration |
|---|---|---|
| Backend Verification | **pass** | 4m34s |
| Frontend Verification | **pass** | 3m42s |
| Runtime Verification | **pass** | 16m37s |
| Analyze (CodeQL) | **pass** | 3m52s |
| Quality Gate | **pass** | 3m54s |
| API Contract Integrity Gate | **pass** | 1m34s |
| E2E Tests (chromium) | **pass** | 7m04s |
| E2E Tests (mobile-chrome) | **pass** | 6m14s |
| M9 Forensic Evidence Collection | **pass** | 5m36s |
| CodeQL (status) | **pass** | 4s |
| **Plan / Execute / Reconcile** | **fail** | 28m43s — see §7 P1 |

**All four required checks pass.** They are pinned by ruleset `20127383` — not
branch protection, whose endpoint returns 404 "Branch not protected" even though
`main` is protected.

### 1.2 Quality metrics

| Metric | Result |
|---|---|
| TypeScript errors (`tsc --noEmit`) | **0** |
| ESLint errors | **0** (179 pre-existing warnings) |
| Build errors | **0** |
| Frontend tests (vitest) | **1,381 / 1,381** |
| Backend unit tests | **3,160 passed** |
| API contracts | **pass** (161 collected) |
| Mutation smoke (consecutive runs) | **pass**, worktree clean after |
| Mutation threshold | **unchanged** |
| Verification threshold | **unchanged** |
| Quality threshold | **unchanged** |
| Security findings | **justified / closed** |

`git diff bfcf336b..HEAD` over the threshold-bearing configuration files
(`backend/pyproject.toml`, `verification.yaml`, verification config) returns
**0 changed lines**.

### 1.3 Safety constraints honoured

Untouched: `feature/program-12-platform-certification` @ `0c8410c3`,
`recovery/program-r-forensic-reconstruction` @ `d5db3c08`,
`recovery/m9-c31-loss-06230db0` @ `06230db0`, and `stash@{0}`.

---

## 2. Repository

### 2.1 Inventory (Agent 1)

4,808 tracked files classified as SOURCE / TEST / CONFIGURATION / GENERATED /
RUNTIME STATE / TOOLING / DOCUMENTATION / LEGACY / UNKNOWN.

| Path | Files | Classification |
|---|---:|---|
| `runtime/foundation/` | 326 | SOURCE — verification/platform core, primary authority |
| `runtime/platform/` | 70 | SOURCE — platform API services, AI control layer |
| `runtime/system/` | 59 | SOURCE — context/workspace/selection runtime |
| `runtime/tests/` | 173 | TEST — 154 `test_*.py`, flat |
| `runtime/generated/` | 2,149 | GENERATED (mixed) — milestone evidence + scripts |
| `runtime/archive/` | 30 | GENERATED — archived execplan logs |
| `backend/src/` | 310 | SOURCE — FastAPI app, engines, services |
| `backend/tests/` | 347 | TEST — 203 `test_*.py` in 13 category directories |
| `frontend/app/` | 54 | SOURCE — Next.js App Router |
| `frontend/tests/` | 162 | TEST |
| `tools/` | 21 | TOOLING |
| `testing/` | 8 | TEST — TypeScript vitest mirror of runtime contracts |

### 2.2 The generated-artifact decision

The brief's proposal to gitignore all of `runtime/generated/` was **refuted by
reproduction** before being implemented:

```
fresh clone, runtime/generated/ removed, pytest runtime/tests --collect-only
→ E   ArchitectureNotDiscovered: Canonical architecture artifact missing:
      runtime/generated/architecture-inventory.json
1 error during collection — Interrupted
```

`runtime/foundation/architecture/provider.py` is the canonical architecture
authority and requires that artifact. **326 test files** read `runtime/generated`
as *inputs*, and no bootstrap step regenerates the milestone evidence. `.gitignore`
also records that a previous blanket attempt was reverted by CI with 90 failures.

The permanent solution shipped instead is a **two-class taxonomy** — both change
on every run, but they answer different questions:

- **Evidence** — *what a run concluded*. `evidence/summary.*`,
  `architecture-inventory.json`, milestone certification records. **Tracked**;
  changing is the point.
- **Telemetry** — *that a run happened*. `engineering-events.jsonl` (append-only
  event log) and the derived `engineering-history.json`. **Ignored**, on the same
  rationale already applied to `git-fetch-events.jsonl`.

Measured result: a full `runtime.verify contracts` run went from **4 dirty files
to 0 non-evidence**.

### 2.3 Cleanup ledger

Every deletion carries an evidence-backed reason from the permitted set
(`unused` | `obsolete` | `duplicate` | `replaced` | `generated` | `demonstrably
unreachable`).

| Item | Reason | Evidence |
|---|---|---|
| `runtime/tests/test_m9_c50_stop_gate9_failure_modes.py` | **duplicate** | 1,263 lines, **zero test functions**, byte-clone of `audit_final_freeze.py` differing by one `sys.path.insert`. Counted among "154 tests" while contributing 0. *(Independently re-verified during integration via AST parse.)* |
| 6 mutmut-generated files under `backend/tests/mutation_infra/mutants/` | **generated** | Already matched by `.gitignore:120`; untracked, files remain on disk |
| 50 tracked-but-ignored files (`runtime/archive/*.stdout/.stderr`, `test-results/`, `dependency-reports/`) | **generated** | Verified: no test reads them; `dependency-update.yml` only produces/uploads them as artifacts |
| `servers/` submodule gitlink | **demonstrably unreachable** | `git cat-file -t ada8803d…` → object absent; `git log --all -- .gitmodules` → 0 commits; `git submodule status` errors on it |
| `check_health()` in `scripts/launch.sh` | **replaced** | Superseded by the real readiness poll |

**Retained deliberately, with reasons:** `backend/tests/probes/test_m4_exit_probe.py`
(an intentional always-failing probe, explicitly excluded by `norecursedirs` —
deleting it removes a deliberate artefact); `runtime/tests/audit_final_freeze.py`
(the *surviving* copy of the deleted pair — removing it deletes the tool);
`.kilo/plans/` and `memory-bank/` (hand-maintained records — **un-ignored** rather
than deleted, since they are the audit trail for past recovery work).

**Untracked-but-ignored contradiction: 76 files → 0.** 50 bulk files were
untracked; 27 records were un-ignored by *removing* the blanket rules rather than
negating them, because git does not descend into an excluded directory and a `!`
exception there is unreachable for any new file.

---

## 3. Tests

### 3.1 Taxonomy (Agent 1)

**Backend — by directory, authoritative:**

| Directory | `test_*.py` | Category |
|---|---:|---|
| `unit/` | 90 | unit, nested by engine |
| `properties/` | 28 | property-based (Hypothesis; own `conftest.py`, 8 strategies) |
| `contract/` | 27 | contract, incl. the tracked `contract/generated/` baseline |
| `capability/` | 13 | capability |
| `integration/` | 12 | integration |
| `invariants/` | 10 | money-representation invariants |
| `mutation_infra/` | 7 | meta/tooling |
| `meta/` `architecture/` `audits/` `golden/` `mutation_trust/` `probes/` | 15 | various |
| root | 1 | — |

**Runtime — by prefix, implicit:** `test_platform_api_phase*` (9),
`test_m9_c4*`/`test_m9_c5*` (20 per-milestone certification gates),
`test_vea5_*` (4), `test_m9c5*`/`m9c6*`/`m9c7*` (14, note: no `_`),
`test_mut*` (6), remainder (~80 by subject).

**Marker drift:** 11 markers are declared but **9 are unused** (`unit`,
`integration`, `property`, `invariant`, `golden`, `meta`, `mutation`,
`capability`, `performance`). Only `contract` (161) and `slow` (2) are used.
Directory is the real taxonomy; the markers are not load-bearing.

**Uncollected:** `runtime/tests` 154 on disk / 153 collected (1 — the proven
duplicate). `backend/tests` 203 / 201 (2, both intentional).

### 3.2 Naming policy

Derived from what the codebase already does, not invented. The strongest signal:
**the repository already prefers capability names** — the milestone-numbered files
are the exception and cluster in one era (M9-C48 → M9-C72).

```
test_<capability>_<behaviour>[_<qualifier>].py        # preferred
```

The policy was **documented but deliberately not executed as a mass rename** —
the highest-value finding was that mass renaming would break CI path references
for no functional gain.

### 3.3 Test defects fixed

| Defect | Fix |
|---|---|
| `test_evidence_cleanup_stress.py` ran real `rmtree` against the tracked `runtime/generated/` tree | Pass `EvidenceRetention(generated_dir=<tmp_path tree>)`; all 4 tests now hermetic |
| `test_f006_configuration_divergence.py` rewrote the real tracked `verification.yaml` in place | `shutil.copy2` to `tmp_path`, redirect `config_loader.DEFAULT_YAML_PATH` via `monkeypatch` |
| `test_edge_cases_property` missing the DB-isolation fixture its 4 siblings use | Now calls `_fresh_reconciliation_db(_pristine_db_template)` |
| `test_coverage_path_authority.py` — 4 byte-identical `_coverage_run` calls whose names promised 4 contexts no body established | Each body now actually chdirs / clears `PYTHONPATH,VIRTUAL_ENV,PYTHONHOME` / sets CI vars. All four would previously have passed even if `_coverage_run` stopped pinning `cwd=BACKEND_DIR` |
| `Path(".venv/bin/coverage").resolve()` resolved against the *pytest process's* cwd | Uses the module's own `VENV_BIN` resolution. Verified by running the test from `/tmp` |
| `test_m9_c55.py` — 4 hardcoded `.venv/bin/python` argv entries | `sys.executable`. Verified equivalent: g30 passes in 133s vs 140s baseline. **The deliberately repeated runs in `test_g20` were preserved — there the repetition *is* the assertion** |

**Zero coverage reduction:** collection counts identical — 2,564 runtime, 4,144
backend.

### 3.4 Slow-test report (headline)

`test_m9_c55.py` is 686s — **55% of the entire runtime suite's cost** — with 11
recursive nested-pytest sites. `test_mutation_infra.py::test_r2_…` is 213s in a
single test.

**Not optimized, deliberately.** `test_g30_regression_green` re-runs three whole
modules the outer suite already executes. Removing it would delete a *named
certification assertion* — coverage reduction, which the brief forbids. Recorded
as P4 (timing fragility) instead.

**Caveat stated by Agent 1:** no BEFORE/AFTER wall-time pair exists, because a
full runtime run projected ~3.6h under 4-core load average 15–18 with two other
agents running. A pair produced under those conditions would not be comparable to
anything. **The counts are trustworthy and unchanged.**

---

## 4. Workflows

### 4.1 The 14-on-disk vs 18-on-GitHub reconciliation (Agent 2)

Every entry's real path resolved via `gh api`. The 4 extras split into two
distinct causes:

| Cause | Entries |
|---|---|
| GitHub-managed `dynamic/` pseudo-paths (no file in the repo) | `dependabot/update-graph` (329940660), `github-code-scanning/codeql` (330860652) |
| **Ghost registrations** — files that never existed on `main` | `codeql.yml` (332570115), `zz-matrix-probe.yml` (372442200) |

Both ghosts return **zero commits** for `git log main -- <path>`. `zz-matrix-probe.yml`
has no reachable git history on any ref at all.

### 4.2 CodeQL — the duplicate is cosmetic

| Workflow ID | Name | State |
|---|---|---|
| 332453015 | CodeQL Security Analysis | **live authority** — `security-codeql.yml`, 110 runs |
| 330860652 | CodeQL | retired default setup, dead since 2026-08-12 |
| 332570115 | CodeQL Security Analysis | ghost |

`code-scanning/default-setup` is **`not-configured`**, so `330860652` cannot be
supplying analysis. `python-database`, `javascript-database` and
`actions-database` were all written by `security-codeql.yml`. **Security coverage
was never traded for a cleaner-looking UI** — the change to `security-codeql.yml`
is comment-only, with `languages: python, javascript, actions`, the `Analyze` job
and the permissions blocks verified byte-identical.

**The ghosts cannot be deleted.** Integration attempted it:

| Workflow ID | `DELETE` result |
|---|---|
| 332570115 | `HTTP/2.0 404 Not Found` |
| 372442200 | `HTTP/2.0 404 Not Found` |
| 330860652 | `HTTP/2.0 404 Not Found` |

All three return 404 **even with an `admin: true` token**. The endpoint resolves
the workflow through the default branch's tree, where none of them exist — not an
authorization problem, unreachable at any privilege. Recorded in-repo so the
duplicate is never "resolved" by weakening coverage.

### 4.3 Overlap resolved

| Finding | Action |
|---|---|
| `m9-forensic-diagnostic-lab.yml` re-ran `verify quick` + `verify backend` on every PR — already run by Quality Gate (`quality.yml:98`) and Backend Verification (`backend-verify.yml:67`) | Duplicated executions removed. ~9 min × 82 runs, and the workflow is **not a required check**. All 19 forensic capture steps and the trigger kept |
| `mutation-pr.yml` inlined `actions/upload-artifact` (Rule 3/4) | Routed through `./.github/actions/upload-runtime` |

### 4.4 Supply-chain hardening

**29 external action references SHA-pinned** across 14 workflows and 6 composite
actions, each resolved through the GitHub API to an immutable commit with the
human-readable version retained as a trailing comment. Three were floating major
tags (`github/codeql-action/*@v3`, `actions/github-script@v7`). Local composite
actions are first-party code and untouched.

### 4.5 The constitution enforcer (integration)

`validate_actions.py` is mandated by `docs/GITHUB_ACTIONS_CONSTITUTION.md`
("must pass with zero errors") and **was wired into no workflow** — so the
architecture it governs drifted unobserved. It reported **24 errors; it now
reports 1.**

| Count | Class | Disposition |
|---:|---|---|
| 11 | Rule 9 — summaries ran `doctor`, constitution mandates `status` | **Fixed.** Measured first: identical output tail, both exit 0, ~12s either way |
| 6 | Rule 8 — mutation shards flagged as wrong profile | **Enforcer bug** (below) |
| 4 | Rule 8 — `doctor`/`mutation` preflights | Enforcer fixed via documented auxiliary allowance |
| 2 | Rule 3/4 — inlined artifact upload | Fixed |
| 1 | Rule 8 — `frontend-verify.yml` bypasses the `frontend` profile | Outstanding → P3 |

**The enforcer was stricter than its own constitution.** Rule 8 as written requires
a workflow to *execute* `runtime/verify.py`; it never required exactly one command
per workflow. `mutation.yml` is one responsibility expressed across the M9-C71
sharded campaign (`mutation-plan` → `mutation --shard` → `mutation-aggregate` →
`mutation-trust`). The enforcer now accepts a documented subcommand of a
workflow's own profile and still rejects a different profile's command.

**This was regression-tested**: substituting `runtime.verify backend` into
`quality.yml` still raises Rule 8 errors, so the check was not weakened.

> **Self-correction:** the validator was initially reported as "exits 0". That was
> a measurement error — `$?` captured `tail`, not the script. It correctly
> `return 1` on errors.

### 4.6 Visual-regression baselines — made a CI operation

Baselines are rasterisation-specific. Integration **regenerated all 10 on a
workstation, saw them pass locally, and had to revert them** because they encoded
this machine's font rendering.

Rather than leave that as tribal knowledge, regeneration became a sanctioned,
repeatable operation:

- `run_playwright_tests.sh` honours `PLAYWRIGHT_UPDATE_SNAPSHOTS=1`
- `playwright.yml`'s existing `workflow_dispatch` gained an `update_snapshots`
  input
- the chromium/mobile jobs upload per-project artifacts

**The first attempt silently did nothing** — `profiles.py` builds the Playwright
command itself and never invokes the script that had been edited. The profile was
then fixed to expand the same variable. 14 baselines were regenerated **on a
GitHub runner** and adopted. Thresholds, masks and diff limits are untouched.

---

## 5. Platform Console

### 5.1 Route matrix (Agent 3) — produced from live browser renders

Every row is an observed render in headless Chromium (1440×900) and Pixel 5, with
`page.on('request')`/`page.on('response')` recorders attached **before**
navigation, cross-checked against the backend request log.

| Route | HTTP | Data source | Functional | States |
|---|---|---|---|---|
| `/platform` | 200 | `/platform/v1/health`, `/events`, `/errors/current`, `/tasks`, `/capabilities` | yes | loading, error, data |
| `/platform/health` | 200 | `/platform/v1/health` | yes — 3 authority rows | loading, error, data |
| **`/platform/status`** | **404** | backend `/platform/v1/status` **is live** | **no surface** | — (P2 #9) |
| `/platform/capabilities` | 200 | `/platform/v1/capabilities` | yes — 8 stages × 55 capabilities | loading, error, data |
| `/platform/capabilities/[id]` | 200 | blast-radius + graph | yes | loading, error, data, empty |
| `/platform/verification` | 200 | recent runs, recommendation, POST run | yes — real execution + polling | loading, error, data, empty |
| `/platform/verification/[capability]` | 200 | capability detail | yes; unknown id → readable state | loading, **error (fixed)**, data |
| `/platform/runs` | 200 | `/platform/v1/runs` | yes | loading, error, data |
| `/platform/runs/[runId]` | 200 | `/platform/v1/runs/{id}` | yes — 50 runs resolved | loading, error, data, empty |
| `/platform/evidence` | 200 | `/platform/v1/evidence` | yes — explicit empty state | loading, error, data, empty |
| `/platform/diagnostics` | 200 | consolidated: health + errors + tasks | yes — 5 categories | loading, error, data, empty |
| `/platform/diagnostics/detail/[id]` | 200 | **local** `/api/diagnostic-signatures` (**fixed** — was a 404 backend path) | partially | loading, error, data, empty |
| `/platform/framework` | 200 | integrity + self-tests | yes — K1–K9 9/9 | counter-mismatch disclosed |
| `/platform/workflows` | 200 | `/platform/v1/workflows` | yes | loading, error, data, empty |
| `/platform/architecture` | 200 | 6 architecture endpoints | yes | loading, error, data, empty |
| `/platform/errors` | 200 | current/recent/recurring | yes | loading, error, data, empty |
| `/platform/history` | 200 | runs + baselines | yes | loading, error, data, empty |
| `/platform/history/compare` | 200 | POST compare | yes **with** `?current=` | **entry state (fixed)** |

Extra routes adjudicated as **keep, not obsolete**: `/architecture`, `/errors`,
`/framework`, `/history` — all in `NAV_ITEMS`, all 200, all live.

### 5.2 Independence — two layers, both stated precisely

This reconciles what Agent 4 proved and what Agent 3 found; they are not in
conflict, they describe different layers.

**Browser level — YES, and now enforced rather than intended.** The console reads
only `/platform/v1/*` (plus its own `/api/diagnostic-signatures`). No
`/api/v1/members`, `/accounts`, `/transactions`, `/workspaces/*` or `/behaviour/*`
is issued from any `/platform/**` page. **This was not true before:** the
root-layout `MemberProvider` fired `GET /api/v1/members` on every console page.
Fixed via `components/os-shell/member-boundary.tsx`, covered by an E2E invariant
across 15 routes.

Agent 4 independently demonstrated the console serving with **nothing listening on
the backend port**.

**Process level — NO, and this is a real architectural finding, not a frontend
defect.** `backend/src/api.py` mounts the platform router on the *same* FastAPI
application as the entire financial API. There is no way to serve `/platform/v1/*`
without booting the financial application (SQLite, all routers, all engines).
Measured cost: first `/platform/v1/health` after boot took **39s**; one batch of
five console requests reported `duration_ms=117218` each (117s) queuing behind it;
`/platform/v1/evidence` once reported `duration_ms=375118` (375s). Warm cache:
2–345ms.

**Operator consequence:** during the cold window every console page shows an
indefinite "Loading…" — the frontend has no request timeout, so it never surfaces
"the platform API is slow or unreachable", it just waits.

---

## 6. Application

### 6.1 Frontend/backend consumption (Agent 3)

Method: every route in `backend/src/routers/*.py` compared against every backend
path literal in `frontend/**`, mismatches confirmed against a live API with
`curl` and in a browser.

**Phantom endpoints (fixed):**

| Endpoint | Symptom |
|---|---|
| `/api/overview` (should be `/api/v1/overview`) | **404 — and invisible.** `useAsyncQuery.refetch` resolves through `queryClient.invalidateQueries`, which does not reject, so statement uploads reported success while the dashboard kept stale pre-upload totals. Phantom `exclude_transfers`/`member` params also dropped |
| `/platform/v1/diagnostics/signatures` | 404 — replaced with a local Next.js route reading the real signature store |

**Backend capabilities with no frontend surface (P1/P2):** three whole feature
areas unconsumed; `POST /api/v1/investments` returns **HTTP 500**, so the
Investments page cannot be populated; `GET /platform/v1/status` is live but has
no route; `POST /platform/v1/diagnostics/diagnose` and `/diagnose/register`
unconsumed.

### 6.2 UI defects fixed

| Defect | Fix |
|---|---|
| Fabricated financial movement in the Command Center | Unbound from a fabricated series |
| Ratios presented as rupees | Corrected |
| Operations dashboard reporting **UNKNOWN** for healthy dimensions | `usePlatformHealthSummary` now reads top-level health fields; the API was reporting HEALTHY/SAFE/CURRENT/VALID/READY all along |
| Sidebar badge hardcoded to always show "5" | Live count |
| Unsupported claim in a metric subtitle | Removed |
| Same score rendering as two different numbers | Frontend corrected; **backend defect remains open (§7 P2)** |
| Stale product identity in the app's About block | Corrected |
| `/platform/history/compare` had no entry state | Direct navigation now explains itself |
| Raw error objects rendered as page content | Readable states |
| Dead link from the dashboard | Fixed |

### 6.3 Charts

**Fixed:** Cashflow Trend two series bound to keys that do not exist; tooltip
suppressed the series name; duplicate chart headings.

**Verified good:** chart availability and empty states.

**Open:** Recharts emits `NaN` geometry on `/forecast` (§7 P0); `/forecast`
fabricated cashflow (§7 P0).

**Recorded as NOT defects** (extraction artifacts, deliberately not "fixed"):
`₹85,000.0085.0%` on `/net-worth` (an `innerText` scrape artifact), `Trend: down`
beside `+0.0% from 1M` (the `-₹` glyph is a separate element), Y-axis tick order
read from a screenshot.

**No frontend money arithmetic.** The behaviour-score display states the value as
the authority gives it and flags the discrepancy rather than dividing.

### 6.4 The behaviour score — root cause

Verified directly against backend source:

```
compute_wellness_score        → wellness_score * 100, clamped [0,100]
                               (wellness.py:88-89)
compute_financial_profile     → wellness_score_bps = int(wellness_score * 10000)
                               (behaviour_service.py:217)   ← scaled again
get_wellness_score            → reads that column straight into the response,
                               no division (:328-333, :548)
classify_wellness_band        → thresholds 90/75/50/25, so ≥90 ⇒ "Excellent"
no-data fallback              → hardcoded Decimal("100")  (:276-289)
                               ← why an empty database masked it entirely
```

Live response: `{"score": "7561.45", "band": "Excellent"}`. Agent 3 initially
tightened the schema to `.max(100)`, then **reverted its own change** after E2E
proved it blanked the whole `/behaviour` workspace. The console now flags the
out-of-contract value (`WELLNESS_SCORE_DOCUMENTED_MAX`) instead of rejecting a
valid HTTP 200 or inventing a corrected one.

`components` keep their 0-100 bound — they are genuinely 0-100 and not
double-scaled.

---

## 7. Operations

### 7.1 Startup inventory (Agent 4)

Exhaustive search across root scripts, `scripts/`, `servers/`, both
`package.json` blocks, backend entrypoints, `docker-compose*`, `Makefile`,
`justfile`, `.husky/`, `backend/scripts/`, `tools/`, Python `__main__` and
`[project.scripts]`, **and git history** for deleted launchers still referenced
by docs.

**Negative results (searched, nothing found):** no `docker-compose*`, no
`Makefile`/`justfile`, no `*.ps1`/`*.cmd`, no second frontend launcher, no Python
`__main__` startup entry, exactly one `[project.scripts]` entry (`verify`, which
is verification not a launcher).

Classification vocabulary: `CANONICAL` · `VALID SECONDARY` · `DUPLICATE` ·
`OBSOLETE` · `BROKEN` · `UNSAFE`.

### 7.2 The canonical entry point

```
./start.sh              # Unix
start.bat               # Windows (WSL2)
```

Both are thin wrappers over **one** implementation, `scripts/launch.sh`, so Unix
and Windows share one code path, one environment contract, one set of URLs.

```
validate environment → port preflight → orphan detection → start backend
→ start frontend → wait for REAL readiness → print URLs
```

- Environment validated **before any process is spawned**, so a broken
  environment cannot leave an orphaned backend.
- Readiness waits on `/ready`, **not** a static `/docs` page that answers 200
  before the app is ready.
- Shutdown: `./scripts/launch.sh stop` (or Ctrl+C), which tears down **only the
  processes this launcher started**.

### 7.3 Nine pre-existing defects fixed

Including an **UNSAFE** teardown that machine-wide `pgrep`'d `next-server` and
would kill a concurrent process — demonstrated live, not theorised. Also:
`start.sh` discarding arguments (so `./start.sh stop` would *start* the app), a
Windows path passed to `bash` under WSL, and port collisions.

### 7.4 Clean-start validation

Performed cold in the agent's worktree, with real output captured: environment
validated, backend ready, frontend ready, Platform Console reachable, main
application reachable, URLs printed, and shutdown clean with **no orphaned
processes** (verified with `ps`/`ss`).

> **Caveat carried forward:** validation ran on ports 8010/3010 because Agent 3
> held the canonical 8000/3000, and `start.bat` remains **unverified at runtime**
> (needs Windows + WSL2).

---

## 8. Remaining work, prioritised

### P1 — `Plan / Execute / Reconcile` fails (`exec-0006`, 0.00s)
`runtime.verify check` fails on a single plan task that exits immediately,
aborting two more. **Not a required check**, and it failed identically *before* the
Agent 3 merge, so it is not from that work. `exec-0006` completing in **0.00s**
indicates a missing precondition rather than a test failure. The
`reconciliation-report` artifact is available from run `37010443180`.
**Next:** extract the plan's `exec-0006` command from that report and run it
locally.

### P1 — `/forecast` renders a fabricated cashflow projection
**Independently reproduced against a live backend.** `GET /api/v1/forecast`
returns 12 `cashflow_projections` in which **every** row is `income_paise:
10000000` (₹1,00,000.00), `expenses_paise: 6000000` (₹60,000.00), `net_paise:
4000000` (₹40,000.00), and the month keys **repeat** (`2026-12` twice, `2027-03`
twice).

Agent 3 attributed this to frontend constants; **the owner is the backend** —
`services/forecast_service.py:159` contains `income = 10000000  # ₹1,00,000`
inside `_generate_cashflow_projections`, and the mapper passes it straight
through. `git diff bfcf336b..HEAD -- backend/src` is empty, so this is untouched
baseline behaviour. A sibling placeholder exists at `services/account_service.py:228`.

Future income and expense are shown to a user as a projection, in the same table
as real net-worth projections.
**Next:** implement a real projection, or stop presenting the series until one exists.

### P1 — Recharts `NaN` geometry on `/forecast`
Follows from the row above — duplicated/empty series produce degenerate geometry.

### P2 — Backend wellness-score scale (finance domain)
Minimal fix identified: divide by 100 on the read path in `get_wellness_score`.
**Deliberately not applied** — it changes what every consumer and golden dataset
sees. **Next:** finance-owner decision, then golden-dataset review.

### P2 — Platform Console cold start is unusable
No request timeout, so the console shows an indefinite "Loading…" during the
39s–375s cold window instead of reporting that the API is slow or unreachable.
The correct fix belongs to the startup path and gateway timeout policy.

### P3 — `frontend-verify.yml` bypasses the `frontend` profile
Delegates to `run_frontend_verification.sh` rather than the registered `frontend`
profile (`profiles.py:468`). Last remaining validator error. **Required check** —
needs a parity proof, not an edit.

### P3 — Three backend feature areas have no frontend surface; `POST /api/v1/investments` returns 500
The Investments page cannot be populated.

### P4 — `test_m9_c55.py` timing fragility
300s internal timeout vs ~345s actual under CPU contention; passes in isolation
(~133s). Raise the timeout or hoist shared work — **without** merging the
deliberately-repeated runs in `test_g20`.

### P4 — No working E2E fixture seed
`tools/e2e_seed.py` cannot seed anything. Blocks reproducible chart validation;
a documented manual seeding recipe was recorded instead.

### P5 — Dead CodeQL workflow registrations
Cosmetic, structurally unremovable (404 even as admin). No action — documented so
the duplicate is never "fixed" by weakening coverage.

---

## 9. Corrections made during this phase

Recorded because they are part of the honest record.

| Claim | Correction |
|---|---|
| "`/platform/runs/[runId]` did not exist at baseline; added" | **Wrong.** The inventory used `find -maxdepth 3`, which cannot reach a depth-5 path. Verified present at `bfcf336b` with `git cat-file -e`. Caught by Agent 3; no such change was made |
| "validate_actions.py exits 0" | **Measurement error** — `$?` captured `tail`. It correctly `return 1` on errors |
| "19 vitest failures after the A3 merge" | **Environmental.** `platform-c67.2.contract.test.ts` requires a live backend on `:8000`, which was down. With it running: 1,381/1,381 |
| "`/forecast` fabrication may not be real — the API returns the field" | **Wrong inference.** The field was returned but every row was an identical placeholder. The defect stands; only the owner was refined (backend, not frontend) |
| "A c55 regression after my edit" | **Contention.** Re-running with an identical selection gave 133s vs 140s baseline |
| "Visual baselines regenerated" | **Wrong environment.** Regenerated on a workstation, reverted, then regenerated on a GitHub runner |

### Regressions introduced and caught

| Regression | Resolution |
|---|---|
| Removing the M9 lab's only two `continue-on-error` steps turned 3 green `test_m9_c54.py` tests red (they use that workflow as the fixture for proving continue-on-error masking is *detectable*) | Restored on "Compare all Git changed-file calculations" — a genuine best-effort probe in an evidence-capturing workflow. `test_m9_c54.py` 87/87 green |
| SHA-pinning invalidated 6 tests matching `@v3` suffixes ("only found 0 external action pins") | Root cause: `USES_PATTERN` anchored to end-of-line, broken by the trailing `# <tag>` comments. Taught the tests to accept immutable SHAs, with `VERIFIED_SHAS` declared exactly as `VERIFIED_PINS` is. **Regression-tested both ways**: a bogus SHA trips 3 tests; 54/54 pass on the real tree |
| `black` rejected 3 test files; later `profiles.py` | Formatted; CI-scope black clean across 849 files |

---

## 10. Deliverables

**This report** — `docs/audits/m10-final-report.md`

| Document | Contents |
|---|---|
| `m10-agent1-repository-inventory.md` | 4,808-file classification, environment caveats |
| `m10-agent1-test-taxonomy.md` | backend/runtime taxonomy, marker drift, uncollected files |
| `m10-agent1-slow-test-report.md` | durations, attribution of failures, measurement limits |
| `m10-agent1-cleanup-ledger.md` | every deletion with evidence |
| `m10-agent1-naming-policy.md` | convention + rationale for not mass-renaming |
| `m10-agent2-workflow-matrix.md` | all 18 workflows: trigger, jobs, deps, status |
| `m10-agent2-codeql-ownership.md` | duplicate root cause + non-removability proof |
| `m10-agent3-01-platform-console-matrix.md` | 23 routes, method, independence proof |
| `m10-agent3-02-consumption-findings.md` | phantom endpoints, unconsumed capabilities |
| `m10-agent3-03-ui-and-charts.md` | UI defects, chart correctness, non-defects |
| `m10-agent3-04-remaining-issues.md` | 21 prioritised product issues |
| `m10-agent4-startup-inventory.md` | every entry point classified |
| `m10-agent4-canonical-startup.md` | operator contract + clean-start transcript |
| `m10-agent4-cleanup-ledger.md` | obsolete-script ledger |
| `m10-ci-constitution-reconciliation.md` | the 24→1 enforcer reconciliation |

Plus a root `README.md` documenting the canonical start/stop contract.
