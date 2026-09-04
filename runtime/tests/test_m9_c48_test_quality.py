# runtime/tests/test_m9_c48_test_quality.py

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.foundation.verification.test_quality import (
    QUALITY_CATEGORIES,
    QualityReport,
    TestClassification,
    classify_test_file,
    classify_tests,
    sample_paths,
)


def test_quality_categories_complete():
    expected = {
        "EXECUTION_ONLY",
        "WEAK_ASSERTION",
        "BEHAVIORAL",
        "INVARIANT",
        "PROPERTY",
        "CONTRACT",
        "INTEGRATION",
        "E2E",
        "GOLDEN",
        "MUTATION_SENSITIVE",
        "DIAGNOSTIC",
        "FALSE_POSITIVE_GUARD",
    }
    assert set(QUALITY_CATEGORIES) == expected


def test_classify_test_file_exec_only(tmp_path):
    p = tmp_path / "test_exec.py"
    p.write_text("def test_x():\n    x = 1 + 1\n")
    cls = classify_test_file(p)
    assert cls.primary_category == "EXECUTION_ONLY"


def test_classify_test_file_weak_assertion(tmp_path):
    p = tmp_path / "test_weak.py"
    p.write_text("def test_x():\n    assert True\n")
    cls = classify_test_file(p)
    assert cls.primary_category == "WEAK_ASSERTION"


def test_classify_test_file_behavioral(tmp_path):
    p = tmp_path / "test_beh.py"
    p.write_text(
        "def test_payment():\n"
        "    actual = compute_payment(100, 0.1)\n"
        "    assert actual == 110.0\n"
    )
    cls = classify_test_file(p)
    assert cls.primary_category == "BEHAVIORAL"
    assert cls.assert_count >= 1


def test_classify_test_file_property(tmp_path):
    p = tmp_path / "test_prop.py"
    p.write_text(
        "from hypothesis import given\n"
        "import hypothesis.strategies as st\n"
        "@given(st.integers())\n"
        "def test_id(x):\n"
        "    assert x == x\n"
    )
    cls = classify_test_file(p)
    assert cls.primary_category == "PROPERTY"
    assert "PROPERTY" in cls.secondary_categories


def test_classify_test_file_golden(tmp_path):
    p = tmp_path / "golden/test_regression.py"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("def test_golden():\n    assert True\n")
    cls = classify_test_file(p)
    assert cls.primary_category == "GOLDEN"


def test_classify_test_file_e2e(tmp_path):
    p = tmp_path / "e2e/test_e2e.py"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("def test_e2e():\n    assert True\n")
    cls = classify_test_file(p)
    assert cls.primary_category == "E2E"


def test_classify_test_file_invariant(tmp_path):
    p = tmp_path / "test_inv.py"
    p.write_text(
        "def test_invariant_must_never_fail():\n"
        "    for x in range(10):\n"
        "        assert x >= 0\n"
    )
    cls = classify_test_file(p)
    # Has multiple asserts + forbidden language → INVARIANT.
    assert cls.primary_category in {"INVARIANT", "BEHAVIORAL"}
    assert "FALSE_POSITIVE_GUARD" in cls.secondary_categories


def test_classify_test_file_not_found(tmp_path):
    cls = classify_test_file(tmp_path / "missing.py")
    assert cls.primary_category == "DIAGNOSTIC"


def test_sample_paths_returns_list():
    paths = sample_paths(max_files=10)
    assert isinstance(paths, list)
    assert len(paths) >= 1


def test_classify_tests_real_repo(tmp_path):
    rep = classify_tests()
    d = rep.to_dict()
    # Persist evidence
    import os
    os.makedirs("runtime/generated/m9-c48", exist_ok=True)
    with open("runtime/generated/m9-c48/test-quality-classification.json", "w") as f:
        json.dump(d, f, indent=2)
    assert d["total_files"] > 0
    assert d["schema"] == "m9-c48/test-quality@1"
    # All primary categories must be in our taxonomy.
    for c in d["classifications"]:
        assert c["primary_category"] in QUALITY_CATEGORIES


def test_report_to_dict_deterministic():
    rep = classify_tests(["nonexistent.py"])
    d1 = rep.to_dict()
    d2 = rep.to_dict()
    assert d1 == d2
