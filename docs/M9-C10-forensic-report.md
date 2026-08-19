# M9-C10 — CI Workflow & Playwright Execution Forensic Report

> **Mode:** DIAGNOSIS ONLY. No workflows, configs, tests, application code, or
> verification-framework code were modified. No CodeQL/forensic workflows deleted.
> No Playwright matrix, test count, retries, or timeouts changed.
> Report generated 2026-08-16 from repository working tree (`m9c9-merge-authorization-resolution`)
> plus live GitHub API evidence (`gh`, authenticated as `simcitysocial97-dev`).

---

## 1. Executive verdict

1. **CodeQL (Track A):** GitHub is showing **three distinct CodeQL surfaces**, not two.
   - **A.** `.github/workflows/security-codeql.yml` — the **authoritative, source-controlled** gate. Job name `Analyze`. **Required by the `protect-main-branch` ruleset** (`required_status_checks` includes `"Analyze"`). Last 3 runs SUCCESS. This is the intended certified security gate.
   - **B.** `dynamic/github-code-scanning/codeql` — **GitHub-managed (Advanced Security default)**. Check name `CodeQL`. **NOT required** by any ruleset. Currently non-blocking/failing. It is a *separate* analysis surface that the architecture explicitly intends `security-codeql.yml` to replace. Do **not** delete without disabling GHAS default code scanning; it is not a duplicate you can simply drop.
   - **C.** `.github/workflows/codeql.yml` — a **stale/ghost API registration**. The file was created and deleted on a feature branch (`6db591c0`/`8100e361`/`4c4b1a44`); `gh api` contents returns **404 on `main`**; `git ls-files` shows it absent. The Actions API still lists it (`id=332570115`, only one run, cancelled). This is the "old/stale workflow registration" hypothesized. It is inert.
   - Conclusion: one intended gate (A), one GitHub-managed (B), one stale ghost (C). **No source-controlled duplicate of A exists.**

2. **M9 Forensic Diagnostic Lab (Track B):** Classified **B — Diagnostic workflow intentionally retained, classify explicitly as non-gating diagnostic infrastructure.** It is active, failing (pre-existing, non-blocking), **not** in the ruleset required checks, generates evidence artifacts consumed by nobody else, and has never been a merge gate. Do not delete; reclassify its intent in documentation.

3. **Playwright (Track C):** The numbers reconcile. `npx playwright test --list` reports **"Total: 1392 tests in 12 files" = 232 unique tests × 6 projects.** The "1,392-test matrix" comment and the "~1,300 local discovery" are the **same full matrix**, not a different test set. The 74,000 lines of CI output is **logging-dominated** (Next.js build + backend `uvicorn` stdio + retries + visual-regression base64), **not** test multiplication — there is exactly one `testDir` and no `test.describe.configure()`. The single most important real defect found is a **CI database/backend provisioning gap**: the backend is launched in `global-setup.ts` via `python3 -m uvicorn`, but **`uvicorn` is declared in neither `pyproject.toml` nor `requirements.lock`**, so it is not guaranteed installed in CI. DB-backed E2E failures are therefore at least partly **environment-precondition failures**, not application failures.

---

## 2. CodeQL workflow inventory

### 2.1 Source workflows
| Path | On `main`? | State | Evidence |
|---|---|---|---|
| `.github/workflows/security-codeql.yml` | YES (`git ls-files`) | active | `gh api actions/workflows` id `332453015`; runs 39–41 SUCCESS |
| `.github/workflows/codeql.yml` | **NO** (404 on `main`) | active (ghost) | `gh api contents …/codeql.yml` → `Not Found`; `git ls-files` absent; only 1 run (cancelled, `6db591c0`) |

Introduced: `security-codeql.yml` in commit `ca59292d` ("VEA-5 M9: CodeQL security-analysis surface (source-controlled)").

### 2.2 GitHub-managed workflows
| Path | State | Evidence |
|---|---|---|
| `dynamic/github-code-scanning/codeql` | active | `gh api actions/workflows` id `330860652`, name `CodeQL`; runs: "CodeQL Setup" (success, 2026-08-10), "PR #3" (success, 2026-08-12). This is GitHub Advanced Security's default code-scanning workflow, not source-controlled. |

### 2.3 Check-run mapping
- `security-codeql.yml` → workflow display name **"CodeQL Security Analysis"**, job **`Analyze`**. The ruleset requires exactly `"Analyze"`.
- `dynamic/github-code-scanning/codeql` → check name **`CodeQL`** (app = GitHub Advanced Security). **Not required.**
- Ghost `codeql.yml` → would surface as "CodeQL Security Analysis" but produces no runs on `main`.
- `gh pr checks 5` historically showed `CodeQL fail` while the real `Analyze` run succeeded — this is the stale/ghost status artifact documented at `progress.md:2607`.

### 2.4 Historical provenance
- `security-codeql.yml`: created `ca59292d` (M9/VEA-5). Comment block states it is the "SOURCE-CONTROLLED successor to the GitHub-managed dynamic CodeQL workflow."
- `codeql.yml` (ghost): created+deleted twice on feature branches (`6db591c0` create, `8100e361` delete, `4c4b1a44` delete). Left a dangling Actions API registration.
- `dynamic/github-code-scanning/codeql`: enabled via repo Security → Code scanning default setup (GHAS).

### 2.5 Functional duplication analysis
- **A vs B (security-codeql.yml vs dynamic):** Both run `github/codeql-action` over `python, javascript`. Latest code-scanning analysis (`id=1624606827`, 2026-08-16) has `analysis_key=".github/workflows/security-codeql.yml:analyze"`, 9 results, 130 rules — i.e., the **active SARIF is produced by A**. B (dynamic) is a parallel, redundant surface. They are functionally duplicative *in analysis coverage* but differ in provenance/control: A is versioned & required; B is GitHub-managed & non-required.
- **A vs C (security-codeql.yml vs ghost):** Not a functional duplicate — C does not exist on disk.

### 2.6 Keep/remove classification
| Entity | Classification | Action |
|---|---|---|
| `security-codeql.yml` | Authoritative, required gate | **KEEP.** Do not remove. |
| `dynamic/github-code-scanning/codeql` | GitHub-managed, redundant, non-required | **KEEP but acknowledge as redundant.** Removal = disable GHAS default code scanning in repo settings; do not "delete a YAML file" (none exists). Decision deferred to repo security policy. |
| `codeql.yml` (ghost) | Stale API registration, no file | **No action needed** (already deleted from all branches). Note stale registration in API. |

---

## 3. M9 Forensic Evidence Collection

### 3.1 Origin
Introduced in `9a996032` ("M9: Add forensic diagnostic lab workflow for CI failure investigation"). Subsequent fixes: `346eb0e2`, `b2e66e95`, `9ff…`, `b9ff22bf`, `6cb0098d`, `6157a4b0`, `b021fed0`, `6d1d24de`, `bc354430`.

### 3.2 Purpose
Collect immutable CI failure diagnostics (git topology, changed-file calculations, `verify.py`/orchestrator/executor identity, Python env, Black differential, `verify.py quick`/`backend` capture) and **upload them as artifacts** (`m9-execution-forensic-<run_id>`, retention 30 days). It was created to investigate the earlier Playwright "hang"/full-suite-expansion failure.

### 3.3 Current dependencies
- Calls `runtime/bootstrap.sh` (or `pip install -e ".[all]"`), then `.github/scripts/run_fast_checks.sh`, a 4-way Black matrix, `python runtime/verify.py quick` and `verify.py backend`, and produces `runtime/generated/evidence/*` + `diagnostic-summary.json`.
- Reads `runtime/verify.py`, `orchestrator.py`, `executor.py` (identity + grep), `backend/pyproject.toml` Black config.

### 3.4 Current consumers
**None.** No workflow depends on its artifacts; it uploads to a dead-letter artifact namespace. It is a terminal diagnostic sink.

### 3.5 Failure analysis
- Last 3 runs (`29`–`31`) all **failure**. Documented pre-existing, non-blocking at `progress.md:2589–2643`: failures are `IndentationError` in an inline heredoc (`Verify runtime dependency health`) and `black: command not found` (`Black identity`) — both **lab-workflow-internal environment issues**, not application/verification defects.
- `progress.md:63` notes the lab intentionally used a *custom minimal bootstrap* that bypassed the canonical actions, explaining missing tools in that run.

### 3.6 Keep/remove classification
**B — Diagnostic workflow intentionally retained, explicitly classified as non-gating diagnostic infrastructure.** It is NOT a required merge check (absent from ruleset `required_status_checks`). It has never been a merge gate. Recommend: keep, but (a) fix its internal heredoc/Black environment defects if it is to remain useful, and (b) document its intent as diagnostic-only. **No deletion during M9-C10.**

---

## 4. Playwright execution chain

```
.github/workflows/playwright.yml
  on: push/PR to main|master|develop (paths: frontend/** e2e/** runtime/**) + dispatch
  concurrency: group per ref, cancel-in-progress
  matrix.project = [chromium, firefox, webkit, mobile-chrome, mobile-safari, tablet]
  steps:
    - actions/checkout@v4 (fetch-depth: 0)
    - actions/bootstrap-runtime            (Python + root pyproject [all])
    - actions/setup-node-runtime (node 20, frontend)
    - actions/setup-playwright (browsers: chromium firefox webkit)
    - env PLAYWRIGHT_PROJECT=${{ matrix.project }}
      run: python runtime/verify.py playwright
        └─ verify.py → profile "playwright" (_VERIFY_PLAYWRIGHT_TASKS, bounded,
           respect_requested_scope=True per M9-C5/C8)
           task "playwright-e2e":
             "cd frontend && npm run build && npx playwright test ${PLAYWRIGHT_PROJECT:+--project=\"$PLAYWRIGHT_PROJECT\"}"
           task "playwright-aggregate": EvidenceAggregator().aggregate()
    - upload-runtime artifacts (cross-layer-map, knowledge-index, verification-cache,
      engineering-history, playwright-report, playwright-evidence)
    - Job Summary: python runtime/verify.py status
```

**Actual command executed per CI job (one project):** `cd frontend && npm run build && npx playwright test --project="<project>"` (env `CI=true`). NOT `run_playwright_tests.sh` (that script still exists and is referenced by `registry.py`/`evidence_contract.py` legacy registrations, but the active profile uses the inline command). Reporters: `html`, `json`, `list`, `junit`. `webServer` (CI): `python3 -m http.server 3000 --directory dist`. `globalSetup`: `./tests/global-setup.ts` (starts backend via `python3 -m uvicorn src.api:app --port 8000`).

---

## 5. Canonical Playwright test inventory

Generated from `npx playwright test --list` (authoritative, run locally 2026-08-16):

- **Files:** 12 spec files in `frontend/tests/e2e/specs/` (the only `testDir`).
- **Unique test declarations:** **232** (Playwright's own count).
- **Per-project executions:** 232 (one matrix job runs exactly one project).
- **Full matrix total:** **1392** (= 232 × 6 projects), matching the `playwright.yml` "1,392-test matrix" comment and the "232 tests" comment in `playwright.config.ts:31`.
- **Describe blocks:** 65 top-level `test.describe` (65 nested describe headings observed in list, e.g., "Layout Overflow" ×78, "Visual Regression - Full Pages" ×60, "Navigation" ×60, "Behavior Risk Deltas" ×42, …).
- **Parameterization/generation:** No `test.describe.configure()`, no `forEach`→`test()` generation loops. The 232 count is hand-written declarations; multiplication to 1392 is **exclusively the 6-project matrix**.
- **Tags:** none (no `test.use({tag})` / `--grep` tags found).
- **Projects:** chromium, firefox, webkit, mobile-chrome, mobile-safari, tablet (devices `Desktop Chrome/Firefox/Safari`, `Pixel 5`, `iPhone 12`, `iPad Pro`).
- **Fixtures:** `frontend/tests/e2e/fixtures/` — `comprehensive-reports.ts`, `css-helpers.ts`, `financial-assertions.ts`, `financial-scenarios.ts`, `mode-helpers.ts`, `report-generator.ts`, `seed-data.ts`, `test-fixtures.ts`.
- **Database dependencies:** only via the backend (see §11). No spec imports sqlite/DB directly.

**Inventory math (answers C1):**
| Metric | Value |
|---|---|
| Unique `test()` declarations | 232 |
| Describe blocks | 65 |
| Parameterized/generated tests | 0 (no generation loops) |
| Tests × projects (expected executions) | 232 × 6 = **1,392** |
| Tests × retries (CI `retries: 2`) | failing tests re-run up to 2× (≤ 3 executions each on failure) |
| Total expected executions (green) | 1,392 |

---

## 6. CI test inventory

CI executes **per-project shards** (6 jobs). Each job runs **232 tests** of one project with `retries: 2`, `workers: 4`, `timeout: 30000ms/test`, `forbidOnly: true` (CI). Build (`npm run build`) precedes the run inside the same step. The 1,392 figure is the union across all 6 jobs, **not** a single job's load.

---

## 7. Local vs CI inventory comparison

| Dimension | Local (`--list`, this env) | CI (per job) |
|---|---|---|
| Test files | 12 (same `testDir`) | 12 |
| Unique tests | 232 | 232 |
| Projects executed | all 6 (if no `--project`) | 1 (matrix shard) |
| Total listed | 1,392 | 232/job |
| Retries | 0 (`retries:0` non-CI) | 2 |
| Workers | undefined (Playwright default = CPUs) | 4 |
| `PLAYWRIGHT_PROJECT` | unset → full matrix | set → single project |
| Build | required by command | required by command |
| Backend launch | `global-setup` via `uvicorn` | `global-setup` via `uvicorn` |

The inventories are **identical in composition**; the only difference is CI shards by project and enables retries. There is **no different/extra test set** discovered in CI. The "~1,300" local discovery is the 1,392 matrix total.

---

## 8. Six-project execution matrix

| Project | Tests/job | Expected executions | Notes |
|---|---|---|---|
| chromium | 232 | 232 (+retries) | desktop Chrome |
| firefox | 232 | 232 | desktop Firefox |
| webkit | 232 | 232 | desktop Safari |
| mobile-chrome | 232 | 232 | Pixel 5 |
| mobile-safari | 232 | 232 | iPhone 12 |
| tablet | 232 | 232 | iPad Pro |
| **Total** | **1,392** | **1,392** | across 6 parallel jobs |

No project is excluded; the matrix is intact (constraint: do not reduce it).

---

## 9. Test multiplication analysis

- **Duplication hypothesis (C2): rejected.** Exactly **one** `playwright.config.ts`, one `testDir` (`frontend/tests/e2e/specs`), no `test.describe.configure()`, no second config, no root `e2e/` dir (only `frontend/tests/e2e`), no `forEach`→`test()` generation. `frontend/tests/.archive/app.test.ts` exists but is **outside** `testDir` and excluded.
- The only multiplication is the legitimate **6-project matrix** (232 → 1,392). This is expected coverage multiplication, not accidental duplication.
- `run_playwright_tests.sh` (which ran "ALL 6 projects" in one process) is **no longer on the CI path** (replaced by the inline per-project command), but is still referenced by `registry.py:432,602` and `evidence_contract.py:513` — a stale internal registration, not a runtime multiplier.

---

## 10. 74,000-line output attribution

`74,000+ lines` is **output volume, not test count**. With 232 tests/job, raw test enumeration (`list` reporter) accounts for only ~232–700 lines. The remainder is logging. Classified sources (estimate; precise counts require downloading a CI run log — see §22):

| Output source | Est. share | Evidence / reasoning |
|---|---|---|
| Next.js production build (`npm run build`) | Large | `npm run build` emits compilation, module, and warning output; runs every job before tests. |
| Backend `uvicorn`/app stdio | Large | `global-setup.ts` pipes backend `stdout`/`stderr` to `console.log`/`console.error`; uvicorn access logs + exception tracebacks. |
| Retries (CI `retries: 2`) | Medium | Failing tests re-execute and re-emit all logs up to 2×. |
| Visual-regression base64 | Medium–Large | `visual-regression.spec.ts` (60 full-page + 30 mobile + 24 states + 24 components snapshots); on failure, base64 diffs can be enormous. |
| Per-test `console.log` in specs/fixtures | Medium | Tests log scenario data, API responses. |
| Playwright `list` reporter | Small | ~1 line/test + status. |
| Verification framework | Small | Bounded profile runs only the E2E task + `EvidenceAggregator` (JSON write); minimal logs. |
| Errors/warnings/debug | Variable | Depends on failure rate. |

**Conclusion (C4):** the volume is **excessive logging + build + retries**, *not* test multiplication. A 232-test job should not emit 74k lines; the dominant contributors are the build and the backend stdio pipe (and retries). Reducing noise (build log verbosity, backend stdio redirection, trace-on-retry only) is a non-gating hygiene fix — deferred, not applied.

---

## 11. Database dependency inventory

DB engine: **SQLite** (stdlib `sqlite3`), not PostgreSQL. Path resolution (`backend/src/core/db/config.py:28`): explicit arg → `FINANCE_DB_PATH` env → `DATABASE_PATH` env → `data/finance.db` (relative to CWD). Schema auto-created idempotently on first connection (`backend/src/core/db/schema.py`).

Tier classification of the 12 spec files:
| Tier | Specs | Basis |
|---|---|---|
| **T1 Pure browser/UI** | `css-integrity`, `navigation`, `visual-regression`, `edge-cases` (partial), `performance` (partial) | No `/api/` references; assert on DOM/snapshots. |
| **T2 Backend/API (no DB or mocked)** | `health-check`, `performance` (API response time), `dashboard` (partial) | Hit `/api/` but may use localStorage fallback when backend absent. |
| **T3 Database-backed** | `behavior`, `behavior-scoring`, `dashboard`, `e2e-financial-logic`, `reconciliation`, `transactions` (partial) | Call `NEXT_PUBLIC_API_URL/api/...`; require backend + seeded SQLite. |
| **T4 External/infra** | none identified | No OAuth/third-party in specs. |

`frontend/lib/api/client.ts:13`: `API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'`. The static `dist/` build calls the backend **directly at :8000** (no Next proxy; `next.config.ts` has no rewrites). Coherent only if backend is running on :8000.

---

## 12. Database provisioning analysis (C6 — the key CI defect)

Trace: `playwright.yml` job → `bootstrap-runtime` (Python, `pip install -e ".[all]"`) → `setup-node-runtime` → `setup-playwright` → `verify.py playwright` → `npm run build` → `npx playwright test` → **`global-setup.ts` starts the backend** via `spawn(pythonCmd, ['-m','uvicorn','src.api:app','--port','8000'])`.

Findings:
1. **No CI step starts PostgreSQL/SQLite or runs migrations/seeds explicitly.** Schema is auto-created by the backend on first connect; seeding depends on the backend being reachable and on test fixtures (`seed-data.ts`).
2. **`uvicorn` is NOT a declared dependency.** Root `pyproject.toml` `[project].dependencies` lists fastapi/pydantic/pandas/… but **not `uvicorn`**; `requirements.lock` contains **no `uvicorn`**; `backend/pyproject.toml` mentions `uvicorn` only inside a `[tool.ruff]` `module` ignore list (line 76), not as a real dependency. Yet the backend is launched with `python3 -m uvicorn`.
3. **No committed `backend/venv`** (`ls -d backend/venv` → absent). The local environment happens to have `uvicorn` (0.51.0) installed, which explains "works locally."
4. `global-setup.ts` degrades gracefully ("Tests will use localStorage fallback data") when the backend is absent — so T3 DB-backed tests either fail at fetch/connection or silently run against fallback, producing inconsistent results.

**Conclusion:** In a clean CI runner, `python3 -m uvicorn` is likely to raise `ModuleNotFoundError: uvicorn`, the backend never starts, and **T2/T3 E2E tests fail as environment-precondition failures (missing backend/DB), not application failures.** This is a genuine CI architecture defect, distinct from test logic. (Confidence: high from static dependency analysis; final confirmation requires a captured CI log showing the backend-startup error — recommended follow-up, not performed here.)

---

## 13. Local-vs-CI environment diff

| Dimension | Local (this env) | CI (ubuntu-latest) |
|---|---|---|
| Python | 3.x (uvicorn present) | 3.12 via setup-python-runtime; uvicorn **not installed by `[all]`** |
| Node | v20.20.2 | 20 via setup-node-runtime |
| Playwright | browsers present | chromium/firefox/webkit installed; mobile projects reuse engines |
| Backend deps | present (incl. uvicorn) | fastapi/pydantic present via `[all]`; **uvicorn missing** |
| DB | SQLite `data/finance.db` | same, but backend may never start |
| API URL | `localhost:8000` default | same (NEXT_PUBLIC_API_URL unset at build) |
| webServer | `npm start` (dev) | `python3 -m http.server 3000 --directory dist` |
| workers | default | 4 |
| retries | 0 | 2 |
| build | run | run |

The precondition gap is **uvicorn/backend-start in CI** — the single most important divergence.

---

## 14. Per-project runtime measurements (C8)

**Cannot be completed from this environment** (no CI run logs available; running 232×6 locally is out of scope and the forensic constraint forbids inferring runtime from a single local run). Historical local measurement recorded at `progress.md:2629`: *"Playwright E2E (local, chromium): 32 passed, 13 skipped"* — note this is far below the canonical 232, indicating that run used a different filter/scope and is **not** a reliable per-project baseline. Recommended follow-up: download each of the 6 CI job logs and record per-project `passed/failed/skipped/flaky/duration/output-lines/DB-failures`. Until then, per-project runtime is **unmeasured**, not extrapolated.

---

## 15. Failure taxonomy

| Class | Examples | Source |
|---|---|---|
| A — App/Test | genuine assertion failures | requires CI logs |
| B — Playwright config | webServer/timeout/project mismatches | partially ruled out (config aligns with CI) |
| C — Verification framework | profile expansion (M9-C5, fixed) | fixed; bounded profile confirmed |
| D — GH/CI env | **missing `uvicorn` → backend won't start** | §12 (high confidence) |
| E — Resource/parallelism | workers=4, retries=2 | config, not yet measured as cause |
| F — Observability | 74k-line log noise | §10 |
| G — Repo/config hygiene | ghost `codeql.yml`, stale `run_playwright_tests.sh` refs | §2.6, §9 |

---

## 16. Timeout analysis

- Job `timeout-minutes: 90` (per project). Test `timeout: 30000ms`, `expect: 10000ms`. `per_step_timeout=5400s` in executor.
- 232 tests × workers 4 → parallelism bounds runtime; no evidence timeouts are the primary failure. The historical "2-hour hang" (M9-C5) was the **planner expanding `playwright` to the full suite** — fixed by bounded profiles. Current risk is **environment failure (backend not starting)** causing fast connection errors, not timeouts. Retries (2) can multiply log volume but not runtime catastrophically.

---

## 17. Root-cause classification

1. **CodeQL "duplicate/failure" appearance** → three surfaces (A required+passing, B GitHub-managed+non-required, C stale ghost). No source-controlled duplicate. (Evidence: Actions API, contents 404, ruleset, git history.)
2. **Forensic lab "failure"** → lab-internal heredoc/Black env defects; non-gating; diagnostic-only. (Evidence: `progress.md:2589–2643`, run conclusions.)
3. **Playwright volume** → logging/build/retries, not test multiplication. (Evidence: 12 files, 232 tests, single testDir, §10.)
4. **Playwright DB/E2E failures** → CI backend-start precondition failure due to undeclared `uvicorn`. (Evidence: `pyproject.toml`, `requirements.lock`, `global-setup.ts`, no `backend/venv`.)

---

## 18. What is actually broken

- **CI backend provisioning:** `uvicorn` not installed in CI → `global-setup` cannot start the backend → T2/T3 E2E tests cannot reach a real backend/DB. This is the most material defect.
- **Log volume / observability:** 74k lines obscures real signal (non-gating, but hinders diagnosis).
- **Stale registrations:** ghost `codeql.yml` API entry; `run_playwright_tests.sh` referenced by `registry.py`/`evidence_contract.py` but off the active path.

## 19. What is merely noisy/non-gating

- The **dynamic `CodeQL`** check (GitHub-managed, non-required, failing) — not blocking merges.
- The **ghost `CodeQL Security Analysis` (codeql.yml)** — inert.
- The **M9 Forensic Lab** failure — non-required, diagnostic-only.
- The **74,000-line output** — noise, not test failure.
- Playwright **retries=2 / workers=4** — present but not proven to be the failure cause.

## 20. Remediation candidates (NOT applied — diagnosis only)

1. Declare `uvicorn` in root `pyproject.toml` `[project].dependencies` (and regenerate `requirements.lock`) so CI can start the backend. (Addresses §12 root cause.)
2. Add an explicit CI step to start the backend + ensure `data/finance.db` schema/seed before Playwright, rather than relying solely on `global-setup`.
3. Redirect backend stdio in `global-setup` to a file instead of `console.error` to cut log volume.
4. Reduce `npm run build` verbosity in CI.
5. Reclassify `m9-forensic-diagnostic-lab.yml` as non-gating diagnostic infra in docs; fix its heredoc/Black env.
6. Decide GHAS policy for the dynamic `CodeQL` (keep redundant or disable default and rely on `security-codeql.yml`).
7. Remove stale `run_playwright_tests.sh` references from `registry.py`/`evidence_contract.py` (or the script) to avoid confusion.

## 21. Items explicitly NOT to change (per forensic constraints)

- No deletion/disable of `security-codeql.yml` or the dynamic `CodeQL`.
- No deletion of `m9-forensic-diagnostic-lab.yml`.
- No reduction of the 6-project matrix.
- No reduction of test count, retries, or timeouts to manufacture green.
- No disabling of database-dependent tests; no mocking/removal of DB requirements.
- No modification of Playwright config, tests, application code, or verification-framework code.

## 22. Evidence appendix

**Live GitHub API (`gh`, repo `simcitysocial97-dev/ClariFin_OS`):**
- `actions/workflows` → 4 CodeQL-related: `CodeQL` (dynamic/github-code-scanning/codeql, id 330860652), `CodeQL Security Analysis` (`.github/workflows/codeql.yml`, id 332570115, ghost), `CodeQL Security Analysis` (`.github/workflows/security-codeql.yml`, id 332453015), plus standard workflows.
- `contents/.github/workflows/codeql.yml?ref=main` → **404 Not Found** (ghost confirmed).
- `rulesets/20127383` → `protect-main-branch`, `required_status_checks = [Quality Gate, Backend Verification, Frontend Verification, Runtime Verification, Plan / Execute / Reconcile, Analyze]`. (`Analyze` = security-codeql.yml job; dynamic `CodeQL` and ghost absent.)
- `code-scanning/analyses` (latest, 2026-08-16) → `analysis_key=".github/workflows/security-codeql.yml:analyze"`, 9 results, 130 rules.
- Workflow runs: security-codeql (runs 39–41 SUCCESS); ghost codeql.yml (1 run, cancelled, `6db591c0`); dynamic CodeQL (success 2026-08-10/12); forensic lab (runs 29–31 FAILURE).

**Repository evidence:**
- `git ls-files` → only `security-codeql.yml` present (no `codeql.yml`).
- `git log --all -- .github/workflows/codeql.yml` → `6db591c0` create, `8100e361` delete, `4c4b1a44` delete.
- `npx playwright test --list` → `Total: 1392 tests in 12 files` (232 unique × 6).
- `frontend/playwright.config.ts` → single `testDir: './tests/e2e/specs'`; 6 projects; `retries: CI?2:0`; `workers: CI?4:undefined`.
- `runtime/foundation/verification/profiles.py:414-442` → bounded playwright task, inline `npm run build && npx playwright test ${PLAYWRIGHT_PROJECT:+--project=...}`.
- `frontend/tests/global-setup.ts:69` → `spawn(pythonCmd, ['-m','uvicorn','src.api:app',...])`.
- `pyproject.toml:39-55` → backend runtime deps **without `uvicorn`**; `requirements.lock` → **no `uvicorn`**; `backend/venv` → absent.
- `backend/src/core/db/config.py:28` & `schema.py` → SQLite, idempotent auto-init, path `FINANCE_DB_PATH`/`DATABASE_PATH`/`data/finance.db`.
- `frontend/lib/api/client.ts:13` → `API_BASE = NEXT_PUBLIC_API_URL || 'http://localhost:8000'`.

**Conflict note:** `progress.md:2629` records a local chromium run of "32 passed, 13 skipped" vs the canonical 232 — this historical measurement used a different scope/filter and is **not** reconcilable with the current inventory; it is reported as a conflict rather than treated as a baseline.

**Unresolved (requires CI log capture):** exact per-project pass/fail/duration (§14) and exact line-by-line 74k attribution (§10) need a downloaded CI run log; static evidence strongly indicates logging/build/retries dominance and a uvicorn/backend-start precondition failure.

---
*End of M9-C10 forensic report. No remediation applied.*
