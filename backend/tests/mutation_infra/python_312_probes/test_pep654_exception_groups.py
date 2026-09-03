# backend/tests/mutation_infra/python_312_probes/test_pep654_exception_groups.py
from __future__ import annotations

import pep654_exception_groups


def test_handle_group_value_errors() -> None:
    eg = BaseExceptionGroup("g", [ValueError("a"), ValueError("b")])
    assert pep654_exception_groups.handle_group(eg) == 2


def test_handle_group_no_value_errors() -> None:
    # Pure-ValueError group — except* ValueError catches them all.
    eg = BaseExceptionGroup("g", [ValueError("a")])
    assert pep654_exception_groups.handle_group(eg) == 1


def test_raise_group_smoke() -> None:
    try:
        pep654_exception_groups.raise_group([ValueError("x")])
    except ExceptionGroup as eg:
        assert len(eg.exceptions) == 1


def test_raise_group_empty() -> None:
    pep654_exception_groups.raise_group([])