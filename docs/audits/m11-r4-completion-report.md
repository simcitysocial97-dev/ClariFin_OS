# M11-R4 — CI Failure Reproduction and Convergence

**Branch** `m11/parallelism-correctness` · **starting HEAD** `5ba872d4` · **final HEAD** `db8fb97d`
**Report date** 2026-10-05 · **Status: complete**

---

## 0. Summary

The mission arrived with a failure table listing four open items. Two of them were
much larger than described, and both turned out to be gates that could not have
passed under any circumstances:

* **The Playwright gate had never read a single leg result.** `read_leg_results`
  delegated to a reader that globs `shard-*.json` while `playwright.yml` writes
  `leg-<id>.json`. Every run reported `legs_reported: 0` and returned NOT CERTIFIED
  regardless of the tests — including run 37254330609, where all ten legs were green.
* **The reconcile aggregate had never produced a verdict.** Every
  `Verification Reconcile` run since the M10-R2 topology landed died with
  `TypeError: TaskExecutionRecord.__init__() missing 20 required positional
  arguments`. The identical traceback appears in run 37257612911 at 03:24 and in run
  37270708886 at 06:29.
* **Reconciliation could never certify a plan containing an escalation task**, because
  shards deliberately omit escalation tasks and the aggregate never decided them.

Both were masked for as long as the shards were independently red: the gate was
already failing, so nobody was reading its traceback. Turning the shards green is what
exposed them, in that order.

Ten of eleven workflows are green at `db8fb97d`. The eleventh, `mutation-pr.yml`, is
the known pre-existing failure and its workflow file is byte-identical to `1c397368`.

---

## 1. Failure convergence

| Original CI failure | Root cause | Fix | Local proof | CI proof |
|---|---|---|---|---|
| `exec-0006` reports `unmapped:UNMAPPED[3]` — a count, not three names | `_expand_control_plane_tasks` seeded the dedup bucket with `{cp_task.capability_id}` and wrote it back into `spec.capabilities`, discarding `VerificationTask.capabilities` (`execution_orchestrator.py:2072,2096-2098`) | Two accumulators: `capability_ids` names the obligation, `capabilities` carries the names | `runtime/tests/test_m11_r4_capability_provenance.py`: 3 of 5 fail at HEAD, pass with the fix | plan artifact of run 37274801285: `exec-0001` carries 6 capabilities, `exec-0006` carries 5 |
| Three capabilities unmapped on CI but not locally | The reconcile **plan** job provisioned Python only, so `npx tsx` failed with `Cannot find module 'ts-morph'`, discovery minted zero frontend capabilities | `setup-node-runtime` added to the plan job | reproduced exactly: `resolve_capabilities` with `frontend_capabilities = {}` → precisely those three paths | run 37274801285 plan has **no** `registry_mapping` task at all |
| Playwright leg result reports `passed: 0, failed: 0` | (a) both passes ran `--reporter=list`, which **replaces** the config's reporters, so the JSON report was never written; (b) `playwright.yml` hard-coded zeros; (c) there was no canonical way to run one leg | `playwright-leg` command + `--reporter` removed from the script | real leg: `passed=23 failed=4 (293.9s)`; CI: `passed=21 failed=0 duration=38.19s` | run 37279314464 gate: `legs_reported: 10, legs_passed: 10` |
| Playwright gate `legs_reported: 0` on every run | `read_leg_results` → `read_shard_results` globbed `shard-*.json`; legs are `leg-*.json` | glob is now an explicit parameter, `leg-*.json` at the call site | the verbatim CI document read as `results=0 absent=['no shard-*.json files found']` before the fix | `legs_reported: 10, final_decision: certified` |
| Playwright visual legs exit 1 | Baselines stale: `cards-page` differed by 216 702 px (23% of frame); two mobile-chrome baselines never existed at all | Regenerated on the canonical renderer, fetched from a runner artifact | reproduced identically: `11 failed / 10 passed` | run 37269522107 (dispatch): all 11 jobs green |
| Regeneration "did not fire" | It did — and was discarded. No workflow step published the rewritten baselines | new upload step, `if-no-files-found: error` | — | `playwright-baselines-chromium` / `-mobile-chrome` artifacts exist |
| `Verification Reconcile` red (5/7 shards) | `exec-0004` (Playwright) and `exec-0006` (registry gap) — see above | see above | — | 7/7 certified, aggregate `Decision: certified` |
| `Verification Reconcile` aggregate `TypeError` | Producer emitted 3-key records; aggregator rebuilds against a 23-field dataclass | producer writes `r.to_dict()`; malformed records reported, not raised | 5 of 8 tests fail at HEAD | `unreadable=0`, `Decision: certified` |
| `not_certifiable: missing 3 task(s): exec-0006/0007/0008` | Shards omit escalation tasks by design; the aggregate was supposed to own them and did not | the aggregate decides the barrier, on the orchestrator's rule | `mandatory green -> certified, escalation: [skipped, skipped, skipped]` | run 37279314488 `tasks=10 shards=7 unreadable=0 Decision: certified` |

---

## 2. CI parity

Every row uses the repository's own canonical command — the one the workflow invokes.

| Workflow | CI command | Local reproduction | Result |
|---|---|---|---|
| Quality Gate | `runtime.verify quick` | identical, `.venv` | **certified** — ruff, black, mypy, unit pass; 170.5s; fingerprint stable |
| API Contract Integrity | `runtime.verify contracts` | identical | **certified** — 122.5s |
| Frontend Verification | `runtime.verify frontend` | identical | **certified** — 351.2s |
| Verification Runtime | `runtime.verify runtime-plan/-shard/-aggregate` | not executed (45-min seven-shard fan-out) | CI green |
| Verification Reconcile | `plan --shard-plan` → `run --shard N --result-out` → `run --aggregate` | plan + capability resolution + merge reproduced directly | CI green; local merge proven both directions |
| Playwright | `playwright-plan` / `playwright-leg` / `playwright-aggregate` | identical, both passes, both modes | reproduced exactly |
| Backend Verification | `backend-plan` / `backend-task` / `backend-aggregate` | not executed | CI green |
| CodeQL | GitHub action only | **not reproducible locally** | environmental |
| M9 Forensic Diagnostic Lab | `runtime.verify` profile | not reproduced locally | CI green |

**Unavoidable deltas**

1. **CodeQL** has no local equivalent.
2. **Verification Runtime** is a 45-minute fan-out; re-running it locally costs the same
   wall clock to exercise the same code.
3. **Node in the reconcile plan job** — until STEP 4b this was a *silent* delta, and it
   is the reason `unmapped` differed between machines. Now closed by provisioning Node.
4. **Chromium rasterisation** — the visual failure was reproduced locally
   (`11 failed / 10 passed`) but nothing was regenerated locally. Skia's hinting and
   subpixel settings come from the host's fontconfig/freetype and cannot be pinned from
   application code.

---

## 3. Runtime correctness

**mutmut trampoline initialization is order-independent.** Closed by M10-R3
(`74cb2baf`), re-verified green in runs 37279314509 and 37279314507. Not re-fixed.

**Capability identity survives serialization/deserialization.** `VerificationTask.capabilities`
→ `ExecutionTaskSpec.capabilities` → JSON → shard record, pinned by
`test_m11_r4_capability_provenance.py`. Confirmed on CI: `exec-0001` reports
`["api-contracts", "behaviour-engine", "credit-card-engine", "financial-intelligence",
"ledger", "loan-engine"]`. The three capabilities CI previously reported only as a
count were named exactly, not inferred from a label:

```
UNMAPPED:frontend/app/api/diagnostic-signatures/route.ts
UNMAPPED:frontend/app/layout.tsx
UNMAPPED:frontend/app/settings/page.tsx
```

**Shard result aggregation is truthful.** Shard records now carry all 23 fields, so the
aggregate receives durations, exit codes, diagnostics, measurement truth and capability
names rather than a three-key summary. A malformed record is named and forces
`not_certifiable` — the opposite of the previous behaviour, where it raised and cost the
whole verdict.

**Certification semantics were not weakened.** Every change moves in the strict
direction:

| | before | after |
|---|---|---|
| Playwright leg without a fingerprint bracket | unreadable, verdict independent of tests | read, **refused certification** |
| Aggregate sees a truncated record | `TypeError`, no verdict | named, **refused certification** |
| Mandatory task fails, escalation unreported | — | still `not_certifiable`, escalation **named, never auto-skipped** |
| Sufficiency met, escalation unreported | `not_certifiable` (deadlock) | `certified`, escalation recorded `SKIPPED` with the orchestrator's own wording |

The only case that moved from red to green is the sufficiency-met case, and only by
reaching the verdict the orchestrator itself reaches for the same evidence. No
threshold, gate, security check, mutation requirement, contract requirement or
certification condition was altered. `DIFF_THRESHOLD`, `MAX_DIFF_PIXELS` and
`maxDiffPixelRatio` are untouched.

**Playwright result counts are real.** From the runner's own JSON reporter, never
fabricated: `chromium-visual` reported `passed: 21, failed: 0, duration_seconds: 38.19`
on the leg that had just failed eleven assertions, where the old document read
`passed: 0, failed: 0, duration_seconds: 0`.

**Snapshot regeneration is deterministic.** The dispatch run both re-records *and*
re-runs the comparison in one pass, so a green leg after regeneration has proved the new
image rather than merely written it. `PROVENANCE.md` records the run id, the SHA and the
reason. Verified before installing: the chromium artifact differs from HEAD only on
`*-chromium-linux.png` and the mobile artifact only on `*-mobile-chrome-linux.png`, so
neither could silently revert the other's work.

---

## 4. Git checkpoints

| SHA | Purpose |
|---|---|
| `fe91dadb` | preserve capability provenance through shard execution |
| `216cb777` | make the playwright leg result real evidence |
| `7a36b00e` | publish regenerated playwright baselines |
| `8d7617ea` | give the reconcile plan job the frontend toolchain it needs |
| `a624857a` | fix unbound `LEG_TIMEOUT_SECONDS` in the leg backstop |
| `82714e15` | regenerate visual baselines on the canonical renderer |
| `c4a73cca` | fix the reconcile aggregate, which had never produced a verdict |
| `db8fb97d` | let the aggregate decide the escalation barrier it owns |
| `7a46822e` | trace the 5/7 shard certification failure (progress.md) |
| `c7a7401e` | record the local CI replication matrix (progress.md) |
| `4dc48deb` | checkpoint pending tracked artifacts |

Test evidence per checkpoint is in `progress.md` under the matching STEP.

---

## 5. Final CI state — `db8fb97d`

| Workflow | Run | State |
|---|---|---|
| Backend Verification | 37279314465 | **PASS** |
| Frontend Verification | 37279314507 | **PASS** |
| Quality Gate | 37279314470 | **PASS** |
| Verification Runtime | 37279314509 | **PASS** |
| Verification Reconcile | 37279314488 | **PASS** — 7/7 shards certified |
| Playwright Tests | 37279314464 | **PASS** — 10/10 legs |
| API Contracts | 37279314467 | **PASS** |
| CodeQL | 37279314466 | **PASS** |
| Forensic Lab | 37279314614 | **PASS** |
| mutation-pr.yml | 37279308373 | **PRE-EXISTING** |

Reconcile certification, run 37279314488:

```
[aggregate] plan=execplan-059051d15471 tasks=10 shards=7 unreadable=0
Decision: certified

reconcile-shard-0..6   passed  certified  (7 of 7)
```

Playwright gate, run 37279314464:

```
legs_reported: 10   legs_passed: 10   visual_legs: 2   final_decision: certified
```

---

## 6. Remaining issues

### `mutation-pr.yml` — PRE-EXISTING, untouched

* **Exact failure.** The run is created and fails at 0 s with no job ever starting —
  GitHub's "workflow file issue" class.
* **Predates M11.** `git diff 1c397368..HEAD -- .github/workflows/mutation-pr.yml` is
  empty: byte-identical to the commit where this was first observed.
* **Evidence.** Runs 37261658209, 37269439011, 37274794908, 37279308373 — all four
  fail the same way, across four heads spanning this entire phase.
* **Why it was not changed.** Rule 10 forbids touching it unless investigation proves
  M11 caused the failure, and it did not.
* **Recommended next action.** Read the annotation set on the workflow in the Actions
  UI (a 0-second failure with no jobs almost always carries one), fix the YAML, then
  re-enable. It is a separate piece of work from failure convergence.

### Local environmental deltas — not failures

Chromium rasterisation and the absence of a local CodeQL are properties of the
workstation, recorded in §2 rather than worked around.

---

## 7. What this phase did not do

* No architecture redesign, no new optimization pass.
* No threshold, gate, security check, mutation requirement, contract requirement or
  certification semantic was weakened.
* The three protected obsolete branches and the pre-existing stash are untouched —
  `stash@{0}` is byte-identical at `40f7f891a0c103850279922a23d8e56d2b99892c`.
* No failure was hidden by `|| true`, an unconditional skip, a fake success record or a
  relaxed assertion.