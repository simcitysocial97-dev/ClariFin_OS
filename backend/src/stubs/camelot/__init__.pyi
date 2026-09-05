"""
Minimal type stubs for the camelot-py public surface actually used by ClariFin_OS.

These stubs intentionally cover only the attributes accessed by the extraction
codebase. The runtime library ships without type information; this module is
declared as a Mypy plugin via [tool.mypy] mypy_path in backend/pyproject.toml
so the strict backend boundary can still type-check against camelot.
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from camelot.core import Table

class TableList:
    """Minimal stub: TableList is a list-like container returned by read_pdf()."""
    n: int
    def __init__(self, tables: list[Table] = ...) -> None: ...
    def __iter__(self) -> Iterator[Table]: ...
    def __len__(self) -> int: ...
    def __getitem__(self, index: int) -> Table: ...
    def export(self, path: str, f: str = ..., compress: bool = ...) -> None: ...
    def filter(self) -> TableList: ...
    def stack_contiguous(self, key: str = ...) -> TableList: ...

def read_pdf(
    filepath: str | bytes | Any,
    pages: str = ...,
    password: str | None = ...,
    flavor: str = ...,
    suppress_stdout: bool = ...,
    parallel: bool = ...,
    cpu_count: int | None = ...,
    layout_kwargs: dict[str, Any] | None = ...,
    per_page: bool = ...,
    debug: bool = ...,
    **kwargs: Any,
) -> TableList: ...

PlotMethods: Any
__version__: str
