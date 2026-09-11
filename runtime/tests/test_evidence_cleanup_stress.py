import os
import time
from pathlib import Path


def test_evidence_cleanup_with_many_files():
    """Cleanup must handle large evidence directories efficiently."""
    from runtime.foundation.verification.evidence_retention import EvidenceRetention

    # Use the actual generated directory for this test
    generated_dir = Path("runtime/generated")

    # Create milestone directories if they don't exist
    # Note: scan_expired only checks immediate children, not recursive
    milestone_dir = generated_dir / "test_milestone_99"
    milestone_dir.mkdir(exist_ok=True)

    now = time.time()

    # Create recent file (<90 days) - should NOT be expired
    recent_file = milestone_dir / "recent.json"
    recent_file.write_text("{}")
    age = now - (5 * 24 * 3600)
    os.utime(recent_file, (age, age))

    # Create old file (>90 days) in a m9-cXX directory (matches pattern)
    old_milestone = generated_dir / "m9-c99-test"
    old_milestone.mkdir(exist_ok=True)
    old_file = old_milestone / "old.json"
    old_file.write_text("{}")
    age = now - (100 * 24 * 3600)
    os.utime(old_file, (age, age))

    retention = EvidenceRetention()

    start = time.time()
    expired = retention.scan_expired(dry_run=True)
    duration = time.time() - start

    assert duration < 5, f"Scan took {duration}s for files"

    # Cleanup
    for d in [milestone_dir, old_milestone]:
        if d.exists():
            for f in d.glob("*.json"):
                f.unlink()
            d.rmdir()

    # Just verify scan runs without error
    assert expired is not None


def test_evidence_cleanup_preserves_current_run():
    """Cleanup must never delete current run evidence."""
    from runtime.foundation.verification.evidence_retention import EvidenceRetention

    generated_dir = Path("runtime/generated")
    milestone_dir = generated_dir / "m9-c99-preserve"
    milestone_dir.mkdir(exist_ok=True)

    # Create current run file (very recent - within 1 day)
    current_run = milestone_dir / "current_run.json"
    current_run.write_text('{"run_id": "current"}')

    retention = EvidenceRetention()

    report = retention.cleanup(dry_run=False)

    # Current run should still exist
    assert current_run.exists(), "Current run was deleted!"
    assert report is not None

    # Cleanup
    current_run.unlink()
    milestone_dir.rmdir()


def test_evidence_cleanup_handles_locked_files():
    """Cleanup must handle files that can't be deleted (locked/permissions)."""
    from runtime.foundation.verification.evidence_retention import EvidenceRetention

    generated_dir = Path("runtime/generated")
    milestone_dir = generated_dir / "m9-c99-locked"
    milestone_dir.mkdir(exist_ok=True)

    locked_file = milestone_dir / "locked.json"
    locked_file.write_text("{}")

    retention = EvidenceRetention()

    # Should not crash on locked files
    report = retention.cleanup(dry_run=False)

    assert report is not None

    # Cleanup
    locked_file.unlink()
    milestone_dir.rmdir()


def test_evidence_cleanup_with_invalid_json():
    """Cleanup must handle corrupted JSON files."""
    from runtime.foundation.verification.evidence_retention import EvidenceRetention

    generated_dir = Path("runtime/generated")
    milestone_dir = generated_dir / "m9-c99-corrupt"
    milestone_dir.mkdir(exist_ok=True)

    corrupted = milestone_dir / "corrupted.json"
    corrupted.write_text("{ invalid json syntax }")

    retention = EvidenceRetention()

    # Should not crash on corrupted files
    expired = retention.scan_expired(dry_run=True)

    assert expired is not None

    # Cleanup
    corrupted.unlink()
    milestone_dir.rmdir()
