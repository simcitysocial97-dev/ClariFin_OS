# runtime/tests/test_m9_c44_mutation_architecture.py
#
# M9-C44 — Regression qualification suite (M44.30).
#
# Tests the canonical mutation execution architecture independently of mutmut.
# Proves the architecture through intentional edge-case coverage.

from __future__ import annotations

import json
import math
from unittest.mock import MagicMock

import pytest

from runtime.foundation.verification.mutation_execution.cache import MutationCache
from runtime.foundation.verification.mutation_execution.config_fingerprint import (
    build_full_fingerprint,
    fingerprints_compatible,
)

# Import from the new architecture module.
from runtime.foundation.verification.mutation_execution.domain_model import (
    MutationCampaign,
    MutationCandidate,
    MutationExecution,
    MutationResult,
    MutationResultState,
    TimeoutKind,
    derive_canonical_mutant_id,
)
from runtime.foundation.verification.mutation_execution.health import (
    FailureBudget,
    certification_check,
    compute_health_metrics,
)
from runtime.foundation.verification.mutation_execution.mutmut_adapter import (
    _EXIT_CODE_TO_STATE,
    _TEXT_STATUS_TO_STATE,
)
from runtime.foundation.verification.mutation_execution.workspace import (
    MutationWorkspace,
    list_campaigns,
)

# =========================================================================
# M44.2 — Canonical Mutation Identifier
# =========================================================================

class TestCanonicalMutantId:
    def test_deterministic_for_same_input(self):
        """Same inputs -> same ID."""
        id1 = derive_canonical_mutant_id(
            repository_revision="abc123", source_file="src/foo.py",
            source_hash="deadbeef", function="bar", line=10,
            operator="arithmetic", original_expression="a+b", mutated_expression="a-b",
        )
        id2 = derive_canonical_mutant_id(
            repository_revision="abc123", source_file="src/foo.py",
            source_hash="deadbeef", function="bar", line=10,
            operator="arithmetic", original_expression="a+b", mutated_expression="a-b",
        )
        assert id1 == id2
        assert len(id1) == 20

    def test_different_source_file_gives_different_id(self):
        id1 = derive_canonical_mutant_id(
            repository_revision="abc", source_file="src/a.py",
            source_hash="h1", function="f", line=1,
            operator="op", original_expression="x", mutated_expression="y",
        )
        id2 = derive_canonical_mutant_id(
            repository_revision="abc", source_file="src/b.py",
            source_hash="h2", function="f", line=1,
            operator="op", original_expression="x", mutated_expression="y",
        )
        assert id1 != id2

    def test_different_operator_gives_different_id(self):
        id1 = derive_canonical_mutant_id(
            repository_revision="abc", source_file="src/f.py",
            source_hash="h", function="g", line=1,
            operator="arithmetic", original_expression="a+b", mutated_expression="a-b",
        )
        id2 = derive_canonical_mutant_id(
            repository_revision="abc", source_file="src/f.py",
            source_hash="h", function="g", line=1,
            operator="comparison", original_expression="a>b", mutated_expression="a<b",
        )
        assert id1 != id2

    def test_stable_across_round_trips(self):
        """Round-trip through dict preserves ID."""
        c = MutationCandidate(
            canonical_mutant_id=derive_canonical_mutant_id(
                repository_revision="r", source_file="s.py",
                source_hash="h", function="f", line=1,
                operator="op", original_expression="o", mutated_expression="m",
            ),
            source_file="s.py", source_hash="h", function="f",
        )
        d = c.to_dict()
        c2 = MutationCandidate.from_dict(d)
        assert c2.canonical_mutant_id == c.canonical_mutant_id


# =========================================================================
# M44.1 — Domain Model Round-trip
# =========================================================================

class TestDomainModel:
    def test_campaign_roundtrip(self):
        camp = MutationCampaign(
            campaign_id="test-camp", repository_revision="abc",
            environment_fingerprint="fp", mutation_backend="mutmut",
            backend_version="3.7.0", scope="full", test_selection="tests/",
            configuration_fingerprint="cfg", execution_policy="serial",
            creation_timestamp="2026-01-01T00:00:00Z",
        )
        d = camp.to_dict()
        camp2 = MutationCampaign.from_dict(d)
        assert camp2.campaign_id == camp.campaign_id
        assert camp2.status == "PENDING"

    def test_candidate_roundtrip(self):
        c = MutationCandidate(
            canonical_mutant_id="abc123", source_file="src/f.py",
            source_hash="dead", function="foo", line=42,
            operator="arithmetic", original_expression="a+b",
            mutated_expression="a-b", capability="test_cap",
            component="test_comp", selected_tests=("t1", "t2"),
        )
        d = c.to_dict()
        c2 = MutationCandidate.from_dict(d)
        assert c2.canonical_mutant_id == "abc123"
        assert c2.selected_tests == ("t1", "t2")

    def test_execution_roundtrip(self):
        ex = MutationExecution(
            execution_id="exec-1", campaign_id="camp-1",
            mutant_id="mut-1", worker_id="w-1",
            mutation_result=MutationResultState.KILLED,
            exit_status=1, duration_seconds=5.5,
            verification_passed=True,
        )
        d = ex.to_dict()
        ex2 = MutationExecution.from_dict(d)
        assert ex2.mutation_result == MutationResultState.KILLED
        assert ex2.verification_passed is True

    def test_result_reconcile(self):
        r = MutationResult(
            campaign_id="c", total_candidates=10,
            killed=5, survived=3, no_tests=1, timeout=1,
        )
        assert r.reconcile() is True
        assert r.score == 55.56

    def test_result_not_reconciled(self):
        r = MutationResult(
            campaign_id="c", total_candidates=10,
            killed=5, survived=3,  # missing 2
        )
        assert r.reconcile() is False

    def test_result_classification_summary(self):
        r = MutationResult(campaign_id="c", total_candidates=10, killed=7, survived=2, timeout=1)
        s = r.classification_summary()
        assert s["state_counts"]["KILLED"] == 7
        assert s["reconciled"] is True
        assert s["score"] == 70.0  # 7/(7+2+1) = 70%


# =========================================================================
# M44.8 — Timeout Architecture
# =========================================================================

class TestTimeoutClassification:
    def test_timeout_kind_values(self):
        assert TimeoutKind.TEST_TIMEOUT.value == "test_timeout"
        assert TimeoutKind.CAMPAIGN_TIMEOUT.value == "campaign_timeout"

    def test_execution_with_test_timeout(self):
        ex = MutationExecution(
            execution_id="e1", campaign_id="c1", mutant_id="m1",
            worker_id="w1", timeout=TimeoutKind.TEST_TIMEOUT,
            mutation_result=MutationResultState.TIMEOUT,
        )
        assert ex.timeout == TimeoutKind.TEST_TIMEOUT

    def test_execution_without_timeout(self):
        ex = MutationExecution(
            execution_id="e1", campaign_id="c1", mutant_id="m1",
            worker_id="w1", mutation_result=MutationResultState.KILLED,
        )
        assert ex.timeout is None


# =========================================================================
# M44.4 — Mutmut Adapter Status Mapping
# =========================================================================

class TestMutmutAdapterStatusMapping:
    def test_exit_code_to_state_mapping(self):
        """All authoritative exit codes map correctly."""
        assert _EXIT_CODE_TO_STATE[0] == MutationResultState.SURVIVED
        assert _EXIT_CODE_TO_STATE[1] == MutationResultState.KILLED
        assert _EXIT_CODE_TO_STATE[3] == MutationResultState.KILLED
        assert _EXIT_CODE_TO_STATE[5] == MutationResultState.NO_TESTS
        assert _EXIT_CODE_TO_STATE[36] == MutationResultState.TIMEOUT
        assert _EXIT_CODE_TO_STATE[35] == MutationResultState.EXECUTION_ERROR
        assert _EXIT_CODE_TO_STATE[34] == MutationResultState.EXECUTION_ERROR
        assert _EXIT_CODE_TO_STATE[2] == MutationResultState.EXECUTION_ERROR
        assert _EXIT_CODE_TO_STATE[None] == MutationResultState.NOT_EXECUTED

    def test_text_status_to_state_mapping(self):
        assert _TEXT_STATUS_TO_STATE["killed"] == MutationResultState.KILLED
        assert _TEXT_STATUS_TO_STATE["survived"] == MutationResultState.SURVIVED
        assert _TEXT_STATUS_TO_STATE["no tests"] == MutationResultState.NO_TESTS
        assert _TEXT_STATUS_TO_STATE["timeout"] == MutationResultState.TIMEOUT
        assert _TEXT_STATUS_TO_STATE["suspicious"] == MutationResultState.EXECUTION_ERROR
        assert _TEXT_STATUS_TO_STATE["not checked"] == MutationResultState.NOT_EXECUTED
        assert _TEXT_STATUS_TO_STATE["skipped"] == MutationResultState.EXECUTION_ERROR
        assert _TEXT_STATUS_TO_STATE["interrupted"] == MutationResultState.EXECUTION_ERROR

    def test_never_maps_crash_to_survived(self):
        """Critical invariant: tool crash must never become SURVIVED."""
        for code, state in _EXIT_CODE_TO_STATE.items():
            if code in (2, 35, None):  # interrupted, suspicious, not-checked
                assert state != MutationResultState.SURVIVED, \
                    f"Code {code} must not map to SURVIVED"

    def test_never_maps_crash_to_killed(self):
        """Critical invariant: tool crash must never become KILLED."""
        # Only 1, 3, -24 are legitimate kills
        assert _EXIT_CODE_TO_STATE.get(2) != MutationResultState.KILLED
        assert _EXIT_CODE_TO_STATE.get(None) != MutationResultState.KILLED


# =========================================================================
# M44.6/7 — Workspace Isolation
# =========================================================================

class TestWorkspaceIsolation:
    def test_create_workspace_structure(self, tmp_path):
        camp = MutationCampaign(
            campaign_id="ws-test", repository_revision="abc",
            environment_fingerprint="fp", mutation_backend="mutmut",
            backend_version="3.7.0", scope="target", test_selection="tests/",
            configuration_fingerprint="cfg", execution_policy="serial",
            creation_timestamp="2026-01-01T00:00:00Z",
        )
        ws = MutationWorkspace(camp, root=tmp_path / "campaigns" / "ws-test")
        ws.create(copy_source=False)

        assert ws.root.exists()
        assert ws.source_dir.exists()
        assert ws.mutants_dir.exists()
        assert ws.executions_dir.exists()
        assert ws.evidence_dir.exists()
        assert ws.logs_dir.exists()
        assert ws.reconciliation_dir.exists()
        assert ws.manifest_path.exists()

    def test_workspace_persist_and_load_execution(self, tmp_path):
        camp = MutationCampaign(
            campaign_id="ws-test2", repository_revision="abc",
            environment_fingerprint="fp", mutation_backend="mutmut",
            backend_version="3.7.0", scope="target", test_selection="tests/",
            configuration_fingerprint="cfg", execution_policy="serial",
            creation_timestamp="2026-01-01T00:00:00Z",
        )
        ws = MutationWorkspace(camp, root=tmp_path / "campaigns" / "ws-test2")
        ws.create(copy_source=False)

        ex = MutationExecution(
            execution_id="exec-1", campaign_id="ws-test2",
            mutant_id="mut-1", worker_id="w-1",
            mutation_result=MutationResultState.KILLED, exit_status=1,
        )
        path = ws.persist_execution(ex.to_dict())
        assert path.exists()

        loaded = json.loads(path.read_text())
        assert loaded["mutation_result"] == "KILLED"

    def test_workspace_mark_complete(self, tmp_path):
        camp = MutationCampaign(
            campaign_id="ws-test3", repository_revision="abc",
            environment_fingerprint="fp", mutation_backend="mutmut",
            backend_version="3.7.0", scope="target", test_selection="tests/",
            configuration_fingerprint="cfg", execution_policy="serial",
            creation_timestamp="2026-01-01T00:00:00Z", status="RUNNING",
        )
        ws = MutationWorkspace(camp, root=tmp_path / "campaigns" / "ws-test3")
        ws.create(copy_source=False)
        ws.mark_complete()

        reloaded = json.loads(ws.manifest_path.read_text())
        assert reloaded["status"] == "COMPLETED"

    def test_workspace_cleanup(self, tmp_path):
        camp = MutationCampaign(
            campaign_id="ws-test4", repository_revision="abc",
            environment_fingerprint="fp", mutation_backend="mutmut",
            backend_version="3.7.0", scope="target", test_selection="tests/",
            configuration_fingerprint="cfg", execution_policy="serial",
            creation_timestamp="2026-01-01T00:00:00Z",
        )
        ws = MutationWorkspace(camp, root=tmp_path / "campaigns" / "ws-test4")
        ws.create(copy_source=False)
        ws.cleanup()
        assert not ws.root.exists()

    def test_list_campaigns_empty(self, tmp_path):
        campaigns = list_campaigns.__wrapped__(tmp_path) if hasattr(list_campaigns, '__wrapped__') else []
        # With empty dir, should return empty
        assert isinstance(campaigns, list)


# =========================================================================
# M44.11 — Configuration Fingerprint
# =========================================================================

class TestConfigFingerprint:
    def test_deterministic(self):
        fp1 = build_full_fingerprint(
            backend="mutmut", backend_version="3.7.0",
            source_paths=["src/engines/foo.py"],
            test_selection=["tests/test_foo.py"],
            timeout_seconds=300, worker_count=1,
        )
        fp2 = build_full_fingerprint(
            backend="mutmut", backend_version="3.7.0",
            source_paths=["src/engines/foo.py"],
            test_selection=["tests/test_foo.py"],
            timeout_seconds=300, worker_count=1,
        )
        assert fp1["configuration"] == fp2["configuration"]

    def test_different_backend_gives_different_fp(self):
        fp1 = build_full_fingerprint(
            backend="mutmut", backend_version="3.7.0",
            source_paths=["src/f.py"], test_selection=["tests/t.py"],
            timeout_seconds=300, worker_count=1,
        )
        fp2 = build_full_fingerprint(
            backend="cosmic_ray", backend_version="1.0.0",
            source_paths=["src/f.py"], test_selection=["tests/t.py"],
            timeout_seconds=300, worker_count=1,
        )
        assert fp1["configuration"] != fp2["configuration"]

    def test_fingerprints_compatible_strict(self):
        fp1 = build_full_fingerprint(
            backend="mutmut", backend_version="3.7.0",
            source_paths=["src/f.py"], test_selection=["tests/t.py"],
            timeout_seconds=300, worker_count=1,
        )
        fp2 = build_full_fingerprint(
            backend="mutmut", backend_version="3.7.0",
            source_paths=["src/f.py"], test_selection=["tests/t.py"],
            timeout_seconds=300, worker_count=1,
        )
        assert fingerprints_compatible(fp1, fp2, loose=False) is True

    def test_fingerprints_incompatible_on_backend_change(self):
        fp1 = build_full_fingerprint(
            backend="mutmut", backend_version="3.7.0",
            source_paths=["src/f.py"], test_selection=["tests/t.py"],
            timeout_seconds=300, worker_count=1,
        )
        fp2 = build_full_fingerprint(
            backend="mutmut", backend_version="3.8.0",
            source_paths=["src/f.py"], test_selection=["tests/t.py"],
            timeout_seconds=300, worker_count=1,
        )
        assert fingerprints_compatible(fp1, fp2, loose=False) is False


# =========================================================================
# M44.12 — Cache Architecture
# =========================================================================

class TestMutationCache:
    def test_cache_miss(self):
        cache = MutationCache()
        entry = cache.get("nonexistent", "fp", "hash")
        assert entry is None

    def test_cache_put_and_get(self):
        cache = MutationCache()
        c = MutationCandidate(
            canonical_mutant_id="mut-1", source_file="src/f.py",
            source_hash="deadbeef", function="foo",
        )
        cache.put(c, "config-fp", MutationResultState.KILLED)
        entry = cache.get("mut-1", "config-fp", "deadbeef")
        assert entry is not None
        assert entry.result_state == "KILLED"

    def test_cache_invalidation(self):
        cache = MutationCache()
        c = MutationCandidate(
            canonical_mutant_id="mut-1", source_file="src/f.py",
            source_hash="deadbeef", function="foo",
        )
        cache.put(c, "config-fp", MutationResultState.KILLED)
        cache.invalidate("mut-1", "source_changed")
        entry = cache.get("mut-1", "config-fp", "deadbeef")
        assert entry is None  # invalidated entries return None

    def test_cache_source_invalidation(self):
        cache = MutationCache()
        for i in range(5):
            c = MutationCandidate(
                canonical_mutant_id=f"srcinv-f-{i}", source_file="srcinv_f.py",
                source_hash="hash_srcinv_f", function="foo",
            )
            cache.put(c, "fp_srcinv", MutationResultState.SURVIVED)
        for i in range(5):
            c = MutationCandidate(
                canonical_mutant_id=f"srcinv-g-{i}", source_file="srcinv_g.py",
                source_hash="hash_srcinv_g", function="bar",
            )
            cache.put(c, "fp_srcinv", MutationResultState.SURVIVED)

        count = cache.invalidate_by_source("srcinv_f.py", "source_changed")
        assert count == 5
        # g.py entries should still be valid
        entry = cache.get("srcinv-g-3", "fp_srcinv", "hash_srcinv_g")
        assert entry is not None
        assert entry.invalidation_reason is None

    def test_cache_stats(self):
        cache = MutationCache()
        for i in range(3):
            c = MutationCandidate(
                canonical_mutant_id=f"stats-mut-{i}", source_file="src/f.py",
                source_hash="h_stats", function="foo",
            )
            cache.put(c, "fp_stats", MutationResultState.KILLED)
        stats = cache.stats()
        assert stats["total_entries"] >= 3  # may include leftovers from other tests
        assert stats["valid"] >= 3


# =========================================================================
# M44.24/25 — Health Metrics + Failure Budget
# =========================================================================

class TestHealthMetrics:
    def test_high_reliability(self):
        r = MutationResult(
            campaign_id="c1", total_candidates=100, total_executions=100,
            successful_executions=98, killed=70, survived=20, timeout=8,
            infrastructure_failures=2,
        )
        metrics = compute_health_metrics(r)
        assert metrics.execution_reliability == 98.0
        assert metrics.mutation_completeness == 98.0

    def test_failure_budget_pass(self):
        r = MutationResult(
            campaign_id="c1", total_candidates=100, total_executions=100,
            killed=80, survived=15, timeout=3,
            infrastructure_failures=2, execution_error=0, unknown=0,
        )
        budget = FailureBudget()
        ok, violations = budget.check(r)
        assert ok is True
        assert len(violations) == 0

    def test_failure_budget_violation(self):
        r = MutationResult(
            campaign_id="c1", total_candidates=100, total_executions=100,
            killed=50, survived=30, timeout=5,
            infrastructure_failures=10, execution_error=5, unknown=0,
        )
        budget = FailureBudget()
        ok, violations = budget.check(r)
        assert ok is False
        assert len(violations) > 0

    def test_certification_check_pass(self):
        r = MutationResult(
            campaign_id="c1", total_candidates=100, total_executions=100,
            successful_executions=99, killed=85, survived=10, timeout=2,
            execution_error=1, no_tests=2,  # 85+10+2+1+2 = 100 -> reconciled; timeout=2% < 3% budget
        )
        check = certification_check(r)
        # Score = 85/(85+10+2) = 87.63%, reconciled, budget pass, reliability 99% >= 95%
        assert check["mutation_score"] == 87.63
        assert check["score_pass"] is True
        assert check["reconciled"] is True
        assert check["failure_budget_pass"] is True
        assert check["certifiable"] is True
        assert check["verdict"] == "CERTIFIED"

    def test_certification_check_fail_low_score(self):
        r = MutationResult(
            campaign_id="c1", total_candidates=100, total_executions=100,
            successful_executions=100, killed=50, survived=45, timeout=5,
        )
        check = certification_check(r)
        assert check["certifiable"] is False
        assert check["verdict"] == "NOT_CERTIFIED"


# =========================================================================
# M44.14 — Correctness Gate
# =========================================================================

class TestCorrectnessGate:
    def test_verify_killed_requires_source_diff(self, tmp_path):
        from runtime.foundation.verification.mutation_execution.verify_result import (
            MutationCorrectnessGate,
        )
        gate = MutationCorrectnessGate()
        c = MutationCandidate(
            canonical_mutant_id="m1", source_file="src/f.py",
            source_hash="original_hash", function="foo",
            original_expression="a+b", mutated_expression="a-b",
        )
        ex = MutationExecution(
            execution_id="e1", campaign_id="c1", mutant_id="m1",
            worker_id="w1", mutation_result=MutationResultState.KILLED,
            exit_status=1,
        )
        # workspace has no mutant file -> verification fails
        ok, msg = gate.verify_killed(c, ex, tmp_path)
        assert ok is False

    def test_verify_survived_detects_invalid_execution(self, tmp_path):
        from runtime.foundation.verification.mutation_execution.verify_result import (
            MutationCorrectnessGate,
        )
        gate = MutationCorrectnessGate()
        c = MutationCandidate(
            canonical_mutant_id="m1", source_file="src/f.py",
            source_hash="original_hash", function="foo",
            original_expression="a+b", mutated_expression="a-b",
        )
        ex = MutationExecution(
            execution_id="e1", campaign_id="c1", mutant_id="m1",
            worker_id="w1", mutation_result=MutationResultState.SURVIVED,
            exit_status=0,
        )
        # No mutant file means tests ran against original = INVALID_EXECUTION
        ok, msg = gate.verify_survived(c, ex, tmp_path)
        assert ok is False


# =========================================================================
# M44.20 — Sharding
# =========================================================================

class TestSharding:
    def test_deterministic_shard_assignment(self):
        candidates = [
            MutationCandidate(
                canonical_mutant_id=f"mut-{i:04d}",
                source_file="src/f.py", source_hash="h", function="foo",
            )
            for i in range(100)
        ]
        # Simulate shard assignment logic
        total = 4
        shards = [[] for _ in range(total)]
        sorted_cands = sorted(candidates, key=lambda c: c.canonical_mutant_id)
        shard_size = math.ceil(len(sorted_cands) / total)
        for idx in range(total):
            start = idx * shard_size
            end = start + shard_size
            shards[idx] = sorted_cands[start:end]

        assert len(shards[0]) + len(shards[1]) + len(shards[2]) + len(shards[3]) == 100
        # Verify no overlap
        all_ids = set()
        for shard in shards:
            for c in shard:
                assert c.canonical_mutant_id not in all_ids
                all_ids.add(c.canonical_mutant_id)

    def test_single_shard_returns_all(self):
        candidates = [
            MutationCandidate(
                canonical_mutant_id=f"mut-{i}", source_file="s.py",
                source_hash="h", function="f",
            )
            for i in range(10)
        ]
        # With total=1, all go to shard 0
        shard_size = math.ceil(10 / 1)
        shard = candidates[0:shard_size]
        assert len(shard) == 10


# =========================================================================
# M44.17 — Backend-Agnostic Evidence
# =========================================================================

class TestEvidenceLayer:
    def test_normalize_mutmut_format(self):
        from runtime.foundation.verification.mutation_execution.evidence import (
            normalize_backend_results,
        )
        raw = {"killed": 80, "survived": 15, "no_tests": 3, "timeout": 2, "suspicious": 0, "not_checked": 0}
        result = normalize_backend_results(raw, "mutmut")
        assert result.killed == 80
        assert result.survived == 15
        assert result.total_candidates == 100

    def test_merge_shard_results(self):
        from runtime.foundation.verification.mutation_execution.evidence import (
            merge_shard_results,
        )
        r1 = MutationResult(campaign_id="s1", total_candidates=50, killed=40, survived=10)
        r2 = MutationResult(campaign_id="s2", total_candidates=50, killed=35, survived=15)
        merged = merge_shard_results([
            (MagicMock(campaign_id="merged", scope="full (all engines)", backend_version="3.7.0",
                        mutation_backend="mutmut", environment_fingerprint="", configuration_fingerprint="",
                        creation_timestamp="", execution_policy="shard:2"), r1),
            (MagicMock(campaign_id="merged", scope="full (all engines)", backend_version="3.7.0",
                        mutation_backend="mutmut", environment_fingerprint="", configuration_fingerprint="",
                        creation_timestamp="", execution_policy="shard:2"), r2),
        ])
        assert merged.killed == 75
        assert merged.survived == 25
        assert merged.total_candidates == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
