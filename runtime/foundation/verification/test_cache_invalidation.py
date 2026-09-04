"""Evidence Invalidation & Reuse Tests.

Tests for the cache contract that ensures:
1. Cached PASS -> reusable with exit_code=0
2. Cached FAIL -> reusable with exit_code=1 (never assume PASS)
3. Missing/invalid cache -> re-execute (caller decides)
4. Fingerprint mismatch -> invalidation
5. Commit mismatch -> invalidation
6. Changed files mismatch -> invalidation
"""

from __future__ import annotations

import json

import pytest

from runtime.foundation.verification.cache import (
    CachedVerdict,
    ReplayResult,
    VerificationCache,
)


class TestCacheInvalidation:
    """Test cache invalidation triggers."""

    def test_cache_invalid_when_commit_mismatch(self, tmp_path) -> None:
        """Cache is invalid when commit SHA changes."""
        cache = VerificationCache(tmp_path / "cache.json")

        cache.save(
            profile="test",
            commit="abc123",
            changed_files=["file1.py"],
            verdict=CachedVerdict(overall_status="pass", passed=10, failed=0, skipped=0),
        )

        is_valid = cache.is_valid(
            commit="different123",
            changed_files=["file1.py"],
            profile="test",
        )
        assert is_valid is False

    def test_cache_invalid_when_changed_files_mismatch(self, tmp_path) -> None:
        """Cache is invalid when changed files differ."""
        cache = VerificationCache(tmp_path / "cache.json")

        cache.save(
            profile="test",
            commit="abc123",
            changed_files=["file1.py"],
            verdict=CachedVerdict(overall_status="pass", passed=10, failed=0, skipped=0),
        )

        is_valid = cache.is_valid(
            commit="abc123",
            changed_files=["file2.py", "file1.py"],
            profile="test",
        )
        assert is_valid is False

    def test_cache_invalid_when_fingerprint_mismatch(self, tmp_path) -> None:
        """Cache is invalid when fingerprint (tool version) changes."""
        cache = VerificationCache(tmp_path / "cache.json")

        cache.save(
            profile="test",
            commit="abc123",
            changed_files=["file1.py"],
            verdict=CachedVerdict(overall_status="pass", passed=10, failed=0, skipped=0),
            fingerprint={"ruff": "0.1.0", "mypy": "1.0"},
        )

        is_valid = cache.is_valid(
            commit="abc123",
            changed_files=["file1.py"],
            profile="test",
            fingerprint={"ruff": "0.2.0", "mypy": "1.0"},
        )
        assert is_valid is False

    def test_cache_valid_when_all_match(self, tmp_path) -> None:
        """Cache is valid when commit, files, and fingerprint all match."""
        cache = VerificationCache(tmp_path / "cache.json")

        cache.save(
            profile="test",
            commit="abc123",
            changed_files=["file1.py"],
            verdict=CachedVerdict(overall_status="pass", passed=10, failed=0, skipped=0),
            fingerprint={"ruff": "0.1.0"},
        )

        is_valid = cache.is_valid(
            commit="abc123",
            changed_files=["file1.py"],
            profile="test",
            fingerprint={"ruff": "0.1.0"},
        )
        assert is_valid is True


class TestCacheReuse:
    """Test cache reuse behavior."""

    def test_replay_returns_pass_for_cached_pass(self, tmp_path) -> None:
        """Cached PASS returns reusable=True with exit_code=0."""
        cache = VerificationCache(tmp_path / "cache.json")

        cache.save(
            profile="test",
            commit="abc123",
            changed_files=["file1.py"],
            verdict=CachedVerdict(overall_status="pass", passed=10, failed=0, skipped=0),
        )

        result = cache.replay(
            commit="abc123",
            changed_files=["file1.py"],
            profile="test",
        )

        assert result.reusable is True
        assert result.overall_status == "pass"
        assert result.exit_code == 0

    def test_replay_returns_fail_for_cached_fail(self, tmp_path) -> None:
        """Cached FAIL returns reusable=True with exit_code=1."""
        cache = VerificationCache(tmp_path / "cache.json")

        cache.save(
            profile="test",
            commit="abc123",
            changed_files=["file1.py"],
            verdict=CachedVerdict(overall_status="fail", passed=8, failed=2, skipped=0),
        )

        result = cache.replay(
            commit="abc123",
            changed_files=["file1.py"],
            profile="test",
        )

        assert result.reusable is True
        assert result.overall_status == "fail"
        assert result.exit_code == 1

    def test_replay_never_returns_pass_for_fail(self, tmp_path) -> None:
        """Cache replay must never return exit_code=0 for cached FAIL."""
        cache = VerificationCache(tmp_path / "cache.json")

        cache.save(
            profile="test",
            commit="abc123",
            changed_files=["file1.py"],
            verdict=CachedVerdict(overall_status="fail", passed=5, failed=5, skipped=0),
        )

        result = cache.replay(
            commit="abc123",
            changed_files=["file1.py"],
            profile="test",
        )

        if result.reusable and result.exit_code is not None:
            assert result.exit_code != 0, "Must never return exit_code=0 for cached FAIL"

    def test_replay_returns_not_reusable_when_invalid(self, tmp_path) -> None:
        """Invalid cache returns reusable=False, caller decides."""
        cache = VerificationCache(tmp_path / "cache.json")

        result = cache.replay(
            commit="abc123",
            changed_files=["file1.py"],
            profile="nonexistent",
        )

        assert result.reusable is False
        assert result.exit_code is None
        assert "invalid" in result.reason or "missing" in result.reason


class TestCachedVerdict:
    """Test CachedVerdict structure."""

    def test_cached_verdict_stores_pass(self) -> None:
        """CachedVerdict correctly stores a passing verdict."""
        verdict = CachedVerdict(
            overall_status="pass",
            passed=100,
            failed=0,
            skipped=5,
        )
        assert verdict.overall_status == "pass"
        assert verdict.passed == 100
        assert verdict.failed == 0
        assert verdict.skipped == 5

    def test_cached_verdict_stores_fail(self) -> None:
        """CachedVerdict correctly stores a failing verdict."""
        verdict = CachedVerdict(
            overall_status="fail",
            passed=95,
            failed=5,
            skipped=0,
        )
        assert verdict.overall_status == "fail"
        assert verdict.passed == 95
        assert verdict.failed == 5

    def test_cached_verdict_stores_unit_statuses(self) -> None:
        """CachedVerdict stores per-unit statuses."""
        verdict = CachedVerdict(
            overall_status="fail",
            passed=8,
            failed=2,
            skipped=0,
            unit_statuses=(
                ("engine1", "pass"),
                ("engine2", "fail"),
            ),
        )
        assert verdict.unit_statuses == (
            ("engine1", "pass"),
            ("engine2", "fail"),
        )


class TestReplayResult:
    """Test ReplayResult structure."""

    def test_replay_result_for_pass(self) -> None:
        """ReplayResult correctly represents a cached pass."""
        result = ReplayResult(
            reusable=True,
            overall_status="pass",
            exit_code=0,
            reason="replay-pass",
        )
        assert result.reusable is True
        assert result.overall_status == "pass"
        assert result.exit_code == 0

    def test_replay_result_for_fail(self) -> None:
        """ReplayResult correctly represents a cached fail."""
        result = ReplayResult(
            reusable=True,
            overall_status="fail",
            exit_code=1,
            reason="replay-fail",
        )
        assert result.reusable is True
        assert result.overall_status == "fail"
        assert result.exit_code == 1

    def test_replay_result_for_invalid(self) -> None:
        """ReplayResult correctly represents an invalid cache."""
        result = ReplayResult(
            reusable=False,
            overall_status=None,
            exit_code=None,
            reason="cache-invalid-or-missing",
        )
        assert result.reusable is False
        assert result.overall_status is None
        assert result.exit_code is None


class TestCachePersistence:
    """Test cache file persistence."""

    def test_cache_survives_round_trip(self, tmp_path) -> None:
        """Cache file survives save and reload."""
        cache = VerificationCache(tmp_path / "cache.json")

        cache.save(
            profile="test",
            commit="abc123",
            changed_files=["file1.py", "file2.py"],
            verdict=CachedVerdict(overall_status="pass", passed=50, failed=0, skipped=0),
        )

        cached = cache.get_verdict("test")
        assert cached is not None
        assert cached.overall_status == "pass"
        assert cached.passed == 50
        assert cached.failed == 0

    def test_cache_contains_all_profiles(self, tmp_path) -> None:
        """Cache stores multiple profiles separately."""
        cache = VerificationCache(tmp_path / "cache.json")

        cache.save(
            profile="quick",
            commit="abc123",
            changed_files=["file1.py"],
            verdict=CachedVerdict(overall_status="pass", passed=100, failed=0, skipped=0),
        )

        cache.save(
            profile="golden",
            commit="abc123",
            changed_files=["file1.py"],
            verdict=CachedVerdict(overall_status="pass", passed=10, failed=0, skipped=0),
        )

        quick_verdict = cache.get_verdict("quick")
        golden_verdict = cache.get_verdict("golden")

        assert quick_verdict is not None
        assert golden_verdict is not None
        assert quick_verdict.passed == 100
        assert golden_verdict.passed == 10


class TestCacheContract:
    """Test the cache contract invariants."""

    def test_exit_code_never_zero_for_fail(self, tmp_path) -> None:
        """Contract: exit_code must never be 0 when stored status is fail."""
        cache = VerificationCache(tmp_path / "cache.json")

        cache.save(
            profile="test",
            commit="abc123",
            changed_files=["file1.py"],
            verdict=CachedVerdict(overall_status="fail", passed=0, failed=10, skipped=0),
        )

        result = cache.replay(
            commit="abc123",
            changed_files=["file1.py"],
            profile="test",
        )

        if result.exit_code is not None:
            assert result.exit_code != 0, "Contract violation: exit_code=0 for FAIL"

    def test_reusable_only_when_valid(self, tmp_path) -> None:
        """Contract: reusable=True only when cache is valid."""
        cache = VerificationCache(tmp_path / "cache.json")

        result = cache.replay(
            commit="abc123",
            changed_files=["file1.py"],
            profile="test",
        )

        assert result.reusable is False

    def test_caller_decides_on_invalid_cache(self, tmp_path) -> None:
        """Contract: caller must decide what to do when cache is invalid."""
        cache = VerificationCache(tmp_path / "cache.json")

        result = cache.replay(
            commit="abc123",
            changed_files=["file1.py"],
            profile="test",
        )

        assert result.exit_code is None
        assert result.overall_status is None
