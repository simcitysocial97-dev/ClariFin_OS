# runtime/foundation/verification/configuration_authority.py
#
# M9-C51 — Canonical tool configuration authority (M51.7).
#
# Encodes which pyproject.toml is authoritative for each quality tool,
# preventing the common mistake of assuming backend/src is the repository-
# wide source scope for ruff/black/mypy.

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@dataclass(frozen=True, slots=True)
class ToolAuthority:
    """One tool's canonical configuration authority."""

    tool: str  # e.g. "ruff", "black", "mypy", "pytest"
    name: str
    canonical_command: str
    config_path: str  # repo-relative path to governing config
    config_scope: str  # "repo" | "backend" | "runtime"
    source_scope: str  # what the tool actually scans
    authoritative: bool = True
    notes: str = ""


_AUTHORITY_TABLE: tuple[ToolAuthority, ...] = (
    ToolAuthority(
        tool="ruff",
        name="Ruff Lint",
        canonical_command="python -m ruff check . --output-format=github",
        config_path="pyproject.toml [tool.ruff]",
        config_scope="repo",
        source_scope=".",
        notes=(
            "The repository-root pyproject.toml is authoritative for ruff. "
            "run_fast_checks.sh runs from backend/ but inherits root config."
        ),
    ),
    ToolAuthority(
        tool="black",
        name="Black Format",
        canonical_command="python -m black --check --diff .",
        config_path="pyproject.toml [tool.black]",
        config_scope="repo",
        source_scope=".",
        notes="Repository-root pyproject.toml is authoritative for black.",
    ),
    ToolAuthority(
        tool="mypy",
        name="Mypy Typecheck (two boundaries)",
        canonical_command=(
            "python -m mypy .  # repo scope;  python -m mypy src/  # backend strict scope"
        ),
        config_path="pyproject.toml [tool.mypy] AND backend/pyproject.toml [tool.mypy]",
        config_scope="dual",
        source_scope="., backend/src/",
        notes=(
            "Root mypy excludes backend/; backend has its own STRICT boundary. "
            "Do not conflate the two scopes."
        ),
    ),
    ToolAuthority(
        tool="pytest",
        name="Pytest",
        canonical_command="python -m pytest tests/unit/ -x -q  # backend;  python -m pytest runtime/tests/  # runtime",
        config_path="backend/pyproject.toml [tool.pytest.ini_options] AND pyproject.toml [tool.pytest.ini_options]",
        config_scope="dual",
        source_scope="backend/tests/, runtime/tests/",
        notes="Backend and runtime have separate pytest rootdirs.",
    ),
    ToolAuthority(
        tool="coverage",
        name="Coverage (C47 canonical)",
        canonical_command="python runtime/verify.py measurement coverage <scope>",
        config_path="backend/pyproject.toml [tool.coverage]",
        config_scope="backend",
        source_scope="backend/src/",
        notes="Canonical coverage path goes through verify.py; raw coverage run is non-canonical.",
    ),
    ToolAuthority(
        tool="mutation",
        name="Mutation Testing (C47)",
        canonical_command="python runtime/verify.py mutation [--smoke|--target <engine>]",
        config_path="backend/pyproject.toml [tool.mutmut]",
        config_scope="backend",
        source_scope="backend/src/",
        notes="Mutmut config is backend-scoped; full campaigns require human authorization.",
    ),
)


def get_configuration_authority() -> list[dict[str, Any]]:
    """Return the complete configuration authority table."""
    return [asdict(t) for t in _AUTHORITY_TABLE]


def validate_authority() -> tuple[bool, list[str]]:
    """Validate that all referenced config paths exist on disk."""
    issues: list[str] = []
    for t in _AUTHORITY_TABLE:
        # Split multi-config entries
        parts = t.config_path.split(" AND ")
        for part in parts:
            # Extract file path from "path [section]" format
            filepath = part.strip().split(" [")[0].strip()
            abs_path = REPO_ROOT / filepath
            if not abs_path.exists():
                issues.append(f"{t.tool}: config path {filepath!r} does not exist")
    return len(issues) == 0, issues


def cmd_config_authority(argv: list[str]) -> int:
    """verify.py config-authority — display canonical tool config authority."""
    import argparse

    parser = argparse.ArgumentParser(prog="verify.py config-authority", add_help=False)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args(argv)

    authority = get_configuration_authority()
    valid, issues = validate_authority()

    if args.validate:
        if issues:
            for i in issues:
                print(i, file=sys.stderr)
            return 1
        print("All configuration authorities validated successfully.")
        return 0

    if args.json:
        output = json.dumps(
            {"authority": authority, "valid": valid, "issues": issues}, indent=2
        )
    else:
        lines = ["CANONICAL CONFIGURATION AUTHORITY (M9-C51)", "=" * 50]
        for t in authority:
            lines.append(f"\n  {t['tool']} ({t['name']})")
            lines.append(f"    command:   {t['canonical_command']}")
            lines.append(f"    config:    {t['config_path']}")
            lines.append(f"    scope:     {t['source_scope']}")
            if t["notes"]:
                lines.append(f"    note:      {t['notes']}")
        output = "\n".join(lines)

    print(output)
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(cmd_config_authority(sys.argv[1:]))
