# M9-C72 — Mutation CI: Evidence-First, Incremental Pipeline

**Goal:** CI green without re-running mutation campaigns, no wasted compute, enterprise-grade.
**Explicitly not:** deleting the workflow, lowering the 80% threshold, or re-running the 26-shard campaign to fix a plumbing bug.

---

## 0. Diagnosis — what is actually wrong

Everything below is measured, not estimated.

### 0.1 The 90-minute limit is not a constraint and never was

The campaign is **26 independent matrix jobs**, not one job:

```yaml
timeout-minutes: 90      # per shard job
strategy:
  fail-fast: false
  max-parallel: 7
```

| Measurement | Value |
|---|---|
| Slowest shard (local, mutmut only) | `ledger_audit_engine` 693 s = **11.5 min** |
| Slowest shard (CI, wall clock) | `behaviour_engine-01` **8 m 07 s** |
| Whole 26-shard campaign in CI | shards ran 03:46 → 04:00 = **~14 min** |
| Budget utilisation, worst shard | **12 % of 90 min** (8× headroom) |
| GitHub hosted limits, for reference | 6 h/job, 35 d/run — so 90 min is a self-imposed guard rail already 8× above the worst case |

**Conclusion:** changing `timeout-minutes` changes nothing. It is not the problem.

### 0.2 The campaign actually worked

From the dispatched run `36374920553`:

```
shard jobs: 26
  success: 26
  failure: 0

artifacts in run: 53
  mutation-shard-*:              26   (all present, expired=false, 90-day retention)
  mutation-coverage-evidence-*:  26
  mutation-aggregate-evidence:    1
```

Every shard measured and uploaded successfully. The **only** failing job is:

```
Mutation Aggregate Gate
  ✓ Download all shard evidence          FAILED
  - Reconcile shards and enforce gate    skipped
```

So **zero compute was wasted, and the failure is entirely in evidence transport.**

### 0.3 Confirmed defects

| # | Defect | Evidence | Severity |
|---|---|---|---|
| **D1** | Aggregate cannot download shard evidence | `Download all shard evidence` FAILED, yet all 26 artifacts exist and are readable | **BLOCKER** |
| **D2** | Exit code is dead code under `bash -e` | `mutation.yml:255-260` runs the gate then `RC=$?`. Under `bash -e` a non-zero exit kills the step, so `RC` is never assigned and `steps.aggregate.outputs.exit_code` stays empty. A below-threshold run (exit 2) would be reported as **"NOT EVALUABLE"** rather than "below threshold" — a gate lying about *why* it failed. | **HIGH** |
| **D3** | Shard timing instrumentation is dead | `measure_shard_budget()` reads `duration_seconds` from `freeze_baseline()["shards"]`, which never populates it. Every row of `shard-results.json` has `duration_seconds: null`, so no budget, throughput or pathological-shard detection works. C71 Phase 15 is therefore non-functional. | **HIGH** |
| **D4** | No provenance on shard verdicts | A summary records counts but not which commit, run, toolchain contract or source hash produced it. Cached or replayed evidence cannot be *proven* current, only assumed. | **HIGH** |
| **D5** | Full recompute every run | 26 shards re-measured regardless of what changed; 25/26 is redundant on a typical PR. | **STRUCTURAL** |
| **D6** | Artifact layout has collision surface | All 26 artifacts contain identically-named `mutmut-toolchain-contract.json` plus a `mutation-logs/` directory, flattened together by `merge-multiple: true`. | MEDIUM |
| **D7** | Shared download action passes `name` and `pattern` together | `download-runtime/action.yml:42-45` forwards both; the aggregate sets only `pattern`, so `name` arrives as `''`. They are documented as mutually exclusive. | MEDIUM |

### 0.4 D1 root cause — unconfirmed; three candidates

The job log was not retrievable through the CLI, so this plan does **not** assume a cause. Ranked by likelihood:

1. **D7** — empty `name` alongside a set `pattern` in the composite action.
2. **D6** — `merge-multiple: true` flattening 26 artifacts that share basenames.
3. Artifact-version or permission behaviour on `actions/download-artifact@v7.0.1`.

The WS-2 fix is designed to be **robust to all three**, and Phase 0 captures the real error so this is never guesswork again.

---

## 1. Architecture — evidence is a product, not a byproduct

The aggregate gate is a **pure function** of 26 shard summaries. Measurement and reconciliation have different costs and different failure modes, so they must not share a failure path.

```
                    ┌──────────────────────────────────────────┐
   MEASURE          │  per-shard job (N in parallel)           │   expensive
   (only what       │  verify mutation --shard <id>            │   2-12 min each
    changed)        │  emit ONE self-contained evidence file   │
                    └──────────────────┬───────────────────────┘
                                       │  mutation-evidence-<shard>.json
                                       │  versioned schema, content-hashed
                    ┌──────────────────▼───────────────────────┐
   RECONCILE        │  aggregate gate                          │   cheap
   (pure, re-runnable)  verify mutation-aggregate              │   <60 s
                    │  verify mutation-trust                   │
                    └──────────────────────────────────────────┘
```

**Governing rule:** reconciliation must be re-runnable at any time, from stored evidence, without re-measuring. That single property is what makes every optimisation below safe.

### Evidence contract (v2)

One file per shard. No shared basenames. No cross-file joins.

```jsonc
{
  "schema": "mutation-evidence/v2",
  "shard": "loan_engine-00",
  "component": "loan_engine",
  "tier": "large",
  "source_paths": ["src/engines/loan_engine/..."],
  "source_hash": "sha256:…",          // hash of this shard's source files
  "test_paths": ["tests/…"],
  "test_hash": "sha256:…",            // hash of the test selection
  "provenance": {
    "commit": "<sha>", "run_id": "…", "run_attempt": "1",
    "measured_at": "2026-09-28T…Z",
    "mutmut_version": "3.7.0",
    "toolchain_contract": "SATISFIED",
    "engine_selection_hash": "sha256:…"
  },
  "measurements": {
    "mutants_generated": 703, "killed": 565, "survived": 131,
    "not_checked": 0, "timeout": 0,
    "duration_seconds": 380, "mutants_per_second": 1.85
  },
  "execution_sentinel": { "armed": 703, "survivors_proven_executed": 131 }
}
```

**Validity rule (checked, not assumed):** evidence may be reused **iff** `source_hash`, `test_hash`, `mutmut_version`, `toolchain_contract` and `engine_selection_hash` all match current state. This is what makes caching *provable* rather than hopeful.

---

## 2. Workstreams

### WS-1 — Unblock CI from EXISTING evidence (no measurement)

**Goal:** green CI today, zero mutation compute, ~3 minutes.

Add replay capability to the aggregate gate:

```bash
# verify.py mutation-aggregate --evidence-run-id 36374920553
# downloads mutation-shard-* from a PRIOR run via the artifacts API, then
# reconciles. No shard job runs.
```

Workflow change — a `mode` input plus a `mutation-replay` job:

```yaml
workflow_dispatch:
  inputs:
    mode:            { default: measure, options: [measure, replay] }
    evidence_run_id: { default: "" }
```

`replay` downloads the 26 artifacts from `evidence_run_id` (defaulting to the most recent run carrying 26 shard artifacts), runs `mutation-aggregate` **and** `mutation-trust`, and enforces the same gates. Runtime ≈ 3 min; mutation cost **zero**.

This makes CI green immediately and proves the reconciliation path against real CI-produced evidence — the evidence the failed run already paid for.

**Acceptance:** `mode=replay, evidence_run_id=36374920553` → verdict `PASS`, score 80.1 %, exit 0.

### WS-2 — Fix the artifact transport (root cause)

1. **Eliminate merge entirely.** One artifact per shard containing one file (`mutation-evidence-<shard>.json`). No `merge-multiple`. Downloads use `name:` per shard into `evidence/<shard>/`. Removes D6 and the whole collision class. `collect_shard_summaries()` already rglobs recursively, so per-shard subdirectories already work.
2. **Make the download action input-safe.** Forward `name` **or** `pattern`, never both, never an empty `name` — fixes D7.
3. **Assert completeness before reconciling.** Count downloaded evidence files; if fewer than expected, fail with the missing shard list *and the download's own message*, so the gate reports the real cause. This closes the D1 blind spot that made the failure cost hours.
4. **Fix D2.** Use the `|| RC=$?` idiom and reserve exit codes distinctly: `0` satisfied · `2` evaluated but below threshold · `1` not evaluable (with named missing shards).
5. **Fix D3.** Populate `duration_seconds` in `freeze_baseline()` from each shard summary, so `measure_shard_budget()` and C71 Phase 15 actually work.

**Acceptance:** full `mode=measure` run green end-to-end; on failure the aggregate job shows the real download output.

### WS-3 — Incremental measurement (stop recomputing)

`mutation-plan` already emits `source_paths` per shard, so change detection needs no new data.

```bash
# verify.py mutation-plan --affected-from <base-sha>
# → matrix limited to shards whose source_paths intersect changed files
```

Algorithm:

1. `git diff --name-only <base>...HEAD` → changed files.
2. Map to shards via the plan's `source_paths`.
3. **Always include** any shard whose *test selection* changed — a new test can kill mutants in any shard, so test changes must not be scoped by source file.
4. Emit `affected` and `full` matrices plus a `cache_key` per shard.

PR behaviour: 0–2 shards instead of 26. Wall clock drops from ~15 min to ~2 min; compute from ~7 900 s to a few hundred seconds.

### WS-4 — Evidence reuse with provable validity

- `mutation-aggregate --cache-dir <dir>`: for shards not re-measured, load stored evidence **only if** its `source_hash` / `test_hash` / `toolchain_contract` / `engine_selection_hash` match current state.
- A stale entry is a **hard failure naming the shard and the mismatched field** — never a silent fallback to a default, which is precisely the C71 failure class.
- Extend `mutation-trust` to verify provenance, not just presence, so the C71 certification stays meaningful under caching.

### WS-5 — Tiered scheduling

| Tier | Trigger | Scope | Budget |
|---|---|---|---|
| **PR** | push / pull_request | affected shards + cache | ~2 min |
| **Nightly** | cron 02:00 | full 26 | ~15 min |
| **Release** | tag | full + `mutation-trust`, `UNKNOWN_SURVIVORS = 0` enforced | ~20 min |
| **Replay** | manual / gate recovery | reconcile stored evidence only | ~3 min |

### WS-6 — Budget from measurement, not guesswork

Once D3 is fixed, derive per-shard `timeout-minutes` from observed p95 plus margin rather than a flat 90. With current data (max 11.5 min) the guard rail lands near 20 min, so a genuinely pathological shard fails fast and visibly instead of occupying a slot for 90 minutes and reporting an ambiguous timeout.

---

## 3. Rollout

| Phase | Work | Cost | Gate to proceed |
|---|---|---|---|
| **0. Diagnose** | Dispatch `mode=measure` with the download step's own output surfaced | ~15 min, 1 run | Actual D1 error captured |
| **1. Unblock** | WS-1 replay job | ~3 min | CI green, 80.1 %, `mutation-trust` all-true |
| **2. Repair** | WS-2 (evidence v2, action inputs, exit codes, timings) | ~20 min | Full `mode=measure` run green end-to-end |
| **3. Incremental** | WS-3 + WS-4 | ~30 min | PR run measures ≤2 shards and still gates correctly |
| **4. Harden** | WS-5 + WS-6 | ~15 min | Nightly full run green; timeout derived from data |

Phases 1–2 are the critical path and can land in one PR. Phases 3–4 are independent and revertible.

---

## 4. Verification

| Check | Command | Expected |
|---|---|---|
| Replay green | `verify.py mutation-aggregate --evidence-run-id 36374920553` | exit 0, 80.1 %, 26/26 shards |
| Trust holds | `verify.py mutation-trust` | `MEASUREMENT_VALID` / `DISPATCH_VALID` / `EXECUTION_PROVEN` true, `UNKNOWN_SURVIVORS = 0` |
| Threshold untouched | config diff | 80, zero diff vs HEAD |
| Full campaign | `mode=measure` | all 26 shards, verdict PASS |
| Incremental correctness | PR touching 1 engine | ≤2 shards run; gate verdict identical to full run |
| Cache validity | tamper a stored `source_hash` | hard failure naming shard + field, never silent |
| Timing telemetry | inspect `shard-results.json` | `duration_seconds` non-null for all shards |

**Regression guards to add:** (a) the evidence schema validates; (b) a cache hit is accepted only on exact hash match; (c) exit code 2 is reported as *below threshold*, not *not evaluable*; (d) the download action never passes `name` and `pattern` together.

---

## 5. Risks

| Risk | Mitigation |
|---|---|
| Artifact retention expires (90 d) | Evidence v2 is small; commit it under `runtime/generated/mutation/registry/` so replay never depends on retention |
| Cached evidence is stale | Validity is hash-checked, not assumed; mismatch is a hard failure naming shard and field |
| Incremental mode misses a kill | Test-selection changes force re-measurement; the nightly full run is the backstop |
| D1 cause differs from the three candidates | Phase 0 captures the real error; WS-2 removes all three by construction |
| Replay could mask a regression | Replay is valid only for a declared `evidence_run_id` with recorded provenance, and is never the PR gate |

---

## 6. Why this is the right shape

The campaign is not too slow — 12 % budget utilisation, 26/26 green. The system fails in *evidence transport*, and the current design forces a full re-measurement to recover from a transport fault, which is why a 3-minute bug costs 15 minutes of compute plus an unbounded debugging session.

The fix is not to delete the gate. It is to make **measurement** and **reconciliation** independent concerns, so recovery from a transport fault costs a re-download rather than a re-measurement — and so the gate can never again fail for a reason it does not report.
