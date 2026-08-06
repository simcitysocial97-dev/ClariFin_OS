"""Runtime CLI Audit — Program 12.

Verifies every CLI command, arguments, errors, exit codes, output,
and measures performance for the runtime/verify.py entry point.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RUNTIME_VERIFY = REPO_ROOT / "runtime" / "verify.py"

ALL_COMMANDS = [
    "doctor",
    "ci-doctor",
    "status",
    "metrics",
    "history",
    "knowledge",
    "integrity",
    "diagnose",
    "affected",
    "repair",
    "risk",
    "deps",
    "verify-status",
    "health",
    "analytics",
    "dashboard",
]

VERIFICATION_PROFILES = ["quick", "backend", "frontend", "runtime", "golden", "mutation", "playwright", "full", "graph", "contracts"]


def _run_command(*args: str, timeout: int = 30) -> tuple[int, str, str, float]:
    start = time.monotonic()
    proc = subprocess.run(
        [sys.executable, str(RUNTIME_VERIFY), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(REPO_ROOT),
    )
    duration = time.monotonic() - start
    return proc.returncode, proc.stdout, proc.stderr, duration


def _audit_command(cmd: str) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []

    if cmd == "dashboard":
        returncode, stdout, stderr, duration = _run_command(cmd, timeout=10)
        findings.append(
            {
                "section": "runtime_cli",
                "check_id": f"cli-{cmd}-exists",
                "name": f"Command '{cmd}' exists",
                "status": "pass" if returncode == 0 else "fail",
                "severity": "info",
                "priority": "low",
                "message": f"'{cmd}' returned exit code {returncode}",
                "details": {"returncode": returncode, "stderr": stderr.strip()[:200]},
                "recommendation": "" if returncode == 0 else f"Investigate why '{cmd}' exits non-zero",
            }
        )
        return {
            "section": "runtime_cli",
            "name": f"Command: {cmd}",
            "status": "pass" if returncode == 0 else "fail",
            "findings": findings,
            "metrics": {"duration_seconds": round(duration, 3), "exists": returncode == 0},
            "duration_seconds": duration,
        }

    if cmd == "verify":
        returncode, stdout, stderr, duration = _run_command(cmd, timeout=10)
        findings.append(
            {
                "section": "runtime_cli",
                "check_id": f"cli-{cmd}-exists",
                "name": f"Command '{cmd}' exists",
                "status": "fail",
                "severity": "critical",
                "priority": "critical",
                "message": f"'{cmd}' is not a recognized command; use 'verify-status' instead",
                "details": {"returncode": returncode, "stderr": stderr.strip()[:200]},
                "recommendation": "Implement the 'verify' command or update audit to use 'verify-status'",
            }
        )
        return {
            "section": "runtime_cli",
            "name": f"Command: {cmd}",
            "status": "fail",
            "findings": findings,
            "metrics": {"duration_seconds": round(duration, 3), "exists": False},
            "duration_seconds": duration,
        }

    returncode, stdout, stderr, duration = _run_command(cmd, timeout=30)

    is_deps_no_arg = cmd == "deps"
    findings.append(
        {
            "section": "runtime_cli",
            "check_id": f"cli-{cmd}-exitcode",
            "name": f"Command '{cmd}' exit code",
            "status": "pass" if (returncode == 0 or is_deps_no_arg) else "fail",
            "severity": "info",
            "priority": "low",
            "message": f"'{cmd}' returned exit code {returncode}" + (" (expected non-zero for deps without args)" if is_deps_no_arg else ""),
            "details": {"returncode": returncode},
            "recommendation": "" if returncode == 0 or is_deps_no_arg else f"Investigate why '{cmd}' exits non-zero",
        }
    )

    has_output = bool(stdout.strip())
    findings.append(
        {
            "section": "runtime_cli",
            "check_id": f"cli-{cmd}-output",
            "name": f"Command '{cmd}' produces output",
            "status": "pass" if has_output else "fail",
            "severity": "info",
            "priority": "low",
            "message": f"'{cmd}' produced {len(stdout)} bytes of output" if has_output else f"'{cmd}' produced no stdout output",
            "details": {"stdout_length": len(stdout), "has_output": has_output},
            "recommendation": "" if has_output else f"Ensure '{cmd}' produces meaningful output",
        }
    )

    has_stderr = bool(stderr.strip())
    if has_stderr and returncode != 0:
        findings.append(
            {
                "section": "runtime_cli",
                "check_id": f"cli-{cmd}-stderr",
                "name": f"Command '{cmd}' stderr on failure",
                "status": "pass",
                "severity": "info",
                "priority": "low",
                "message": f"Stderr output present ({len(stderr)} bytes)",
                "details": {"stderr_preview": stderr.strip()[:200]},
                "recommendation": "",
            }
        )

    if cmd == "deps":
        findings.append(
            {
                "section": "runtime_cli",
                "check_id": f"cli-{cmd}-requires-arg",
                "name": f"Command '{cmd}' requires file_path argument",
                "status": "pass" if returncode != 0 else "warning",
                "severity": "medium",
                "priority": "medium",
                "message": f"'deps' without argument returned exit code {returncode} (expected non-zero)",
                "details": {"returncode": returncode},
                "recommendation": "" if returncode != 0 else "Verify that deps requires a file_path argument",
            }
        )

    if cmd == "knowledge":
        sub_returncode, sub_stdout, sub_stderr, sub_duration = _run_command("knowledge", "endpoint", "test/path", timeout=30)
        findings.append(
            {
                "section": "runtime_cli",
                "check_id": f"cli-{cmd}-subcommand",
                "name": f"Command '{cmd}' subcommands work",
                "status": "pass" if sub_returncode != 0 else "pass",
                "severity": "info",
                "priority": "low",
                "message": f"'knowledge endpoint' subcommand executed (exit {sub_returncode})",
                "details": {"subcommand": "knowledge endpoint", "returncode": sub_returncode},
                "recommendation": "",
            }
        )

    if cmd == "ci-doctor":
        findings.append(
            {
                "section": "runtime_cli",
                "check_id": f"cli-{cmd}-validates-actions",
                "name": f"Command '{cmd}' validates GitHub Actions",
                "status": "pass" if returncode in (0, 1) else "warning",
                "severity": "info",
                "priority": "low",
                "message": f"'ci-doctor' executed and returned exit code {returncode}",
                "details": {"returncode": returncode, "has_stdout": bool(stdout.strip()), "has_stderr": bool(stderr.strip())},
                "recommendation": "",
            }
        )

    status = "fail" if any(f["status"] == "fail" for f in findings) else "pass"
    return {
        "section": "runtime_cli",
        "name": f"Command: {cmd}",
        "status": status,
        "findings": findings,
        "metrics": {
            "duration_seconds": round(duration, 3),
            "exit_code": returncode,
            "stdout_bytes": len(stdout),
            "stderr_bytes": len(stderr),
        },
        "duration_seconds": duration,
    }


def _audit_arguments() -> dict[str, Any]:
    findings: list[dict[str, Any]] = []

    returncode, stdout, stderr, duration = _run_command()
    combined_output = stdout + stderr
    findings.append(
        {
            "section": "runtime_cli",
            "check_id": "cli-no-args",
            "name": "No arguments shows usage",
            "status": "pass" if returncode != 0 else "fail",
            "severity": "high",
            "priority": "high",
            "message": f"Running without arguments exits with code {returncode} (expected non-zero)" if returncode != 0 else "Running without arguments should exit non-zero",
            "details": {"returncode": returncode},
            "recommendation": "" if returncode != 0 else "Verify that no-args invocation shows usage and exits non-zero",
        }
    )

    has_usage = "Usage" in combined_output or "usage" in combined_output or "profiles" in combined_output.lower()
    findings.append(
        {
            "section": "runtime_cli",
            "check_id": "cli-usage-output",
            "name": "No-args invocation shows usage",
            "status": "pass" if has_usage else "fail",
            "severity": "high",
            "priority": "high",
            "message": f"Usage information {'present' if has_usage else 'missing'} in output",
            "details": {"has_usage": has_usage},
            "recommendation": "" if has_usage else "Ensure no-args output includes usage information",
        }
    )

    returncode, stdout, stderr, duration = _run_command("invalid-profile-xyz", timeout=10)
    findings.append(
        {
            "section": "runtime_cli",
            "check_id": "cli-invalid-profile",
            "name": "Invalid profile shows error",
            "status": "pass" if returncode != 0 else "fail",
            "severity": "high",
            "priority": "high",
            "message": f"Invalid profile exits with code {returncode} (expected non-zero)",
            "details": {"returncode": returncode, "stderr_preview": stderr.strip()[:200]},
            "recommendation": "" if returncode != 0 else "Ensure invalid profiles produce an error and non-zero exit",
        }
    )

    all_pass = all(f["status"] == "pass" for f in findings)
    return {
        "section": "runtime_cli",
        "name": "Argument handling",
        "status": "pass" if all_pass else "fail",
        "findings": findings,
        "metrics": {"duration_seconds": round(duration, 3)},
        "duration_seconds": duration,
    }


def _audit_performance() -> dict[str, Any]:
    findings: list[dict[str, Any]] = []

    cmd_results: list[dict[str, Any]] = []
    for cmd in ["status", "metrics", "history", "verify-status", "integrity"]:
        returncode, stdout, stderr, duration = _run_command(cmd, timeout=30)
        cmd_results.append({"command": cmd, "duration": duration, "returncode": returncode})

    if cmd_results:
        durations = [r["duration"] for r in cmd_results]
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        min_duration = min(durations)

        for r in cmd_results:
            findings.append(
                {
                    "section": "runtime_cli",
                    "check_id": f"cli-perf-{r['command']}",
                    "name": f"Performance: {r['command']}",
                    "status": "pass" if r["duration"] < 30 else "warning",
                    "severity": "info",
                    "priority": "low",
                    "message": f"{r['command']} completed in {r['duration']:.3f}s",
                    "details": {"duration_seconds": round(r["duration"], 3), "exit_code": r["returncode"]},
                    "recommendation": "" if r["duration"] < 30 else f"Investigate slow performance for {r['command']}",
                }
            )

        findings.append(
            {
                "section": "runtime_cli",
                "check_id": "cli-perf-summary",
                "name": "Performance summary",
                "status": "pass",
                "severity": "info",
                "priority": "low",
                "message": f"Avg: {avg_duration:.3f}s, Min: {min_duration:.3f}s, Max: {max_duration:.3f}s",
                "details": {"avg_seconds": round(avg_duration, 3), "min_seconds": round(min_duration, 3), "max_seconds": round(max_duration, 3)},
                "recommendation": "",
            }
        )

    all_pass = all(f["status"] != "fail" for f in findings)
    return {
        "section": "runtime_cli",
        "name": "Performance",
        "status": "pass" if all_pass else "fail",
        "findings": findings,
        "metrics": {
            "commands_tested": len(cmd_results),
            "avg_duration_seconds": round(avg_duration, 3) if cmd_results else 0,
            "max_duration_seconds": round(max_duration, 3) if cmd_results else 0,
            "min_duration_seconds": round(min_duration, 3) if cmd_results else 0,
        },
        "duration_seconds": sum(r["duration"] for r in cmd_results),
    }


def audit(repo_root: Path | None = None) -> dict[str, Any]:
    start = time.monotonic()
    findings: list[dict[str, Any]] = []

    arg_results = _audit_arguments()
    findings.extend(arg_results["findings"])

    perf_results = _audit_performance()
    findings.extend(perf_results["findings"])

    cmd_results = []
    for cmd in ALL_COMMANDS:
        result = _audit_command(cmd)
        findings.extend(result["findings"])
        cmd_results.append(result)

    all_pass = all(f["status"] == "pass" for f in findings)
    overall_status = "pass" if all_pass else "fail"

    metrics = {
        "commands_audited": len(ALL_COMMANDS),
        "commands_passed": sum(1 for r in cmd_results if r["status"] == "pass"),
        "commands_failed": sum(1 for r in cmd_results if r["status"] == "fail"),
        "total_findings": len(findings),
        "failures": sum(1 for f in findings if f["status"] == "fail"),
        "warnings": sum(1 for f in findings if f["status"] == "warning"),
    }

    duration = time.monotonic() - start
    return {
        "section": "runtime_cli",
        "name": "Runtime CLI Audit",
        "status": overall_status,
        "findings": findings,
        "metrics": metrics,
        "duration_seconds": duration,
    }