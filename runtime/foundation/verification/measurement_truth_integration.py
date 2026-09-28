"""
M9-C48 — Measurement Truth Integration for Capability Decisions.

Connects the C47 Measurement Truth contract to capability verification decisions.

For every capability measurement, the system now knows:
* measurement kind (coverage vs mutation — explicitly separate)
* scope
* completion state (7-state vocabulary)
* evidence classification (authoritative vs derived)
* repository/configuration/toolchain fingerprint
* durable evidence location
* whether evidence is reusable
* whether evidence is certifiable

Never allows:
* timeout → pass
* partial → authoritative
* infrastructure failure → certification
* stale evidence → current evidence
* derived projection → authoritative measurement

Coverage and mutation remain separate dimensions.
Mutation score must never substitute for capability behavioral verification.
Coverage must never substitute for mutation effectiveness.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from runtime.foundation.verification.capability_contract import (
    CapabilityContractRegistry,
    CapabilityMaturity,
    CapabilityMissing,
    MeasurementMapping,
    OperationalCapability,
    get_capability_contract_registry,
)
from runtime.foundation.verification.measurement_truth import (
    EvidenceClassification,
    MeasurementCompletionStatus,
    MeasurementKind,
    MeasurementTruthRecord,
    certification_gate,
    classify_completion,
    load_measurement_truth,
)

# ---------------------------------------------------------------------------
# Measurement Truth Integration Models
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CapabilityMeasurementTruth:
    """Measurement truth status for a capability."""

    capability_id: str
    measurement_kind: MeasurementKind
    record: MeasurementTruthRecord | None = None
    record_path: str = ""
    completion_status: MeasurementCompletionStatus = MeasurementCompletionStatus.UNKNOWN
    evidence_classification: EvidenceClassification = EvidenceClassification.DERIVED
    is_authoritative: bool = False
    is_certifiable: bool = False
    is_reusable: bool = False
    fingerprint: str = ""
    repository_sha: str = ""
    tree_sha: str = ""
    config_hash: str = ""
    toolchain_hash: str = ""
    duration_seconds: float = 0.0
    error: str | None = None
    missing_requirements: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "measurement_kind": self.measurement_kind.value,
            "completion_status": self.completion_status.value,
            "evidence_classification": self.evidence_classification.value,
            "record": self.record.to_dict() if self.record else None,
        }


@dataclass(frozen=True, slots=True)
class CapabilityMeasurementDecision:
    """Decision about capability measurement based on truth."""

    capability_id: str
    measurement_kind: MeasurementKind
    decision: Literal[
        "use_existing_authoritative",
        "use_existing_reusable",
        "revalidate_recommended",
        "fresh_measurement_required",
        "no_measurement_exists",
        "measurement_invalid",
        "measurement_partial",
        "measurement_timeout",
        "measurement_infrastructure_failure",
    ]
    reason: str
    existing_record: CapabilityMeasurementTruth | None = None
    required_action: str = ""
    escalation_needed: bool = False

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "measurement_kind": self.measurement_kind.value,
            "existing_record": (
                self.existing_record.to_dict() if self.existing_record else None
            ),
        }


@dataclass
class CapabilityMeasurementTruthReport:
    """Complete measurement truth report for all capabilities."""

    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    repository_sha: str = ""
    measurements: list[CapabilityMeasurementTruth] = field(default_factory=list)
    decisions: list[CapabilityMeasurementDecision] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "repository_sha": self.repository_sha,
            "measurements": [m.to_dict() for m in self.measurements],
            "decisions": [d.to_dict() for d in self.decisions],
            "summary": self.summary,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


# ---------------------------------------------------------------------------
# Measurement Truth Integrator
# ---------------------------------------------------------------------------


class MeasurementTruthIntegrator:
    """
    Integrates Measurement Truth into capability decisions.

    Loads durable measurement truth records and evaluates them against
    capability certification requirements.
    """

    def __init__(
        self,
        contract_registry: CapabilityContractRegistry | None = None,
        measurement_dir: Path | None = None,
    ):
        self._contract_registry = (
            contract_registry or get_capability_contract_registry()
        )
        self._measurement_dir = measurement_dir or (
            Path(__file__).parent.parent.parent / "generated" / "m9-c47"
        )

    def evaluate_all_capabilities(self) -> CapabilityMeasurementTruthReport:
        """Evaluate measurement truth for all registered capabilities."""
        self._contract_registry.load()

        report = CapabilityMeasurementTruthReport()
        repo_root = Path(__file__).parent.parent.parent.parent
        try:
            import subprocess

            report.repository_sha = (
                subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=str(repo_root),
                    capture_output=True,
                    text=True,
                    timeout=10,
                ).stdout.strip()
                or "unknown"
            )
        except Exception:
            report.repository_sha = "unknown"

        for contract in self._contract_registry.get_all_contracts():
            # Check mutation measurement
            if self._requires_mutation(contract):
                truth = self._load_measurement_truth(contract, MeasurementKind.MUTATION)
                decision = self._decide_measurement(
                    contract, truth, MeasurementKind.MUTATION
                )
                report.measurements.append(truth)
                report.decisions.append(decision)

            # Check coverage measurement
            if self._requires_coverage(contract):
                truth = self._load_measurement_truth(contract, MeasurementKind.COVERAGE)
                decision = self._decide_measurement(
                    contract, truth, MeasurementKind.COVERAGE
                )
                report.measurements.append(truth)
                report.decisions.append(decision)

        # Build summary
        report.summary = self._build_summary(report)
        return report

    def _requires_mutation(self, contract: OperationalCapability) -> bool:
        """Check if capability requires mutation measurement."""
        return any(
            m.measurement_kind == MeasurementKind.MUTATION
            for m in contract.measurement_mappings
        )

    def _requires_coverage(self, contract: OperationalCapability) -> bool:
        """Check if capability requires coverage measurement."""
        return any(
            m.measurement_kind == MeasurementKind.COVERAGE
            for m in contract.measurement_mappings
        )

    def _load_measurement_truth(
        self, contract: OperationalCapability, kind: MeasurementKind
    ) -> CapabilityMeasurementTruth:
        """Load measurement truth record for a capability."""
        # Find the measurement mapping for this kind
        mapping = next(
            (m for m in contract.measurement_mappings if m.measurement_kind == kind),
            None,
        )

        record = None
        record_path = ""

        if mapping and mapping.authoritative_evidence_path:
            record_path = mapping.authoritative_evidence_path
            path = Path(record_path)
            if path.exists():
                try:
                    record = load_measurement_truth(path)
                except Exception:
                    record = None

        if not record:
            # Try default locations
            default_paths = [
                self._measurement_dir / f"measurement-truth-{contract.id}.json",
                self._measurement_dir / "coverage" / "measurement-truth-coverage.json",
                Path("backend/tests/generated/mutation")
                / f"measurement-truth-{contract.id}.json",
                Path(
                    "backend/tests/generated/mutation/local-smoke/measurement-truth.json"
                ),
            ]
            for p in default_paths:
                if p.exists():
                    try:
                        record = load_measurement_truth(p)
                        record_path = str(p)
                        break
                    except Exception:
                        continue

        if record and record.measurement_kind != kind.value:
            # Verify measurement kind matches
            record = None
            record_path = ""

        if record:
            # Recompute completion status from current state
            completion = classify_completion(record=record)
            is_certifiable = certification_gate(record)
            fingerprint = record.evidence_fingerprint

            return CapabilityMeasurementTruth(
                capability_id=contract.id,
                measurement_kind=kind,
                record=record,
                record_path=record_path,
                completion_status=MeasurementCompletionStatus(completion),
                evidence_classification=EvidenceClassification(
                    record.evidence_classification
                ),
                is_authoritative=record.evidence_classification
                == EvidenceClassification.AUTHORITATIVE.value,
                is_certifiable=is_certifiable,
                is_reusable=record.evidence_classification
                == EvidenceClassification.AUTHORITATIVE.value
                and completion
                == MeasurementCompletionStatus.AUTHORITATIVE_COMPLETE.value,
                fingerprint=fingerprint,
                repository_sha=record.repository_sha,
                tree_sha=record.tree_sha,
                config_hash=record.configuration_fingerprint,
                toolchain_hash=record.toolchain_fingerprint,
                duration_seconds=record.duration_seconds,
                error=record.error,
                missing_requirements=self._check_missing_requirements(record, mapping),
            )
        else:
            return CapabilityMeasurementTruth(
                capability_id=contract.id,
                measurement_kind=kind,
                record=None,
                record_path="",
                completion_status=MeasurementCompletionStatus.UNKNOWN,
                evidence_classification=EvidenceClassification.DERIVED,
                is_authoritative=False,
                is_certifiable=False,
                is_reusable=False,
                missing_requirements=[
                    f"No {kind.value} measurement truth record found"
                ],
            )

    def _check_missing_requirements(
        self, record: MeasurementTruthRecord, mapping: MeasurementMapping | None
    ) -> list[str]:
        """Check if measurement meets completion requirements."""
        missing = []

        if not mapping:
            return ["No measurement mapping defined"]

        reqs = mapping.completion_requirements
        if kind := record.measurement_kind:
            if kind == "mutation":
                if "minimum_score" in reqs:
                    score = record.mutation_score or 0
                    if score < reqs["minimum_score"]:
                        missing.append(
                            f"Mutation score {score}% < required {reqs['minimum_score']}%"
                        )
                if (
                    reqs.get("completion") == "AUTHORITATIVE_COMPLETE"
                    and record.completion_status
                    != MeasurementCompletionStatus.AUTHORITATIVE_COMPLETE.value
                ):
                    missing.append(
                        f"Completion status {record.completion_status} != AUTHORITATIVE_COMPLETE"
                    )

            elif kind == "coverage":
                if "minimum_line_percent" in reqs:
                    pct = (
                        record.coverage_result_percent
                        or record.coverage.line_percent
                        or 0
                    )
                    if pct < reqs["minimum_line_percent"]:
                        missing.append(
                            f"Coverage {pct}% < required {reqs['minimum_line_percent']}%"
                        )

        if record.error:
            missing.append(f"Recorded error: {record.error}")

        return missing

    def _decide_measurement(
        self,
        contract: OperationalCapability,
        truth: CapabilityMeasurementTruth,
        kind: MeasurementKind,
    ) -> CapabilityMeasurementDecision:
        """Decide what measurement action is needed for a capability."""
        if not truth.record:
            return CapabilityMeasurementDecision(
                capability_id=contract.id,
                measurement_kind=kind,
                decision="no_measurement_exists",
                reason=f"No {kind.value} measurement truth record exists for {contract.name}",
                required_action=f"Run measurement for {kind.value}: verify.py measurement {kind.value} <scope>",
                escalation_needed=True,
            )

        # Check completion status
        if (
            truth.completion_status
            == MeasurementCompletionStatus.AUTHORITATIVE_COMPLETE
        ):
            if truth.is_certifiable:
                return CapabilityMeasurementDecision(
                    capability_id=contract.id,
                    measurement_kind=kind,
                    decision="use_existing_authoritative",
                    reason=f"Authoritative {kind.value} measurement exists and is certifiable",
                    existing_record=truth,
                    required_action="No action needed — evidence is authoritative and certifiable",
                )
            else:
                return CapabilityMeasurementDecision(
                    capability_id=contract.id,
                    measurement_kind=kind,
                    decision="use_existing_reusable",
                    reason=f"Authoritative {kind.value} measurement exists but not certifiable (missing requirements: {', '.join(truth.missing_requirements)})",
                    existing_record=truth,
                    required_action="Address missing requirements for certification",
                    escalation_needed=bool(truth.missing_requirements),
                )

        elif truth.completion_status == MeasurementCompletionStatus.PARTIAL:
            return CapabilityMeasurementDecision(
                capability_id=contract.id,
                measurement_kind=kind,
                decision="measurement_partial",
                reason=f"{kind.value.capitalize()} measurement is partial — population not fully processed",
                existing_record=truth,
                required_action="Re-run full measurement scope",
                escalation_needed=True,
            )

        elif truth.completion_status == MeasurementCompletionStatus.TIMEOUT:
            return CapabilityMeasurementDecision(
                capability_id=contract.id,
                measurement_kind=kind,
                decision="measurement_timeout",
                reason=f"{kind.value.capitalize()} measurement timed out",
                existing_record=truth,
                required_action="Re-run with higher --max-runtime",
                escalation_needed=True,
            )

        elif (
            truth.completion_status
            == MeasurementCompletionStatus.INFRASTRUCTURE_FAILURE
        ):
            return CapabilityMeasurementDecision(
                capability_id=contract.id,
                measurement_kind=kind,
                decision="measurement_infrastructure_failure",
                reason=f"{kind.value.capitalize()} measurement failed due to infrastructure error: {truth.error}",
                existing_record=truth,
                required_action="Diagnose infrastructure (verify.py env-check) and re-run",
                escalation_needed=True,
            )

        elif truth.completion_status == MeasurementCompletionStatus.EVIDENCE_FAILURE:
            return CapabilityMeasurementDecision(
                capability_id=contract.id,
                measurement_kind=kind,
                decision="measurement_invalid",
                reason=f"{kind.value.capitalize()} measurement evidence is corrupt or incomplete",
                existing_record=truth,
                required_action="Re-check evidence artifacts and re-run measurement",
                escalation_needed=True,
            )

        elif truth.completion_status == MeasurementCompletionStatus.INVALID_SCOPE:
            return CapabilityMeasurementDecision(
                capability_id=contract.id,
                measurement_kind=kind,
                decision="measurement_invalid",
                reason=f"{kind.value.capitalize()} measurement has invalid scope: {truth.record.scope_invalid_reason if truth.record else 'unknown'}",
                existing_record=truth,
                required_action="Align requested and actual scope, then re-run",
                escalation_needed=True,
            )

        elif truth.completion_status == MeasurementCompletionStatus.DERIVED_ONLY:
            return CapabilityMeasurementDecision(
                capability_id=contract.id,
                measurement_kind=kind,
                decision="revalidate_recommended",
                reason=f"{kind.value.capitalize()} evidence is derived, not authoritative — fresh measurement recommended for certification",
                existing_record=truth,
                required_action="Run fresh authoritative measurement for certification",
                escalation_needed=False,
            )

        else:
            return CapabilityMeasurementDecision(
                capability_id=contract.id,
                measurement_kind=kind,
                decision="measurement_invalid",
                reason=f"Unknown completion status: {truth.completion_status}",
                existing_record=truth,
                required_action="Inspect measurement truth record and re-run",
                escalation_needed=True,
            )

    def _build_summary(
        self, report: CapabilityMeasurementTruthReport
    ) -> dict[str, int]:
        """Build summary statistics."""
        summary = {
            "total_capabilities": len(self._contract_registry.get_all_contracts()),
            "capabilities_with_mutation": 0,
            "capabilities_with_coverage": 0,
            "authoritative_mutations": 0,
            "certifiable_mutations": 0,
            "authoritative_coverages": 0,
            "fresh_required": 0,
            "revalidation_recommended": 0,
        }

        for m in report.measurements:
            if m.measurement_kind == MeasurementKind.MUTATION:
                summary["capabilities_with_mutation"] += 1
                if m.is_authoritative:
                    summary["authoritative_mutations"] += 1
                if m.is_certifiable:
                    summary["certifiable_mutations"] += 1
            elif m.measurement_kind == MeasurementKind.COVERAGE:
                summary["capabilities_with_coverage"] += 1
                if m.is_authoritative:
                    summary["authoritative_coverages"] += 1

        for d in report.decisions:
            if d.decision == "fresh_measurement_required":
                summary["fresh_required"] += 1
            elif d.decision == "revalidate_recommended":
                summary["revalidation_recommended"] += 1

        return summary

    def evaluate_capability(
        self, capability_id: str
    ) -> CapabilityMeasurementTruthReport:
        """Evaluate measurement truth for a specific capability."""
        contract = self._contract_registry.get_contract(capability_id)
        if not contract:
            return CapabilityMeasurementTruthReport()

        report = CapabilityMeasurementTruthReport()

        if self._requires_mutation(contract):
            truth = self._load_measurement_truth(contract, MeasurementKind.MUTATION)
            decision = self._decide_measurement(
                contract, truth, MeasurementKind.MUTATION
            )
            report.measurements.append(truth)
            report.decisions.append(decision)

        if self._requires_coverage(contract):
            truth = self._load_measurement_truth(contract, MeasurementKind.COVERAGE)
            decision = self._decide_measurement(
                contract, truth, MeasurementKind.COVERAGE
            )
            report.measurements.append(truth)
            report.decisions.append(decision)

        report.summary = self._build_summary(report)
        return report


# ---------------------------------------------------------------------------
# Capability Contract Enhancement
# ---------------------------------------------------------------------------


def enhance_capability_with_measurement_truth(
    contract: OperationalCapability,
    integrator: MeasurementTruthIntegrator,
) -> OperationalCapability:
    """Enhance a capability contract with current measurement truth status."""
    report = integrator.evaluate_capability(contract.id)

    # Update maturity based on measurement truth
    has_authoritative_mutation = any(
        m.is_authoritative and m.measurement_kind == MeasurementKind.MUTATION
        for m in report.measurements
    )
    has_authoritative_coverage = any(
        m.is_authoritative and m.measurement_kind == MeasurementKind.COVERAGE
        for m in report.measurements
    )
    has_certifiable = any(m.is_certifiable for m in report.measurements)

    # Determine new maturity
    if contract.maturity == CapabilityMaturity.DESCRIPTIVE:
        pass  # No executable verification
    elif has_authoritative_mutation and has_authoritative_coverage and has_certifiable:
        new_maturity = CapabilityMaturity.CERTIFIED
    elif has_authoritative_mutation or has_authoritative_coverage:
        new_maturity = CapabilityMaturity.MEASURED
    else:
        new_maturity = CapabilityMaturity.OPERATIONAL

    # Update missing based on measurement truth
    missing = list(contract.missing)
    if CapabilityMissing.NO_MEASUREMENT_TRUTH in missing and (
        has_authoritative_mutation or has_authoritative_coverage
    ):
        missing.remove(CapabilityMissing.NO_MEASUREMENT_TRUTH)

    # Create enhanced contract (operational capability is mutable for this)
    contract.maturity = new_maturity
    contract.missing = missing

    return contract


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def get_measurement_truth_integrator() -> MeasurementTruthIntegrator:
    """Get or create the measurement truth integrator."""
    return MeasurementTruthIntegrator()


def format_measurement_truth_report(report: CapabilityMeasurementTruthReport) -> str:
    """Format measurement truth report for display."""
    lines = []
    lines.append("=" * 80)
    lines.append("  MEASUREMENT TRUTH INTEGRATION REPORT")
    lines.append("=" * 80)
    lines.append(f"  Generated: {report.generated_at}")
    lines.append(f"  Repository SHA: {report.repository_sha[:8]}")
    lines.append("-" * 80)

    lines.append("  SUMMARY:")
    for k, v in report.summary.items():
        lines.append(f"    {k}: {v}")

    lines.append("-" * 80)
    lines.append("  MEASUREMENTS:")
    for m in report.measurements:
        lines.append(f"    {m.capability_id} [{m.measurement_kind.value}]")
        lines.append(f"      Completion: {m.completion_status.value}")
        lines.append(f"      Classification: {m.evidence_classification.value}")
        lines.append(f"      Authoritative: {'Yes' if m.is_authoritative else 'No'}")
        lines.append(f"      Certifiable: {'Yes' if m.is_certifiable else 'No'}")
        lines.append(f"      Reusable: {'Yes' if m.is_reusable else 'No'}")
        lines.append(f"      Duration: {m.duration_seconds:.1f}s")
        if m.error:
            lines.append(f"      Error: {m.error}")
        if m.missing_requirements:
            lines.append(f"      Missing: {', '.join(m.missing_requirements)}")

    lines.append("-" * 80)
    lines.append("  DECISIONS:")
    for d in report.decisions:
        lines.append(
            f"    {d.capability_id} [{d.measurement_kind.value}]: {d.decision}"
        )
        lines.append(f"      Reason: {d.reason}")
        lines.append(f"      Action: {d.required_action}")
        if d.escalation_needed:
            lines.append("      ⚠ ESCALATION NEEDED")

    lines.append("=" * 80)
    return "\n".join(lines)


if __name__ == "__main__":
    # Demo
    integrator = MeasurementTruthIntegrator()
    report = integrator.evaluate_all_capabilities()
    print(format_measurement_truth_report(report))

    # Save to file
    out_path = (
        Path(__file__).parent.parent.parent
        / "generated"
        / "m9-c48"
        / "measurement-truth-integration.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report.to_json())
    print(f"\nSaved to {out_path}")
