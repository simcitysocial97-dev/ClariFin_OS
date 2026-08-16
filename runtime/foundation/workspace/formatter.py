"""Professional terminal formatting — Program 9.

Adaptive width. Unicode tables when supported. Plain ASCII fallback.
No JSON printing.
"""

from __future__ import annotations

import sys
from typing import Any


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
    _X = "┼"
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
    _X = "+"


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


class Table:
    """Simple adaptive-width terminal table."""

    def __init__(self, headers: list[str], rows: list[list[Any]]) -> None:
        self.headers = [str(h) for h in headers]
        self.rows = [[str(c) for c in row] for row in rows]
        self.col_widths = [len(h) for h in self.headers]
        for row in self.rows:
            for idx, cell in enumerate(row):
                if idx < len(self.col_widths):
                    self.col_widths[idx] = max(self.col_widths[idx], len(cell))

        terminal_width = shutil_get_terminal_width()
        total = sum(self.col_widths) + (len(self.col_widths) - 1) * 3 + 2
        if total > terminal_width and self.col_widths:
            overflow = total - terminal_width
            max_width = max(self.col_widths)
            if max_width > 10:
                reduce = min(overflow // len(self.col_widths) + 1, max_width - 10)
                self.col_widths = [max(10, w - reduce) for w in self.col_widths]

    def render(self) -> str:
        lines: list[str] = []
        header_line = (
            f"{_TL}{_H * (sum(self.col_widths) + (len(self.col_widths) - 1) * 3)}{_TR}"
        )
        lines.append(header_line)

        header_cells = []
        for idx, h in enumerate(self.headers):
            header_cells.append(_pad(_truncate(h, self.col_widths[idx]), self.col_widths[idx]))
        lines.append(f"{_V} " + f" {_TJ} ".join(header_cells) + f" {_V}")

        separator = (
            f"{_LR}{_H * (sum(self.col_widths) + (len(self.col_widths) - 1) * 3)}{_CR}"
        )
        lines.append(separator)

        for row in self.rows:
            cells = []
            for idx, cell in enumerate(row):
                cells.append(_pad(_truncate(cell, self.col_widths[idx]), self.col_widths[idx]))
            lines.append(f"{_V} " + f" {_V} ".join(cells) + f" {_V}")

        footer_line = (
            f"{_BL}{_H * (sum(self.col_widths) + (len(self.col_widths) - 1) * 3)}{_BR}"
        )
        lines.append(footer_line)
        return "\n".join(lines)


def shutil_get_terminal_width() -> int:
    try:
        import shutil
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def render_table(headers: list[str], rows: list[list[Any]]) -> str:
    return Table(headers, rows).render()


def print_table(headers: list[str], rows: list[list[Any]]) -> None:
    print(render_table(headers, rows))


def render_section(title: str) -> str:
    width = shutil_get_terminal_width()
    if _USE_UNICODE:
        return f"\n{_TL}{_H * (width - 2)}{_TR}\n{_V} {_pad(title, width - 4)} {_V}\n{_BL}{_H * (width - 2)}{_BR}\n"
    return f"\n+{'-' * (width - 2)}+\n| {_pad(title, width - 4)} |\n+{'-' * (width - 2)}+\n"


def print_section(title: str) -> None:
    print(render_section(title))


def format_status(value: str) -> str:
    value = str(value).lower()
    if value in ("passed", "success", "ok", "healthy", "executed"):
        return _color(32, value)
    if value in ("failed", "error", "unhealthy"):
        return _color(31, value)
    if value in ("skipped", "warning", "pending"):
        return _color(33, value)
    return value


def _color(code: int, text: str) -> str:
    if not _USE_UNICODE:
        return str(text)
    return f"\033[{code}m{text}\033[0m"


def format_duration(seconds: float) -> str:
    if seconds < 1.0:
        return f"{seconds * 1000:.0f}ms"
    if seconds < 60.0:
        return f"{seconds:.1f}s"
    minutes, secs = divmod(seconds, 60.0)
    return f"{int(minutes)}m {secs:.0f}s"


def format_percent(value: float) -> str:
    return f"{value:.1f}%"


def format_number(value: int) -> str:
    return f"{value:,}"
