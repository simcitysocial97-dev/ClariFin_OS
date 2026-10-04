"""M10-R2 — deterministic runtime-test sharding, and the shard gate.

The runtime suite is ~26 minutes of serial pytest and is therefore the longest single
obligation in the repository: until it is sharded, the Runtime Verification critical
path *is* that suite. These tests pin the properties that make sharding safe rather
than merely fast:

* the partition is deterministic and covers every test file **exactly once**;
* it is balanced by a real cost proxy, not by file count;
* the gate refuses to certify on a missing shard, a duplicate shard, an unknown shard,
  or any failing shard — so "the aggregate job succeeded" can never be mistaken for
  "every shard succeeded";
* the shard executor targets whole files, so module fixtures never straddle processes.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.foundation.verification.runtime_shards import (
    DEFAULT_SHARD_COUNT,
    ShardResult,
    build_test_shards,
    expected_shard_ids,
    read_shard_results,
    runtime_test_files,
    shard_matrix,
    verify_shards,
)

FILES = [
    "runtime/tests/test_a.py",
    "runtime/tests/test_b.py",
    "runtime/tests/test_c.py",
    "runtime/tests/test_d.py",
    "runtime/tests/test_e.py",
]
COUNTS = {
    "runtime/tests/test_a.py": 100,
    "runtime/tests/test_b.py": 1,
    "runtime/tests/test_c.py": 1,
    "runtime/tests/test_d.py": 1,
    "runtime/tests/test_e.py": 1,
}


def _ok(shard_id: str) -> ShardResult:
    return ShardResult(
        shard_id=shard_id,
        status="passed",
        exit_code=0,
        duration_seconds=1.0,
        file_count=1,
        passed=10,
    )


# ---------------------------------------------------------------------------
# Partition
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("count", [1, 2, 3, 4, 5, 8])
def test_partition_covers_every_file_exactly_once(count):
    plan = build_test_shards(FILES, count, COUNTS)
    assert plan.all_files() == set(FILES)
    assert sum(len(s) for s in plan.shards) == len(FILES)


@pytest.mark.parametrize("count", [2, 3, 4, 5])
def test_partition_is_deterministic(count):
    a = build_test_shards(FILES, count, COUNTS)
    b = build_test_shards(list(reversed(FILES)), count, COUNTS)
    assert a.shards == b.shards


def test_no_shard_is_empty_for_a_sane_shard_count():
    """An empty matrix leg is a runner that runs nothing. With more shards than files
    the partition must still place every file somewhere, and the matrix renderer drops
    empty legs rather than emitting them."""
    for count in (1, 2, 5):
        plan = build_test_shards(FILES, count, COUNTS)
        assert all(len(s) > 0 for s in plan.shards), count


def test_shards_are_balanced_by_a_cost_proxy_not_file_count():
    """The heavy file must not share a shard with the light ones.

    Balance here is bounded below by the heaviest single file — it cannot be split — so
    the property worth asserting is that LPT reaches that floor rather than the
    unreachable ``sum/N``. Splitting [100] | [1,1,1,1] is optimal; [100,1,1,1] | [1] is
    what a naive round-robin would produce.
    """
    plan = build_test_shards(FILES, 2, COUNTS)
    loads = [sum(COUNTS[f] for f in s) for s in plan.shards]
    heaviest = max(COUNTS.values())
    # Reached the indivisibility floor.
    assert max(loads) == heaviest, loads
    # And the heavy file really is alone on its shard.
    heavy_shard = next(s for s in plan.shards if "runtime/tests/test_a.py" in s)
    assert len(heavy_shard) == 1


def test_balance_improves_as_the_heavy_file_stops_dominating():
    """With evenly weighted files, LPT must actually balance."""
    even = dict.fromkeys(FILES, 10)
    plan = build_test_shards(FILES, 5, even)
    loads = [sum(even[f] for f in s) for s in plan.shards]
    assert max(loads) == min(loads), loads


def test_excluded_files_are_never_silently_dropped():
    """An omitted file must be a recorded decision, not a gap."""
    plan = build_test_shards(
        FILES, 2, COUNTS, excluded={"runtime/tests/test_b.py": "known unsafe"}
    )
    assert "runtime/tests/test_b.py" not in plan.all_files()
    assert plan.excluded == {"runtime/tests/test_b.py": "known unsafe"}
    assert sum(len(s) for s in plan.shards) == len(FILES) - 1


def test_weight_falls_back_to_one_without_counts():
    """Balance degrades; coverage must not."""
    plan = build_test_shards(FILES, 2, None)
    assert plan.all_files() == set(FILES)


def test_shard_id_is_stable_and_indexed():
    plan = build_test_shards(FILES, 3, COUNTS)
    assert plan.shard_id(0) == "runtime-tests-shard-0"
    assert expected_shard_ids(3) == [
        "runtime-tests-shard-0",
        "runtime-tests-shard-1",
        "runtime-tests-shard-2",
    ]


# ---------------------------------------------------------------------------
# Real suite
# ---------------------------------------------------------------------------


def test_real_suite_partitions_completely_and_deterministically():
    files = runtime_test_files()
    assert files == sorted(files), "file list must be sorted for reproducibility"
    assert len(files) > 100, "expected the full runtime suite"
    plan = build_test_shards(files, DEFAULT_SHARD_COUNT)
    assert plan.all_files() == set(files)
    assert sum(len(s) for s in plan.shards) == len(files)
    again = build_test_shards(runtime_test_files(), DEFAULT_SHARD_COUNT)
    assert plan.shards == again.shards


def test_real_suite_matrix_document_is_actionable():
    document = json.loads(shard_matrix(build_test_shards(runtime_test_files(), 4)))
    assert document["shard_count"] == 4
    assert document["file_count"] == len(runtime_test_files())
    assert 1 < document["estimated_speedup"] <= 4
    for leg in document["include"]:
        assert leg["shard_id"].startswith("runtime-tests-shard-")
        assert leg["file_count"] > 0


# ---------------------------------------------------------------------------
# Matrix rendering
# ---------------------------------------------------------------------------


def test_matrix_never_emits_an_empty_leg():
    """More shards requested than files exist: empty legs are dropped, not emitted."""
    plan = build_test_shards(FILES, 8, COUNTS)
    document = json.loads(shard_matrix(plan))
    assert all(leg["file_count"] > 0 for leg in document["include"])
    assert document["shard_count"] < 8


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------


def test_all_shards_passing_certifies():
    results = [_ok(s) for s in expected_shard_ids(4)]
    assert verify_shards(4, results) == []


def test_a_missing_shard_blocks_certification():
    results = [_ok(expected_shard_ids(4)[0])]
    problems = verify_shards(4, results)
    assert problems
    assert "missing" in problems[0]
    assert expected_shard_ids(4)[3] in problems[0]


def test_a_failing_shard_blocks_certification():
    results = [_ok(s) for s in expected_shard_ids(4)]
    results[2] = ShardResult(
        shard_id=expected_shard_ids(4)[2],
        status="failed",
        exit_code=1,
        duration_seconds=1.0,
        passed=5,
        failed=2,
    )
    problems = verify_shards(4, results)
    assert problems
    assert "failed" in problems[0]


def test_a_timed_out_shard_blocks_certification():
    results = [_ok(s) for s in expected_shard_ids(3)]
    results[1] = ShardResult(
        shard_id=expected_shard_ids(3)[1],
        status="timed_out",
        exit_code=124,
        duration_seconds=1.0,
    )
    assert verify_shards(3, results)


def test_a_duplicate_shard_blocks_certification():
    """Two legs claiming the same shard means either double execution or a plan
    mismatch. Both are certification problems."""
    results = [_ok(expected_shard_ids(2)[0])] * 2
    problems = verify_shards(2, results)
    assert any("more than one leg" in p for p in problems)


def test_an_unknown_shard_blocks_certification():
    results = [_ok(s) for s in expected_shard_ids(2)] + [_ok("runtime-tests-shard-99")]
    problems = verify_shards(2, results)
    assert any("unknown shard" in p for p in problems)


def test_a_failed_integrity_obligation_blocks_certification():
    """The integrity scan is a separate canonical obligation. A green suite must not
    be able to mask a red integrity scan."""
    results = [_ok(s) for s in expected_shard_ids(2)]
    assert verify_shards(2, results, integrity_ok=True) == []
    assert verify_shards(2, results, integrity_ok=False)
    # Not run is not failed: the caller decides whether to report it.
    assert verify_shards(2, results, integrity_ok=None) == []


def test_no_results_at_all_blocks_certification():
    assert verify_shards(3, [])


# ---------------------------------------------------------------------------
# Result I/O
# ---------------------------------------------------------------------------


def test_unreadable_results_are_reported_not_skipped(tmp_path):
    """A leg that died mid-flight leaves no result. That must surface as an unreadable
    entry, because silently skipping it is indistinguishable from success."""
    (tmp_path / "shard-0.json").write_text("{ truncated", encoding="utf-8")
    (tmp_path / "shard-1.json").write_text(
        json.dumps(_ok("runtime-tests-shard-1").to_dict()), encoding="utf-8"
    )
    results, absent, malformed, rejected = read_shard_results(tmp_path)
    assert len(results) == 1
    assert absent == []
    assert len(malformed) == 1
    assert "shard-0.json" in malformed[0]
    assert rejected == []


def test_results_round_trip(tmp_path):
    shard = ShardResult(
        shard_id="runtime-tests-shard-0",
        status="passed",
        exit_code=0,
        duration_seconds=12.5,
        file_count=40,
        passed=647,
        failed=0,
    )
    (tmp_path / "shard-0.json").write_text(
        json.dumps(shard.to_dict()), encoding="utf-8"
    )
    results, absent, malformed, rejected = read_shard_results(tmp_path)
    assert absent == [] and malformed == [] and rejected == []
    assert results[0] == shard
    assert results[0].ok is True


def test_a_shard_count_below_one_is_rejected():
    with pytest.raises(ValueError):
        build_test_shards(FILES, 0)


# ---------------------------------------------------------------------------
# Shard execution boundary
# ---------------------------------------------------------------------------


def test_shards_are_whole_files():
    """Never split mid-module: module fixtures and module-level state must stay inside
    one process. Shards are therefore sets of complete file paths."""
    plan = build_test_shards(FILES, 3, COUNTS)
    for shard in plan.shards:
        for path in shard:
            assert path in FILES
            assert "::" not in path, "a shard targets files, not individual tests"


def test_shard_execution_uses_serial_pytest_not_xdist():
    """Regression against the xdist pilot: a shard already owns a dedicated runner, so
    forking workers inside it re-creates the contention that disqualified ``-n``."""
    from runtime.foundation.verification import runtime_shards as module

    source = Path(module.__file__).read_text(encoding="utf-8")
    runner = source.split("def run_test_shard(")[1]
    assert '"-n"' not in runner
    assert "numprocesses" not in runner
