#!/usr/bin/env python3
"""Test mutation runner process group killing on timeout"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "/home/vasantha/AI-Projects/ClariFin_OS")
from runtime.foundation.verification.mutation_runner import execute_mutation

REPO_ROOT = Path("/home/vasantha/AI-Projects/ClariFin_OS")


def check_mutmut_orphans():
    """Check for orphaned mutmut-related processes."""
    result = subprocess.run(["pgrep", "-f", "mutmut"], capture_output=True, text=True)
    if result.stdout.strip():
        return result.stdout.strip().split()
    return []


def test_mutation_timeout_kills_tree():
    """Test: Mutation runner timeout kills entire process tree"""
    print("=" * 60)
    print("  Test: Mutation runner timeout kills process tree")
    print("=" * 60)

    # Use a very short timeout to trigger timeout
    result = execute_mutation(
        mode="smoke",
        max_runtime=1,  # 1 second timeout
        max_children=1,
    )
    print(f"Exit code: {result.mutmut_rc}")
    print(f"Status: {result.execution_status}")
    print(f"Duration: {result.duration_seconds}s")
    print(f"Error: {result.error}")

    # Check for orphaned mutmut processes
    orphans = check_mutmut_orphans()
    if orphans:
        print(f"ORPHANED MUTMUT PROCESSES: {orphans}")
        print("FAIL: Process group NOT killed")
    else:
        print("No orphaned mutmut processes")
        print("PASS: Process group killed successfully")


if __name__ == "__main__":
    from pathlib import Path

    print("============================================================")
    print("  Mutation Runner Process Group Killing Test")
    print("============================================================")

    test_mutation_timeout_kills_tree()

    print("\n============================================================")
    print("  Test Complete")
    print("============================================================")
