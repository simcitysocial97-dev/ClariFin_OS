# backend/tests/mutation_infra/python_312_probes/test_pep604_union.py
from __future__ import annotations

import pep604_union


def test_coerce_none() -> None:
    assert pep604_union.coerce(None) == "empty"


def test_coerce_int() -> None:
    assert pep604_union.coerce(5) == "5"


def test_coerce_str() -> None:
    assert pep604_union.coerce("hi") == "hi"


def test_union_arg_left() -> None:
    assert pep604_union.union_arg(3, 1) == 3


def test_union_arg_right() -> None:
    assert pep604_union.union_arg(1, 4) == 4


def test_union_arg_equal() -> None:
    assert pep604_union.union_arg(7, 7) == 7