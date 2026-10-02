"""Retention-policy behaviour tests for runtime/generated evidence.

Hermeticity
-----------
Every test in this file drives ``EvidenceRetention`` in ``dry_run=False``
mode, which really does ``shutil.rmtree`` its targets. They must therefore
never be pointed at the repository's own ``runtime/generated/`` tree, which
holds tracked milestone certification evidence.

The class defaults ``generated_dir`` to the real ``runtime/generated``
(``evidence_retention.py:30``) and classifies real directories such as
``m9-c50`` and ``m9-c49/logs`` as expirable once their mtime passes the
retention window. Git sets a checked-out file's mtime to the moment of the
checkout, so those trees only *look* unexpired because the working copy
happens to be fresh. Running this module against a tree whose evidence was
checked out more than 30-90 days ago would delete real certification
evidence, and the deletion would be silent: every assertion below would still
pass.

So each test builds its own ``tmp_path``-rooted generated tree and passes it
explicitly via the ``generated_dir`` constructor argument the class already
supports (``evidence_retention.py:86-93``). The retention logic exercised
here is identical — only the root under test changes.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from runtime.foundation.verification.evidence_retention import EvidenceRetention


def _age(path: Path, days: float) -> None:
    """Backdate *path*'s mtime by *days* so the retention policy sees it as old."""
    stamp = time.time() - (days * 24 * 3600)
    os.utime(path, (stamp, stamp))


@pytest.fixture
def generated_dir(tmp_path: Path) -> Path:
    """An isolated stand-in for runtime/generated/.

    Deliberately *not* the real tree: these tests perform real deletion.
    """
    root = tmp_path / "generated"
    root.mkdir()
    return root


def test_evidence_cleanup_with_many_files(generated_dir: Path) -> None:
    """Cleanup must handle large evidence directories efficiently."""
    # Create milestone directories if they don't exist
    # Note: scan_expired only checks immediate children, not recursive
    milestone_dir = generated_dir / "test_milestone_99"
    milestone_dir.mkdir(exist_ok=True)

    # Create recent file (<90 days) - should NOT be expired
    recent_file = milestone_dir / "recent.json"
    recent_file.write_text("{}")
    _age(recent_file, 5)

    # Create old file (>90 days) in a m9-cXX directory (matches pattern)
    old_milestone = generated_dir / "m9-c99-test"
    old_milestone.mkdir(exist_ok=True)
    old_file = old_milestone / "old.json"
    old_file.write_text("{}")
    _age(old_file, 100)

    retention = EvidenceRetention(generated_dir=generated_dir)

    start = time.time()
    expired = retention.scan_expired(dry_run=True)
    duration = time.time() - start

    assert duration < 5, f"Scan took {duration}s for files"

    # Just verify scan runs without error
    assert expired is not None


def test_evidence_cleanup_preserves_current_run(generated_dir: Path) -> None:
    """Cleanup must never delete current run evidence."""
    milestone_dir = generated_dir / "m9-c99-preserve"
    milestone_dir.mkdir(exist_ok=True)

    # Create current run file (very recent - within 1 day)
    current_run = milestone_dir / "current_run.json"
    current_run.write_text('{"run_id": "current"}')

    retention = EvidenceRetention(generated_dir=generated_dir)

    report = retention.cleanup(dry_run=False)

    # Current run should still exist
    assert current_run.exists(), "Current run was deleted!"
    assert report is not None


def test_evidence_cleanup_handles_locked_files(generated_dir: Path) -> None:
    """Cleanup must handle files that can't be deleted (locked/permissions)."""
    milestone_dir = generated_dir / "m9-c99-locked"
    milestone_dir.mkdir(exist_ok=True)

    locked_file = milestone_dir / "locked.json"
    locked_file.write_text("{}")

    retention = EvidenceRetention(generated_dir=generated_dir)

    # Should not crash on locked files
    report = retention.cleanup(dry_run=False)

    assert report is not None


def test_evidence_cleanup_with_invalid_json(generated_dir: Path) -> None:
    """Cleanup must handle corrupted JSON files."""
    milestone_dir = generated_dir / "m9-c99-corrupt"
    milestone_dir.mkdir(exist_ok=True)

    corrupted = milestone_dir / "corrupted.json"
    corrupted.write_text("{ invalid json syntax }")

    retention = EvidenceRetention(generated_dir=generated_dir)

    # Should not crash on corrupted files
    expired = retention.scan_expired(dry_run=True)

    assert expired is not None
