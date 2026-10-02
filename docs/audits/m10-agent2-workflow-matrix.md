# M10 Agent 2 — GitHub Actions Workflow Ownership Matrix

- **Repository:** `simcitysocial97-dev/ClariFin_OS` (public, default branch `main`)
- **Baseline:** `bfcf336b5b7f46e759c7486f3eb02d0f8d92e14b` ("security: stop the contract gate checking out a fork-controlled ref (#15)")
- **Observed:** 2026-10-02, via `gh` against the live repository
- **Scope:** `.github/workflows/**`, `.github/actions/**`

> The task brief named the repo as `vasantha/ClariFin_OS`. The verified slug is
> `simcitysocial97-dev/ClariFin_OS` (`gh repo view --json nameWithOwner`). All
> evidence below was gathered against that slug.

---

## 1. Reconciling 14-on-disk vs 18-on-GitHub

`.github/workflows/` contains **14** files. `gh workflow list --all` reports **18**.
Every entry's real path was resolved with
`gh api repos/simcitysocial97-dev/ClariFin_OS/actions/workflows/{id}`:

| # | ID | GitHub name | Resolved path | On disk? |
|---|----|-------------|---------------|----------|
| 1 | 306534415 | Playwright Tests | `.github/workflows/playwright.yml` | yes |
| 2 | 320316305 | Quality Gate | `.github/workflows/quality.yml` | yes |
| 3 | 323403665 | Golden Dataset Regression | `.github/workflows/golden.yml` | yes |
| 4 | 323403666 | Mutation Testing | `.github/workflows/mutation.yml` | yes |
| 5 | 326155893 | Backend Verification | `.github/workflows/backend-verify.yml` | yes |
| 6 | 327831807 | Frontend Verification | `.github/workflows/frontend-verify.yml` | yes |
| 7 | 327831808 | Verification Runtime | `.github/workflows/verification-runtime.yml` | yes |
| 8 | 327866785 | Dependency Updates | `.github/workflows/dependency-update.yml` | yes |
| 9 | 327866789 | Release | `.github/workflows/release.yml` | yes |
| 10 | **329940660** | **Dependency Graph** | **`dynamic/dependabot/update-graph`** | **NO — GitHub-managed** |
| 11 | **330860652** | **CodeQL** | **`dynamic/github-code-scanning/codeql`** | **NO — GitHub-managed** |
| 12 | 332407953 | Verification Reconcile | `.github/workflows/verification-reconcile.yml` | yes |
| 13 | 332453015 | CodeQL Security Analysis | `.github/workflows/security-codeql.yml` | yes |
| 14 | **332570115** | **CodeQL Security Analysis** | **`.github/workflows/codeql.yml`** | **NO — ghost** |
| 15 | 332950098 | M9 Forensic Diagnostic Lab | `.github/workflows/m9-forensic-diagnostic-lab.yml` | yes |
| 16 | 339062466 | API Contract Integrity | `.github/workflows/api-contracts.yml` | yes |
| 17 | 369150738 | Mutation Testing (PR Incremental) | `.github/workflows/mutation-pr.yml` | yes |
| 18 | **372442200** | **Matrix Shape Probe** | **`.github/workflows/zz-matrix-probe.yml`** | **NO — ghost** |

The 4 extra entries split into two distinct causes:

### 1a. GitHub-managed "dynamic" workflows (2)

These have no file in the repository at all. Their `path` begins with `dynamic/`,
which is how the API reports GitHub-generated workflows:

- **`Dependency Graph`** — Dependabot's dependency-graph updater. Latest run
  2026-09-28 (`Graph Update: pip in /., /backend, ...`), success. Note there is
  **no `.github/dependabot.yml`** on disk; the graph update is running from
  repository settings, not a committed config.
- **`CodeQL`** — the *retired default setup* (see §2 and
  `m10-agent2-codeql-ownership.md`).

### 1b. Ghost registrations from deleted files (2)

GitHub retains a workflow entry (and its run history) after the file is removed.
Neither file exists on `main` or on any current branch head:

- **`codeql.yml`** (id 332570115) — one cancelled `pull_request` run on
  2026-08-12 at `head_sha=6db591c0`. Git history shows it was created and deleted
  twice on the branch `verification-framework-codeql-integration`:
  `6db591c0 Create` → `8100e361 Delete` → `00344319 Create` → `4c4b1a44 Delete`.
  It was **never merged to `main`** (confirmed: `gh api .../contents/.github/workflows/codeql.yml`
  → 404, and it is absent from `git ls-tree origin/main`).
- **`zz-matrix-probe.yml`** (id 372442200) — 7 `push` runs on 2026-10-01 from
  branch `probe/matrix-shape`, which is **not** in `git ls-remote --heads origin`
  (i.e. the branch was deleted after the runs).

**Conclusion:** the 14↔18 delta is fully explained. There is no missing, untracked,
or orphaned source-controlled workflow on `main`.

---

## 2. Merge gating — the authoritative ruleset

`GET /branches/main/protection` returns **`404 Branch not protected`**. That 404 is
misleading: protection is defined by a **ruleset**, which the legacy
branch-protection endpoint does not reflect.

`GET /rulesets/20127383` (`protect-main-branch`, `enforcement=active`,
`target=branch`, `conditions.ref_name.include=["~DEFAULT_BRANCH"]`) is the real
gate. Its `required_status_checks` are exactly four contexts:

| Required context | Produced by |
|---|---|
| `Backend Verification` | `backend-verify.yml` → job `verify` |
| `Frontend Verification` | `frontend-verify.yml` → job `verify` |
| `Runtime Verification` | `verification-runtime.yml` → job `verify-runtime` |
| **`Analyze`** | **`security-codeql.yml` → job `analyze`** |

The ruleset also enforces `deletion`, `non_fast_forward`, and `pull_request`
(0 required approvals, `require_extra_approval_for_unattributed_changes=true`,
all three merge methods allowed).

**Operational hazard:** `Analyze` is a CodeQL job name. Renaming that job, or
adding/removing a job in `security-codeql.yml`, will make `main` permanently
unmergeable — the same failure mode already fixed once for path filters (see the
header comments in `backend-verify.yml` and `verification-runtime.yml`).

---

## 3. Source-controlled workflow matrix

Required? is resolved against the four ruleset contexts above.
All statuses are the **latest run observed on 2026-10-02** via
`GET /actions/workflows/{id}/runs?per_page=1`.

| Workflow (file) | Trigger | Purpose | Jobs (name) | Depends on | Paths filter | Required? | Scheduled / manual | Duplicate? | Latest |
|---|---|---|---|---|---|---|---|---|---|
| `quality.yml` | push(main,develop), pull_request(main,develop), dispatch | Static quality: `runtime.verify quick` + frontend eslint/tsc/vitest | `quality` (**Quality Gate**) | — | yes (backend, runtime, frontend, tools, scripts, .github/workflows/quality.yml, .github/actions, pyproject) | No | manual | partly — see §4 | ✅ success |
| `backend-verify.yml` | push(main,develop), pull_request(main,develop), dispatch | Total backend verification: `runtime.verify backend` | `verify` (**Backend Verification**) | — | **no** (deliberate; required check) | **YES** | manual | partly — see §4 | ✅ success |
| `frontend-verify.yml` | push(main,develop), pull_request(main,develop), dispatch | Frontend build + verification via `run_frontend_verification.sh` | `verify` (**Frontend Verification**) | — | no | **YES** | manual | no | ✅ success |
| `verification-runtime.yml` | push(main,develop), pull_request(main,develop), dispatch | Runtime self-validation: `runtime.verify runtime` | `verify-runtime` (**Runtime Verification**) | — | **no** (deliberate; required check) | **YES** | manual | no | ✅ success |
| `verification-reconcile.yml` | pull_request(main,develop), dispatch | Change-boundary verification: `runtime.verify check` | `reconcile-gate` (**Plan / Execute / Reconcile**) | — | yes (`runtime/**`, `backend/**`) | No | manual | no | ✅ success |
| `security-codeql.yml` | pull_request(main,develop), push(main), schedule `27 4 * * 1`, dispatch | CodeQL analysis: python, javascript, actions | `analyze` (**Analyze**) | — | no (deliberate) | **YES** | scheduled + manual | **no** (live single authority) | ✅ success |
| `api-contracts.yml` | push(main,develop), pull_request(main,develop), dispatch, **workflow_run(Playwright Tests → failed)** | Contract integrity gate: `runtime.verify contracts` | `api-contracts` (**API Contract Integrity Gate**) | — | yes (`backend/**`, `frontend/**`, `runtime/**`) | No | manual + event-driven | no | ✅ success |
| `playwright.yml` | push(main,master,develop), pull_request(main,master,develop), dispatch | E2E: `runtime.verify playwright` (matrix: chromium, mobile-chrome) | `test` (**E2E Tests (${{ matrix.project }})**) | — | yes (`frontend/**`, `e2e/**`, `runtime/**`) | No | manual | no | ✅ success |
| `mutation.yml` | schedule `0 2 * * *`, dispatch | Full mutation campaign (sharded) | `mutation-smoke`, `mutation-plan`, `mutation` (sharded, count computed at runtime by the plan job — 26 shards reported on the baseline run), `mutation-replay`, `mutation-aggregate` | `mutation` ← smoke+plan; `mutation-aggregate` ← plan+mutation | no | No | **scheduled** + manual | no | ✅ success |
| `mutation-pr.yml` | pull_request | Incremental mutation on affected engines/services | `incremental-mutation` (**Incremental Mutation (PR)**) | — | yes (`backend/src/engines/**`, `backend/src/services/**`, `backend/tests/**`) | No | event only | no | ✅ success |
| `golden.yml` | schedule `0 3 * * *`, dispatch | Golden dataset regression: `runtime.verify golden` | `golden` (**Golden Dataset Regression**) | — | no | No | **scheduled** + manual | no | ✅ success |
| `dependency-update.yml` | schedule `0 4 * * 1`, dispatch | Dependency health (pip/npm audit) | `dependency-health` (**Dependency Health**) | — | no | No | **scheduled** + manual | no | ✅ success |
| `m9-forensic-diagnostic-lab.yml` | pull_request(main) | M9 forensic evidence collection | `diagnostician` (**M9 Forensic Evidence Collection**) | — | no | No | event only | **yes** — see §4 | ✅ success |
| `release.yml` | release(published), dispatch(version) | Build frontend dist + release notes | `build` (**Build Release**) | — | no | No | event + manual | no | ✅ success |

### Composite actions (`.github/actions/`)

All 6 are live. Usage counts are by direct reference:

| Action | Referenced by | Notes |
|---|---|---|
| `bootstrap-runtime` | 13 workflows | Delegates to `setup-python-runtime` (line 29) |
| `setup-python-runtime` | via `bootstrap-runtime` | **Not directly referenced by any workflow — still live.** Nested composite. |
| `setup-node-runtime` | 10 workflows | Node 24 |
| `setup-playwright` | 2 workflows | Browser cache |
| `upload-runtime` | 12 workflows | Evidence upload |
| `download-runtime` | 1 workflow (`mutation.yml`, lines 577/589) | Mutation shard hand-off |

---

## 4. Duplicate / obsolete findings

### F-1 — `m9-forensic-diagnostic-lab.yml` re-runs work two required checks already own (**duplicate**)

This is the only workflow performing genuinely duplicated verification work.

- It runs `.venv/bin/python -m runtime.verify quick` (step "Run verify.py quick
  with complete capture") — **identical to `quality.yml`**.
- It runs `.venv/bin/python -m runtime.verify backend` (step "Run verify.py
  backend with complete capture") — **identical to `backend-verify.yml`**.
- Both therefore run **twice per pull request**.
- Cost: 8–13 minutes per run, 81 runs to date, on every PR to `main`.

It is not a required check, no workflow consumes its artifacts
(`m9-execution-forensic-${{ github.run_id }}` is unique per run), and it is not
referenced by any other `.github/` file.

**Not changed — and why.** The obvious minimal fix (replace `pull_request` with
`workflow_dispatch`) is **not** safe as a one-line change: the job's steps read
`github.event.pull_request.head.sha` (line 25) and
`github.event.pull_request.base.sha` (the "Fetch exact PR base commit" step,
which runs under `set -euxo pipefail` and asserts `git cat-file -e`). On a manual
dispatch those expressions are empty and the step fails. Making the conversion
correctly means rewriting several PR-context steps — larger than the "smallest
safe change" the brief allows, and it would break the forensic tool in the one
mode it still needs.

Recommended, for a maintainer decision:

- **Option A (preferred).** Keep the `pull_request` trigger but drop the two
  duplicated `verify quick` / `verify backend` steps; the lab's unique value is
  the *forensic capture* (git changed-file reconciliation, black matrix, shell
  differential), not re-running the verification profiles. Drops ~6 min/PR and
  preserves every PR-visible artefact.
- **Option B.** Convert to `workflow_dispatch` **and** parameterise the PR-context
  inputs (`base_sha` / `head_sha` as `workflow_dispatch` inputs) so the lab runs
  on demand. Removes the per-PR cost entirely; loses automatic per-PR evidence.

### F-2 — Ghost workflow registrations (obsolete; **repository settings, not source**)

`codeql.yml` (id 332570115) and `zz-matrix-probe.yml` (id 372442200) still appear
`active` in the Actions UI with no corresponding file. Neither contributes
analysis, coverage, or gating.

- Cannot be cleared by a commit — the files are already absent.
- Clearing requires `DELETE /repos/{owner}/{repo}/actions/workflows/{id}` (or the
  Actions UI). **Recommended only** — this is a repository-settings mutation with
  repo-wide blast radius, and the brief forbids pushing. Left untouched.
- Neither is referenced by any ruleset required check, so deletion cannot turn a
  required context red.

### F-3 — Retired default CodeQL setup (obsolete registration)

`CodeQL` (id 330860652, `dynamic/github-code-scanning/codeql`). Last run
2026-08-12; not scheduled any more. Full analysis in
`m10-agent2-codeql-ownership.md`. Recommended only, for the same reason as F-2.

### F-4 — `.github/scripts/validate_actions.py` is not wired into any workflow (**gap, not duplication**)

`.github/scripts/validate_actions.py` exists but no workflow invokes it
(`grep -rn validate_actions .github/workflows/` → no match). The repository
therefore has no CI enforcement of its own action schema.

Not changed: wiring it in requires adding a new job or a new workflow, which is
"redesigning CI architecture" and is out of scope. Recommended for a maintainer.

### F-5 — Stale header comments (documentation drift; no behaviour impact)

`backend-verify.yml:4` and `verification-runtime.yml:4` both state
*"RESPONSIBILITY: Run `runtime/verify.py check`"*, but the jobs actually run
`runtime.verify backend` and `runtime.verify runtime` respectively. The prose in
`quality.yml` is the accurate one. Left unchanged to keep this diff to a single
file; recorded here for a follow-up.

### F-6 — `.github/scripts/README.md` staleness (out of my ownership)

The README's "Called By" column cites `backend.yml`, which does not exist, and
attributes `run_fast_checks.sh` / `check_coverage_threshold.py` to `quality.yml`,
which now delegates to `runtime.verify quick` instead. It also lists 5 composite
actions; there are 6 (`download-runtime` is missing). `.github/scripts/**` is not
in Agent 2's ownership — reported, not edited.

### Non-findings (checked and cleared)

- **`api-contracts.yml` `workflow_run` trigger** — narrowly scoped to
  `workflows: ["Playwright Tests"]`, `types: [failed]`, not "any workflow failed".
  Event breakdown over the last 100 runs: `pull_request` 50, `push` 50,
  `workflow_run` **0**. Not a duplicate-work source today. Its `permissions` is
  `contents: read` only, which is the documented fix for the
  `actions/untrusted-checkout/critical` finding, and it deliberately checks out
  `github.sha` (default-branch head) rather than `workflow_run.head_sha`.
- **`mutation.yml` vs `mutation-pr.yml`** — not duplicates. `mutation.yml` is the
  nightly full campaign (schedule `0 2 * * *`, 28 shards); `mutation-pr.yml` is
  scoped PR feedback on `engines/`+`services/` only. Different cadence, different
  scope, different gating. The shard count is produced at runtime by
  `mutation-plan` (its `strategy.matrix` is a `fromJSON(...)` expression, not a
  static list), so it cannot be read statically from the YAML.
- **`dependency-update.yml` vs dynamic `Dependency Graph`** — not duplicates.
  The workflow runs `run_dependency_checks.sh` (pip/npm **audit**); the dynamic
  workflow updates the **dependency graph** metadata.
- **All 8 external action pins resolve to real upstream tags** —
  `actions/cache@v6.1.0`, `actions/checkout@v7.0.1`,
  `actions/download-artifact@v7.0.0`, `actions/github-script@v7`,
  `actions/setup-node@v7.0.0`, `actions/setup-python@v7.0.0`,
  `actions/upload-artifact@v7`, `actions/upload-artifact@v7.0.1`
  (each verified with `GET /repos/{owner}/git/ref/tags/{tag}`). Note
  `upload-artifact@v7` and `@v7.0.1` resolve to the **same** commit
  (`043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`) — inconsistent tag spelling, not a
  problem. All pins are **tags, not full SHAs**; SHA-pinning would harden supply
  chain but touches 20 files and is recommended only.
- **Every script referenced by a workflow exists on disk** — no broken
  `.github/scripts/*.sh` references.

---

## 5. Check-run reality on the baseline commit

`GET /commits/bfcf336b.../check-runs?per_page=100` → **38 total**, of which
**37 success** and **1 skipped** (`Mutation Replay (no measurement)`, which is
correct: its `if` requires `workflow_dispatch` with `inputs.mode == 'replay'`).
All four required contexts reported green: `Backend Verification`,
`Frontend Verification`, `Runtime Verification`, `Analyze`.