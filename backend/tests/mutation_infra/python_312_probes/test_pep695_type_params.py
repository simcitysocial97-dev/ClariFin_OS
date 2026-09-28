# backend/tests/mutation_infra/python_312_probes/test_pep695_type_params.py
from __future__ import annotations

import pep695_type_params


def test_box_int() -> None:
    box = pep695_type_params.Box(42)
    assert box.get() == 42


def test_box_str() -> None:
    box = pep695_type_params.Box("hello")
    assert box.get() == "hello"


def test_first_some() -> None:
    assert pep695_type_params.first([1, 2, 3]) == 1


def test_first_empty() -> None:
    assert pep695_type_params.first([]) is None


def test_first_strings() -> None:
    assert pep695_type_params.first(["a", "b"]) == "a"
