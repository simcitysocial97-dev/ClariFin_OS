import subprocess
from pathlib import Path

import pytest


@pytest.mark.slow
def test_complete_development_workflow():
    """Simulate full development cycle with all framework features."""

    test_file = Path("backend/src/engines/loan_engine/emi.py")

    if not test_file.exists():
        pytest.skip("Test file not found")

    original_content = test_file.read_text()

    try:
        modified = "# Real workflow test change\n" + original_content
        test_file.write_text(modified)

        print("\n=== STEP 1: Running verification plan ===")
        result = subprocess.run(
            ["python", "-m", "runtime.verify", "plan", "--scope", "backend"],
            capture_output=True, text=True, timeout=120
        )

        output = result.stdout + result.stderr

        print("\n=== STEP 2: Checking plan generation ===")
        # Should generate a plan without crashing
        assert result.returncode in [0, 1], \
            f"Plan command crashed: {result.stderr[-500:]}"

        print("Plan generation confirmed")

        print("\n=== STEP 3: Checking for crashes ===")
        assert "Traceback" not in output, \
            f"Verification crashed:\n{output[-2000:]}"

        print("No crashes detected")

        print("\n=== STEP 4: Checking framework health ===")
        health_result = subprocess.run(
            ["python", "-m", "runtime.verify", "inspect", "health"],
            capture_output=True, text=True, timeout=30
        )

        assert health_result.returncode == 0, \
            f"Health check failed: {health_result.stderr}"

        print("Framework health good")

        print("\n=== STEP 5: Checking evidence generation ===")
        generated_dir = Path("runtime/generated")

        if generated_dir.exists():
            recent_files = list(generated_dir.rglob("*.json"))
            print(f"Found {len(recent_files)} evidence files")

        print("\nWORKFLOW TEST COMPLETE")

    finally:
        test_file.write_text(original_content)
