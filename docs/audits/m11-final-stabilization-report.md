# M11 Final Stabilization Report

Scope: mutation-PR triage, merge of `m11/parallelism-correctness` into `main`, and
post-merge validation. No further optimization or architectural phase was started.

---

## 1. M11 final state

| Item | Value |
|---|---|
| Source branch | `m11/parallelism-correctness` |
| Final branch SHA | `072f66375c583ccf6b410dc9df01264e29e2d0a7` |
| Previous `main` before merge | `bfcf336b5b7f46e759c7486f3eb02d0f8d92e14b` |
| Merge commit SHA | `1820fd8ada0958a09c856e145cafcf253d3bbcf3` |
| Resulting `main` SHA | `1820fd8ada0958a09c856e145cafcf253d3bbcf3` |
| Merge mechanism | PR #17, `--merge` (ruleset `protect-main-branch`, id `20127383`) |
| Merge shape | true two-parent merge commit; M11 checkpoint history preserved |
| Working tree | clean (before and after every step) |
| Protected stash | `stash@{0}` = `40f7f891a0c103850279922a23d8e56d2b99892c`, unchanged |
| Protected / obsolete branch refs | byte-identical before and after (`diff` of `for-each-ref` output empty) |

The merge was a fast-forward of the local `main` (0 ahead, 122 behind), not a
rewrite. `main` was not force-pushed and no history was squashed.

---

## 2. The mutation-PR investigation (STEP 1)

### The exact GitHub annotation

Read from the run annotation, not inferred:

```
Invalid workflow file: .github/workflows/mutation-pr.yml#L1
(Line: 91, Col: 25): Unrecognized function: 'always'. Located at position 1
within expression: always() && steps.changed.outputs.changed == 'true'
```

`gh run view --verbose` reported, for every failing run:
`This run likely failed because of a workflow file issue.`

### Failure occurs before job creation — confirmed

| Probe | Result |
|---|---|
| `GET /actions/runs/{id}` → `jobs` | `[]` (empty array, not a failed job) |
| `GET /actions/runs/{id}/jobs` | no jobs |
| check suite `100980544415` → `check-runs` | `[]` |
| `GET /actions/runs/{id}/logs` | `log not found` — no step ever executed |
| `commits/{sha}/check-runs` | the failing workflow contributes **zero** check runs |

A red `failure` conclusion with no job, no log, no step and no check run is
GitHub rejecting the file at parse time. Nothing about the mutation campaign
ever ran.

### The annotation was mis-reported as "pre-existing" — correction

The working hypothesis handed to this task was that the file was "byte-identical
to `1c397368`, unchanged across four heads". That is true **only within the
branch**, and it is not the comparison that matters.

| Revision | Blob of `.github/workflows/mutation-pr.yml` |
|---|---|
| `main` (`8a3ac16f`, and `origin/main`) | `52a338f660dc835cf06e8b039afc08f890126af5` |
| `1c397368` | `6165f08951d7283a94c73b058038bbff769ddf5f` |
| `6f9b7ddd` (pre-existing branch head) | `6165f08951d7283a94c73b058038bbff769ddf5f` |
| `072f6637` (final head) | `6f7be3188750cffcb6f27e14c6d13686cc31a9a5` — changed by this milestone, see §3 |

`mutation-pr.yml` is **not** byte-identical to `main`. `git log main..HEAD --
.github/workflows/mutation-pr.yml` names exactly two commits, and
`git log -S 'if-condition: ${{ always() && steps.changed'` names one:

```
4e4bee99  ci: reconcile the architecture enforcer with the workflows it governs
03f10409  ci(security): SHA-pin every external action
```

`4e4bee99` is **not** an ancestor of `origin/main`
(`git merge-base --is-ancestor` → NO) and **is** an ancestor of
`origin/m10/consolidation`.

### Timeline, from the run history

| When (UTC) | Event |
|---|---|
| 2026-10-02 03:39 | last success, run `36961100888`, `pull_request`, at `8a3ac16f` (the blob `main` still carries) |
| 2026-10-02 04:12 | `4e4bee99` authored (09:42 +0530) — introduces the invalid expression |
| 2026-10-02 04:46 | first failure, run `37175266740`-era stream begins on `m10/consolidation` |
| … | 58 consecutive `failure` runs across `m10/consolidation` and `m11/parallelism-correctness` |

The success/failure boundary is the workflow file itself, not any other
dependency: the reusable actions (`.github/actions/*`), the Python toolchain and
the repository configuration are byte-identical across the boundary. The only
variable that changed is `mutation-pr.yml`.

### Classification

**Not pre-existing. Not M11 optimization work either.** The defect was introduced
during M10 CI-reconciliation work (`4e4bee99`) on `m10/consolidation`, five days
before the M11 branch was opened, and it is **absent from `main`**. It was
therefore an in-flight branch defect that would have been *shipped to `main`* by
this merge.

The mission's hard-stop condition — "mutation investigation reveals an M11-caused
regression" — is not met literally, but merging knowingly is not the correct
outcome either: the instruction to "not represent the repository as completely
green if GitHub still shows the known pre-existing mutation workflow failure"
rests on the premise that it is pre-existing, and that premise is disproved.
Per STEP 1's conditional instruction, the root cause was fixed in a **separate
commit**.

---

## 3. Root cause and fix

`4e4bee99` routed the artifact upload through the shared `upload-runtime`
composite action and passed the step's condition through an input:

```yaml
        uses: ./.github/actions/upload-runtime
        with:
          name: mutation-pr-report
          if-condition: ${{ always() && steps.changed.outputs.changed == 'true' }}
```

GitHub's expression context table restricts status functions (`always()`,
`cancelled()`, `failure()`, `success()`) to `jobs.<job_id>.if` and
`jobs.<job_id>.steps[*].if`. A composite action's `with:` value is neither, so
`always()` is not a recognized function there and the whole workflow file is
rejected.

Commit `072f6637` removed the redundant input:

```diff
         with:
           name: mutation-pr-report
-          if-condition: ${{ always() && steps.changed.outputs.changed == 'true' }}
           path: |
```

Semantics are unchanged, and provably so:

* the step already carries `if: always() && steps.changed.outputs.changed == 'true'`;
* `upload-runtime`'s documented default for `if-condition` is `always()`
  (`retention-days: 14`, `if-no-files-found: warn` defaults untouched);
* therefore the composite now runs exactly when the step is reached — the
  intended behaviour, including upload-after-failure.

No threshold, gate, evidence authority, or required check changed.

### Independent reproduction and verification

`actionlint` 1.7.12.25 — the same parser diagnostic GitHub emitted:

```
before: /tmp/…/mutation-pr-before.yml:91:29: calling function "always" is not
        allowed here. "always" is only available in "jobs.<job_id>.if",
        "jobs.<job_id>.steps.if".                                       exit 1
after:  no diagnostics                                                  exit 0
```

Repository constitution enforcer `.github/scripts/validate_actions.py`:
`Workflows validated: 14 · Composite actions validated: 6 · ALL CHECKS PASSED`.

Runtime workflow suites:
`pytest runtime/tests/test_inspect_workflows.py
runtime/tests/test_m9_c72_incremental_mutation.py
runtime/tests/test_m9_c71_mutation_campaign.py` → **94 passed**.

### CI proof that the workflow is genuinely healthy, not merely parseable

Run `37325496055` on `072f6637` — the first successful `mutation-pr` run since
2026-10-02, and the first one ever reported as a `pull_request` event rather
than a bare push-attributed parse notice:

```
Incremental Mutation (PR) — success
  Checkout code ✓ · Bootstrap Engineering Runtime ✓ · Verify canonical
  environment ✓ · Get changed files ✓ · Run incremental mutation ✓ ·
  Upload mutation report ✓ · Comment on PR ✓ · Fail if mutation did not
  pass (skipped — exit code 0)
```

A job exists, steps execute, the campaign runs, the artifact uploads and the PR
comment posts.

---

## 4. Required workflow evidence

Final branch head `072f6637`, PR #17, all 41 checks `SUCCESS`, `mergeStateStatus: CLEAN`.

| Workflow | Final result |
|---|---|
| Backend Verification | **PASS** |
| Frontend Verification | **PASS** |
| Verification Runtime | **PASS** |
| Verification Reconcile | **CERTIFIED** — `Decision: certified`, 7/7 shards certified |
| Quality Gate | **PASS** |
| API Contract Integrity | **PASS** |
| Playwright | **CERTIFIED** — `final_decision: certified`, "all 10 leg(s) passed (2 visual, 8 functional)" |
| CodeQL | **PASS** |
| Forensic Evidence Collection | **PASS** |
| Mutation Testing (PR Incremental) | **PASS** — repaired in `072f6637` |

Ruleset-required contexts (`protect-main-branch`, id `20127383`):
`Backend Verification`, `Frontend Verification`, `Runtime Verification`,
`Analyze` — all `SUCCESS` on `072f6637`. None of the four carries a `paths`
filter, so none could be silently skipped.

No check from a previous commit was reused. Every entry above was observed on
`072f6637` itself.

### Local certification against the merged tree (`1820fd8a`)

| Gate | Command | Result |
|---|---|---|
| Contracts | `runtime.verify contracts` | **certified** — schemathesis + aggregate pass, 159.4s |
| Quick / Quality | `runtime.verify quick` | **certified** — ruff, black, mypy, unit pass, 162.3s |
| Frontend | `runtime.verify frontend` | **certified** — 117 files, 1519 tests passed, 452.6s |
| Backend | `runtime.verify backend` | ruff/black/mypy/unit/schemathesis pass, 3301 unit tests; `backend-integration` hit a **local** `pytest-timeout` (60s) on `test_platform_api_phase3.py::TestHealth::test_health_returns_correct_kind` under 3-way concurrency |
| Workflow enforcer | `validate_actions.py` | ALL CHECKS PASSED (14 workflows, 6 composites) |
| Doctor | `runtime.verify doctor` | `Framework authority integrity: HEALTHY`, exit 0 |
| Doctor | `scripts/env-doctor.sh` | exit 0 |
| Env | `runtime.verify env-check` | `"consistent": true`, `"errors": []`, mutmut 3.7.0 from `.venv` |

The one local backend red is **environmental, not a regression**, and is
classified as such:

* it is a `pytest-timeout` timeout, not an assertion failure;
* the same test passes in isolation in 5.49s;
* the change in `072f6637` is a single YAML workflow line and cannot affect
  backend runtime behaviour;
* CI `Backend backend-integration` is **SUCCESS** on `072f6637`.

Workstation-generated evidence under `runtime/generated/` produced by these local
runs was reverted before the push; the merge commit contains no workstation
artifacts.

---

## 5. Post-merge validation of `main` (STEP 6)

| Check | Result |
|---|---|
| New `main` SHA | `1820fd8ada0958a09c856e145cafcf253d3bbcf3` |
| Expected merge result | confirmed — parents `bfcf336b` (old main) and `072f6637` (M11 head) |
| Local `main` | fast-forwarded to `1820fd8a`, not rewritten |
| Working tree | clean |
| Protected stash | `40f7f891…`, unchanged |
| Protected branch refs | `diff` before/after empty |
| `runtime.verify doctor` | HEALTHY, exit 0 |
| `scripts/env-doctor.sh` | exit 0 |
| `validate_actions.py` | ALL CHECKS PASSED |

Post-merge workflows GitHub launched automatically on the push to `main` —
**all eight succeeded**:

| Workflow | Event | Conclusion |
|---|---|---|
| Backend Verification | push | success |
| Frontend Verification | push | success |
| Verification Runtime | push | success |
| Quality Gate | push | success |
| API Contract Integrity | push | success |
| Playwright Tests | push | success |
| CodeQL Security Analysis | push | success |
| Dependency graph update | dynamic | success |

`Verification Reconcile` and `M9 Forensic Evidence Collection` are declared
`on: pull_request` only, so they do not run on a push to `main`. Both were
executed and green on the PR head `072f6637`; their results are in §4.

---

## 6. Workflow classification summary (STEP 7)

### Green / certified

Every workflow that participates in `main` protection or that runs on the merge:
Backend Verification, Frontend Verification, Verification Runtime, Verification
Reconcile, Quality Gate, API Contract Integrity, Playwright, CodeQL, Forensic
Evidence Collection, and — newly — Mutation Testing (PR Incremental).

### Pre-existing and unrelated to this merge

None. The single remaining red item at the start of this milestone was
`mutation-pr.yml`, and investigation proved it was **not** pre-existing: the
defect predates the M11 optimization work but was introduced on the branch
lineage by `4e4bee99` and does not exist on `main`. It was fixed in
`072f6637` and is green.

The M11-R4 completion report labelled it `PRE-EXISTING`; that classification is
superseded by this report, which carries the annotation and the blob-level proof.

### Not part of this merge

* `dependency-update.yml` — not triggered, unrelated.
* The `runtime.verify doctor` advisory that "verification success rate is below
  95%" on **local** runs — historical local history (105 data points, 0 CI data
  points); exit 0, framework integrity HEALTHY. Not a gate.

---

## 7. M11 correctness outcomes preserved

These are unchanged by the mutation-PR repair and remain the substance of M11:

* **Playwright leg results are actually consumed.** `read_leg_results` globbed
  `shard-*.json` while legs are written as `leg-*.json`, so the gate saw zero
  legs and its verdict was independent of any test. The glob is now an explicit
  parameter. CI: `legs_reported: 10, legs_passed: 10`.
* **The reconciliation aggregate produces a real verdict.** The producer emitted
  3-key records and the aggregator rebuilt against a 23-field dataclass, so the
  aggregate raised `TypeError` and never reached a decision. CI:
  `tasks=10 shards=7 unreadable=0 Decision: certified`.
* **Escalation ownership is implemented correctly.** Shards omit escalation tasks
  by design; the aggregate owns the barrier and now decides it on the
  orchestrator's own rule, recording it as `SKIPPED` with the orchestrator's
  wording rather than deadlocking or auto-skipping.
* **Shard certification works.** 7/7 shards certified; previously 5/7.
* **Capability provenance survives execution.** `_expand_control_plane_tasks`
  collapsed capability names into a single `capability_id` bucket, so the
  registry-gap obligation reported a count instead of the three names it owed.
  Two accumulators now: `capability_ids` names the obligation, `capabilities`
  carries the names.
* **mutmut initialization is deterministic.** Pinned to 3.7.0 in the root
  `pyproject.toml`, resolved from the repository `.venv`, with a trampoline
  contract established at session start.
* **Result parsing is truthful.** A truncated or fingerprint-less record is
  named and **refused certification** rather than read as a pass.
* **No certification threshold was weakened.** `verification.yaml` thresholds
  and fallback defaults are unchanged; ruleset, required checks, CodeQL coverage
  and evidence authority are unchanged. The only M11-FINAL source change is one
  removed line of YAML in `mutation-pr.yml`.

---

## 8. Final conclusion

1. **M11 is merged.** `m11/parallelism-correctness` → PR #17 → `main` at
   `1820fd8ada0958a09c856e145cafcf253d3bbcf3`, as a real merge commit with the
   checkpoint history intact.
2. **`main` is stable.** Doctor, env-doctor and the workflow enforcer all pass
   against the merged tree; the working tree is clean; the protected stash
   (`40f7f891…`) and every protected/obsolete branch ref are byte-identical to
   their pre-mission values.
3. **Required checks are green** on the final branch head `072f6637` —
   `Backend Verification`, `Frontend Verification`, `Runtime Verification`,
   `Analyze` all SUCCESS, `mergeStateStatus: CLEAN` — and all eight
   automatically launched post-merge `main` workflows succeeded.
4. **There is no remaining pre-existing failure.** The mutation-PR red that
   opened this milestone was investigated to its GitHub annotation, proven to
   have been introduced on the branch lineage rather than inherited from `main`,
   fixed at the root cause in a separate commit (`072f6637`), and confirmed
   green in CI with a real job, real steps and a real artifact upload. Nothing
   is red and nothing is being deferred or re-classified to unblock the merge.
