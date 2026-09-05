"""
Minimal type stubs for camelot.core (the Table/TableList sub-module).

This stub mirrors the top-level camelot/__init__.pyi so that both:
  from camelot import read_pdf, Table
  from camelot.core import Table
can be type-checked under the strict backend boundary.
"""
from __future__ import annotations

from typing import Any

class Table:
    accuracy: float
    whitespace: float
    shape: tuple[int, int]
    page: int
    order: int
    flavor: str
    rotation: str
    parsing_report: dict[str, Any]
    confidence: float
    cells: list[list[Any]]
    cols: list[Any]
    rows: list[Any]
    df: Any
    filename: str | None

    def __init__(self, cols: Any = ..., rows: Any = ...) -> None: ...
    @property
    def data(self) -> list[list[str]]: ...
    def to_csv(self, path: str, **kwargs: Any) -> None: ...
    def to_json(self, path: str, **kwargs: Any) -> None: ...
    def to_excel(self, path: str, **kwargs: Any) -> None: ...
    def to_html(self, path: str, **kwargs: Any) -> None: ...
    def to_markdown(self, path: str, **kwargs: Any) -> None: ...
    def to_sqlite(self, path: str, **kwargs: Any) -> None: ...
    def get_pdf_image(
        self,
        filepath: str = ...,
        resolution: int = ...,
    ) -> bytes | None: ...
    def set_all_edges(self) -> None: ...
    def set_border(self) -> None: ...
    def set_edges(self, edges: Any) -> None: ...
    def copy_spanning_text(self, spanning_text: Any, spanning_cells: Any) -> None: ...
