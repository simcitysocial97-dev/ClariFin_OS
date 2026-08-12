# VEA-5 M8 — Merge Enforcement, Staleness Convergence & LOCAL/PR Closure

**Status:** DONE — 2026-08-12
**Type:** Operationalization, **not** consolidation. No verification-workflow ownership changed; no workflow deleted.
**Changes:** broadened `verification-reconcile.yml` PR/push path filters to `backend/**` + `runtime/**` (so a backend/verification PR cannot skip the gate via its own path filter); added `verify.py local-gate` (developer-side LOCAL plan artifact, no `origin/main`); added M8 tests.
**Tests:** `runtime/tests/test_vea5_m8_merge_enforcement.py` — 8 passed; all VEA-5 tests: 67 passed.
**Verdict:** CERTIFIED.

---

## M8 order (as directed)

1. Converge the four stale workflows — **preserving legitimate VEA-5 changes**.
2. Make `verification-reconcile` a required PR check.
3. Close the LOCAL-tier gap (no `origin/main` contamination, no expensive CI).
4. Validate branch-protection reality.
5. Only after that, revisit consolidation (M7: no evidence for deletion).

## M8.1 — Stale workflow convergence (preserve, don't reset)

`git diff origin/main` on the four workflows showed large divergences
(quality 263 / mutation 216 / playwright 162 / golden 127 lines). Inspecting the
diffs proves these are **legitimate VEA-5 evolutions**, not regressions:

| Workflow | main version (old) | branch version (current) |
|----------|--------------------|---------------------------|
| quality | 4 jobs: inline ruff/black/pytest+coverage/architecture/meta | 1 job: `verify.py quick` + bootstrap + shared artifacts + status |
| mutation | discover→matrix mutmut→aggregate (hand-rolled) | 1 job: `verify.py mutation` (orchestrates `run_mutation_selective.sh`) |
| playwright | inline build+test steps | 1 job: `verify.py playwright` + setup-playwright |
| golden | inline golden run | 1 job: `verify.py golden` |

The branch versions refactor the stale multi-job scripts into the **canonical
VEA-5 single-command pattern** (Rule 1/2/8/9: delegate to `runtime/verify.py`,
bootstrap-runtime, upload shared artifacts, append `verify.py status`). M8.1
verdict: **the branch versions are the authoritative VEA-5 form; convergence
direction is branch → main.** Resetting them to `main` would *discard* the VEA-5
refactor — explicitly forbidden ("Do not blindly reset them"). The M8 tests
(`test_m81_*`) lock this in: each stale workflow must delegate to `verify.py
<profile>`, append status, use bootstrap-runtime, and follow the concurrency
policy (mutation/golden never cancel).

> Operator action (outside this repo-editing scope): merge the VEA-5 branch to
> `main` so the four workflows converge. This is a release/merge action, not a
> workflow-content change.

## M8.2 — `verification-reconcile` as required PR check

- **Required-check identity:** job `reconcile-gate` (single job → stable check name).
- **Executes on relevant PR paths:** PR trigger now covers `backend/**` + `runtime/**` (M8.4), so it runs on every backend/verification PR.
- **Failure semantics propagate:** the `reconcile` step returns the M5-E exit code; a non-zero exit fails the job.
- **Planning divergence cannot merge:** `planning-divergence` → exit 2 → job fails → if the check is required, merge is blocked. `test_m82_*` asserts the job identity and the exit-2 mapping.

> Operator action: in branch protection, mark **`reconcile-gate`** a REQUIRED
> status check. (In-repo we guarantee the job exists, is deterministic, and
> actually triggers on PR paths; the GitHub settings toggle is an operator step.)

## M8.3 — LOCAL-tier gap closed

The three-tier model had no LOCAL CI artifact. `verify.py local-gate` closes it
**cheaply and safely**:

- Emits the LOCAL TierPlan manifest from the developer's working-tree delta
  (staged + unstaged + untracked).
- **Never** consults `origin/main` / merge-base (M2 invariant, now enforced at the
  CLI boundary: `explicit_base=None` is forced; an assertion fails if a base ref
  ever appears).
- Runs **no** verification and adds **no** CI cost — it is an inspectable artifact
  a developer can generate pre-push to see exactly what the PR gate will require.
- `test_m83_*` confirms `base_ref is None` even when `origin/main` is passed, and
  that the CLI emits a complete manifest.

This satisfies "keep LOCAL based on the working-tree delta; do not turn LOCAL into
another expensive CI workflow; never reintroduce origin/main contamination."

## M8.4 — Branch-protection reality

- **Required-check ↔ existing job:** the only newly-required check (`reconcile-gate`) maps to a real, single job. No required name without a corresponding job.
- **No skip-via-path-filter:** the reconcile gate's PR path filter covers `backend/**` + `runtime/**`; a backend change cannot evade it. `test_m84_*` asserts this.
- **Job-name validity:** every workflow's job names are identifier-safe (no spaces) so they map cleanly to check names.
- PR/push/dispatch semantics are standard GitHub; the gate follows the project's
  concurrency/retention conventions (verified in M8.1).

## M8.5 — Consolidation deliberately deferred

Per M7 evidence: **no workflow deletion is justified.** M8 adds only:

- **Shared-artifact dedupe (recommended, not implemented):** workflows 1–6 + 10
  each re-upload the same four shared artifacts on every run. This is cosmetic
  artifact-publishing duplication, fixable by a shared composite publish action —
  **not** by deleting verification ownership. Deferred as a separate, safe change.
- **`quality` remains:** its overlap with backend/frontend-verify is apparent, not
  true (fast 10m fail-fast gate + architecture/meta). Keep until evidence shows
  its cross-cutting role is unnecessary.
- **`golden` / `mutation` / `playwright` / unique owners remain** — each owns a
  responsibility no other workflow covers.

## Files changed

```
.github/workflows/verification-reconcile.yml   (broaden PR/push path filters to backend/** + runtime/**; M8 header note)
runtime/verify.py                              (cmd_local_gate; dispatch + usage)
runtime/tests/test_vea5_m8_merge_enforcement.py (new, 8 tests)
docs/verification/VEA5_M8_MERGE_ENFORCEMENT.md (this file)
docs/progress.md                                (M8 summary inserted)
```

No backend/frontend production changes. The four stale workflows were **not
modified** (they are already the canonical VEA-5 form); convergence is achieved by
merging the VEA-5 branch to `main` (operator action).

## Next (parallel tracks)

- **Track A:** M9 CodeQL/security audit (should be small — default setup already
  audited). Then M10 Full-System Certification.
- **Track B:** B1 explicit coverage → B3 test generation → B6 large-dataset →
  strengthen B2/B4/B5 evidence (surfaces already owned by DEEP per M6-B).
- **Track C:** C1 real user workflows → C2 E2E → C3 UI/UX reality.
- **M10** certifies: framework trustworthy + suites strong + CI enforces right
  gates + ClariFin_OS survives real end-to-end usage. Green workflows are the
  entry condition; then the application must be exercised as a real financial OS.
