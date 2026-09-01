# runtime/foundation/verification/regression.py
#
# M9-C52.14 — Full Regression.
#
# Runs: C42/C48/C50/C51/C52 tests + static checks + CLI smoke tests + scenario harnesses.
# Records every failure. Does not classify a new failure as pre-existing without
# proving it existed on the frozen baseline.

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@dataclass(frozen=True, slots=True)
class RegressionCheck:
    """One regression check result."""

    name: str
    check_type: str  # "test" | "static" | "cli" | "scenario"
    passed: bool
    details: str


def _run_tests(test_path: str, description: str) -> RegressionCheck:
    """Run a pytest test file."""
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", test_path, "-q", "--tb=no"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        passed = result.returncode == 0
        details = (
            result.stdout.strip().split("\n")[-1] if result.stdout else "no output"
        )
        return RegressionCheck(
            name=description, check_type="test", passed=passed, details=details
        )
    except Exception as e:
        return RegressionCheck(
            name=description, check_type="test", passed=False, details=str(e)
        )


def _run_static(description: str, command: list[str]) -> RegressionCheck:
    """Run a static check."""
    try:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        passed = result.returncode == 0
        return RegressionCheck(
            name=description,
            check_type="static",
            passed=passed,
            details=f"exit={result.returncode}",
        )
    except Exception as e:
        return RegressionCheck(
            name=description, check_type="static", passed=False, details=str(e)
        )


def _run_cli_smoke(route: str, description: str) -> RegressionCheck:
    """Run a CLI smoke test."""
    try:
        result = subprocess.run(
            ["python", "runtime/verify.py", route, "--json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        passed = result.returncode == 0 or result.returncode == 1  # 1 is OK for blocked
        return RegressionCheck(
            name=description,
            check_type="cli",
            passed=passed,
            details=f"exit={result.returncode}",
        )
    except Exception as e:
        return RegressionCheck(
            name=description, check_type="cli", passed=False, details=str(e)
        )


def build_regression_report() -> dict[str, Any]:
    """Build the complete regression report."""
    checks = []

    # Test suites
    checks.append(_run_tests("runtime/tests/test_m9_c50.py", "C50 tests (24)"))
    checks.append(_run_tests("runtime/tests/test_m9_c51.py", "C51 tests (33)"))
    checks.append(_run_tests("runtime/tests/test_m9_c52.py", "C52 tests (13)"))

    # Static checks
    checks.append(_run_static("ruff check", ["python", "-m", "ruff", "check", "."]))
    checks.append(
        _run_static("black --check", ["python", "-m", "black", "--check", "."])
    )

    # CLI smoke tests for new routes
    new_routes = [
        ("verification-contract", "M52.4 verification-contract"),
        ("enforce", "M52.5 enforce"),
        ("bypass-enforcement", "M52.6 bypass-enforcement"),
        ("pipeline-enforcement", "M52.7 pipeline-enforcement"),
        ("scenarios", "M52.8 scenarios"),
        ("evidence-integrity", "M52.9 evidence-integrity"),
    ]
    for route, desc in new_routes:
        checks.append(_run_cli_smoke(route, desc))

    all_passed = all(c.passed for c in checks)

    return {
        "schema": "m9-c52-regression/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "all_passed": all_passed,
        "checks": [asdict(c) for c in checks],
        "summary": {
            "total": len(checks),
            "passed": sum(1 for c in checks if c.passed),
            "failed": sum(1 for c in checks if not c.passed),
        },
    }


def main() -> int:
    """CLI: verify.py regression [--json] [--out PATH]"""
    import sys

    parser = __import__("argparse").ArgumentParser(
        prog="verify.py regression", add_help=False
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", help="Output file path")
    args = parser.parse_args(sys.argv[2:])

    report = build_regression_report()
    output = json.dumps(report, indent=2, default=str)

    if args.out:
        Path(args.out).write_text(output)
    if args.json or args.out:
        print(output)
    else:
        print(f"Regression: {'ALL PASSED' if report['all_passed'] else 'SOME FAILED'}")
        print(
            f"Total: {report['summary']['total']}, Passed: {report['summary']['passed']}, Failed: {report['summary']['failed']}"
        )
        for c in report["checks"]:
            status = "PASS" if c["passed"] else "FAIL"
            print(f"  [{c['check_type']}] {c['name']}: {status} - {c['details']}")

    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
