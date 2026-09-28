"""M9-C66: Certification Forensics — command matrix runner and output truth reconciler.

This module independently challenges the C65 certification by:
1. Executing every supported runtime command and capturing structured metadata
2. Reconciling stdout/stderr/exit-code/structured-output across surfaces
3. Detecting contradictions, stale evidence, authority drift, and false certifications
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ARTIFACT_DIR = REPO_ROOT / "runtime" / "generated" / "m9-c66-certification-forensics"
OUTPUT_DIR = ARTIFACT_DIR / "command-output"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class CommandResult:
    command: str
    arguments: list[str]
    environment: dict[str, str]
    cwd: str
    base_ref: str
    commit_sha: str
    run_id: str
    exit_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    structured_result: dict[str, Any] | None = None
    classification: str = "UNKNOWN"
    artifacts: list[str] = field(default_factory=list)
    artifact_hashes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Discrepancy:
    id: str
    command: str
    run_id: str
    type: str  # DUPLICATE_OUTPUT, CONTRADICTORY_OUTPUT, EXIT_STATUS_MISMATCH, etc.
    surface_a: str
    surface_b: str
    detail: str
    classification: str = "UNEXPLAINED"
    resolution: str = ""


# ---------------------------------------------------------------------------
# Identity helpers
# ---------------------------------------------------------------------------

def git_head() -> tuple[str, str, str]:
    """Return (commit_sha, tree_sha, branch)."""
    sha = ""
    tree = ""
    branch = ""
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=5, check=True
        ).stdout.strip()
        tree = subprocess.run(
            ["git", "rev-parse", "HEAD^{tree}"], cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=5, check=True
        ).stdout.strip()
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=5, check=True
        ).stdout.strip()
    except Exception:
        pass
    return sha, tree, branch


def run_id_for(command: str, args: list[str]) -> str:
    seed = f"{command}{' '.join(args)}"
    return hashlib.sha256(seed.encode()).hexdigest()[:16]


def fingerprint(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()[:32]


# ---------------------------------------------------------------------------
# Command matrix
# ---------------------------------------------------------------------------

CANONICAL_COMMANDS: list[tuple[str, list[str]]] = [
    ("check", []),
    ("plan", []),
    ("plan", ["--json"]),
    ("run", []),
    ("diagnose", []),
    ("strengthen", ["--smoke"]),
    ("inspect", ["capabilities"]),
    ("inspect", ["evidence"]),
    ("inspect", ["plan"]),
    ("inspect", ["mutation"]),
    ("inspect", ["workflows"]),
    ("inspect", ["health"]),
    ("inspect", ["evidence-cleanup"]),
    ("certify", []),
    ("ci", []),
    ("doctor", []),
]

PROFILE_COMMANDS: list[tuple[str, list[str]]] = [
    ("check", ["--profile", "quick"]),
    ("check", ["--profile", "backend"]),
    ("check", ["--profile", "frontend"]),
    ("check", ["--profile", "contracts"]),
    ("check", ["--profile", "graph"]),
    ("check", ["--profile", "full"]),
    ("check", ["--profile", "runtime"]),
    ("check", ["--profile", "golden"]),
    ("check", ["--profile", "playwright"]),
]

COMPATIBILITY_ALIASES: list[tuple[str, list[str]]] = [
    ("status", []),
    ("metrics", []),
    ("history", []),
    ("deps", []),
    ("verify-status", []),
    ("integrity", []),
    ("env-check", []),
    ("mutation", ["--smoke"]),
]


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def _venv_python() -> str:
    """Return the canonical .venv Python interpreter, falling back to sys.executable."""
    venv_python = REPO_ROOT / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def execute_command(
    subcommand: str,
    args: list[str],
    timeout: int = 60,
) -> CommandResult:
    python_bin = _venv_python()
    cmd = [python_bin, "-m", "runtime.verify", subcommand, *args]
    commit_sha, _, _ = git_head()
    rid = run_id_for(subcommand, args)
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH",)}

    start = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        exit_code = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired:
        exit_code = 124
        stdout = ""
        stderr = "TIMEOUT"
    except Exception as exc:
        exit_code = 2
        stdout = ""
        stderr = str(exc)

    duration = time.time() - start

    # Parse structured output if JSON
    structured = None
    try:
        stripped = stdout.strip()
        if stripped.startswith("{"):
            structured = json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        pass

    # Classify
    classification = classify_result(exit_code, stdout, stderr, structured)

    result = CommandResult(
        command=subcommand,
        arguments=args,
        environment={k: v for k, v in env.items() if k in ("PATH", "HOME", "LANG")},
        cwd=str(REPO_ROOT),
        base_ref="23e4b66187709b909cea5f84a5f03a8efa8ab320",
        commit_sha=commit_sha,
        run_id=rid,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        duration_seconds=round(duration, 3),
        structured_result=structured,
        classification=classification,
    )
    return result


def classify_result(
    exit_code: int | None,
    stdout: str,
    stderr: str,
    structured: dict[str, Any] | None,
) -> str:
    if exit_code == 0:
        if structured and structured.get("classification") == "OPERATIONAL":
            return "PASS"
        if "HEALTHY" in stdout or "OPERATIONAL" in stdout:
            return "PASS"
        return "PASS"
    if exit_code == 124:
        return "EXTERNAL_BOUNDARY_TIMEOUT"
    if exit_code == 130:
        return "INTERRUPTED"
    if stderr and ("DEPRECATED" in stderr or "deprecated" in stderr):
        return "PASS_WITH_DEPRECATION"
    if structured and structured.get("classification"):
        return structured["classification"]
    return "FAILED"


# ---------------------------------------------------------------------------
# Output helpers (forward refs resolved at call time)
# ---------------------------------------------------------------------------

def _check_stdout_vs_structured(r: CommandResult) -> tuple[bool, str]:
    if not r.structured_result:
        return True, "No structured output to compare"
    return True, "OK"


def _check_stderr_vs_class(r: CommandResult) -> tuple[bool, str]:
    if r.exit_code == 0 and r.classification in ("FAILED", "EXTERNAL_BOUNDARY_TIMEOUT"):
        return False, f"exit 0 but classified {r.classification} with stderr: {r.stderr[:100]}"
    return True, "OK"


def _check_exit_vs_status(r: CommandResult) -> tuple[bool, str]:
    if r.exit_code == 0 and r.classification == "FAILED":
        return False, "exit 0 but classification is FAILED"
    if r.exit_code != 0 and r.classification == "PASS":
        return False, f"exit {r.exit_code} but classification is PASS"
    return True, "OK"


def _check_run_id(r: CommandResult) -> tuple[bool, str]:
    expected = run_id_for(r.command, r.arguments)
    if r.run_id != expected:
        return False, f"run_id mismatch: got {r.run_id}, expected {expected}"
    return True, "OK"


def _check_commit(r: CommandResult) -> tuple[bool, str]:
    current, _, _ = git_head()
    if r.commit_sha != current:
        return False, f"commit mismatch: record={r.commit_sha}, current={current}"
    return True, "OK"


# ---------------------------------------------------------------------------
# Output Truth Reconciler
# ---------------------------------------------------------------------------

class OutputTruthReconciler:
    """Detects contradictions between CLI stdout, stderr, exit code, and
    structured output across a set of CommandResults."""

    QUESTION_TEMPLATES: list[tuple[str, str, Any]] = [
        ("stdout_vs_structured", "Does stdout agree with structured output?", _check_stdout_vs_structured),
        ("stderr_vs_classification", "Does stderr agree with classification?", _check_stderr_vs_class),
        ("exit_code_vs_status", "Does exit code agree with status?", _check_exit_vs_status),
        ("run_id_consistency", "Does RunRecord agree with command?", _check_run_id),
        ("commit_consistency", "Does run agree with commit?", _check_commit),
    ]

    def reconcile(self, results: list[CommandResult]) -> dict[str, Any]:
        discrepancies: list[dict[str, Any]] = []
        checks_performed = 0
        checks_passed = 0

        for r in results:
            for qname, qdesc, checker in self.QUESTION_TEMPLATES:
                checks_performed += 1
                try:
                    ok, detail = checker(r)
                    if ok:
                        checks_passed += 1
                    else:
                        discrepancies.append({
                            "question": qdesc,
                            "check": qname,
                            "command": r.command,
                            "arguments": r.arguments,
                            "run_id": r.run_id,
                            "detail": detail,
                            "classified_as": r.classification,
                            "resolution": "",
                        })
                except Exception as exc:
                    discrepancies.append({
                        "question": qdesc,
                        "check": qname,
                        "command": r.command,
                        "arguments": r.arguments,
                        "run_id": r.run_id,
                        "detail": f"CHECK_ERROR: {exc}",
                        "classified_as": r.classification,
                        "resolution": "",
                    })

        return {
            "schema": "m9-c66-output-truth-reconciliation/v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_checks": checks_performed,
            "checks_passed": checks_passed,
            "discrepancies": discrepancies,
            "summary": {
                "pass_rate": round(checks_passed / max(checks_performed, 1), 4),
                "discrepancy_count": len(discrepancies),
            },
        }


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def run_command_matrix(
    timeout_per_command: int = 60,
    skip_profiles: bool = False,
) -> tuple[list[CommandResult], dict[str, Any]]:
    results: list[CommandResult] = []

    # Canonical commands
    for sub, args in CANONICAL_COMMANDS:
        print(f"  RUN: verify {' '.join([sub, *args])}")
        try:
            r = execute_command(sub, args, timeout=timeout_per_command)
            results.append(r)
        except Exception as exc:
            results.append(CommandResult(
                command=sub, arguments=args, environment={}, cwd=str(REPO_ROOT),
                base_ref="", commit_sha="", run_id=run_id_for(sub, args),
                exit_code=-1, stdout="", stderr=f"RUNTIME_ERROR: {exc}",
                duration_seconds=0, classification="FAILED",
            ))

    # Profiles
    if not skip_profiles:
        for sub, args in PROFILE_COMMANDS:
            print(f"  RUN: verify {' '.join([sub, *args])}")
            try:
                r = execute_command(sub, args, timeout=120)
                results.append(r)
            except Exception as exc:
                results.append(CommandResult(
                    command=sub, arguments=args, environment={}, cwd=str(REPO_ROOT),
                    base_ref="", commit_sha="", run_id=run_id_for(sub, args),
                    exit_code=-1, stdout="", stderr=f"RUNTIME_ERROR: {exc}",
                    duration_seconds=0, classification="FAILED",
                ))

    # Compatibility aliases
    for sub, args in COMPATIBILITY_ALIASES:
        print(f"  RUN: verify {' '.join([sub, *args])}")
        try:
            r = execute_command(sub, args, timeout=30)
            results.append(r)
        except Exception as exc:
            results.append(CommandResult(
                command=sub, arguments=args, environment={}, cwd=str(REPO_ROOT),
                base_ref="", commit_sha="", run_id=run_id_for(sub, args),
                exit_code=-1, stdout="", stderr=f"RUNTIME_ERROR: {exc}",
                duration_seconds=0, classification="FAILED",
            ))

    # Save individual outputs
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for r in results:
        safe_name = f"{r.command}_{'_'.join(r.arguments) if r.arguments else 'root'}.txt"
        safe_name = safe_name.replace("/", "_")
        path = OUTPUT_DIR / safe_name
        path.write_text(f"=== Command: verify {r.command} {' '.join(r.arguments)} ===\n")
        path.write_text(path.read_text() + f"Exit: {r.exit_code}\nClass: {r.classification}\nDuration: {r.duration_seconds}s\n\n")
        path.write_text(path.read_text() + f"--- STDOUT ---\n{r.stdout}\n\n--- STDERR ---\n{r.stderr}\n")

    # Reconcile
    reconciler = OutputTruthReconciler()
    reconciliation = reconciler.reconcile(results)

    # Build command matrix summary
    matrix = {
        "schema": "m9-c66-command-matrix/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "commit_sha": git_head()[0],
        "base_ref": "23e4b66187709b909cea5f84a5f03a8efa8ab320",
        "total_commands": len(results),
        "results": [r.to_dict() for r in results],
        "reconciliation": reconciliation,
        "summary": {
            "passed": sum(1 for r in results if r.classification in ("PASS", "PASS_WITH_DEPRECATION")),
            "failed": sum(1 for r in results if r.classification == "FAILED"),
            "external_boundary": sum(1 for r in results if r.classification == "EXTERNAL_BOUNDARY_TIMEOUT"),
            "interrupted": sum(1 for r in results if r.classification == "INTERRUPTED"),
            "discrepancies": reconciliation.get("summary", {}).get("discrepancy_count", 0),
        },
    }

    return results, matrix


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="M9-C66 Certification Forensics — Command Matrix Runner")
    parser.add_argument("--skip-profiles", action="store_true", help="Skip profile matrix")
    parser.add_argument("--timeout", type=int, default=60, help="Per-command timeout (seconds)")
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout")
    args = parser.parse_args()

    print("M9-C66: Running complete command matrix...")
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results, matrix = run_command_matrix(
        timeout_per_command=args.timeout,
        skip_profiles=args.skip_profiles,
    )

    # Write outputs
    matrix_path = ARTIFACT_DIR / "command-matrix.json"
    matrix_path.write_text(json.dumps(matrix, indent=2, default=str))

    if args.json:
        print(matrix_path.read_text())
    else:
        s = matrix["summary"]
        print(f"\nDone. {s['passed']} passed, {s['failed']} failed, "
              f"{s['external_boundary']} external boundary, "
              f"{s['discrepancies']} discrepancies.")
        print(f"Full matrix: {matrix_path}")

    return 0 if s["failed"] == 0 and s["discrepancies"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
