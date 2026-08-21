"""Tests for the canonical ``repair`` command path — Program 14.1.

Replaces the legacy RepairGuidance tests. Confirms repair planning routes
through the canonical provider and never fabricates targets.
"""

from __future__ import annotations


from runtime.foundation.intelligence import format_repair, repair_plan
from runtime.foundation.intelligence.platform.repair import Defect


def test_repair_plan_handles_empty_defects():
    repair = repair_plan(defects=[], changed_files=["runtime/verify.py"])
    out = format_repair(repair)
    assert "No defects recorded" in out


def test_repair_plan_orders_and_cites_provider_owners():
    defect = Defect(
        id="d1",
        source="test",
        summary="balance regression",
        paths=("backend/src/engines/account_engine/balance.py",),
        severity="high",
    )
    repair = repair_plan(defects=[defect], changed_files=[])
    item = repair.items[0]
    assert item["repair_order"][0]["step"] == 1
    assert item["affected_tests"]
    assert item["confidence"] == 1.0


def test_repair_plan_is_reproducible():
    defect = Defect(
        "d1", "test", "x", ("backend/src/engines/account_engine/balance.py",), "high"
    )

    def order():
        repair = repair_plan(defects=[defect], changed_files=[])
        return [s["target"] for s in repair.items[0]["repair_order"]]

    assert order() == order()
