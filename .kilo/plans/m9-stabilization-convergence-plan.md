# M9 Stabilization — Final Convergence (narrowed)

**Objective:** make `main` stable and green. Fix the two remaining reconcile
defects, converge, certify. Nothing else.

**Explicitly out of scope** (identified, characterised, deferred — not rejected,
simply not now): cross-workflow evidence reuse, composable profiles, profile
deduplication, timeout tuning, CI caching, and repository cleanup. The reconcile
job's ~30-minute runtime is finite, deterministic and meaningful; it is not a
defect. Reconsider only if an observed failure requires it.

**No threshold changes.** No new verification mechanism. No deletion of
evidence to obtain green.

---

## Current state

Branch `m9-stabilize-platform-routing-cache` @ `59a6d76a` — 12 of 13 workflow
runs green. Sole red: **Verification Reconcile**.

Local `runtime.verify check` on the 207-file boundary: **9/9 obligations
completed** (was 52 tasks), plan reduced 52 → 9. Remaining causes:

| Cause | Status |
|---|---|
| `tests/meta/test_validation_orchestrator.py` (4) — `risk-rules.yaml` absent | **recoverable — see A** |
| `tests/meta/test_selective_verify.py` (1–6) | **diagnose — see C** |
| coverage measurement exits 1 | **diagnose — see B** |
| unmapped-review obligation exits 1 | by design, fail-closed gate |

---

## A. Restore `risk-rules.yaml` — RECOVERABLE

### Finding

`tools/development/validation_audit.py:159` records the file's provenance as
**"Manual"**, yet `load_risk_rules()` reads it from `GENERATED_DIR`
(`backend/tests/generated/`). Nothing generates it. It was deleted by commit
`aab992ce` (*"M9-C64-R2: Clean up .gitignore and remove large generated
artifacts from tracking"*) — a bulk generated-artifact sweep that swept up a
hand-maintained file. It is absent everywhere on disk.

### Verified recoverable

`git show aab992ce^:backend/tests/generated/risk-rules.yaml` returns the
complete **67-line** file: 18 rules across `LOW` / `MEDIUM` / `HIGH` /
`CRITICAL` / `UNKNOWN`, covering `**/*.md`, `docs/**`, `backend/src/routers/**`,
`backend/src/services/**`, `backend/src/engines/**`, `backend/src/repositories/**`,
`backend/src/models/**`, `backend/src/db.py`, `backend/scripts/migration_*.py`,
`backend/src/config.py`, `backend/pyproject.toml`, `backend/tests/**`,
`frontend/**`, and a `*` fallback.

**This is a genuine recovery, not a stub. Do not author replacement content.**

### Action

1. Restore the file byte-for-byte from `aab992ce^` to
   `backend/tests/fixtures/risk-rules.yaml` (a tracked, non-generated location
   matching the file's documented "Manual" provenance).
2. Change `load_risk_rules()` in `tools/development/validation_orchestrator.py`
   to read the fixture path first, falling back to the legacy
   `GENERATED_DIR` path so any external producer still works.
3. Update `validation_audit.py:159` if it asserts the old path.
4. Confirm `.gitignore` does not exclude `backend/tests/fixtures/` (the
   `backend/tests/generated/` rule is path-specific; verify rather than assume).
5. If any of the 4 meta-tests hardcode the path, update them to import the
   canonical location. **Do not weaken an assertion.**

### Verification

- `pytest backend/tests/meta/test_validation_orchestrator.py` → all pass.
- `load_risk_rules()` returns `len(rules) == 18`.
- `git show aab992ce^:...` is the *only* source of the content; if the executor
  finds the file differs from history, stop and report.

---

## B. Coverage measurement — diagnose first, then fix

### Do not assume the cause

The earlier note described this as "coverage below threshold". That was **not
verified** and is probably wrong. Evidence:

- The scope emitted by the planner is `backend/src/engines/account_engine` —
  a **source** directory, passed to pytest.
- Measured `coverage_threshold: 40` (`verification.yaml:47`); the recorded
  result was 7.4%.
- `measure_coverage_cli` maps `rc != 0` → `INFRASTRUCTURE`
  (`coverage_measurement.py:214-218`), then `classify_completion()` derives
  `INFRASTRUCTURE_FAILURE` from it.

pytest exits **5** when it collects no tests, and **1** on test failure. A
source directory most plausibly yields *no tests collected* — an invalid scope,
not a threshold miss. Those are different defects with different fixes.

### Step B1 — establish the actual cause (blocking)

Run the task's exact command and record pytest's exit code and collection count:

```
.venv/bin/python -m runtime.verify measurement coverage backend/src/engines/account_engine --out /tmp/cov.json
```

Determine which applies:

| Observation | Meaning |
|---|---|
| exit 5, 0 tests collected | **Invalid scope** — the planner passes a source path as a pytest scope |
| exit 1, tests collected, % < 40 | **Threshold miss** reported as infrastructure |
| non-zero from coverage itself | genuine infrastructure failure — leave as is |

### Step B2 — fix only what B1 proves

**If invalid scope (most likely):** the defect is that the planner builds the
coverage scope from an engine *module path* while the CLI's documented contract
is a pytest scope (`--help`: *"pytest path scope to measure (relative to
backend/)"*). Fix the producer, not the classifier: have the coverage task
resolve the engine's **test** directory, or emit the tests scope the profile
declares. If the engine genuinely has no tests, the task should say so as a
*measurement outcome*, not as an infrastructure error.

**If threshold miss:** then, and only then, split the semantics the brief
requires — a completed measurement whose result fails a gate is not an
infrastructure failure. Distinguish by comparing the measured percentage
against `coverage_threshold`, never by exit code alone.

### Invariants either way

- **`coverage_threshold: 40` is not changed.** This is a classification fix.
- The measurement record is still written in both cases.
- Tests cover all three outcomes: pass / below-threshold-or-invalid-scope /
  genuine infrastructure failure.

---

## C. `test_selective_verify.py` — establish, then act

### It IS workflow-blocking

`run_fast_checks.sh:111` runs `pytest tests/meta/`, which includes this file;
`meta-tests` failing makes fast-checks fail, which fails reconcile. So it is not
"merely a pre-existing suite outside the gate".

### It IS also broken on main

10 failures on `origin/main` vs 5 on this branch. So it is pre-existing, not a
regression from stabilization.

### C1 — classify it (blocking)

Determine, for each failing test, which of these it is:

| Class | Action |
|---|---|
| **Same root cause as A** — a missing "Manual" artifact swept by `aab992ce` | Fix in this PR; note it alongside A |
| **Genuinely broken on main**, unrelated to the artifact sweep | It is a pre-existing defect. Fix it if small and clearly correct; otherwise **document it and exclude the suite from the gate with an explicit, justified, time-boxed exemption** — not silently |
| **A stale test asserting an obsolete contract** | Fix the test, with the reason recorded |

Start by checking whether `aab992ce` removed other inputs these tests read, in
the same way it removed `risk-rules.yaml`:

```
git show --stat aab992ce | grep -E 'tests/generated|risk-rules'
git log --all --oneline -- 'backend/tests/generated/**'
```

If the sweep removed a shared fixture set, A and C are one defect, not two.

### Invariant

If any of these must be exempted, the exemption names the tests, the reason,
and the condition for revisiting. **A blanket `--ignore` or a skipped suite is
not acceptable.**

---

## D. Converge

Execute strictly in this order. Fix only what is actually red at each step.

```
1. A  risk-rules.yaml recovery
2. B1 coverage diagnosis  → B2 fix per finding
3. C1 selective_verify classification → act per class
4. runtime verify check                       (local, PR boundary)
5. .github/scripts/run_fast_checks.sh         (local)  → must exit 0
6. push → GitHub Verification Reconcile       → must be green
7. inspect the complete workflow matrix on main
8. if anything red → fix only that defect → repeat from 4
9. all applicable workflows green → main stabilization certified
```

### Merge

- The `protect-main-branch` ruleset requires: Backend Verification, Frontend
  Verification, Runtime Verification, Analyze. **Verification Reconcile is not
  required.**
- **Do not add Reconcile to branch protection** until it has ≥5 consecutive
  green runs. A required check that fails intermittently blocks every later
  merge, which is worse than not requiring it.
- Squash-merge PR #7: 18 commits spanning distinct concerns, one logical change.
- Merge on the strength of the four required checks plus a locally reproduced
  reconcile run — not on a red reconcile.
- Watch `main` push runs to completion before opening the next PR.

### Protected state — do not touch

`feature/program-12-platform-certification`,
`recovery/program-r-forensic-reconstruction`,
`recovery/m9-c31-loss-06230db0`, `stash@{0}` (`40f7f891`, 5 files).

**Never run bare `git stash` here.** During this work a `git stash pop` was
issued with nothing to stash and resolved to the *protected* entry; it
conflicted and the index had to be cleared manually. Use `git stash push` only
after confirming the count, never `pop` by index, and prefer a throwaway
worktree for experiments.

### Certification report

Final SHA; workflow ownership map; complete workflow result matrix; CodeQL alert
status after the default-branch re-baseline (alerts only re-classify on `main`,
so the 33 open alerts from the August default-setup run are re-triaged after
merge); Playwright chromium and mobile-chrome results; and:

```
unexplained workflow failures = 0
unjustified security findings = 0
verification threshold changes = 0
quality threshold changes     = 0
mutation threshold changes    = 0
```

---

## Scope guard

If a step reveals something that looks like an optimization opportunity —
duplicated commands in `profiles.py`, a slow suite, clutter, an unused script —
**record it and move on.** Do not fix it in this pass. The programme ends when
`main` is green, not when the repository is optimal.
