"""Evidence Accuracy Tests — Program 7B.5

Tests for EvidenceAggregator dependency-chain enrichment and formatting.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from runtime.system.evidence.aggregator import EvidenceAggregator, _find_dependency_chain


class TestEvidenceAggregator:
    """Tests for evidence aggregation accuracy."""

    def test_dependency_chain_lookup_by_test_name(self):
        cross_map = {
            "backend/src/engines/loan_engine/amortization.py": {
                "engine": "backend/src/engines/loan_engine/amortization.py",
                "services": ["LoanService"],
                "routers": ["backend/src/routers/loans.py"],
                "endpoints": ["GET /api/loans/{loan_id}/schedule"],
                "capabilities": ["useLoansCapability"],
                "mappers": ["loansMapper"],
                "viewModels": ["LoansViewModel"],
                "pages": ["app/loans/page.tsx"],
                "workspace": ["LoansWorkspace"],
                "components": ["AmortizationTable"],
                "tests": [
                    "backend/tests/unit/engines/loan/test_amortization.py",
                    "backend/tests/contract/generated/test_loans.py",
                ],
                "graphRenderers": [],
            }
        }

        result = _find_dependency_chain("useloanscapability.contract.test.ts", cross_map)
        assert result is not None
        assert result["engine_name"] == "loan"

    def test_dependency_chain_lookup_by_engine_name(self):
        cross_map = {
            "backend/src/engines/loan_engine/amortization.py": {
                "engine": "backend/src/engines/loan_engine/amortization.py",
                "services": ["LoanService"],
                "routers": ["backend/src/routers/loans.py"],
                "endpoints": ["GET /api/loans/{loan_id}/schedule"],
                "capabilities": ["useLoansCapability"],
                "mappers": ["loansMapper"],
                "viewModels": ["LoansViewModel"],
                "pages": ["app/loans/page.tsx"],
                "workspace": ["LoansWorkspace"],
                "components": ["AmortizationTable"],
                "tests": [
                    "backend/tests/unit/engines/loan/test_amortization.py",
                    "backend/tests/contract/generated/test_loans.py",
                ],
                "graphRenderers": [],
            }
        }

        result = _find_dependency_chain("test_loan_amortization.py", cross_map)
        assert result is not None
        assert result["engine_name"] == "loan"

    def test_dependency_chain_formatting_in_report(self, tmp_path: Path):
        cross_map = {
            "backend/src/engines/loan_engine/amortization.py": {
                "engine": "backend/src/engines/loan_engine/amortization.py",
                "services": ["LoanService"],
                "routers": ["backend/src/routers/loans.py"],
                "endpoints": ["GET /api/loans/{loan_id}/schedule"],
                "capabilities": ["useLoansCapability"],
                "mappers": ["loansMapper"],
                "viewModels": ["LoansViewModel"],
                "pages": ["app/loans/page.tsx"],
                "workspace": ["LoansWorkspace"],
                "components": ["AmortizationTable"],
                "tests": [
                    "backend/tests/unit/engines/loan/test_amortization.py",
                    "backend/tests/contract/generated/test_loans.py",
                ],
                "graphRenderers": [],
            }
        }

        map_path = tmp_path / "cross-layer-map.json"
        map_path.write_text(json.dumps(cross_map), encoding="utf-8")

        with patch(
            "runtime.system.evidence.aggregator.CROSS_LAYER_MAP_PATH", map_path
        ):
            aggregator = EvidenceAggregator(tmp_path)
            summary = aggregator.aggregate(tmp_path)

            md = summary.to_markdown()
            assert "Verification Evidence" in md

    def test_find_chain_for_failure_dependency_chain_string(self):
        cross_map = {
            "backend/src/engines/loan_engine/amortization.py": {
                "engine": "backend/src/engines/loan_engine/amortization.py",
                "services": ["LoanService"],
                "routers": ["backend/src/routers/loans.py"],
                "endpoints": ["GET /api/loans/{loan_id}/schedule"],
                "capabilities": ["useLoansCapability"],
                "mappers": ["loansMapper"],
                "viewModels": ["LoansViewModel"],
                "pages": ["app/loans/page.tsx"],
                "workspace": ["LoansWorkspace"],
                "components": ["AmortizationTable"],
                "tests": [
                    "backend/tests/unit/engines/loan/test_amortization.py",
                    "backend/tests/contract/generated/test_loans.py",
                ],
                "graphRenderers": [],
            }
        }

        aggregator = EvidenceAggregator(Path("."))
        result = aggregator._find_chain_for_failure("contract_tests", cross_map)
        assert "dependency_chain" in result
        chain = result["dependency_chain"]
        assert "backend/src/engines/loan_engine/amortization.py" in chain
        assert "LoanService" in chain
        assert "GET /api/loans/{loan_id}/schedule" in chain
        assert "useLoansCapability" in chain
        assert "loansMapper" in chain
        assert "LoansWorkspace" in chain
        assert "AmortizationTable" in chain

    def test_find_chain_for_failure_unit_tests(self):
        cross_map = {
            "backend/src/engines/loan_engine/amortization.py": {
                "engine": "backend/src/engines/loan_engine/amortization.py",
                "services": ["LoanService"],
                "routers": ["backend/src/routers/loans.py"],
                "endpoints": ["GET /api/loans/{loan_id}/schedule"],
                "capabilities": ["useLoansCapability"],
                "mappers": ["loansMapper"],
                "viewModels": ["LoansViewModel"],
                "pages": ["app/loans/page.tsx"],
                "workspace": ["LoansWorkspace"],
                "components": ["AmortizationTable"],
                "tests": [
                    "backend/tests/unit/engines/loan/test_amortization.py",
                    "backend/tests/contract/generated/test_loans.py",
                ],
                "graphRenderers": [],
            }
        }

        aggregator = EvidenceAggregator(Path("."))
        result = aggregator._find_chain_for_failure("unit_tests", cross_map)
        assert "dependency_chain" in result
        assert result["likely_consumer"] == "LoanService"

    def test_empty_cross_map_returns_empty_chain(self):
        result = _find_dependency_chain("useloanscapability.contract.test.ts", {})
        assert result is None

    def test_aggregate_with_empty_evidence_dir(self, tmp_path: Path):
        aggregator = EvidenceAggregator(tmp_path)
        summary = aggregator.aggregate(tmp_path)
        assert summary.overall_status == "not_run"

    def test_aggregate_with_synthetic_failing_tests(self, tmp_path: Path):
        import xml.etree.ElementTree as ET

        test_dir = tmp_path / "backend" / "tests" / "generated"
        test_dir.mkdir(parents=True)

        root = ET.Element("testsuite", name="test", tests="2", failures="1", errors="0", skipped="0", time="0.1")
        tc1 = ET.SubElement(root, "testcase", name="useloanscapability.contract.test.ts", classname="test", time="0.05")
        ET.SubElement(tc1, "failure", message="AssertionError", type="AssertionError")
        tc2 = ET.SubElement(root, "testcase", name="test_amortization.py", classname="test", time="0.05")

        tree = ET.ElementTree(root)
        xml_path = test_dir / "junit.xml"
        tree.write(xml_path, encoding="utf-8")

        cross_map = {
            "backend/src/engines/loan_engine/amortization.py": {
                "engine": "backend/src/engines/loan_engine/amortization.py",
                "services": ["LoanService"],
                "routers": ["backend/src/routers/loans.py"],
                "endpoints": ["GET /api/loans/{loan_id}/schedule"],
                "capabilities": ["useLoansCapability"],
                "mappers": ["loansMapper"],
                "viewModels": ["LoansViewModel"],
                "pages": ["app/loans/page.tsx"],
                "workspace": ["LoansWorkspace"],
                "components": ["AmortizationTable"],
                "tests": [
                    "backend/tests/unit/engines/loan/test_amortization.py",
                    "backend/tests/contract/generated/test_loans.py",
                ],
                "graphRenderers": [],
            }
        }

        map_path = tmp_path / "cross-layer-map.json"
        map_path.write_text(json.dumps(cross_map), encoding="utf-8")

        with patch(
            "runtime.system.evidence.aggregator.CROSS_LAYER_MAP_PATH", map_path
        ):
            aggregator = EvidenceAggregator(tmp_path)
            summary = aggregator.aggregate(tmp_path)

        assert summary.backend["unit_tests"]["failed"] == 1
        assert len(summary.attention_needed) > 0
