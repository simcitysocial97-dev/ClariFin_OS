# MAIN Stabilization Audit — M9-AUDIT

**Scope:** read-only diagnostic. Nothing was modified, committed, pushed, deleted, or closed.
**Baseline:** `main` @ `f9d8777e` (merge of PR #6, 244 commits).

---

## 1. ROOT CAUSES (ordered by technical dependency, not importance)

| # | Root cause | Evidence | Blast radius |
|---|---|---|---|
| **R1** | **4568 generated evidence files are tracked in git** and enter every verification boundary | `git ls-files runtime/generated` = 4568; 4417 of the 5803-file merge diff (76%) are `runtime/generated/` | Inflates every boundary; makes planning unbounded |
| **R2** | **`quality.yml` and `verification-reconcile.yml` run byte-identical work** | `quality.yml:52-56` and `verification-reconcile.yml:42-46` both: `.venv/bin/python -m runtime.verify check` with `VERIFICATION_BASE_REF: ${{ github.base_ref \|\| github.event.before }}` and `VERIFICATION_HEAD_REF: ${{ github.sha }}` | 2× the slowest workflow for zero extra coverage |
| **R3** | **The >500-file boundary is a warning with no enforcement** | `control_plane_facade.py:163,201` — `VERIFY_MAX_CHANGED_FILES_WARN` default 500, printed to stderr, then execution proceeds with all files | The guardrail cannot prevent the failure it describes |
| **R4** | **`pull_request` uses the whole branch as the boundary** | `orchestrator.py:407-437`. `${{ github.base_ref \|\| github.event.before }}`: on push `base_ref` is empty → previous tip → small diff. On PR `base_ref`="main" → full branch vs main → 1386 files | Quality Gate passes on push, fails on PR |
| **R5** | **10 workflows bootstrap independently on the same event** | All 10 fired at `14:12:56` (PR) / `14:12:51` (push); each runs its own `bootstrap-runtime` (venv + `pip install -e ".[all]"` + `npm install`) | 10× duplicated environment setup; runner-minutes waste |
| **R6** | **CodeQL default setup and source-controlled workflow likely both active** | 3 databases exist (`python`, `javascript`, `actions`); the workflow declares only `python, javascript`; no `codeql-config.yml` | Duplicate analysis, duplicate alerts |
| **R7** | **19 diff paths are quoted and unparsed** | `git diff --name-only` emits `"runtime…` for 19 paths | Those files silently fail capability matching → failed tasks |
| **R8** | **E2E console routing waits only for a shell marker at 10s × 3** | `platform-c67.2.spec.ts:61,84,114` — `CONSOLE_TIMEOUT/3` per attempt, `resolved:false` skips the data wait | ~31s failure; not a backend read-path defect |

---

## 2. WORKFLOW MAP

Single PR event → **10 workflows start in the same second**, each self-bootstrapping:

```
pull_request @ 14:12:56
  ├─ Quality Gate                    FAIL  (verify check, base_ref=main → 1386 files)
  ├─ Verification Reconcile          FAIL  (verify check, IDENTICAL env to Quality Gate)
  ├─ Backend Verification            PASS  (verify backend — profile-scoped, NO base ref)
  ├─ Verification Runtime            PASS  (verify runtime — profile-scoped, NO base ref)
  ├─ Frontend Verification           PASS
  ├─ API Contract Integrity          PASS
  ├─ CodeQL Security Analysis        PASS
  ├─ Playwright Tests                FAIL  (platform-c67.2, ~31s timeouts)
  ├─ M9 Forensic Diagnostic Lab      PASS
  └─ Mutation Testing (PR Incremental) PASS
```

The decisive difference is **not** the workflow — it is the command and env:

| Workflow | Command | `VERIFICATION_BASE_REF` | Boundary |
|---|---|---|---|
| Backend Verification | `verify backend` | **unset** | profile-scoped |
| Verification Runtime | `verify runtime` | **unset** | profile-scoped |
| Quality Gate | `verify check` | **set** | full, 1386 files |
| Verification Reconcile | `verify check` | **set** (identical) | full, 1386 files |

---

## 3. SLOW WORKFLOW ROOT CAUSE

`Plan / Execute / Reconcile` measured: **14:14:24 → 15:07:50 = 53 m 26 s**

Breakdown:

| Stage | Duration | Note |
|---|---|---|
| Checkout + bootstrap + npm | ~2 min | 14:12:56 → 14:15:42 |
| `runtime.verify check` | **~52 min** | 14:15:42 → 15:07:42 |
| Upload + summary | seconds | |

Inside the 52 minutes, the orchestrator built a plan of **240 tasks**, of which the vast majority failed — many in **0.00 s**, which is the signature of a *systemic* failure (unresolvable path/spec) rather than 240 real defects.

**First operation where runtime diverges from the fast workflows:** the boundary resolution and `orchestrator.build_execution_plan(changed_files)` with 1386 files. Fast workflows never reach an unbounded plan because they run profile-scoped commands.

---

## 4. LARGE-PR ROOT CAUSE

Measured merge diff (`git diff f9d8777e^1 f9d8777e`) = **5803 files**, not 1386:

| Area | Files | Share |
|---|---|---|
| `runtime/generated/` | **4417** | **76%** |
| `runtime/foundation` (real source) | 298 | 5% |
| `runtime/tests` | 152 | 3% |
| `backend/` | 364 | 6% |
| `frontend/` | 281 | 5% |
| `.github/` | 43 | <1% |
| other | ~248 | 4% |

So the real code touched by this merge is roughly **1100 files**; the other **~4700 are generated evidence**.

Key facts:
- The 500 threshold lives in `control_plane_facade.py` (env var `VERIFY_MAX_CHANGED_FILES_WARN`, default 500) and appears **twice** — once before planning, once after — purely as a print.
- **There is no generated-file exclusion anywhere** in the boundary calculation.
- `orchestrator.py:417` uses a two-dot diff `base..head` on PRs; this is the same branch of code push uses, but push supplies a *previous tip* as base while PR supplies *main*.
- The planner is handed all 1386 files; there is no incremental/bounded mode observed in the reviewed path.

**Answer to the A–G question: this is primarily (C) generated-file exclusion + (F) workflow restructuring.**
Planner optimization (A) is second-order — even a linear planner still plans verification for 4417 JSON evidence files. Caching (E) does not help because the input genuinely changed. Changed-file filtering (B) alone is insufficient because the generated files *are* the changed files. The boundary calc (D) is behaving as designed.

---

## 5. QUALITY GATE ROOT CAUSE (push vs pull_request)

Both events execute the **same code path** — `orchestrator.py:417` two-dot diff. The difference is entirely the value of the base ref, injected by:

```yaml
VERIFICATION_BASE_REF: ${{ github.base_ref || github.event.before }}
```

| Event | `github.base_ref` | Effective base | Diff size | Result |
|---|---|---|---|---|
| `push` | *(empty)* | `github.event.before` — previous tip of the branch | small (that push only) | **PASS** |
| `pull_request` | `"main"` | `main` | **1386 files** | **FAIL** |

Additional, non-causal differences observed: `pull_request` checks out the synthetic merge commit (detached HEAD) — which is what broke repository identity earlier today — while push checks out the branch tip. Permissions and artifact sets are identical.

**The pull_request boundary is created specifically by PR comparison logic.** It is not a defect in the diff implementation; it is a defect in *choosing* `main` as the base for a 244-commit PR.

---

## 6. E2E ROOT CAUSE

`frontend/tests/e2e/specs/platform-c67.2.spec.ts`

```ts
const CONSOLE_TIMEOUT = 30_000;
const CONSOLE_NAV_ATTEMPTS = 3;
...
await page.goto(url, { waitUntil: 'domcontentloaded', timeout: CONSOLE_TIMEOUT });
await page.waitForSelector(CONSOLE_TITLE_BAR, { timeout: CONSOLE_TIMEOUT / CONSOLE_NAV_ATTEMPTS });
```

- The 8 "Page Routing" tests call `gotoConsole(page, path, { resolved: false })`.
- `resolved: false` **skips** the `CONSOLE_RESOLVED` wait (line 92-94) — so these tests never wait for API data.
- They wait only for the title-bar shell marker, at `30_000/3 = 10 s` per attempt, 3 attempts → **~30 s**, matching the observed **~31 s** exactly.

**This does not support the "GET triggers expensive verification planning" hypothesis.** These tests never wait for data resolution, so backend read-path latency cannot be what they are measuring. The failure is that the shell marker does not appear within 10 s.

The spec's own header documents the likelier cause: *"A freshly spawned `next start` intermittently answers the first navigations with the not-found page"*, and the retry loop exists precisely for that. With 10 concurrent workflows hammering one runner, frontend cold-start contention is the more probable cause.

**Classification: test/environment readiness issue, not a proven production read-path defect.** A production read-path defect remains plausible for the *Content Rendering* tests (which do wait for data), but the routing failures specifically do not demonstrate it.

---

## 7. CODEQL CONFIGURATION

| # | Configuration | Location | Trigger | Languages | Query suite | Runner | Action ver | SARIF | Active? | Overlap |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Source-controlled workflow | `.github/workflows/security-codeql.yml` | `pull_request`, `push`(main), weekly cron, dispatch | `python, javascript` | **default** (no config file) | ubuntu-latest | `github/codeql-action/*@v3` | yes | yes | overlaps #2 on python+javascript |
| 2 | GitHub **default setup** | repo settings (not in tree) | push/PR/schedule | python, javascript, **actions** | default | GitHub-managed | n/a | yes | **strongly suspected** | overlaps #1; uniquely owns `actions-database` |

Evidence for #2: three databases exist — `python-database` (550233740), `javascript-database` (550234201), `actions-database` (476796586). The `actions-database` has a **much lower id**, i.e. it predates the other two, and `actions` is **not** a language the source-controlled workflow requests. No `codeql-config.yml` or `.github/codeql/` exists, so the workflow uses default setup.

---

## 8. CODEQL ALERT PLAN (33 open alerts)

| Rule | N | Sev | Category | Assessment |
|---|---|---|---|---|
| `actions/missing-workflow-permissions` | 14 | med | **C — stale** | 12 created **2026-08-10**; `quality.yml` permissions added **2026-09-26**. Alerts predate the fix and were never dismissed; CodeQL does not auto-close. |
| `py/stack-trace-exposure` | 6 | med | **A — genuine (low)** | `import_router.py`, `platform.py`, `errors.py` returning stack details. Worth fixing; no auth boundary evidence gathered. |
| `py/path-injection` | 5 | **high** | **A — genuine, needs investigation** | `import_router.py` (2) + `runtime/platform/ai/orchestrator.py` (3). Path from request → filesystem. Highest-risk group. |
| `py/clear-text-logging-sensitive-data` | 6 | **high** | **F — needs manual investigation** | `metadata_extractor.py`, `ingest.py`, `extraction/metadata_extractor.py`. May be PII-by-design. Requires a data-classification decision. |
| `py/redos` | 1 | high | **A — genuine** | `frontend_financial_arithmetic_lint.py` regex. Small, well-scoped. |
| `js/incomplete-multi-character-sanitization` | 1 | high | **F** | `verify-mock-sync.ts` — test tooling, not production. |
| `js/identity-replacement` | 1 | med | **E — likely false positive** | `diagnostics/page.tsx`; React escapes by default. |
| `js/double-escaping` | 1 | high | **E — likely false positive** | `pdf.worker.mjs` is a vendored build artifact. |

Proposed sequence: investigate `py/path-injection` → `py/redos` → `py/stack-trace-exposure` → resolve the PII logging question → dismiss the 12 stale `actions/*` after re-analysis confirms them fixed → confirm duplicate CodeQL config and disable one.

---

## 9. GENERATED ARTIFACT ASSESSMENT

- **Tracked:** 4568 files under `runtime/generated/`, plus `backend/tests/generated/`.
- **Dominant directories:** `m9-c42.21` (2096), `m9-c50` (580), `m9-c49` (420), `ai-runs` (240), `m9-c57` (118).
- **Produced by:** `runtime.verify check` and friends, on every run, in every workflow that delegates to them.
- **In the verification boundary:** yes — they are ordinary tracked files, so they are diffed and planned like source.
- **In CodeQL analysis:** yes — CodeQL scans the working tree, so 4568 JSON/JSONL files are walked during database creation and analysis.
- **Necessary in git:** `runtime/generated/m9-c71-mutation-trust/` genuinely is evidence and should stay. The per-milestone `m9-c42.21` / `m9-c50` / `m9-c49` directories are regenerable.
- **Behavioural effect of ignoring:** none at runtime — every consumer regenerates them. The only risk is losing historical evidence that a specific milestone depends on as an input; that must be checked per directory before ignoring.
- **`.gitignore` correctness:** `runtime/generated` is **not** ignored; the ignore rules cover only specific transient files (mutation sinks, `mutants/`, `__pycache__`).

---

## 10. PROPOSED REMEDIATION ORDER

Ranked by how much each unblocks, not by effort.

1. **Exclude generated evidence from the verification boundary** (R1, R3, R7).
   Highest leverage by a wide margin: removes ~4417 of 5803 files, which collapses the 1386-file boundary to ~1100, makes the >500 warning meaningful, and makes the push/PR asymmetry disappear as a practical concern. Must be a *boundary* filter (not blanket `.gitignore`) so the C71 evidence directory remains intact. Also fixes the 19 quoted paths by using `-z`/NUL-delimited diff output.

2. **Collapse the duplicated `verify check` workflows** (R2).
   `quality.yml` and `verification-reconcile.yml` are byte-equivalent. One should become a scoped follow-up (e.g. reconcile-only, or remove). Immediately removes ~52 minutes of duplicate work per PR and one guaranteed failure.

3. **Make the >500 guardrail real** (R3).
   Either cap the plan, or fall back to a profile-scoped verification, or fail fast with an actionable message. Today it warns and then spends 52 minutes failing.

4. **Share the bootstrap across workflows** (R5).
   10 concurrent full environment builds per event. A prebuilt venv artifact or a single setup workflow that others depend on would cut minutes from every run and reduce runner-minute spend.

5. **Resolve the CodeQL duplication** (R6), then re-baseline alerts and dismiss the 12 stale `actions/*` (Phase 8).

6. **Fix the E2E console routing budget** (R8).
   The 10 s shell-marker budget against a cold `next start` is too tight under 10-way runner contention. This is a test-harness change, and it is *not* evidence of a backend read-path defect.

7. **Address the genuine CodeQL findings** — `py/path-injection` (5, high) first.

**Explicitly not recommended:** raising any threshold, dismissing alerts without re-analysis, deleting the obsolete branches or `stash@{0}`, or "optimising" the planner before the boundary is fixed — a faster planner over 4417 JSON files is still wasted work.
