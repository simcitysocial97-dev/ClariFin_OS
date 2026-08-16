"""Tests for the canonical ``diagnose`` command path — Program 14.1."""

from __future__ import annotations


from runtime.foundation.intelligence import (
    affected_entities,
    format_diagnostic,
)
from runtime.foundation.intelligence.platform.blast import compute_blast_radius
from runtime.foundation.intelligence.platform.change import analyze_changes
from runtime.foundation.intelligence.platform.optimizer import optimize_verification
from runtime.foundation.intelligence.platform.risk import assess_risk
from runtime.foundation.intelligence.platform.repair import build_repair_intelligence


def test_diagnose_resolves_ownership_from_provider():
    change = affected_entities(["backend/src/engines/account_engine/balance.py"])
    assert change["owning_engines"]
    assert "account_engine" in change["owning_engines"][0]


def test_diagnose_formats_change_blast_risk_repair():
    changed = ["backend/src/engines/account_engine/balance.py",
               "backend/src/routers/accounts.py"]
    change = analyze_changes(paths=changed)
    blast = compute_blast_radius(change)
    risk = assess_risk(change, blast, optimize_verification(blast), memory={"recurring_ci_failures": []})
    repair = build_repair_intelligence(blast)
    out = format_diagnostic(change, blast, risk, repair)
    assert "Developer Diagnostic" in out
    assert "Blast radius" in out
    assert "Risk" in out


def test_diagnose_reports_unmapped_paths_explicitly():
    change = affected_entities(["backend/src/does-not-exist/gone.py"])
    assert change["unmapped_paths"] == ["backend/src/does-not-exist/gone.py"]
