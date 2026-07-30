#!/usr/bin/env python3
"""
ClariFin OS Verification Runtime CLI

Delegates to existing verification modules:
  - backend/tests/runtime/ci_targets.py  (CI target derivation)
  - backend/src/verification/             (Verification Intelligence Layer)

This is a thin wrapper for Program 1.
Program 3 will expand this into a full CLI.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def _import_ci_targets():
    """Import the existing ci_targets module."""
    project_root = _get_project_root()
    runtime_dir = project_root / "backend" / "tests" / "runtime"
    sys.path.insert(0, str(runtime_dir))
    try:
        import ci_targets
        return ci_targets
    except ImportError as e:
        print(f"ERROR: Cannot import ci_targets module: {e}")
        print(f"Expected location: {runtime_dir / 'ci_targets.py'}")
        sys.exit(1)


def delegate_to_ci_targets(args: list[str]) -> int:
    """Delegate to the existing ci_targets main() function."""
    ci_targets = _import_ci_targets()
    
    # Save original argv
    original_argv = sys.argv[:]
    try:
        # Set argv to simulate command-line invocation
        sys.argv = ["ci_targets"] + args
        return ci_targets.main()
    finally:
        # Restore original argv
        sys.argv = original_argv


def print_roadmap() -> None:
    """Print the CLI roadmap for Program 3."""
    print("ClariFin OS Verification Runtime CLI")
    print("=" * 50)
    print()
    print("Available commands (implemented in Program 3):")
    print("  verify quick        - Fast local checks")
    print("  verify backend      - Backend verification")
    print("  verify frontend     - Frontend verification")
    print("  verify mutation     - Mutation testing")
    print("  verify e2e          - End-to-end tests")
    print("  verify repository   - Full repository verification")
    print("  verify ai-plan      - AI-assisted planning")
    print("  verify github-log   - Parse GitHub Actions logs")
    print()
    print("Current available commands:")
    print("  ci-targets --property    - List property test targets")
    print("  ci-targets --contract    - List contract test targets")
    print("  ci-targets --capability  - List capability test targets")
    print("  ci-targets --invariant   - List invariant test targets")
    print("  ci-targets --mutation    - List mutation targets")
    print("  ci-targets --all         - List all targets")
    print()
    print("For now, use the existing scripts directly:")
    print("  .github/scripts/run_fast_checks.sh")
    print("  .github/scripts/run_contract_tests.sh")
    print("  .github/scripts/run_mutation_selective.sh")


def main() -> int:
    """Main entry point for the verification CLI."""
    if len(sys.argv) <= 1:
        print_roadmap()
        return 0
    
    command = sys.argv[1]
    remaining_args = sys.argv[2:]
    
    if command == "ci-targets":
        return delegate_to_ci_targets(remaining_args)
    
    elif command == "verify":
        print("Verification CLI — Program 3 (not yet implemented)")
        print("For now, use the existing scripts directly:")
        print("  .github/scripts/run_fast_checks.sh")
        print("  .github/scripts/run_contract_tests.sh")
        print("  .github/scripts/run_mutation_selective.sh")
        return 0
    
    elif command in ("--help", "-h", "help"):
        print_roadmap()
        return 0
    
    else:
        print(f"Unknown command: {command}")
        print("Run with --help for available commands")
        return 1


if __name__ == "__main__":
    sys.exit(main())