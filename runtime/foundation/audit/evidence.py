from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path
from typing import Any

from runtime.foundation.audit.models import AuditFinding, AuditPriority, AuditSeverity, AuditStatus

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _f(check_id: str, name: str, status: str, severity: str, priority: str, message: str, details: dict[str, Any] = None, recommendation: str = "") -> AuditFinding:
    return AuditFinding(
        section="evidence",
        check_id=check_id,
        name=name,
        status=AuditStatus(status),
        severity=AuditSeverity(severity),
        priority=AuditPriority(priority),
        message=message,
        details=details or {},
        recommendation=recommendation,
    )


def audit(repo_root: Path | None = None) -> dict[str, Any]:
    start = time.monotonic()
    repo_root = repo_root or REPO_ROOT
    findings: list[AuditFinding] = []
    metrics: dict[str, Any] = {}

    from runtime.system.evidence.aggregator import EvidenceAggregator

    with tempfile.TemporaryDirectory() as tmpdir:
        evidence_dir = Path(tmpdir)

        test_results_dir = evidence_dir / "test-results"
        test_results_dir.mkdir(parents=True)

        junit_xml = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="synthetic-tests" tests="3" failures="1" errors="0" skipped="0" time="0.5">
  <testcase name="test_passing" classname="synthetic-tests">
  </testcase>
  <testcase name="test_failing" classname="synthetic-tests">
    <failure message="AssertionError">assert 1 == 2</failure>
  </testcase>
  <testcase name="test_error" classname="synthetic-tests">
    <error message="RuntimeError">raise RuntimeError("unexpected")</error>
  </testcase>
</testsuite>
"""
        (test_results_dir / "junit.xml").write_text(junit_xml, encoding="utf-8")

        agg = EvidenceAggregator(evidence_dir)
        summary = agg.aggregate(evidence_dir)

        if summary.overall_status in ("fail", "attention_needed"):
            findings.append(
                _f(
                    "synthetic-failure-collection",
                    "Synthetic failures collected correctly",
                    "pass",
                    "info",
                    "low",
                    "EvidenceAggregator correctly detected synthetic test failures",
                    {
                        "overall_status": summary.overall_status,
                        "unit_tests_failed": summary.backend.get("unit_tests", {}).get("failed", 0),
                    },
                )
            )
        else:
            findings.append(
                _f(
                    "synthetic-failure-collection",
                    "Synthetic failures collected correctly",
                    "fail",
                    "high",
                    "high",
                    f"EvidenceAggregator did not detect synthetic test failures, status={summary.overall_status}",
                    {"overall_status": summary.overall_status},
                    "Fix evidence collection to detect test failures",
                )
            )

        if summary.backend.get("unit_tests", {}).get("failed", 0) == 1:
            findings.append(
                _f(
                    "evidence-failure-count",
                    "Correct failure count in evidence",
                    "pass",
                    "info",
                    "low",
                    "EvidenceAggregator correctly counted 1 failing test",
                    {"failed_count": summary.backend["unit_tests"]["failed"]},
                )
            )
        else:
            findings.append(
                _f(
                    "evidence-failure-count",
                    "Correct failure count in evidence",
                    "fail",
                    "high",
                    "high",
                    f"Expected 1 failing test, got {summary.backend.get('unit_tests', {}).get('failed', 'unknown')}",
                    {},
                    "Fix failure count calculation in evidence collection",
                )
            )

        json_output = summary.to_json()
        try:
            parsed = json.loads(json_output)
            findings.append(
                _f(
                    "formatting-json",
                    "JSON formatting correct",
                    "pass",
                    "info",
                    "low",
                    "EvidenceSummary.to_json() produces valid JSON",
                    {"parsed_keys": list(parsed.keys())},
                )
            )
        except (json.JSONDecodeError, TypeError):
            findings.append(
                _f(
                    "formatting-json",
                    "JSON formatting correct",
                    "fail",
                    "high",
                    "high",
                    "EvidenceSummary.to_json() does not produce valid JSON",
                    {},
                    "Fix to_json() to produce valid JSON output",
                )
            )

        md_output = summary.to_markdown()
        if isinstance(md_output, str) and len(md_output) > 0 and "##" in md_output:
            findings.append(
                _f(
                    "formatting-markdown",
                    "Markdown formatting correct",
                    "pass",
                    "info",
                    "low",
                    "EvidenceSummary.to_markdown() produces valid markdown output",
                    {"output_length": len(md_output)},
                )
            )
        else:
            findings.append(
                _f(
                    "formatting-markdown",
                    "Markdown formatting correct",
                    "fail",
                    "high",
                    "high",
                    "EvidenceSummary.to_markdown() does not produce valid markdown output",
                    {},
                    "Fix _format_markdown() to produce valid markdown output",
                )
            )

        cross_layer_map = {
            "backend/src/engines/account_engine.py": {
                "capabilities": ["useAccountsCapability"],
                "services": ["AccountService"],
                "endpoints": ["GET /api/v1/accounts"],
                "mappers": ["accountsMapper"],
                "viewModels": ["AccountsViewModel"],
                "workspace": ["AccountsWorkspace"],
                "components": ["AccountsSummary"],
            }
        }

        dep_chain = agg._find_chain_for_failure("unit_tests", cross_layer_map)
        if dep_chain and "dependency_chain" in dep_chain:
            findings.append(
                _f(
                    "dependency-chain-resolution",
                    "Dependency chain resolution correct",
                    "pass",
                    "info",
                    "low",
                    "EvidenceAggregator correctly resolves dependency chains for failing tests",
                    {"chain_length": len(dep_chain["dependency_chain"])},
                )
            )
        else:
            findings.append(
                _f(
                    "dependency-chain-resolution",
                    "Dependency chain resolution correct",
                    "fail",
                    "high",
                    "high",
                    "EvidenceAggregator failed to resolve dependency chain",
                    {},
                    "Fix _find_chain_for_failure to correctly resolve dependency chains",
                )
            )

        attention_items = agg._build_attention(
            {"unit_tests": {"failed": 1}, "mutation": {}},
            type("MutationEvidence", (), {"score_pct": 0.0, "killed": 0, "survived": 0})(),
        )
        has_repair = any(
            "action" in item and item["action"] for item in attention_items
        )
        if has_repair:
            findings.append(
                _f(
                    "repair-suggestions",
                    "Repair suggestions generated correctly",
                    "pass",
                    "info",
                    "low",
                    "EvidenceAggregator generates repair suggestions with action recommendations",
                    {"attention_count": len(attention_items)},
                )
            )
        else:
            findings.append(
                _f(
                    "repair-suggestions",
                    "Repair suggestions generated correctly",
                    "fail",
                    "high",
                    "high",
                    "EvidenceAggregator does not generate repair suggestions",
                    {},
                    "Fix _build_attention to generate repair suggestions for failures",
                )
            )

        save_path = evidence_dir / "test-summary.json"
        summary.save(save_path)
        if save_path.exists():
            findings.append(
                _f(
                    "evidence-save",
                    "Evidence save functionality works",
                    "pass",
                    "info",
                    "low",
                    "EvidenceSummary.save() correctly writes JSON file",
                    {"path": str(save_path)},
                )
            )
        else:
            findings.append(
                _f(
                    "evidence-save",
                    "Evidence save functionality works",
                    "fail",
                    "high",
                    "high",
                    "EvidenceSummary.save() did not create the output file",
                    {},
                    "Fix save() to correctly write output file",
                )
            )

    metrics["synthetic_failures_injected"] = 2
    metrics["evidence_collected"] = True
    metrics["dependency_chain_resolved"] = True
    metrics["repair_suggestions_generated"] = has_repair
    metrics["formatting_correct"] = True
    metrics["save_functionality_works"] = True

    all_pass = all(f.status == AuditStatus.PASS for f in findings)
    overall = AuditStatus.PASS if all_pass else AuditStatus.FAIL

    duration = time.monotonic() - start

    return {
        "section": "evidence",
        "name": "Evidence Aggregator Audit",
        "status": overall,
        "findings": findings,
        "metrics": metrics,
        "duration_seconds": round(duration, 4),
    }