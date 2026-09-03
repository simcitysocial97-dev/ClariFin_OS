# backend/tests/mutation_infra/python_312_probes/test_pep634_match.py
from __future__ import annotations

import pep634_match


def test_classify_zero() -> None:
    assert pep634_match.classify_with_match(0) == "zero"


def test_classify_small_one() -> None:
    assert pep634_match.classify_with_match(1) == "small"


def test_classify_small_two() -> None:
    assert pep634_match.classify_with_match(2) == "small"


def test_classify_large() -> None:
    assert pep634_match.classify_with_match(200) == "large"


def test_classify_other() -> None:
    assert pep634_match.classify_with_match(50) == "other"


def test_shape_origin() -> None:
    assert pep634_match.match_on_shape((0, 0)) == "origin"


def test_shape_x_axis() -> None:
    assert pep634_match.match_on_shape((3, 0)) == "x-axis-3"


def test_shape_y_axis() -> None:
    assert pep634_match.match_on_shape((0, 4)) == "y-axis-4"


def test_shape_point() -> None:
    assert pep634_match.match_on_shape((2, 5)) == "point-2-5"


def test_shape_unknown() -> None:
    assert pep634_match.match_on_shape("oops") == "unknown"