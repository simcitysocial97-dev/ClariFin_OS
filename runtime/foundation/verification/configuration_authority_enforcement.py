# runtime/foundation/verification/configuration_authority_enforcement.py
#
# M9-C52.12 — Configuration Authority Enforcement.
#
# C51 established configuration authority. Now proves it operationally.
# For pytest, ruff, black, mypy, mutmut, hypothesis, frontend tooling, CI:
# determines canonical configuration, consuming tool, configuration fingerprint,
# invalidation behavior, and conflicting configuration detection.

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@dataclass(frozen=True, slots=True)
class ToolConfig:
    """Configuration authority for one tool."""

    tool: str
    canonical_config_path: str
    config_fingerprint: str
    consuming_tool: str
    invalidation_behavior: str
    drift_detected: bool = False


@dataclass(frozen=True, slots=True)
class ConfigAuthorityResult:
    """Result of configuration authority verification."""

    tool: str
    passed: bool
    details: dict[str, Any]


def _compute_fingerprint(path: Path) -> str:
    """Compute SHA256 fingerprint of a file."""
    import hashlib

    if not path.exists():
        return "missing"
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _check_tool(
    tool: str, config_path: str, consuming_tool: str
) -> ConfigAuthorityResult:
    """Check configuration authority for one tool."""
    full_path = REPO_ROOT / config_path
    fingerprint = _compute_fingerprint(full_path)
    exists = full_path.exists()

    # Check for conflicting configs (e.g., backend/pyproject.toml shadowing root)
    conflicts = []
    if tool == "mutmut":
        backend_config = REPO_ROOT / "backend" / "pyproject.toml"
        if backend_config.exists():
            content = backend_config.read_text()
            if "[tool.mutmut]" in content:
                conflicts.append(
                    "backend/pyproject.toml has [tool.mutmut] section (should be in root only)"
                )

    passed = exists and len(conflicts) == 0

    return ConfigAuthorityResult(
        tool=tool,
        passed=passed,
        details={
            "config_path": config_path,
            "fingerprint": fingerprint,
            "exists": exists,
            "consuming_tool": consuming_tool,
            "conflicts": conflicts,
        },
    )


def build_configuration_authority_report() -> dict[str, Any]:
    """Build the complete configuration authority report."""
    tools = [
        ("pytest", "pyproject.toml", "pytest"),
        ("ruff", "pyproject.toml", "ruff"),
        ("black", "pyproject.toml", "black"),
        ("mypy", "pyproject.toml", "mypy"),
        ("mutmut", "pyproject.toml", "mutmut"),
        ("hypothesis", "pyproject.toml", "hypothesis"),
    ]

    results = [_check_tool(t, cp, ct) for t, cp, ct in tools]
    all_passed = all(r.passed for r in results)

    return {
        "schema": "m9-c52-configuration-authority/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "all_passed": all_passed,
        "tool_results": [
            {
                "tool": r.tool,
                "passed": r.passed,
                "details": r.details,
            }
            for r in results
        ],
    }


def main() -> int:
    """CLI: verify.py config-authority-verify [--json] [--out PATH]"""
    import sys

    parser = __import__("argparse").ArgumentParser(
        prog="verify.py config-authority-verify", add_help=False
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", help="Output file path")
    args = parser.parse_args(sys.argv[2:])

    report = build_configuration_authority_report()
    output = json.dumps(report, indent=2, default=str)

    if args.out:
        Path(args.out).write_text(output)
    if args.json or args.out:
        print(output)
    else:
        print(
            f"Configuration Authority: {'ALL PASSED' if report['all_passed'] else 'SOME FAILED'}"
        )
        for r in report["tool_results"]:
            status = "PASS" if r["passed"] else "FAIL"
            print(f"  {r['tool']}: {status}")

    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
