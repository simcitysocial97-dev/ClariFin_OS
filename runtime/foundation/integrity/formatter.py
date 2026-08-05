"""Professional terminal formatter — Program 10.

Renders Architectural Integrity reports as adaptive-width terminal
tables with Unicode support and plain-ASCII fallback.
"""

from __future__ import annotations

import sys
from typing import Any

from runtime.foundation.integrity.models import (
    IntegrityReport,
    Violation,
    ViolationSeverity,
)


def _supports_unicode() -> bool:
    if not hasattr(sys.stdout, "isatty"):
        return False
    if not sys.stdout.isatty():
        return False
    encoding = getattr(sys.stdout, "encoding", "ascii")
    if not encoding:
        return False
    try:
        "─│├┬┴◆●■□".encode(encoding)
        return True
    except (UnicodeEncodeError, LookupError):
        return False


_USE_UNICODE = _supports_unicode()

if _USE_UNICODE:
    _H = "─"
    _V = "│"
    _TL = "┌"
    _TR = "┐"
    _BL = "└"
    _BR = "┘"
    _TJ = "┬"
    _BJ = "┴"
    _LR = "├"
    _CR = "┤"
else:
    _H = "-"
    _V = "|"
    _TL = "+"
    _TR = "+"
    _BL = "+"
    _BR = "+"
    _TJ = "+"
    _BJ = "+"
    _LR = "+"
    _CR = "+"


def _color(code: int, text: str) -> str:
    if not _USE_UNICODE:
        return str(text)
    return f"\033[{code}m{text}\033[0m"


def _bold(text: str) -> str:
    return _color(1, text)


def _red(text: str) -> str:
    return _color(31, text)


def _yellow(text: str) -> str:
    return _color(33, text)


def _green(text: str) -> str:
    return _color(32, text)


def _cyan(text: str) -> str:
    return _color(36, text)


def _pad(text: str, width: int, align: str = "left") -> str:
    text = str(text)
    if align == "right":
        return text.rjust(width)
    return text.ljust(width)


def _truncate(text: str, width: int) -> str:
    text = str(text)
    if len(text) > width:
        return text[: width - 1] + "…"
    return text


def _severity_color(severity: ViolationSeverity) -> str:
    if severity == ViolationSeverity.CRITICAL:
        return _red(severity.value)
    if severity == ViolationSeverity.HIGH:
        return _yellow(severity.value)
    if severity == ViolationSeverity.MEDIUM:
        return _cyan(severity.value)
    return _green(severity.value)


def _status_color(passed: bool) -> str:
    if passed:
        return _green("PASS")
    return _red("FAIL")


def format_integrity_report(report: IntegrityReport) -> str:
    """Format an IntegrityReport as a professional terminal report."""
    lines: list[str] = []

    width = _terminal_width()

    # Header
    lines.append(_TL + _H * (width - 2) + _TR)
    title = "Architectural Integrity"
    lines.append(_V + _pad(title, width - 2) + _V)
    lines.append(_BL + _H * (width - 2) + _BR)
    lines.append("")

    # Summary box
    lines.append(_status_color(report.passed))
    lines.append("")

    summary_headers = ["Metric", "Value"]
    summary_rows = [
        ["Rules", str(report.rules_evaluated)],
        ["Violations", str(report.total_violations)],
        ["Critical", str(report.critical_count)],
        ["High", str(report.high_count)],
        ["Medium", str(report.medium_count)],
        ["Low", str(report.low_count)],
        ["Info", str(report.info_count)],
        ["Files Scanned", str(report.files_scanned)],
        ["Cross-Layer Entries", str(report.cross_layer_entries)],
        ["Graph Nodes", str(report.graph_nodes)],
        ["Graph Edges", str(report.graph_edges)],
    ]
    lines.append(format_table(summary_headers, summary_rows))
    lines.append("")

    # Violations detail
    if report.violations:
        lines.append(_bold("Violations"))
        lines.append("")

        for v in report.violations:
            lines.append(f"{_bold(v.rule_id)}  {_severity_color(v.severity)}")
            lines.append(f"  {v.file_path}")
            lines.append(f"  {v.description}")
            if v.details:
                lines.append(f"  Details: {v.details}")
            if v.suggested_action:
                lines.append(f"  {_cyan('Suggested:')} {v.suggested_action}")
            lines.append("")
    else:
        lines.append(_green("No violations detected."))
        lines.append("")

    # Footer
    lines.append(_TL + _H * (width - 2) + _TR)
    lines.append(
        _V
        + _pad(
            f"Scan completed at {report.timestamp[:19]} UTC",
            width - 2,
        )
        + _V
    )
    lines.append(_BL + _H * (width - 2) + _BR)

    return "\n".join(lines)


def format_violation_detail(violation: Violation) -> str:
    """Format a single violation as a compact detail block."""
    lines: list[str] = []
    lines.append(f"{_bold(violation.rule_id)}")
    lines.append(_severity_color(violation.severity))
    lines.append(violation.file_path)
    lines.append(violation.description)
    if violation.details:
        lines.append(f"Found: {violation.details}")
    if violation.suggested_action:
        lines.append(f"Expected: {violation.suggested_action}")
    return "\n".join(lines)


def _terminal_width() -> int:
    try:
        import shutil

        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def format_table(headers: list[str], rows: list[list[Any]]) -> str:
    """Render a simple adaptive-width table."""
    if not rows:
        return ""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            if idx < len(col_widths):
                col_widths[idx] = max(col_widths[idx], len(str(cell)))

    terminal_width = _terminal_width()
    total = sum(col_widths) + (len(col_widths) - 1) * 3 + 2
    if total > terminal_width and col_widths:
        overflow = total - terminal_width
        max_width = max(col_widths)
        if max_width > 10:
            reduce = min(overflow // len(col_widths) + 1, max_width - 10)
            col_widths = [max(10, w - reduce) for w in col_widths]

    header_line = (
        _TL + _H * (sum(col_widths) + (len(col_widths) - 1) * 3) + _TR
    )
    lines: list[str] = [header_line]

    header_cells = [
        _pad(_truncate(h, w), w) for h, w in zip(headers, col_widths)
    ]
    lines.append(_V + " " + " ".join(header_cells) + " " + _V)

    sep = (
        _LR + _H * (sum(col_widths) + (len(col_widths) - 1) * 3) + _CR
    )
    lines.append(sep)

    for row in rows:
        cells = [
            _pad(_truncate(str(c), w), w)
            for c, w in zip(row, col_widths)
        ]
        lines.append(_V + " " + " ".join(cells) + " " + _V)

    footer_line = (
        _BL + _H * (sum(col_widths) + (len(col_widths) - 1) * 3) + _BR
    )
    lines.append(footer_line)
    return "\n".join(lines)