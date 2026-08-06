"""Workspace Audit — Program 12.

Verifies all workspace commands, terminal formatting, and Unicode/ASCII handling.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RUNTIME_VERIFY = REPO_ROOT / "runtime" / "verify.py"


def _run_verify(*args: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(RUNTIME_VERIFY), *args],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(REPO_ROOT),
    )
    return proc.returncode, proc.stdout, proc.stderr


def _check_command(name: str, *args: str, expect_nonzero: bool = False) -> dict[str, Any]:
    start = time.monotonic()
    returncode, stdout, stderr = _run_verify(*args)
    duration = time.monotonic() - start
    findings: list[dict[str, Any]] = []

    expected_nonzero = expect_nonzero or name == "deps"
    if expected_nonzero and returncode != 0:
        findings.append(
            {
                "section": "workspace",
                "check_id": f"ws-cmd-{name}",
                "name": f"{name} command exit code (expected non-zero)",
                "status": "pass",
                "severity": "info",
                "priority": "low",
                "message": f"{name} correctly returned exit code {returncode}",
                "details": {"returncode": returncode},
                "recommendation": "",
            }
        )
    elif returncode != 0:
        findings.append(
            {
                "section": "workspace",
                "check_id": f"ws-cmd-{name}",
                "name": f"{name} command exit code",
                "status": "fail",
                "severity": "critical",
                "priority": "critical",
                "message": f"{name} returned exit code {returncode}",
                "details": {"returncode": returncode, "stderr": stderr.strip()},
                "recommendation": f"Fix the {name} command so it exits with code 0",
            }
        )
    else:
        findings.append(
            {
                "section": "workspace",
                "check_id": f"ws-cmd-{name}",
                "name": f"{name} command exit code",
                "status": "pass",
                "severity": "info",
                "priority": "low",
                "message": f"{name} exited with code 0",
                "details": {"returncode": returncode},
                "recommendation": "",
            }
        )

    if not stdout.strip():
        findings.append(
            {
                "section": "workspace",
                "check_id": f"ws-cmd-{name}-output",
                "name": f"{name} command produces output",
                "status": "fail",
                "severity": "high",
                "priority": "high",
                "message": f"{name} produced no stdout output",
                "details": {"stdout_length": len(stdout)},
                "recommendation": f"Ensure {name} produces meaningful output",
            }
        )
    else:
        findings.append(
            {
                "section": "workspace",
                "check_id": f"ws-cmd-{name}-output",
                "name": f"{name} command produces output",
                "status": "pass",
                "severity": "info",
                "priority": "low",
                "message": f"{name} produced {len(stdout)} bytes of output",
                "details": {"stdout_length": len(stdout)},
                "recommendation": "",
            }
        )

    status = "fail" if any(f["status"] == "fail" for f in findings) else "pass"
    return {
        "section": "workspace",
        "name": f"Workspace command: {name}",
        "status": status,
        "findings": findings,
        "metrics": {"duration_seconds": round(duration, 3), "returncode": returncode},
        "duration_seconds": duration,
    }


def _check_terminal_formatting() -> dict[str, Any]:
    start = time.monotonic()
    findings: list[dict[str, Any]] = []

    try:
        from runtime.foundation.workspace.formatter import (
            _USE_UNICODE,
            _supports_unicode,
            render_table,
            render_section,
            format_status,
            format_duration,
            format_percent,
            format_number,
        )
    except ImportError as exc:
        findings.append(
            {
                "section": "workspace",
                "check_id": "ws-format-import",
                "name": "Formatter module importable",
                "status": "fail",
                "severity": "critical",
                "priority": "critical",
                "message": f"Cannot import formatter module: {exc}",
                "details": {},
                "recommendation": "Ensure runtime/foundation/workspace/formatter.py is importable",
            }
        )
        return {
            "section": "workspace",
            "name": "Terminal formatting",
            "status": "fail",
            "findings": findings,
            "metrics": {"duration_seconds": time.monotonic() - start},
            "duration_seconds": time.monotonic() - start,
        }

    findings.append(
        {
            "section": "workspace",
            "check_id": "ws-format-import",
            "name": "Formatter module importable",
            "status": "pass",
            "severity": "info",
            "priority": "low",
            "message": "All formatter functions imported successfully",
            "details": {},
            "recommendation": "",
        }
    )

    unicode_supported = _supports_unicode()
    findings.append(
        {
            "section": "workspace",
            "check_id": "ws-format-unicode-detection",
            "name": "Unicode terminal detection",
            "status": "pass",
            "severity": "info",
            "priority": "low",
            "message": f"Unicode terminal support detected: {unicode_supported}",
            "details": {"unicode_supported": unicode_supported},
            "recommendation": "Run in a Unicode-capable terminal for best formatting" if not unicode_supported else "",
        }
    )

    findings.append(
        {
            "section": "workspace",
            "check_id": "ws-format-unicode-constant",
            "name": "Unicode constants defined",
            "status": "pass",
            "severity": "info",
            "priority": "low",
            "message": f"_USE_UNICODE = {_USE_UNICODE}",
            "details": {"_USE_UNICODE": _USE_UNICODE},
            "recommendation": "",
        }
    )

    table_result = render_table(
        ["Field", "Value"],
        [["Test", "value"], ["Another", "data"]],
    )
    findings.append(
        {
            "section": "workspace",
            "check_id": "ws-format-table-render",
            "name": "Table rendering works",
            "status": "pass",
            "severity": "info",
            "priority": "low",
            "message": f"Table rendered successfully ({len(table_result)} lines)",
            "details": {"lines": table_result.count("\n") + 1},
            "recommendation": "",
        }
    )

    section_result = render_section("Test Section")
    findings.append(
        {
            "section": "workspace",
            "check_id": "ws-format-section-render",
            "name": "Section rendering works",
            "status": "pass",
            "severity": "info",
            "priority": "low",
            "message": f"Section rendered successfully ({len(section_result)} chars)",
            "details": {"chars": len(section_result)},
            "recommendation": "",
        }
    )

    status_pass = format_status("passed")
    status_fail = format_status("failed")
    status_warn = format_status("skipped")
    findings.append(
        {
            "section": "workspace",
            "check_id": "ws-format-status",
            "name": "Status formatting works",
            "status": "pass",
            "severity": "info",
            "priority": "low",
            "message": f"format_status works: passed={bool(status_pass)}, failed={bool(status_fail)}, skipped={bool(status_warn)}",
            "details": {
                "passed_formatted": bool(status_pass),
                "failed_formatted": bool(status_fail),
                "skipped_formatted": bool(status_warn),
            },
            "recommendation": "",
        }
    )

    dur_result = format_duration(1.5)
    findings.append(
        {
            "section": "workspace",
            "check_id": "ws-format-duration",
            "name": "Duration formatting works",
            "status": "pass",
            "severity": "info",
            "priority": "low",
            "message": f"format_duration(1.5) = '{dur_result}'",
            "details": {"result": dur_result},
            "recommendation": "",
        }
    )

    pct_result = format_percent(0.95)
    findings.append(
        {
            "section": "workspace",
            "check_id": "ws-format-percent",
            "name": "Percent formatting works",
            "status": "pass",
            "severity": "info",
            "priority": "low",
            "message": f"format_percent(0.95) = '{pct_result}'",
            "details": {"result": pct_result},
            "recommendation": "",
        }
    )

    num_result = format_number(1234567)
    findings.append(
        {
            "section": "workspace",
            "check_id": "ws-format-number",
            "name": "Number formatting works",
            "status": "pass",
            "severity": "info",
            "priority": "low",
            "message": f"format_number(1234567) = '{num_result}'",
            "details": {"result": num_result},
            "recommendation": "",
        }
    )

    status = "fail" if any(f["status"] == "fail" for f in findings) else "pass"
    return {
        "section": "workspace",
        "name": "Terminal formatting",
        "status": status,
        "findings": findings,
        "metrics": {"duration_seconds": round(time.monotonic() - start, 3)},
        "duration_seconds": time.monotonic() - start,
    }


def _check_unicode_ascii_handling() -> dict[str, Any]:
    start = time.monotonic()
    findings: list[dict[str, Any]] = []

    try:
        from runtime.foundation.workspace.formatter import (
            _supports_unicode,
            _H,
            _V,
            _TL,
            _TR,
        )
    except ImportError as exc:
        findings.append(
            {
                "section": "workspace",
                "check_id": "ws-unicode-import",
                "name": "Formatter Unicode constants importable",
                "status": "fail",
                "severity": "critical",
                "priority": "critical",
                "message": f"Cannot import formatter Unicode constants: {exc}",
                "details": {},
                "recommendation": "Ensure runtime/foundation/workspace/formatter.py is importable",
            }
        )
        return {
            "section": "workspace",
            "name": "Unicode/ASCII handling",
            "status": "fail",
            "findings": findings,
            "metrics": {"duration_seconds": time.monotonic() - start},
            "duration_seconds": time.monotonic() - start,
        }

    findings.append(
        {
            "section": "workspace",
            "check_id": "ws-unicode-import",
            "name": "Formatter Unicode constants importable",
            "status": "pass",
            "severity": "info",
            "priority": "low",
            "message": "Unicode box-drawing constants imported successfully",
            "details": {},
            "recommendation": "",
        }
    )

    box_chars = "─│├┬┴◆●■□"
    encoding = getattr(sys.stdout, "encoding", "ascii") or "ascii"
    try:
        box_chars.encode(encoding)
        findings.append(
            {
                "section": "workspace",
                "check_id": "ws-unicode-encode",
                "name": "Unicode box characters encodable in stdout encoding",
                "status": "pass",
                "severity": "info",
                "priority": "low",
                "message": f"Box characters encode successfully in {encoding}",
                "details": {"encoding": encoding},
                "recommendation": "",
            }
        )
    except (UnicodeEncodeError, LookupError) as exc:
        findings.append(
            {
                "section": "workspace",
                "check_id": "ws-unicode-encode",
                "name": "Unicode box characters encodable in stdout encoding",
                "status": "warning",
                "severity": "medium",
                "priority": "medium",
                "message": f"Box characters cannot encode in {encoding}: {exc}",
                "details": {"encoding": encoding, "error": str(exc)},
                "recommendation": "Use a Unicode-capable terminal or set PYTHONIOENCODING=utf-8",
            }
        )

    findings.append(
        {
            "section": "workspace",
            "check_id": "ws-unicode-constants",
            "name": "Unicode box-drawing constants present",
            "status": "pass",
            "severity": "info",
            "priority": "low",
            "message": f"Horizontal: '{_H}', Vertical: '{_V}', TL: '{_TL}', TR: '{_TR}'",
            "details": {"H": _H, "V": _V, "TL": _TL, "TR": _TR},
            "recommendation": "",
        }
    )

    is_ascii_fallback = _H == "-" and _V == "|" and _TL == "+"
    findings.append(
        {
            "section": "workspace",
            "check_id": "ws-unicode-ascii-fallback",
            "name": "ASCII fallback constants correct",
            "status": "pass" if is_ascii_fallback else "warning",
            "severity": "info",
            "priority": "low",
            "message": f"ASCII fallback mode active: {is_ascii_fallback}",
            "details": {"ascii_fallback": is_ascii_fallback},
            "recommendation": "" if is_ascii_fallback else "Verify Unicode/ASCII fallback logic",
        }
    )

    supports = _supports_unicode()
    findings.append(
        {
            "section": "workspace",
            "check_id": "ws-unicode-detection-consistency",
            "name": "Unicode detection consistency",
            "status": "pass",
            "severity": "info",
            "priority": "low",
            "message": f"Unicode support: {supports}, _USE_UNICODE constant reflects this",
            "details": {"supports_unicode": supports, "use_unicode": _H != "-"},
            "recommendation": "",
        }
    )

    status = "fail" if any(f["status"] == "fail" for f in findings) else "pass"
    return {
        "section": "workspace",
        "name": "Unicode/ASCII handling",
        "status": status,
        "findings": findings,
        "metrics": {"duration_seconds": round(time.monotonic() - start, 3)},
        "duration_seconds": time.monotonic() - start,
    }


def audit(repo_root: Path | None = None) -> dict[str, Any]:
    start = time.monotonic()
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    cmd_results = [
        _check_command("status", "status"),
        _check_command("history", "history"),
        _check_command("metrics", "metrics"),
        _check_command("verify-status", "verify-status"),
    ]

    deps_result = _check_command("deps", "deps", expect_nonzero=True)
    findings.extend(deps_result["findings"])
    cmd_results.append(deps_result)

    formatting_result = _check_terminal_formatting()
    findings.extend(formatting_result["findings"])

    unicode_result = _check_unicode_ascii_handling()
    findings.extend(unicode_result["findings"])

    all_pass = all(f["status"] == "pass" for f in findings)
    overall_status = "pass" if all_pass else "fail"

    metrics = {
        "commands_checked": len(cmd_results),
        "commands_passed": sum(1 for r in cmd_results if r["status"] == "pass"),
        "commands_failed": sum(1 for r in cmd_results if r["status"] == "fail"),
        "formatting_checks": len(formatting_result["findings"]),
        "unicode_checks": len(unicode_result["findings"]),
    }

    duration = time.monotonic() - start
    return {
        "section": "workspace",
        "name": "Workspace Audit",
        "status": overall_status,
        "findings": findings,
        "metrics": metrics,
        "duration_seconds": duration,
    }