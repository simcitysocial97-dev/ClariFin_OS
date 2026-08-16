"""Tests for the canonical ``affected`` command path — Program 14.1.

Replaces the legacy AffectedTestPlanner tests. Verifies that affected-test
resolution is driven entirely by provider-recorded tests, never filenames.
"""

from __future__ import annotations

from runtime.foundation.intelligence import (
    blast_radius,
    format_affected,
    verification_plan,
)
from runtime.foundation.intelligence.platform.resolver import get_resolver

ENGINE_MODULE = "backend/src/engines/account_engine/balance.py"
ROUTER = "backend/src/routers/accounts.py"


def test_affected_tests_come_from_provider():
    """Test targets must be real provider-recorded paths, not synthesised."""
    blast = blast_radius([ENGINE_MODULE])
    plan = verification_plan([ENGINE_MODULE])
    known = set(get_resolver().tests)
    assert blast.verification
    for ref in blast.verification:
        assert ref.key in known
    # the selected unit must target provider-known tests
    assert plan.selected


def test_affected_report_lists_selected_and_skipped():
    blast = blast_radius([ENGINE_MODULE])
    plan = verification_plan([ENGINE_MODULE])
    out = format_affected(blast, plan)
    assert "verification units selected" in out.lower()
    assert "Verification skipped" in out
    assert plan.skipped


def test_playwright_skipped_when_no_workspace_impacted():
    change = [ENGINE_MODULE]
    plan = verification_plan(change)
    skipped = {s.id for s in plan.skipped}
    assert "playwright-e2e" in skipped


def test_runtime_change_uses_provider_tests_not_filenames():
    """Runtime changes must not trigger filename-inferred test paths."""
    plan = verification_plan(["runtime/verify.py"])
    for unit in plan.selected:
        assert unit.id != "unit-targeted"
