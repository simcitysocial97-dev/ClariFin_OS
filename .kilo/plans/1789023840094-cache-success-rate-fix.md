# M9-C58: Cache Hit Rate & Verification Success Rate Fix

**Date:** 2026-09-10  
**Status:** Implementation Plan  
**Scope:** Runtime verification framework — cache wiring and analytics accuracy

---

## Problem Statement

The engineering health report flags two persistent recommendations:
- `Local: Verification success rate below 95%`
- `Local: Cache hit rate below 50%`

Both are caused by missing production wiring, not by actual verification failures.

### Root Cause 1: Cache Never Checked (hit_rate = 0%)

`runtime/foundation/verification/cache.py` implements a fully tested `VerificationCache` class with content-aware invalidation (R-CACHE-1). However, `runtime/foundation/verification/control_plane_facade.py:1001` (`_run_profile_alias`) never calls `cache.replay()` before executing tasks, and never calls `cache.save()` after execution. Every profile run is a cold miss by design.

**Evidence:** All 17,644 entries in `engineering-history.json` have `"cache_hit": false`. The event store has 4 entries, 0 with `cache_hit: true`.

### Root Cause 2: Analytics Count Non-Execution Events (success_rate = 0%)

`runtime/platform/api/services/verification_write.py:94-111` emits `VerificationCompleted` events with `status="unknown"` and `executed=false` for plan-only runs. The analytics engine (`analytics.py:156-170`) counts these in `total_runs` but they match neither `"passed"` nor `"failed"`, making `outcome_denominator = 0` and `success_rate = 0.0`.

Additionally, the analytics engine reads exclusively from `engineering-events.jsonl` (4 entries, all plan-only), while the rich historical run data lives in `engineering-history.json` (17,644 entries) — a file the analytics engine ignores.

---

## Design Decisions

### D1: Cache Key Strategy

**Decision:** Use `(commit_sha, sorted_changed_files, profile_name)` as the cache key, augmented with content hash of changed files (already implemented in `_compute_tree_digest`).

**Rationale:** This matches the existing `VerificationCache.is_valid()` contract and the R-CACHE-1 content-aware invalidation already in place. No changes needed to the cache key scheme.

### D2: Cache Location

**Decision:** Store cache at `runtime/generated/verification-cache.json` (same path used by `workspace.py:232`).

**Rationale:** Consistent with existing workspace cache loading. The path is already known to the workspace layer.

### D3: Analytics Filtering

**Decision:** Exclude events where `executed=false` from success rate calculation. These are plan-only events that never ran verification.

**Rationale:** A plan-only event is not a verification outcome — it's an architectural decision record. Counting it as a non-pass/non-fail run artificially deflates the success rate to 0%.

### D4: Legacy History Migration

**Decision:** Add a one-time migration that imports `engineering-history.json` entries into the event store, filtering to only executed runs. After migration, the analytics engine will have full historical context.

**Rationale:** The 17,644-entry history contains real verification runs with accurate outcomes. Losing this data would set the trend analysis back to zero. Migrating it gives the analytics engine proper baseline data.

---

## Implementation Tasks

### Task 1: Wire Cache Replay into Profile Execution

**File:** `runtime/foundation/verification/control_plane_facade.py`  
**Function:** `_run_profile_alias` (line 1001)

Before the task execution loop (line 1036), add:
1. Resolve current commit SHA via `_get_current_commit()`
2. Discover changed files via `_collect_changed_files_result()`
3. Load cache from `runtime/generated/verification-cache.json`
4. Call `cache.replay(commit, changed_files, operation)`
5. If `result.reusable`:
   - Print `[profile:{op}] cache hit — replaying {result.overall_status}`
   - Record event with `cache_hit=True`, `status=result.overall_status`
   - Return `result.exit_code`
6. If not reusable: proceed with normal execution

After successful execution (line 1123, before the final `_record_verification_event`):
1. Build `CachedVerdict` from `passed`/`failed`/`skipped` counts
2. Call `cache.save(profile=operation, commit=..., changed_files=..., verdict=...)`

**Test:** Add `test_profile_cache_replay` and `test_profile_cache_save` to `runtime/tests/test_m9_c50_operational_validation.py`.

---

### Task 2: Filter Non-Execution Events from Analytics

**File:** `runtime/system/observability/analytics.py`  
**Function:** `_compute_verification_metrics` (line 148)

Add filter: exclude records where `cache_hit=False` AND `evidence_count==0` AND `duration_seconds==0` — these are plan-only stubs. Alternatively, add explicit `executed` field check if propagated.

Better approach: In `_extract_run_records` (line 117), skip records where the payload indicates `executed=false` (plan-only). These should not contribute to any metric.

Also in `_compute_cache_metrics` (line 221): same filter applied.

**Test:** Add test verifying that plan-only events are excluded from metrics.

---

### Task 3: Migrate Legacy History to Event Store

**File:** New — `runtime/foundation/verification/history_migration.py`

One-shot migration script:
1. Read `runtime/generated/engineering-history.json`
2. For each entry with `status` in `("passed", "failed")`:
   - Create `EngineeringEvent` with `event_type="VerificationCompleted"`
   - Map fields: `run_id→event_id`, `timestamp→timestamp`, `profile→payload.profile`, etc.
   - Set `cache_hit` from entry (all false in legacy data)
   - Set `execution_context.environment="local"`, `source="legacy-history"`
3. Append to `engineering-events.jsonl`
4. Write migration manifest to `runtime/generated/migration-history-to-events.json`

**Guard:** Skip if event store already has >100 entries (idempotency check).

**Test:** `test_history_migration_imports_executed_runs` in new test file.

---

### Task 4: Regenerate Analytics After Migration

**File:** Call `generate_analytics()` after migration completes.

This ensures `engineering-analytics.json` reflects the migrated data.

---

### Task 5: Add Cache Health to Engineering Health Report

**File:** `runtime/system/observability/health_report.py`

Add a cache-specific section that reports:
- Total cache lookups (from events with `cache_hit` field)
- Hit vs miss counts
- Stale cache entries (entries where tree_digest doesn't match current working tree)

This gives operators visibility into whether caching is actually helping.

---

## Validation Plan

| # | Test | Location | Expected Result |
|---|------|----------|-----------------|
| 1 | `test_profile_cache_replay_pass` | `test_m9_c50_operational_validation.py` | Second identical run returns cached PASS without executing tasks |
| 2 | `test_profile_cache_replay_fail` | same | Cached FAIL replay returns exit_code=1, cache_hit=True |
| 3 | `test_profile_cache_invalidated_on_change` | same | Changing a source file invalidates cache, forces re-execution |
| 4 | `test_plan_only_events_excluded_from_metrics` | `test_analytics_filtering.py` (new) | Events with executed=false don't affect success_rate |
| 5 | `test_history_migration_idempotent` | `test_history_migration.py` (new) | Running migration twice doesn't duplicate events |
| 6 | `test_health_report_no_false_recommendations` | `test_health_report.py` | After fix, no "success rate below 95%" recommendation for clean repo |
| 7 | Full suite | `pytest runtime/tests/ -q --timeout=120` | All existing tests still pass |

---

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `runtime/foundation/verification/control_plane_facade.py` | Modify | Add cache replay + save in `_run_profile_alias` |
| `runtime/system/observability/analytics.py` | Modify | Filter non-execution events from metrics |
| `runtime/system/observability/health_report.py` | Modify | Add cache health section |
| `runtime/foundation/verification/history_migration.py` | Create | Legacy history → event store migration |
| `runtime/tests/test_m9_c50_operational_validation.py` | Modify | Add cache replay tests |
| `runtime/tests/test_analytics_filtering.py` | Create | New: analytics filtering tests |
| `runtime/tests/test_history_migration.py` | Create | New: migration tests |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Cache replay returns stale PASS for a broken repo | Cache already uses content-aware invalidation (R-CACHE-1). tree_digest mismatch forces re-execution. |
| Migration duplicates events on re-run | Idempotency guard: skip if event store has >100 entries. Also use unique event_ids from legacy runs. |
| Filtering plan-only events hides real failures | Plan-only events have `executed=false` AND `duration_seconds=0`. Real failures have `duration>0`. Dual-check prevents over-filtering. |
| Cache file grows unbounded | Existing `evidence_retention.py` cleanup already handles old cache entries. No new cleanup needed. |

---

## Out of Scope

- CI cache distribution (multi-runner cache sync) — future Phase
- Cross-commit cache sharing — not needed for single-developer local workflow
- Cache compression / deduplication — not a current bottleneck
- Real-time cache warming — over-engineered for current scale

---

## Success Criteria

1. `verify inspect health` shows cache hit rate ≥ 50% after 2+ identical runs
2. `verify inspect health` shows verification success rate ≥ 95% (based on actual executed runs)
3. No regression in existing test suite
4. Migration is idempotent and reversible
