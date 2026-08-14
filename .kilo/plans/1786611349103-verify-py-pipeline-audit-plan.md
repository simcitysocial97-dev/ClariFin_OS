# verify.py / Verification Pipeline — Audit & Hardening Plan (revised)

## Context & Corrections (verified against the repo, not assumed)
A 4-day red CI exists. The earlier audit plan was correct as *hardening* but must be
re-scoped end-to-end and its triage corrected against the real workflows:

- **All workflows use `fetch-depth: 0`** (verification-runtime.yml:54, quality.yml:46,
  backend-verify.yml:51, verification-reconcile.yml:59). The "shallow clone" hypothesis is
  **invalid for this repo**. Do NOT add shallow-clone fallbacks as if that were the bug.
- **`verify.py pr` does not exist.** The only PR-plan command is
  `verify.py plan --tier pr --base ${GITHUB_BASE_REF:-main}` (verification-reconcile.yml:71-76),
  which already supplies a `main` fallback. The claim "GITHUB_BASE_REF missing makes cmd_plan
  reject" is **invalid** — CI always passes a base.
- **Actual red-producing commands**: `verify.py runtime`, `verify.py quick`, `verify.py backend`
  (the profile branch in verify.py → cache replay + `VerificationOrchestrator.run()`), and
  `verify.py reconcile` (verification-reconcile.yml:110-116 is NOT `continue-on-error`, so
  reconcile CAN fail the workflow). Inside verification-reconcile.yml, `plan` (line 69) and
  `runtime` (line 82) are `continue-on-error: true`, so they cannot turn the workflow red.
- **`verify.py diagnose-failures` is NOT in any CI workflow** (grep-confirmed). Its exit code
  cannot be the 4-day cause; changing it is hardening only, adopted per user request.
- **Executor timeout is 3600s** (executor.py:80), not "hang forever". Real risk is a 1-hour
  stall, not infinity. Hangs are not the prime suspect.

Root cause is UNKNOWN. Phase 0 exists to extract it; the plan does not assume it.

## Affected files (scope)
- `runtime/verify.py` (CLI dispatch + all `cmd_*`)
- `runtime/foundation/verification/cache.py` (cache key, atomic write, lock)
- `runtime/foundation/verification/orchestrator.py` (`_collect_changed_files`, run path)
- `runtime/foundation/verification/executor.py` (subprocess, debug logging)
- `runtime/foundation/verification/reconciliation.py` + `evidence_contract.py` (pre-flight)
- `runtime/foundation/verification/tier.py` (`FRAMEWORK_VERSION` reuse, `--debug`)
- `runtime/tests/test_diagnose_failures.py` (exit-code contract split)
- `.github/workflows/*.yml` (forensic step, stderr artifact, smoke-test job)

## Phase 0 — Triage (MUST run FIRST — no Phase 1 Python changes until the traceback is captured)
**Hard gate:** implement ONLY workflow YAML in Phase 0. Do NOT touch `runtime/*.py` until the
Phase 0 artifact shows the real error. Root cause is unknown; Phase 1 item #2–#4 are the most
likely to surface it, but implementing blind wastes effort. Goal: capture the raw traceback for
the ACTUAL red commands.

1. **Pre-flight Diagnostics step** prepended to `verification-runtime.yml`, `quality.yml`,
   `backend-verify.yml`, and the `reconcile-gate` job:
   ```yaml
   - name: 🔍 Pre-flight Diagnostics
     run: |
       echo "=== ENVIRONMENT ==="
       echo "GITHUB_BASE_REF=$GITHUB_BASE_REF"
       echo "GITHUB_HEAD_REF=$GITHUB_HEAD_REF"
       echo "GITHUB_SHA=$GITHUB_SHA"
       echo "GITHUB_EVENT_NAME=$GITHUB_EVENT_NAME"
       echo "RUNNER_OS=$RUNNER_OS"
       echo "=== GIT STATE ==="
       git status --short
       git log -1 --oneline
       git remote -v
       git branch -a | head -5
       echo "=== FILES ==="
       ls -la runtime/generated/ || echo "NO_GENERATED_DIR"
       echo "=== PYTHON ==="
       python --version
       python -c "import sys; print('sys.path:', sys.path[:3])"
       python -c "import runtime.foundation.verification.tier; print('✅ tier ok')" || echo "❌ import fail"
       python -c "import runtime.foundation.verification.orchestrator; print('✅ orchestrator ok')" || echo "❌ import fail"
   ```
2. **Full stderr capture + upload.** Replace the bare run with (use the SAME profile the job runs:
   `runtime`/`quick`/`backend`; or `reconcile` for the reconcile-gate job — NOT `pr`):
   ```yaml
   - name: Run verification (with stderr capture)
     id: verify
     continue-on-error: true
     run: |
       python -u runtime/verify.py runtime 2> verify_stderr.log
       echo "exit_code=$?" >> $GITHUB_OUTPUT
   - name: Upload stderr diagnostics
     if: always()
     uses: actions/upload-artifact@v4
     with:
       name: verify-stderr-${{ github.run_id }}
       path: verify_stderr.log
       retention-days: 7
   - name: Fail workflow if verification failed
     if: steps.verify.outputs.exit_code != '0'
     run: exit 1
   ```
3. **Local repro with CI's changed_files.** In the runner (or locally) run
   `python runtime/verify.py plan --tier pr --base main --head $GITHUB_SHA --no-write` then
   `python runtime/verify.py <profile>` using the exact changed file list CI computed, to
   reproduce outside GitHub.
4. **Map the traceback to Phase 1 (implement only what the evidence warrants).** After running the
   workflow and inspecting the `verify-stderr-<run_id>` artifact, pick the matching items:
   - reconcile schema/evidence error (`Evidence file not found`, `missing key`, `units count !=`)
     → Phase 1 #2 (pre-flight) + #3 (schema validation).
   - `verify.py runtime/quick/backend` failing / subprocess masked → Phase 1 #1 (`--debug`) + #4
     (orchestrator visibility).
   - cache corruption / stale pass → Phase 1 #5 (env-aware cache).
   - audit/knowledge failures → Phase 1 #9 + #10.
   If `cmd_diagnose_failures` is the error (unlikely — not wired into CI), the exit-code change
   is irrelevant. Add the Phase 2 tests for each changed item BEFORE editing the source.

## Phase 1 — Hardening (the user's expanded scope + original plan)
Ordered by diagnostic value first.

1. **`--debug` global flag (verify.py `main()`).** At the TOP of `main()`, BEFORE dispatch:
   ```python
   debug_mode = "--debug" in sys.argv or "--verbose" in sys.argv
   if debug_mode:
       sys.argv = [a for a in sys.argv if a not in ("--debug", "--verbose")]
       logging.basicConfig(level=logging.DEBUG)
       print(f"[DEBUG] sys.argv: {sys.argv}", file=sys.stderr)
       print(f"[DEBUG] cwd: {os.getcwd()}", file=sys.stderr)
   ```
   When set: print `sys.argv`, filtered `os.environ` (redact `GITHUB_TOKEN`/`*TOKEN*`/`*SECRET*`),
   and the full `changed_files` list to stderr; set a module-level `_DEBUG` that
   `executor._execute_once` uses to log the exact command, `cwd`, timeout, and return code.
   No third-party deps.
2. **`cmd_reconcile` pre-flight (reconciliation.py / evidence_contract.py).** Before parsing CI
   artifacts, assert `--plan` and `--evidence` files EXIST and are valid JSON containing the
   required schema keys (`tier`, `selected`/`unit_id`, `planner_version`/`framework_version`
   for plan; `schema`/`units`/`records` for evidence). On missing/invalid → print detailed
   error naming the file + missing key, exit **non-zero** (use 1 for artifact fault). Do NOT
   fall back to a ghost diff.
3. **Schema validation on write (tier.py, evidence_contract.py, atomic_write_json).** Wrap
   `plan.write`, `save_execution_evidence*`, and `save_reconciliation_report` so a serialization
   error prints the exact field mismatch (no silent truncation). Add `runtime/foundation/verification/_io.py`
   with `atomic_write_json(path, data)` (temp file in same dir + `os.replace`) and route ALL
   artifact writes through it; ensure parent dirs exist in one place.
4. **`_collect_changed_files` visibility + safety (orchestrator.py).** Keep `fetch-depth:0`
   semantics. Add an explicit, LOUD stderr warning when the resolved diff is EMPTY (do not
   silently proceed). Wrap the `git fetch origin` (line 245) in try/except and, on failure,
   fall back to local ref + warn. Handle detached HEAD (merge-base may fail → fall back to
   `HEAD` + warn). Missing `.git` (`_is_git_available()` False) → return `[]`; let the caller
   decide (already does). No shallow-clone hack.
5. **Cache key = environment-aware (cache.py).** Add `env_version` = stable hash of `sys.version`,
   `runtime/` source mtimes, and `FRAMEWORK_VERSION` (reuse from tier.py). Store at top level;
   include in `is_valid`/`replay`. Mismatch → miss (re-run). Preserve the never-replay-fail-as-pass
   guarantee (cache.py:119). Existing contract tests must add `env_version` to fixtures.
6. **Non-silent observability (verify.py `_record_verification_event`).** Replace
   `except Exception: pass` (line 130-131) with `logging.warning` of the error; return `bool`
   (success). A broken metrics store must be visible, never crash the run.
7. **`cmd_diagnose_failures` exit contract (verify.py:245-253 + tests).** Adopt the user's
   resolved contract:
   - evidence_dir MISSING → exit **3** ("pipeline state unknown").
   - evidence exists, no failures → exit **0** ("nothing to diagnose").
   - failures present, change implicated → exit **1** (unchanged).
   - failures present, not implicated → exit **0** (unchanged).
   Add `--ignore-missing-evidence` escape hatch (docs-only skip) → exit 0.
   Split `test_no_evidence_state_is_explicit_not_fabricated` into `test_missing_evidence_exits_3`,
   `test_empty_evidence_exits_0`, keep the implicated/non-implicated tests at 1/0.
8. **`cmd_ci_doctor` timeout (verify.py:182-195).** Add
   `timeout=int(os.environ.get("CI_DOCTOR_TIMEOUT", 300))` (configurable), `TimeoutExpired` →
   non-zero + clear message. Never hang.
9. **`cmd_audit` graceful degradation (verify.py:952-1023).** Wrap each `audit_*` import in
   try/except; register a module returning a structured "import failed" section instead of
   aborting; report degraded-module count. One bad import no longer kills the whole audit.
10. **`cmd_knowledge` index cache.** mtime+size-keyed cache in `build_index` so repeated queries
    skip rebuild; invalid fragments trigger rebuild. Correctness first.

## Phase 2 — E2E test suite (write BEFORE the matching Phase 1 change — test-driven)
- New `runtime/tests/test_verify_robustness.py`: `_record_verification_event` warns on broken
  store; `cmd_diagnose_failures` exit 3 on missing dir / 0 on empty; `cmd_ci_doctor` timeout
  path (mock subprocess sleep); `cmd_audit` continues when one module import fails; reconcile
  pre-flight exits non-zero on missing `--evidence`.
- New `runtime/tests/test_vea5_verification_cache.py` additions: `env_version` mismatch → miss;
  atomic write leaves no `.tmp`; concurrent write under lock (temp dir) does not corrupt.
- Integration smoke test (Docker/act): fake shallow clone + missing ref + corrupted evidence to
  prove Phase 1 items surface errors instead of hanging or silently passing.

## New CI job — Smoke test (`.github/workflows/`)
Add `verification-smoke.yml`: runs `verify.py plan --tier local --no-write` and
`verify.py local-gate` only (no execution). If this passes but the full profile fails, the fault
is isolated to the executor/evidence path. `fetch-depth: 0`, same setup composite action.

## Decisions locked
- diagnose-failures exit codes: 0/1/3 (3 = missing evidence dir), plus `--ignore-missing-evidence`.
- `--debug` parsed before dispatch; no new deps.
- cache key gains `env_version`; forces one re-run, acceptable.
- No shallow-clone fix (repo uses fetch-depth: 0).
- Only `reconcile` + profile runs can turn CI red; triage targets those, not `diagnose-failures`.

## Validation
- `python -m pytest runtime/tests/test_vea5_verification_cache.py runtime/tests/test_vea5_m8r_cache_observability.py runtime/tests/test_diagnose_failures.py runtime/tests/test_verify_robustness.py -q`
- `python -m ruff check runtime/verify.py runtime/foundation/verification/` (or `py_compile`).
- Manual: delete `runtime/generated/verification-cache.json`, run `verify.py quick` twice (2nd =
  cache hit); touch a `runtime/` file, rerun → must be a miss (proves env_version).
- Manual: `rm -rf runtime/generated/evidence && python runtime/verify.py diagnose-failures` → exit 3.
- Re-run the red workflow with Phase 0 forensic + stderr-upload; confirm the traceback is captured.

## Open questions / risks
- Unknown root cause: Phase 0 may reveal a reconcile schema-drift or an executor/pytest hang —
  Phase 1 items 2-4 are the most likely to surface it; implementation must follow the evidence.
- `env_version` invalidates all existing CI caches once (one forced re-run).
- `fcntl` is Linux-only; confirm CI is Linux (it is). macOS dev falls back to no lock.
- reconcile pre-flight exit code (1) vs M5 contract (0/1/2): use 1 = artifact fault, distinct
  from environment-divergence (also 1) — acceptable since pre-flight runs BEFORE classify.
