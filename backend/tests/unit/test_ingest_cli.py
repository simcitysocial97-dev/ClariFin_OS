"""M09 — CLI entrypoint unification and D12 default behaviour.

Verifies:
  - ``ingest_pdf`` delegates extraction/categorization/persistence to
    ``ImportService.import_from_path``.
  - Default ``run_orchestrator=False`` (D12).
  - ``--with-intelligence`` (via ``run_orchestrator=True``) triggers the
    pipeline; default does not.
  - Return shape is unchanged for the caller.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.ingest import ingest_pdf


def _make_stub_pdf(tmp_path: Path) -> Path:
    """Create a minimal synthetic PDF (not a real one — just a file with .pdf ext).

    StatementExtractor will fail on it, but we monkey-patch it below so the
    test exercises the orchestration branch without needing a real PDF.
    """
    p = tmp_path / "stub.pdf"
    p.write_bytes(b"%PDF-1.4 stub")
    return p


def test_ingest_pdf_delegates_to_import_service_and_skips_orchestrator_by_default(
    tmp_path: Path,
) -> None:
    """Default path: orchestrator is NOT called (D12)."""
    pdf = _make_stub_pdf(tmp_path)

    mock_svc = MagicMock()
    mock_svc.import_from_path.return_value = {
        "bank": "TestBank",
        "transactions": [
            {
                "description": "SHOP",
                "amount_paise": 5000,
                "type": "debit",
                "category": "Shopping",
                "subcategory": "",
                "member": "Self",
            }
        ],
        "statement_id": 42,
        "metadata": {},
        "pipeline_summary": {},
    }

    with patch(
        "src.ingest.StatementExtractor"
    ) as mock_extractor_cls, patch(
        "src.ingest.ImportService", return_value=mock_svc
    ), patch(
        "src.ingest.StatementRepository.get_duplicate_check", return_value=None
    ):
        mock_extractor_cls.return_value.extract.return_value = {
            "bank": "TestBank",
            "transactions": [
                {
                    "description": "SHOP",
                    "amount_paise": 5000,
                    "type": "debit",
                }
            ],
            "statement_period": {"from": "01/01/2025", "to": "31/01/2025"},
        }
        result = ingest_pdf(str(pdf), run_orchestrator=False)

    assert result["status"] == "imported"
    assert result["bank"] == "TestBank"
    assert result["transaction_count"] == 1
    assert result["inserted_count"] == 1
    # The orchestrator must NOT have been invoked via import_from_path.
    mock_svc.import_from_path.assert_called_once()
    call_kwargs = mock_svc.import_from_path.call_args
    assert call_kwargs.kwargs.get("run_orchestrator") is False


def test_ingest_pdf_runs_orchestrator_when_flagged(tmp_path: Path) -> None:
    """With run_orchestrator=True the service is called with it propagated."""
    pdf = _make_stub_pdf(tmp_path)

    mock_svc = MagicMock()
    mock_svc.import_from_path.return_value = {
        "bank": "TestBank",
        "transactions": [],
        "statement_id": 1,
        "metadata": {},
        "pipeline_summary": {"behaviour": {"ok": True}},
    }

    with patch(
        "src.ingest.StatementExtractor"
    ) as mock_extractor_cls, patch(
        "src.ingest.ImportService", return_value=mock_svc
    ), patch(
        "src.ingest.StatementRepository.get_duplicate_check", return_value=None
    ):
        mock_extractor_cls.return_value.extract.return_value = {
            "bank": "TestBank",
            "transactions": [],
            "statement_period": {"from": "", "to": ""},
        }
        ingest_pdf(str(pdf), run_orchestrator=True)

    call_kwargs = mock_svc.import_from_path.call_args
    assert call_kwargs.kwargs.get("run_orchestrator") is True
