# M10 — Repository, Console and Application Consolidation

**Baseline:** `main` @ `bfcf336b` · **Branch:** `m10/consolidation` @ `304af027` · **PR:** [#16](https://github.com/simcitysocial97-dev/ClariFin_OS/pull/16)

41 commits, 147 files, +6,750 / −12,731.

---

## Final health

| Metric | Result |
|---|---|
| TypeScript errors | **0** (`tsc --noEmit` clean) |
| ESLint errors | **0** (179 pre-existing warnings) |
| Build errors | **0** (Next.js build succeeds) |
| Frontend unit tests | **1,380 passed** / 1,380 |
| Backend unit tests | **3,160 passed** |
| API contracts | **pass** (161 collected) |
| Mutation smoke | **pass**, consecutive runs green |
| Backend / Frontend / Quality Gate | **pass** |
| CodeQL (`Analyze`) | **pass** — python, javascript, actions all written |
| Unresolved test failures | **0 outside the 7 visual baselines below** |
| Workflow failures | **E2E only** (see Outstanding) |
| Mutation / verification / quality thresholds | **unchanged** — 0 lines changed in threshold config |

### Out of scope, untouched
`feature/program-12-platform-certification` @ `0c8410c`, `recovery/program-r-forensic-reconstruction` @ `d5db3c0`, `recovery/m9-c31-loss-06230db0` @ `06230db`, and `stash@{0}` — all unmodified.

---

## Resolved, with evidence

| # | Issue | Resolution |
|---|---|---|
| 1 | `runtime/generated/` blanket-ignore proposed | **Refuted by reproduction.** Fresh clone without the subtree fails collection: `ArchitectureNotDiscovered`. 326 test files read it as inputs. Shipped a permanent evidence/telemetry taxonomy instead — full contracts run went 4 dirty files → **0 non-evidence**. |
| 2 | Mutation dirty-worktree guard self-contradictory | `_capture_hashes` exempted `mutation_infra` as expected-to-change while `_check_dirty_worktree` aborted on it, and **smoke never checked `backend/src` at all**. Now scoped to the protected path for all modes. Tested both directions. Strictly wider coverage. |
| 3 | 4 byte-identical coverage tests | Names promised 4 contexts no body established; all would pass if `_coverage_run` stopped pinning its cwd. Bodies now actually chdir / clear-env / set CI vars. Same call count. |
| 4 | Hardcoded `.venv/bin/*` in tests | `Path(".venv/bin/coverage")` was resolved against the *pytest process's cwd*. Now uses the module's own `VENV_BIN` resolution — verified by running from `/tmp`. |
| 5 | 76 tracked-but-gitignored files | **→ 0.** 50 bulk files untracked (verified no test reads them); 27 hand-maintained records *un-ignored* rather than deleted. |
| 6 | Duplicate CodeQL workflow | **Structurally unremovable** — `DELETE` returns 404 even with an `admin` token, because the endpoint resolves through the default-branch tree. Coverage untouched and documented. |
| 7 | M9 lab duplicating Quality Gate + Backend Verification | Removed the 2 duplicate `runtime.verify` runs (~9 min × 82 runs, non-required check). All 19 forensic steps and the trigger kept. |
| 8 | CI constitution validator | Wired into no workflow, reporting **24 errors**. Now **1**. 11 summaries moved `doctor`→`status`; 1 artifact upload routed through the shared composite; 6 were an enforcer bug (stricter than its own constitution) — regression-tested so a wrong profile still errors. |
| 9 | Tag-pinned actions | **29 references SHA-pinned** (incl. 3 floating majors), each resolved via API, version retained as a comment. |
| 10 | `/behaviour` left in an error state | A3 tightened `score` to `.max(100)`; the backend returns **7561.45**. Rejected data → error page. Bound restored, defect filed (below). |
| 11 | 3 of A3's own E2E tests red | Over-broad signature matcher flagging the repo's *own* route; uppercase-vs-DOM-text label mismatch; and a `not.toContain('UNKNOWN')` scanning all page badges instead of the 8 dimensions. All fixed without weakening intent. |

---

## Outstanding — pending work

### 1. 7 visual-regression baselines need CI-side regeneration (blocking E2E)
The UI changed intentionally in M10 (metrics strip rewritten, member boundary added, cashflow chart unbound, console health grid rebuilt), so the committed PNGs no longer describe the product. **These must be regenerated from a GitHub runner** — I proved the trap by regenerating them locally and then reverting: baselines are rasterisation-specific, so local regeneration encodes this machine's fonts and fails in CI while looking correct locally.

Procedure: run the `chromium` Playwright project with `--update-snapshots` on a CI runner and commit the resulting `*-snapshots/*.png`. Thresholds, masks and diff limits are untouched and must stay that way.

### 2. Backend wellness-score scale defect (finance domain — major)
The behaviour score violates its own contract:
- `models/behaviour.py:31` documents *"between 0 and 100"*
- `wellness.py:83-86` computes and **clamps to `[0,100]`**
- `classify_wellness_band` bands on 0-100
- but `get_wellness_score` returns the **raw stored** `snapshot["wellness_score"]` → live **7561.45**

`7561.45 / 100 = 75.61`, so the stored snapshot is double-scaled. Deliberately **not** fixed here: normalising in the frontend is forbidden money arithmetic, and changing the backend changes what every consumer and golden dataset sees. That is a finance-owner decision.

### 3. `frontend-verify.yml` bypasses the `frontend` profile (1 validator error)
Delegates to `run_frontend_verification.sh` rather than the registered `frontend` profile. A **required check** — needs a parity proof, not an edit.

### 4. `test_m9_c55.py` nested-regression gates are timing-fragile
Internal 300 s timeout vs ~345 s actual under CPU contention. Passes in isolation (~133 s). A flake risk on shared runners.

---

## Deliverables

`docs/audits/` — `m10-agent1-*` (inventory, taxonomy, slow-test report, cleanup ledger, naming policy), `m10-agent2-*` (workflow matrix, CodeQL ownership), `m10-agent3-*` (console capability matrix, consumption/chart/E2E findings), `m10-agent4-*` (startup inventory, clean-start transcript), plus `m10-ci-constitution-reconciliation.md`. Root `README.md` documents the canonical start/stop contract.