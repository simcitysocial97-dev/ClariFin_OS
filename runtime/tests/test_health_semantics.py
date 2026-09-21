"""M9-C65 — Historical health semantics tests.

Verifies that the doctor report distinguishes CURRENT FRAMEWORK HEALTH
from HISTORICAL EXECUTION STATISTICS, preventing the operator from
conflating framework integrity with pre-convergence run data.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.system.observability.health_report import EngineeringHealthReport


class TestHealthSemantics:
    """Doctor must separate framework health from historical stats."""

    def test_current_framework_health_section_present(self):
        """Report must contain explicit 'Current Framework Health' section."""
        report = EngineeringHealthReport()
        output = report.generate()
        assert "## Current Framework Health" in output
        assert "Framework Integrity" in output
        assert "Data Freshness" in output

    def test_historical_execution_stats_section_present(self):
        """Report must contain explicit 'Historical Execution Statistics' section."""
        report = EngineeringHealthReport()
        output = report.generate()
        assert "## Historical Execution Statistics" in output

    def test_sections_are_semantically_distinct(self):
        """Framework health section must not reference historical run counts."""
        report = EngineeringHealthReport()
        output = report.generate()
        # Find the Current Framework Health section
        idx_framework = output.index("## Current Framework Health")
        idx_historical = output.index("## Historical Execution Statistics")
        idx_verification = output.index("## Verification Success")

        # Framework section must come before historical section
        assert idx_framework < idx_historical < idx_verification, (
            "Sections must be ordered: Framework Health → Historical Stats → Verification Success"
        )

        # Framework section content must not contain run counts
        framework_block = output[idx_framework:idx_historical]
        assert "Total runs:" not in framework_block
        assert "Success rate:" not in framework_block

    def test_framework_integrity_marked_operational(self):
        """Framework Integrity status must be OPERATIONAL, not derived from history."""
        report = EngineeringHealthReport()
        output = report.generate()
        assert "Status: OPERATIONAL" in output

    def test_no_conflation_warning(self):
        """Report must explicitly state that historical stats are NOT framework health."""
        report = EngineeringHealthReport()
        output = report.generate()
        assert "This is NOT framework health" in output

    def test_authority_integrity_still_printed(self):
        """The doctor footer must still print 'Framework authority integrity: HEALTHY'."""
        from runtime.foundation.verification.control_plane_facade import ControlPlane

        cp = ControlPlane()
        # Capture stdout
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            rc = cp.doctor()
        out = f.getvalue()
        assert "Framework authority integrity: HEALTHY" in out
        assert rc == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
