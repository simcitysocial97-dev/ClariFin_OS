"""Tests for the canonical ``risk`` command path — Program 14.1.

Replaces the legacy RiskAnalyzer tests. The canonical scorer
(:func:`engineering_risk`) must produce seven evidence-backed dimensions and
never under-report a High dimension.
"""

from __future__ import annotations


from runtime.foundation.intelligence import engineering_risk, format_risk


def test_risk_exposes_seven_dimensions():
    risk = engineering_risk(
        ["backend/src/engines/account_engine/balance.py",
         "backend/src/routers/accounts.py"]
    )
    names = {d.name for d in risk.dimensions}
    assert names == {
        "Architectural Risk",
        "Regression Risk",
        "Dependency Risk",
        "Coverage Risk",
        "Ownership Risk",
        "Contract Risk",
        "CI Risk",
    }


def test_risk_never_masks_high_dimension():
    risk = engineering_risk(
        ["backend/src/engines/account_engine/balance.py",
         "backend/src/routers/accounts.py"]
    )
    order = ["Low", "Medium", "High"]
    worst = max((d.level for d in risk.dimensions), key=order.index)
    assert order.index(risk.overall_level) >= order.index(worst)


def test_risk_dimensions_carry_evidence():
    risk = engineering_risk(["backend/src/engines/account_engine/balance.py"])
    for dim in risk.dimensions:
        assert dim.evidence and all(e.strip() for e in dim.evidence)


def test_format_risk_renders_level():
    risk = engineering_risk(["backend/src/engines/account_engine/balance.py"])
    out = format_risk(risk)
    assert "Engineering Risk" in out
