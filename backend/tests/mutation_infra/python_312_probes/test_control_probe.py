# backend/tests/mutation_infra/python_312_probes/test_control_probe.py
from __future__ import annotations

import control_probe


def test_classify_zero() -> None:
    assert control_probe.classify(0) == "zero"


def test_classify_small() -> None:
    assert control_probe.classify(1) == "small"
    assert control_probe.classify(2) == "small"


def test_classify_large() -> None:
    assert control_probe.classify(150) == "large"


def test_classify_other() -> None:
    assert control_probe.classify(50) == "other"


def test_coerce_none() -> None:
    assert control_probe.coerce_baseline(None) == "empty"


def test_coerce_int() -> None:
    assert control_probe.coerce_baseline(7) == "7"
