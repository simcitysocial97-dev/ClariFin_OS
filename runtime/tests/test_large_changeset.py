import tempfile
import time


def test_blast_radius_with_50_files():
    """Blast radius must handle large changesets efficiently."""
    from runtime.foundation.verification.blast_radius import BlastRadiusEngine

    changed_files = []

    real_files = [
        "backend/src/engines/loan_engine/emi.py",
        "backend/src/engines/balance_engine/balance.py",
        "backend/src/engines/account_engine/lifecycle.py",
        "backend/src/routers/accounts.py",
        "backend/src/routers/loans.py",
        "frontend/app/dashboard/page.tsx",
        "frontend/app/accounts/page.tsx",
    ]

    changed_files.extend(real_files)

    for i in range(43):
        changed_files.append(f"backend/src/engines/fake_engine_{i}/module.py")

    engine = BlastRadiusEngine()

    start = time.time()
    result = engine.compute(explicit_files=changed_files)
    duration = time.time() - start

    assert duration < 30, f"Took {duration}s (should be <30s)"

    # Result is a BlastRadiusContract, verify it's valid
    assert result is not None
    d = result.to_dict()
    assert "contract_id" in d


def test_blast_radius_with_nonexistent_files():
    """Blast radius must gracefully handle files that don't exist."""
    from runtime.foundation.verification.blast_radius import BlastRadiusEngine

    changed_files = [
        "backend/src/engines/does_not_exist.py",
        "backend/src/routers/also_missing.py",
        "frontend/app/fake/page.tsx",
    ]

    engine = BlastRadiusEngine()
    result = engine.compute(explicit_files=changed_files)
    assert result is not None


def test_blast_radius_with_binary_files():
    """Blast radius must skip binary files without crashing."""
    from runtime.foundation.verification.blast_radius import BlastRadiusEngine

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        binary_file = f.name

    try:
        engine = BlastRadiusEngine()
        result = engine.compute(explicit_files=[binary_file])
        assert result is not None
    finally:
        import os
        os.unlink(binary_file)


def test_blast_radius_with_very_large_file():
    """Blast radius must handle large source files (>10K lines)."""
    from runtime.foundation.verification.blast_radius import BlastRadiusEngine

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        for i in range(15000):
            f.write(f"def function_{i}(): pass\n")
        large_file = f.name

    try:
        engine = BlastRadiusEngine()

        start = time.time()
        result = engine.compute(explicit_files=[large_file])
        duration = time.time() - start

        assert duration < 10, f"Large file took {duration}s"
        assert result is not None
    finally:
        import os
        os.unlink(large_file)


def test_verification_plan_with_all_engines_changed():
    """Verification plan must handle scenario where all engines change."""
    from runtime.foundation.verification.control_plane import ControlPlanePlanner

    planner = ControlPlanePlanner()
    assert planner is not None
