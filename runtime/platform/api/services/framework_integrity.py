"""Framework Integrity service adapter (Phase 2 — ``/platform/v1/framework/integrity``).

Exposes the C62 FrameworkIntegrityResult through the Platform API.
No new authority — delegates to runtime.foundation.verification.framework_integrity.
"""

from __future__ import annotations

from typing import Any

from runtime.foundation.verification.framework_integrity import (
    ArtifactFreshnessDetector,
    FrameworkIntegrityResult,
    FrameworkSelfTests,
)
from runtime.platform.api.contracts import framework_integrity as fi_contract
from runtime.platform.api.services._helpers import envelope, now_iso

__all__ = [
    "build_framework_integrity",
    "build_framework_self_tests",
]


def build_framework_integrity() -> dict[str, Any]:
    """Build the ``platform.framework_integrity`` envelope from C62 detectors."""

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

    # Run self-tests (K1-K9)
    st = FrameworkSelfTests()
    self_test_result = st.run_all()
    diagnostic = self_test_result.diagnostic

    # Build FrameworkIntegrityResult from combined findings
    result = FrameworkIntegrityResult.from_drift_report(
        drift_report,
        artifact_summary={"detector": "authority_drift_detector + artifact_freshness_detector"},
    )

    # Convert to Platform API contract format
    findings_data = []
    for f in all_findings:
        findings_data.append({
            "check_name": f.check_name,
            "detected_component": f.detected_component,
            "expected_authority": f.expected_authority,
            "actual_authority": f.actual_authority,
            "classification": f.classification,
            "source_evidence": f.source_evidence,
            "severity": f.severity,
        })

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

    st = FrameworkSelfTests()
    result = st.run_all()

    test_results = []
    for name, passed in result.diagnostic["self_tests"].items():
        test_results.append({
            "name": name,
            "passed": passed,
            "detail": "PASS" if passed else "FAIL",
        })

    data = {
        "results": test_results,
        "passed": result.diagnostic["passed"],
        "total": result.diagnostic["total"],
    }
    return envelope(kind=fi_contract.FrameworkSelfTestsEnvelope.__fields__["kind"].default, data=data)