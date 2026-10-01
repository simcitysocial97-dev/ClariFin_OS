"""Framework Integrity service adapter (Phase 2 — ``/platform/v1/framework/integrity``).

Exposes the C62 FrameworkIntegrityResult through the Platform API.
No new authority — delegates to runtime.foundation.verification.framework_integrity.
"""

from __future__ import annotations

import threading
import time
from typing import Any

from runtime.foundation.verification.framework_integrity import (
    ArtifactFreshnessDetector,
    FrameworkIntegrityResult,
    FrameworkSelfTests,
)
from runtime.platform.api.contracts import framework_integrity as fi_contract
from runtime.platform.api.services._helpers import envelope

__all__ = [
    "build_framework_integrity",
    "build_framework_self_tests",
]

#: How long a self-test diagnostic is reused before it is recomputed.
#:
#: The K1-K9 self-tests measure 8.2 s of the 12.8 s a health snapshot costs, and
#: the health read only needs two counters from them (`self_tests_passed`,
#: `self_tests_total`). Re-running the framework's test suite inside a status
#: endpoint is both the single largest cost on the console's data path and work
#: that changes only when the code does. The dedicated
#: `/platform/v1/framework/self-tests` endpoint still forces a fresh run, so
#: nothing is hidden from an operator who asks for it directly.
_SELF_TEST_TTL_SECONDS = 600

_self_test_cache: dict[str, Any] = {"at": 0.0, "diagnostic": None}
_self_test_lock = threading.Lock()


def _self_test_diagnostic(*, nocache: bool = False) -> dict[str, Any]:
    """Return the K1-K9 diagnostic, reusing a recent run.

    Single-flight via a module lock, because a cold console page resolves
    health and framework integrity in parallel and would otherwise run the
    suite once per caller.
    """

    global _self_test_cache

    with _self_test_lock:
        now = time.monotonic()
        cached = _self_test_cache
        if (
            not nocache
            and cached["diagnostic"] is not None
            and (now - cached["at"]) < _SELF_TEST_TTL_SECONDS
        ):
            return cached["diagnostic"]
        result = FrameworkSelfTests().run_all()
        _self_test_cache = {"at": time.monotonic(), "diagnostic": result.diagnostic}
        return result.diagnostic


def build_framework_integrity(*, nocache: bool = False) -> dict[str, Any]:
    """Build the ``platform.framework_integrity`` envelope from C62 detectors.

    ``nocache=True`` forces the self-test suite to re-run rather than reuse a
    recent diagnostic.
    """

    # Run authority drift detector (same as C62 doctor)
    from runtime.foundation.verification.authority_drift_detector import (
        run_authority_drift_detection,
    )

    drift_report = run_authority_drift_detection()

    # Run artifact freshness detector
    artifact_detector = ArtifactFreshnessDetector()
    artifact_findings = artifact_detector.check()

    # Combine all findings
    all_findings = list(drift_report.findings) + artifact_findings

    # Self-tests (K1-K9), memoized: see _self_test_diagnostic.
    diagnostic = _self_test_diagnostic(nocache=nocache)

    # Build FrameworkIntegrityResult from combined findings
    result = FrameworkIntegrityResult.from_drift_report(
        drift_report,
        artifact_summary={
            "detector": "authority_drift_detector + artifact_freshness_detector"
        },
    )

    # Convert to Platform API contract format
    findings_data = []
    for f in all_findings:
        findings_data.append(
            {
                "check_name": f.check_name,
                "detected_component": f.detected_component,
                "expected_authority": f.expected_authority,
                "actual_authority": f.actual_authority,
                "classification": f.classification,
                "source_evidence": f.source_evidence,
                "severity": f.severity,
            }
        )

    data = {
        "schema_version": result.schema,
        "generated_at": result.generated_at,
        "health": result.health.value,
        "critical_count": result.critical_count,
        "high_count": result.high_count,
        "medium_count": result.medium_count,
        "low_count": result.low_count,
        "info_count": result.info_count,
        "total_findings": len(all_findings),
        "findings": findings_data,
        "artifact_summary": result.artifact_summary,
        "diagnostic": diagnostic,
    }
    return envelope(kind=fi_contract.FRAMEWORK_INTEGRITY_KIND, data=data)


def build_framework_self_tests() -> dict[str, Any]:
    """Build the ``platform.framework_self_tests`` envelope from C62 K1-K9."""

    # This endpoint exists to report the self-tests, so it always runs them
    # fresh rather than reusing the health snapshot's memoized diagnostic.
    diagnostic = _self_test_diagnostic(nocache=True)
    result = type("R", (), {"diagnostic": diagnostic})()

    test_results = []
    for name, passed in result.diagnostic["self_tests"].items():
        test_results.append(
            {
                "name": name,
                "passed": passed,
                "detail": "PASS" if passed else "FAIL",
            }
        )

    data = {
        "results": test_results,
        "passed": result.diagnostic["passed"],
        "total": result.diagnostic["total"],
    }
    return envelope(kind=fi_contract.FRAMEWORK_SELF_TESTS_KIND, data=data)
