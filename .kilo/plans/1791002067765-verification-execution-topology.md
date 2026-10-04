# M10-R2 Closeout — Live Execution Observability, Then the Two Opaque Failures

Narrow closeout. The runtime and backend fan-out architecture is **demonstrated on live
CI** and is closed:

| Gate | Measured | Status |
|---|---|---|
| Runtime Verification | **11m00s**, 4 shards + required aggregate (was ~26–30m single-job) | GREEN |
| Backend Verification | **6m59s**, 6 obligations + required aggregate | GREEN |

Required identities preserved (`Runtime Verification`, `Backend Verification`,
`Frontend Verification`, `Analyze`); `validate_actions.py` ALL CHECKS PASSED.

**Out of scope**, per review direction and because the evidence does not justify it:
reopening the runtime/backend architecture; splitting `backend/tests/` per-directory (the
profile already exposes the useful obligations, and the gate finishes in 6m59s); moving
runtime sharding 4→8 (4 already delivered ~2.4x from ~4x theoretical); Frontend
Verification (single obligation).

**Root cause of this closeout, stated once:** M10-R2-C3 moved profile/task output from
stdout into per-task evidence files. That was correct — it fixed the 0-byte-log problem —
but it silently removed the only live signal a CI operator had. The two remaining opaque
failures are not new defects; they are the *absence* of the signal needed to diagnose them.
So observability is Step 1, not an afterthought, and it is built **once** in the shared
primitive so no future matrix workflow can regress it again.

---

## 1. The three surfaces, and why only two were instrumented

| Surface | Lifetime | Carries | Status today |
|---|---|---|---|
| **Job log (stdout/stderr)** | live | lifecycle, progress, liveness | **missing** ← the gap |
| **Artifacts** | after the job | full stdout/stderr per task | partial (Playwright legs omit `profile-logs/`) |
| **Step Summary** | after the job | human report | present, but unreadable via `gh` |

Consequence, verbatim from the failing run:

```
[run] shard 1/7 executing 1/11 task(s)
... nothing ...
```

Four of seven reconcile legs died leaving 0 bytes and no indication of which canonical
task was executing. That is the observability gap, not a mystery.

---

## 2. Design: instrument the primitive, inherit everywhere

### 2.1 The seam

`runtime/foundation/verification/parallel_executor.py::run_streaming_command` is the single
choke point. Every verification subprocess in the repository already routes through it:

| Caller | Path |
|---|---|
| `ExecutionOrchestrator._execute_shell_task` | `verify check`, `run --plan` |
| `ParallelExecutor._execute_one` | group façade |
| `profile_tasks.run_obligation_leg` | backend legs, playwright legs |
| `runtime_shards.run_test_shard` | runtime shards |
| `ControlPlane._run_profile_alias._run_task` | profile aliases |
| `_run_runtime_integrity` | runtime gate |

One change here covers all six. That is the whole argument for putting it here rather than
in three YAML files — three copies would drift, and the previous regression is precisely
what drift looks like.

### 2.2 Contract

```python
@dataclass(frozen=True, slots=True)
class ProgressContext:
    """Optional live-logging context for one long-running command."""
    label: str          # "runtime-shard-2" | "backend-backend-unit" | "exec-0003"
    kind: str           # "shard" | "obligation" | "task" | "integrity"
    log_dir: Path       # where the FULL output lives, echoed once at start
    timeout_seconds: int

def run_streaming_command(
    command, *, stdout_path, stderr_path, timeout_seconds,
    cwd=None, env=None,
    progress: ProgressContext | None = None,   # default None => today's behaviour
    heartbeat_seconds: int | None = None,      # default: VERIFY_HEARTBEAT_SECONDS or 60
) -> CommandResult: ...
```

Emitted to **stderr** (stdout stays reserved for machine-readable documents — the
invariant established when the `[check] boundary=` banner corrupted shard reports):

```
[<label>] start kind=<kind> timeout=<n>s logs=<log_dir>
[<label>] running elapsed=60s
[<label>] running elapsed=120s
[<label>] exit=1 elapsed=137s timeout=false term=EXIT_NONZERO stdout=<path> stderr=<path>
```

Rules that make this safe rather than noisy:

- **Default `progress=None` is byte-identical to today.** Local runs and all 2717 existing
  tests are unaffected. Instrumentation is opt-in per call site.
- **Heartbeat comes from a watchdog thread**, not from the output stream, so it fires while
  `proc.wait(timeout=…)` blocks. Without this there is no live signal at all — which is the
  current failure.
- **No task content is ever streamed to the job log.** Full output stays in the artifact.
  A 20-minute pytest run must not produce a 20-minute CI log.
- Heartbeat suppressed entirely when the command finishes in under ~2 s, so the ~50 fast
  backend obligations do not each emit a start/exit pair for nothing.
- `VERIFY_HEARTBEAT_SECONDS=0` disables; `VERIFY_PROGRESS=0` silences locally.
- The final line always includes `term=<kind>` from the existing `classify_termination`,
  so the log distinguishes `WRAPPER_TIMEOUT` / `SIGNAL_TERMINATION` / `EXIT_NONZERO` /
  `INFRASTRUCTURE` without opening an artifact.

### 2.3 Per-leg framing

Call sites add their own `[leg n/m]` framing so the log reads as a unit:

```
[reconcile-shard] shard=1/7 plan=execplan-2ea6aa539c48 tasks=1
[reconcile-shard] task exec-0004 kind=integration start
[reconcile-shard] task exec-0004 running elapsed=60s
[reconcile-shard] task exec-0004 exit=1 elapsed=137s term=EXIT_NONZERO
[reconcile-shard] report=runtime/generated/execution/shards/shard-1.json bytes=1842
[reconcile-shard] finished status=failed outcome=terminal
```

| Leg kind | Label | Emitted by |
|---|---|---|
| runtime | `runtime-shard-N` | `runtime_shards.run_test_shard` |
| backend | `backend-<task_id>` | `profile_tasks.run_obligation_leg` |
| playwright | `playwright-<leg_id>` | `profile_tasks.run_obligation_leg` |
| reconcile | `reconcile-shard` + `exec-NNNN` | `ExecutionOrchestrator._execute_shell_task`, label derived from `plan_id`/`task_id` |

For reconcile the label must reach `_execute_shell_task`, which is inside the orchestrator —
so `ExecutionOrchestrator` takes an optional `progress_prefix` that it composes into each
task's `ProgressContext`. That is the only orchestrator change required.

---

## 3. Step 1 — Make execution observable (no behaviour change)

**1a. `run_streaming_command`** — add `ProgressContext`, the watchdog heartbeat, and the
terminal line. Default off.

**1b. `ExecutionOrchestrator`** — accept `progress_prefix`; pass a per-task
`ProgressContext` down. Default off.

**1c. Leg entry points** — build and pass `ProgressContext`:
`run_test_shard`, `run_obligation_leg`, `_run_profile_alias._run_task`, `_run_runtime_integrity`,
and the reconcile `run` shard path. Each also emits its `[leg n/m] … report=… bytes=…`
footer.

**1d. Artifacts.**
- Playwright legs: add `runtime/generated/profile-logs/` to `Upload leg artifacts`. Without
  it the visual-leg cause is unreadable — `_run_profile_alias` streams there.
- Reconcile legs: add `runtime/generated/profile-logs/` and
  `runtime/generated/m9-c49/logs/` so a dead leg's per-task logs survive.

**1e. Pre-upload assertion** (renamed from 1c), between run and upload. Fails loudly and
still uploads:

```bash
REPORT="$OUT_DIR/shard-${SHARD_INDEX}.json"
if [ ! -s "$REPORT" ]; then
  echo "::error::shard ${SHARD_INDEX}: NO TERMINAL RESULT — 0 bytes; see the [reconcile-shard] lines above for the last task reached"
elif ! jq -e . "$REPORT" >/dev/null 2>&1; then
  echo "::error::shard ${SHARD_INDEX}: malformed report"; head -c 400 "$REPORT"
fi
```

**Gate for step 1.** Re-run Verification Reconcile and Playwright once. Every non-green
leg must show, in its **job log**: which canonical task was executing, its exit code,
duration, termination kind, and whether a terminal result was written. **Do not proceed to
step 2 until the cause is read, not guessed.**

---

## 4. Step 2 — Fix only demonstrated defects

### 4a. The three-state leg-result contract (corrected)

Not "write JSON at the end". The contract:

> Every **terminal** execution outcome produces a machine-readable result. An externally
> killed process is inherently allowed to leave none — and that absence is itself a
> meaningful, distinguishable state.

`ControlPlane.run` (and, for symmetry, the two leg runners) gain
`--result-out <path>`, written on **every** terminal path: success, task failure, blocked
validation, and interrupt. It is no longer a stdout redirect.

```json
{
  "schema": "m10r2-leg-result/v1",
  "leg_id": "reconcile-shard-1",
  "outcome": "terminal",
  "status": "failed",
  "final_decision": "not_certified",
  "exit_code": 1,
  "duration_seconds": 137.2,
  "tasks": [ … ],
  "records": [ … ]
}
```

The aggregate then classifies three states, not two:

| Condition | Meaning | Verdict contribution |
|---|---|---|
| **no file** | leg never reached a terminal result — killed, cancelled, or never started | `NOT_CERTIFIABLE`, *"infrastructure: leg produced no terminal result"* |
| **file, `status=failed`** | leg ran and failed a verification obligation | `NOT_CERTIFIABLE`, naming the failing tasks |
| **file, `status=passed`** | leg completed | counts toward certification |

Two tightenings this forces, both of which are latent bugs today:

1. `read_shard_results` currently defaults missing fields
   (`payload.get("exit_code", 1)`) and lumps JSON errors under "unreadable". Change it to
   **reject an unknown `schema`** and to separate **`absent`** from **`malformed`** — they
   are different failures with different owners.
2. A malformed document must never be coerced into a passing state. The existing
   `_as_state` fallback already refuses that; the document-level equivalent must too.

### 4b. Restore the Playwright environment on reconcile shards (verified defect)

`run_playwright_tests.sh` exits 1 when `FINANCE_DB_PATH` is unset. The reconcile shard job
sets only `VERIFICATION_BASE_REF`/`VERIFICATION_HEAD_REF`, so **any** reconcile shard
assigned the Playwright task is guaranteed to fail it. The pre-M10-R2 single job carried
this environment; the split dropped it. Verified from source, not inferred.

Add to the reconcile shard job env:

- `FINANCE_DB_PATH: ${{ github.workspace }}/backend/data/e2e-playwright-${{ matrix.shard }}.db`
- `PLAYWRIGHT_PROJECT: chromium`
- `CLARIFIN_PYTHON: ${{ github.workspace }}/.venv/bin/python`

Per-shard, so two reconcile legs never share a database — the exact cross-shard mutation
`run_playwright_tests.sh` documents as the cause of drifting screenshots.

### 4c. Conditional

If step 1 shows the 0-byte legs died of something else (OOM, a specific task crash), fix
*that* and record it. Do **not** ship 4a as a substitute for a diagnosed cause — ship it
because it is correct independently, and say which defect it fixed.

---

## 5. Step 3 — Final validation

1. `verify quick` — exit 0.
2. `.venv/bin/python .github/scripts/validate_actions.py` — exit 0, 14 workflows.
3. Full `pytest runtime/tests/` — 2717 passed / 16 skipped / 0 failed.
4. `black --check runtime/ backend/src/` — clean (861 files).
5. `ruff check runtime/ backend/src/` — clean.
6. `cd backend && mypy src/` — clean (308 files).
7. Live CI: Verification Reconcile and Playwright; then confirm the four required
   identities are byte-identical.

**Acceptance**

- **While a shard is running, the GitHub Actions job log shows the shard is alive and
  which canonical task is executing. Diagnosis must never require waiting for artifacts
  after completion.** This is the criterion step 1 exists to satisfy, and it is checked by
  watching a live run, not by reading a finished one.
- Verification Reconcile: every shard produces a terminal result, or is explicitly and
  correctly classified as having none; the aggregate is never `shard coverage incomplete`
  for a reason the job log does not state.
- Playwright: 10/10 legs accounted for; every visual-leg failure has a named cause and, if
  it is a re-seed or isolation problem, is fixed at that dependency rather than masked.
- No required check renamed; no `paths:` on a required check; no threshold changed.

---

## 6. Tests to add

| Test | Asserts |
|---|---|
| `run_streaming_command` with `progress=None` | output files and `CommandResult` byte-identical to today |
| `progress` set, fast command | exactly one start line and one terminal line, **no** heartbeat |
| `progress` set, command outlives one interval | ≥1 heartbeat with monotonic `elapsed`, and none after exit |
| terminal line contains `term=` matching `classify_termination` | log and record agree |
| heartbeat disabled via `VERIFY_HEARTBEAT_SECONDS=0` | no heartbeat lines |
| `progress_prefix` composition | reconcile label is `reconcile-shard/exec-NNNN` |
| leg result written on task failure | file exists, `status=failed`, `outcome=terminal` |
| leg result written on blocked validation | file exists, not an exception |
| aggregate: missing file | classified `absent`, **not** merged |
| aggregate: `status=failed` | `NOT_CERTIFIABLE` naming the failing task, **not** `absent` |
| aggregate: unknown `schema` | rejected loudly; never coerced to pass |
| aggregate: malformed JSON | classified `malformed`, distinct from `absent` |

The last four are the regression guard for 4a: a failed shard must keep the aggregate red
and must not be mistaken for a shard that never ran.

---

## 7. Risk

| Risk | Sev | Mitigation |
|---|---|---|
| Instrumentation floods CI logs | Med | Heartbeat-only; content never streamed; suppressed for sub-2s commands; opt-in per call site |
| 4a lets a failed shard read as *absent* (or vice versa) and the gate mishandles it | **High** | §4a three-state table + the four aggregate tests in §6 |
| An unknown `schema` is coerced into a pass | **High** | Explicit rejection; `_as_state` precedent already refuses this |
| Heartbeat thread leaks or outlives the child | Low | Daemon thread, joined after `proc.wait`, plus an `is_alive()` guard |
| Restoring `FINANCE_DB_PATH` on reconcile changes DB behaviour | Med | Per-shard path; `tools/e2e_seed.py:656,663` verified to honour the env var with `--reset` |
| Scope creep into the proven gates | Med | Steps 1–3 touch only the primitive, reconcile, and Playwright. Runtime/backend are read-only |

---

## 8. Process corrections carried forward

Three authoring mistakes cost CI cycles last session and belong to the process, not to
one-offs:

1. **A failed assertion inside a multi-edit script silently skipped steps.** Two step
   insertions aborted and were pushed without verifying the step list; one caused every
   reconcile leg to fail its own guard. **Rule: after any programmatic YAML edit, assert
   the expected step names are present before committing.**
2. **Diagnostics written only to `$GITHUB_STEP_SUMMARY` are unreadable via `gh`.** Two
   rounds produced nothing. **Rule: diagnostics go to stdout; the summary is supplementary.**
3. **Local CLI verification cannot see YAML-shell defects.** Every primitive was green
   locally while the workflow failed. The checks that caught these were `bash -n` over
   every extracted `run:` block and a scan for `${` placeholders missing their `$`. **Keep
   both as pre-commit gates on any workflow edit.**

---

## 9. Execution note

Plan only — no files modified. Steps 1–3 require source edits to
`runtime/foundation/verification/{parallel_executor,execution_orchestrator,runtime_shards,profile_tasks,control_plane_facade}.py`
and `.github/workflows/{verification-reconcile,playwright}.yml`, plus mutating CI runs.
Switch to an implementation-capable agent.