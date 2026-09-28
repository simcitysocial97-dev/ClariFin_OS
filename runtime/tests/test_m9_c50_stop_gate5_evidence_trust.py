# runtime/tests/test_m9_c50_stop_gate5_evidence_trust.py
#
# M9-C50 PHASE 5 — STOP GATE 5: EVIDENCE TRUST GATE
#
# Live-injection tests. Every case mutates real evidence state (cache files,
# file contents, fingerprints) and verifies the enforcement surface REJECTS
# it. No test asserts a hardcoded verdict: each failure mode is produced.

from __future__ import annotations

import json
from pathlib import Path

from runtime.foundation.verification.cache import CachedVerdict, VerificationCache

COMMIT = "abc123def456"
FILES = ["backend/src/engines/credit_card_engine/core.py"]
PROFILE = "quick"


def _write_source(root: Path, content: str) -> None:
    p = root / FILES[0]
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _make_cache(tmp_path: Path) -> tuple[VerificationCache, Path]:
    cache_path = tmp_path / "verification-cache.json"
    return VerificationCache(cache_path, root=tmp_path), cache_path


def _populate_pass(cache: VerificationCache, root: Path, content: str) -> None:
    _write_source(root, content)
    cache.save(
        PROFILE,
        COMMIT,
        FILES,
        CachedVerdict(overall_status="pass", passed=10, failed=0, skipped=0),
        fingerprint={"toolchain": "pytest-8", "config": "ci-v1"},
    )


# ── 1. Stale evidence (commit drift) is rejected ────────────────────────────


def test_stale_commit_evidence_rejected(tmp_path: Path) -> None:
    cache, _ = _make_cache(tmp_path)
    _populate_pass(cache, tmp_path, "x = 1\n")
    assert cache.replay("older-commit", FILES, PROFILE).reusable is False


# ── 2. Wrong-content evidence is rejected (same files, edited contents) ─────


def test_wrong_content_evidence_rejected(tmp_path: Path) -> None:
    cache, _ = _make_cache(tmp_path)
    _populate_pass(cache, tmp_path, "x = 1\n")
    # Same commit, same file list — but the file CONTENT changed on disk.
    _write_source(tmp_path, "x = 2  # bug fix\n")
    result = cache.replay(COMMIT, FILES, PROFILE)
    assert result.reusable is False
    assert result.reason == "cache-invalid-or-missing"


# ── 3. Wrong-configuration evidence is rejected ─────────────────────────────


def test_wrong_config_fingerprint_rejected(tmp_path: Path) -> None:
    cache, _ = _make_cache(tmp_path)
    _populate_pass(cache, tmp_path, "x = 1\n")
    result = cache.replay(
        COMMIT, FILES, PROFILE, fingerprint={"toolchain": "pytest-8", "config": "ci-v2"}
    )
    assert result.reusable is False


def test_wrong_toolchain_fingerprint_rejected(tmp_path: Path) -> None:
    cache, _ = _make_cache(tmp_path)
    _populate_pass(cache, tmp_path, "x = 1\n")
    result = cache.replay(
        COMMIT, FILES, PROFILE, fingerprint={"toolchain": "pytest-9", "config": "ci-v1"}
    )
    assert result.reusable is False


# ── 4. Corrupted evidence is rejected ───────────────────────────────────────


def test_corrupted_cache_file_rejected(tmp_path: Path) -> None:
    cache, cache_path = _make_cache(tmp_path)
    _populate_pass(cache, tmp_path, "x = 1\n")
    cache_path.write_text("{not valid json!!!", encoding="utf-8")
    result = cache.replay(COMMIT, FILES, PROFILE)
    assert result.reusable is False


def test_truncated_cache_file_rejected(tmp_path: Path) -> None:
    cache, cache_path = _make_cache(tmp_path)
    _populate_pass(cache, tmp_path, "x = 1\n")
    raw = json.loads(cache_path.read_text(encoding="utf-8"))
    del raw["profiles"][PROFILE]["overall_status"]
    cache_path.write_text(json.dumps(raw), encoding="utf-8")
    result = cache.replay(COMMIT, FILES, PROFILE)
    assert result.reusable is False
    assert result.reason == "cache-corrupt-missing-status"


def test_status_field_corruption_cannot_flip_fail_to_pass(tmp_path: Path) -> None:
    cache, cache_path = _make_cache(tmp_path)
    _write_source(tmp_path, "x = 1\n")
    cache.save(
        PROFILE,
        COMMIT,
        FILES,
        CachedVerdict(overall_status="fail", passed=8, failed=2, skipped=0),
    )
    # Corrupt the verdict fields but keep overall_status="fail": the derived
    # exit code must remain non-zero regardless of the corrupted counters.
    raw = json.loads(cache_path.read_text(encoding="utf-8"))
    raw["profiles"][PROFILE]["failed"] = 0
    cache_path.write_text(json.dumps(raw), encoding="utf-8")
    result = cache.replay(COMMIT, FILES, PROFILE)
    assert result.reusable is True
    assert result.exit_code == 1
    assert result.overall_status == "fail"


# ── 5. Reused evidence is explicitly classified ─────────────────────────────


def test_reused_evidence_is_explicitly_classified(tmp_path: Path) -> None:
    cache, _ = _make_cache(tmp_path)
    _populate_pass(cache, tmp_path, "x = 1\n")
    result = cache.replay(COMMIT, FILES, PROFILE)
    assert result.reusable is True
    assert result.reason == "replay-pass"


def test_non_reused_evidence_is_explicitly_classified(tmp_path: Path) -> None:
    cache, _ = _make_cache(tmp_path)
    result = cache.replay(COMMIT, FILES, PROFILE)
    assert result.reusable is False
    assert result.reason == "cache-invalid-or-missing"


# ── 6. Incomplete evidence cannot close obligations (links Phase 2 rule) ────


def _ob(cap_id: str, kind):  # type: ignore[no-untyped-def]
    from runtime.foundation.verification.obligation import (
        Capability,
        Change,
        Requirement,
        VerificationObligation,
    )

    change = Change(path="x.py", change_type="modified")
    cap = Capability(capability_id=cap_id, authority="Test")
    req = Requirement(
        requirement_id=f"r-{cap_id}",
        capability_id=cap_id,
        obligation_kind=kind,
        rationale="gate5",
        severity="required",
    )
    return VerificationObligation(
        obligation_id=f"obl-{cap_id}",
        change=change,
        capability=cap,
        requirement=req,
    )


def test_incomplete_evidence_cannot_close_obligations() -> None:
    """No execution evidence at all → obligation cannot reach CLOSED and the
    reconciliation is incomplete (no successful verification possible)."""
    from runtime.foundation.verification.obligation import (
        ObligationKind,
        ObligationSet,
    )
    from runtime.foundation.verification.obligation_reconciliation import (
        reconcile_obligations,
    )

    res = reconcile_obligations(
        ObligationSet("sg5", (_ob("c1", ObligationKind.UNIT),)), []
    )
    assert not res.complete
    assert res.obligations[0].disposition.value != "closed"


def test_failed_execution_cannot_close_obligation() -> None:
    from types import SimpleNamespace

    from runtime.foundation.verification.obligation import (
        ObligationKind,
        ObligationSet,
    )
    from runtime.foundation.verification.obligation_reconciliation import (
        reconcile_obligations,
    )

    rec = SimpleNamespace(
        capabilities=["c1"],
        primary_capability="c1",
        verification_kind="unit",
        completion_state="failed",
    )
    res = reconcile_obligations(
        ObligationSet("sg5", (_ob("c1", ObligationKind.UNIT),)), [rec]
    )
    assert not res.complete


# ── 7. Evidence lineage is complete ─────────────────────────────────────────


def test_cache_entry_records_lineage(tmp_path: Path) -> None:
    cache, cache_path = _make_cache(tmp_path)
    _populate_pass(cache, tmp_path, "x = 1\n")
    raw = json.loads(cache_path.read_text(encoding="utf-8"))
    entry = raw["profiles"][PROFILE]
    # A trusted evidence record must carry its identity lineage.
    assert raw["last_commit"] == COMMIT
    assert entry["changed_files"] == FILES
    assert entry["fingerprint"] == {"toolchain": "pytest-8", "config": "ci-v1"}
    assert entry["tree_digest"]
    assert entry["overall_status"] == "pass"
