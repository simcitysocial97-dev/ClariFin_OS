"""VEA-5 M3 — Verification Cache Integrity acceptance tests.

Proves the M3-C contract:

    Fresh successful execution  -> PASS / exit 0
    Fresh failed execution      -> FAIL / exit != 0
    Cached successful execution -> PASS / exit 0
    Cached failed execution     -> FAIL / exit != 0
    Missing / corrupt evidence  -> re-execute or fail safely (never assume PASS)
    Fingerprint mismatch        -> do not reuse
    Stale failure               -> must not silently become PASS

Run:
    python3 -m pytest runtime/tests/test_vea5_verification_cache.py -q
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from runtime.foundation.verification.cache import (
    CachedVerdict,
    VerificationCache,
)


def _cache(tmp_path: Path) -> VerificationCache:
    return VerificationCache(tmp_path / "verification-cache.json")


def _save(cache: VerificationCache, profile: str, status: str, passed: int = 0, failed: int = 0, skipped: int = 0, changed_files: list[str] | None = None):
    verdict = CachedVerdict(
        overall_status=status,
        passed=passed,
        failed=failed,
        skipped=skipped,
        unit_statuses=(
            (("unit-targeted", "passed"),)
            if status == "pass"
            else (("unit-targeted", "failed"),)
        ),
    )
    cache.save(
        profile=profile,
        commit="abc123",
        changed_files=changed_files or ["backend/src/engines/loan_engine.py"],
        verdict=verdict,
        duration=12.3,
    )


# ---------------------------------------------------------------------------
# Cache miss / corrupt / mismatch -> reusable=False
# ---------------------------------------------------------------------------


def test_missing_cache_is_not_reusable():
    with TemporaryDirectory() as td:
        cache = _cache(Path(td))
        r = cache.replay("deadbeef", ["a.py"], "backend")
        assert not r.reusable
        assert r.exit_code is None
        assert r.overall_status is None
        assert "cache-invalid-or-missing" in r.reason


def test_corrupt_cache_without_status_is_not_reusable():
    with TemporaryDirectory() as td:
        cache = _cache(Path(td))
        (Path(td) / "verification-cache.json").write_text("{bad json", encoding="utf-8")
        r = cache.replay("abc123", ["a.py"], "backend")
        assert not r.reusable
        assert r.exit_code is None
        assert "cache-invalid-or-missing" in r.reason


def test_fingerprint_mismatch_is_not_reusable():
    with TemporaryDirectory() as td:
        cache = _cache(Path(td))
        _save(cache, "backend", "pass")
        r = cache.replay("different-commit", ["a.py"], "backend")
        assert not r.reusable
        assert r.exit_code is None


def test_profile_mismatch_is_not_reusable():
    with TemporaryDirectory() as td:
        cache = _cache(Path(td))
        _save(cache, "backend", "pass")
        r = cache.replay("abc123", ["a.py"], "frontend")
        assert not r.reusable


# ---------------------------------------------------------------------------
# Cached PASS -> exit 0
# ---------------------------------------------------------------------------


def test_cached_pass_replays_as_pass_exit_zero():
    with TemporaryDirectory() as td:
        cache = _cache(Path(td))
        _save(cache, "backend", "pass", passed=10, failed=0)
        r = cache.replay("abc123", ["backend/src/engines/loan_engine.py"], "backend")
        assert r.reusable is True
        assert r.overall_status == "pass"
        assert r.exit_code == 0
        assert "replay-pass" in r.reason


# ---------------------------------------------------------------------------
# Cached FAIL -> exit != 0 (the critical M3-C invariant)
# ---------------------------------------------------------------------------


def test_cached_fail_replays_as_fail_nonzero_exit():
    with TemporaryDirectory() as td:
        cache = _cache(Path(td))
        _save(cache, "backend", "fail", passed=5, failed=1)
        r = cache.replay("abc123", ["backend/src/engines/loan_engine.py"], "backend")
        assert r.reusable is True
        assert r.overall_status == "fail"
        assert r.exit_code == 1
        assert "replay-fail" in r.reason


def test_stale_failure_never_silently_becomes_pass():
    with TemporaryDirectory() as td:
        cache = _cache(Path(td))
        _save(cache, "backend", "fail", failed=2)
        # The cache stores a failure. Replaying must NOT produce PASS/0.
        for _ in range(3):
            r = cache.replay("abc123", ["backend/src/engines/loan_engine.py"], "backend")
            assert r.overall_status == "fail"
            assert r.exit_code == 1
            assert r.reusable is True


# ---------------------------------------------------------------------------
# Save / load round-trip preserves status
# ---------------------------------------------------------------------------


def test_save_and_reload_preserves_failed_status():
    with TemporaryDirectory() as td:
        cache = _cache(Path(td))
        _save(cache, "backend", "fail", passed=3, failed=1, skipped=2)
        loaded = cache.get_verdict("backend")
        assert loaded is not None
        assert loaded.overall_status == "fail"
        assert loaded.passed == 3
        assert loaded.failed == 1
        assert loaded.skipped == 2
        r = cache.replay("abc123", ["backend/src/engines/loan_engine.py"], "backend")
        assert r.exit_code == 1


def test_multiple_profiles_do_not_interfere():
    with TemporaryDirectory() as td:
        cache = _cache(Path(td))
        _save(cache, "backend", "pass", passed=10, changed_files=["backend/src/engines/loan_engine.py"])
        _save(cache, "frontend", "fail", failed=1, changed_files=["frontend/src/App.tsx"])
        rb = cache.replay("abc123", ["backend/src/engines/loan_engine.py"], "backend")
        rf = cache.replay("abc123", ["frontend/src/App.tsx"], "frontend")
        assert rb.overall_status == "pass" and rb.exit_code == 0
        assert rf.overall_status == "fail" and rf.exit_code == 1
