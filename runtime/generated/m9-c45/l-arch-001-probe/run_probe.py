#!/usr/bin/env python3
# runtime/generated/m9-c45/l-arch-001-probe/run_probe.py
#
# M9-C45 L-ARCH-001 — Drive mutmut 3.7.0 against each Python 3.10+ / 3.11+ /
# 3.12+ syntax probe, capturing the mutant population produced per feature.
#
# Design:
#   - Each probe is a flat top-level module in backend/tests/mutation_infra/
#     python_312_probes/ — mutmut trampoline accepts top-level names only.
#   - For each feature, we swap pyproject.toml [tool.mutmut] source_paths and
#     runner to the feature's test, invoke mutmut run --max-children 1, then
#     read the .mutmut-cache population. Result: mutants_generated per module.
#   - The "control" probe uses pure 3.9 syntax — its mutant count is the
#     baseline we compare against.
#
# Output: runtime/generated/m9-c45/l-arch-001-probe/results.json

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
PROBE_DIR = REPO_ROOT / "backend" / "tests" / "mutation_infra" / "python_312_probes"
MUTMUT = REPO_ROOT / ".venv" / "bin" / "mutmut"
RESULTS_PATH = (
    REPO_ROOT / "runtime" / "generated" / "m9-c45" / "l-arch-001-probe" / "results.json"
)

PROBES = [
    {
        "id": "control",
        "module": "control_probe",
        "test": "test_control_probe.py",
        "python_version": "3.9-style",
        "syntax_feature": "if/elif/else + typing.Optional via str | None (PEP 604)",
    },
    {
        "id": "pep604_union",
        "module": "pep604_union",
        "test": "test_pep604_union.py",
        "python_version": "3.10+",
        "syntax_feature": "PEP 604 X | Y union syntax",
    },
    {
        "id": "pep634_match",
        "module": "pep634_match",
        "test": "test_pep634_match.py",
        "python_version": "3.10+",
        "syntax_feature": "PEP 634 structural pattern matching (match/case)",
    },
    {
        "id": "pep654_exception_groups",
        "module": "pep654_exception_groups",
        "test": "test_pep654_exception_groups.py",
        "python_version": "3.11+",
        "syntax_feature": "PEP 654 ExceptionGroup / except*",
    },
    {
        "id": "pep695_type_params",
        "module": "pep695_type_params",
        "test": "test_pep695_type_params.py",
        "python_version": "3.12+",
        "syntax_feature": "PEP 695 generic class/function (class Box[T]: / def first[T](...))",
    },
]


def swap_pyproject(module: str, test: str) -> Path:
    """Write a per-probe pyproject.toml and return its path."""
    pyproject = PROBE_DIR / "pyproject.toml"
    backup = PROBE_DIR / "pyproject.toml.bak"
    if not backup.exists():
        shutil.copy2(pyproject, backup)
    content = (
        "[tool.mutmut]\n"
        f'source_paths = ["{module}.py"]\n'
        f'runner = "python3 -m pytest -x -q {test}"\n'
        "no_progress = true\n"
    )
    pyproject.write_text(content)
    return pyproject


def restore_pyproject() -> None:
    backup = PROBE_DIR / "pyproject.toml.bak"
    if backup.exists():
        shutil.copy2(backup, PROBE_DIR / "pyproject.toml")
        backup.unlink()


def run_mutmut_for_probe(module: str, test: str, timeout: int = 180) -> dict:
    """Run mutmut for one probe; return dict with mutants_generated + status."""
    swap_pyproject(module, test)
    try:
        # Clear stale cache so each probe gets a fresh population count.
        cache_dir = PROBE_DIR / "mutants"
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
        env = os.environ.copy()
        env["PATH"] = f"{REPO_ROOT}/.venv/bin:{env.get('PATH', '')}"
        proc = subprocess.run(
            [str(MUTMUT), "run"],
            cwd=PROBE_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        # Count mutants: mutmut 3.7.0 writes <module>.py.meta with an
        # `exit_code_by_key` mapping; length = mutant count for that module.
        meta_path = cache_dir / f"{module}.py.meta"
        mutants_count = 0
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text())
                mutants_count = len(meta.get("exit_code_by_key", {}))
            except Exception as exc:
                mutants_count = -1
                print(f"  WARN: cache parse failed: {exc}", file=sys.stderr)
        return {
            "mutmut_exit_code": proc.returncode,
            "mutants_generated": mutants_count,
            "stdout_tail": proc.stdout[-400:] if proc.stdout else "",
            "stderr_tail": proc.stderr[-400:] if proc.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {
            "mutmut_exit_code": -1,
            "mutants_generated": 0,
            "error": "timeout",
            "timeout_seconds": timeout,
        }
    finally:
        restore_pyproject()


def main() -> int:
    if not MUTMUT.exists():
        print(f"mutmut not found at {MUTMUT}", file=sys.stderr)
        return 1
    results = []
    for probe in PROBES:
        print(f"=== {probe['id']} ===", file=sys.stderr)
        outcome = run_mutmut_for_probe(probe["module"], probe["test"])
        outcome.update(probe)
        results.append(outcome)
        print(
            f"  mutants_generated={outcome['mutants_generated']} "
            f"exit={outcome['mutmut_exit_code']}",
            file=sys.stderr,
        )
    payload = {
        "schema": "m9-c45-l-arch-001-probe/v1",
        "objective": "Quantify mutmut 3.7.0 mutation population for Python 3.10+/3.11+/3.12+ syntax features.",
        "mutmut_binary": str(MUTMUT),
        "mutmut_version_expected": "3.7.0",
        "probe_dir": str(PROBE_DIR),
        "probes": results,
    }
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(payload, indent=2))
    print(f"wrote {RESULTS_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())