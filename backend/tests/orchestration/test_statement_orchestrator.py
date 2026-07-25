"""Tests for StatementProcessingOrchestrator.

Validates the post-upload pipeline stages and graceful degradation.
"""

from __future__ import annotations

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from src.orchestration.statement_orchestrator import StatementProcessingOrchestrator


class TestStatementProcessingOrchestrator:
    """Tests for StatementProcessingOrchestrator."""

    def test_orchestrator_initialization(self, temp_db: str) -> None:
        """Test orchestrator can be initialized with db_path."""
        orchestrator = StatementProcessingOrchestrator(db_path=temp_db)
        assert orchestrator.db_path == temp_db
        assert orchestrator.behaviour_service is not None
        assert orchestrator.cashflow_service is not None
        assert orchestrator.intelligence_service is not None
        assert orchestrator.loan_service is not None
        assert orchestrator.dashboard_service is not None
        assert orchestrator.transaction_intelligence_service is not None

    def test_process_after_upload_returns_summary(self, temp_db: str) -> None:
        """Test process_after_upload returns summary with all stages."""
        orchestrator = StatementProcessingOrchestrator(db_path=temp_db)
        summary = orchestrator.process_after_upload(statement_id=1)

        assert summary["statement_id"] == 1
        assert "behaviour" in summary
        assert "cashflow" in summary
        assert "intelligence" in summary
        assert "recommendations" in summary
        assert "dashboard" in summary
        assert "transaction_intelligence" in summary

    def test_process_after_upload_graceful_degradation(self, temp_db: str) -> None:
        """Test orchestrator handles failures gracefully."""
        orchestrator = StatementProcessingOrchestrator(db_path=temp_db)
        summary = orchestrator.process_after_upload(statement_id=999999)

        # All stages should either succeed or record an error
        stages = [
            "behaviour", "cashflow", "intelligence",
            "recommendations", "dashboard", "transaction_intelligence",
        ]
        for stage in stages:
            assert stage in summary
            # Either result or error key should exist
            assert stage in summary or f"{stage}_error" in summary

    @patch("src.orchestration.statement_orchestrator.BehaviourService")
    def test_run_behaviour_returns_dict(self, mock_behaviour: MagicMock, temp_db: str) -> None:
        """Test _run_behaviour returns expected dict structure."""
        mock_profile = MagicMock()
        mock_profile.profile_type = "saver"
        mock_behaviour.return_value.compute_financial_profile.return_value = mock_profile

        orchestrator = StatementProcessingOrchestrator(db_path=temp_db)
        result = orchestrator._run_behaviour()
        assert isinstance(result, dict)
        assert result["profile_generated"] is True
        assert result["profile_type"] == "saver"

    @patch("src.orchestration.statement_orchestrator.CashflowService")
    def test_run_cashflow_returns_dict(self, mock_cashflow: MagicMock, temp_db: str) -> None:
        """Test _run_cashflow returns expected dict structure."""
        mock_summary = MagicMock()
        mock_summary.net_cashflow_paise = 50000
        mock_cashflow.return_value.calculate_summary.return_value = mock_summary

        orchestrator = StatementProcessingOrchestrator(db_path=temp_db)
        result = orchestrator._run_cashflow()
        assert isinstance(result, dict)
        assert result["summary_generated"] is True
        assert result["net_cashflow_paise"] == 50000

    @patch("src.orchestration.statement_orchestrator.FinancialIntelligenceService")
    def test_run_intelligence_returns_dict(self, mock_intelligence: MagicMock, temp_db: str) -> None:
        """Test _run_intelligence returns expected dict structure."""
        mock_intelligence.return_value.get_financial_outlook.return_value = {"outlook": "positive"}
        mock_intelligence.return_value.get_optimization_plan.return_value = {"plan": "save more"}
        mock_intelligence.return_value.get_financial_intelligence_report.return_value = {"report": "good"}

        orchestrator = StatementProcessingOrchestrator(db_path=temp_db)
        result = orchestrator._run_intelligence()
        assert isinstance(result, dict)
        assert result["outlook_generated"] is True
        assert result["optimization_generated"] is True
        assert result["report_generated"] is True

    @patch("src.orchestration.statement_orchestrator.DashboardService")
    def test_run_dashboard_refresh_returns_dict(self, mock_dashboard: MagicMock, temp_db: str) -> None:
        """Test _run_dashboard_refresh returns expected dict structure."""
        mock_summary = MagicMock()
        mock_dashboard.return_value.get_summary.return_value = mock_summary

        orchestrator = StatementProcessingOrchestrator(db_path=temp_db)
        result = orchestrator._run_dashboard_refresh()
        assert isinstance(result, dict)
        assert result["refreshed"] is True
        assert result["summary_available"] is True

    @patch("src.orchestration.statement_orchestrator.TransactionIntelligenceService")
    def test_run_transaction_intelligence_returns_dict(self, mock_ti: MagicMock, temp_db: str) -> None:
        """Test _run_transaction_intelligence returns expected dict structure."""
        mock_ti.return_value.classify_emi_payments.return_value = [1, 2]
        mock_ti.return_value.classify_cc_payments.return_value = [3]
        mock_ti.return_value.classify_cash_conversions.return_value = [4, 5]

        orchestrator = StatementProcessingOrchestrator(db_path=temp_db)
        result = orchestrator._run_transaction_intelligence()
        assert isinstance(result, dict)
        assert result["emi_classified"] == 2
        assert result["cc_classified"] == 1
        assert result["cash_conversions_classified"] == 2
        assert result["total_classified"] == 5
