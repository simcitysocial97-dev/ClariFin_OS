"""Import Service - Orchestration layer for statement and CSV import operations.

Coordinates StatementService, TransactionService, and BehaviourService to implement import business logic.
No direct database access in routers — all data operations go through this service layer.
"""

from pathlib import Path
from typing import Any

from src.extraction.categorizer import categorize
from src.extraction.csv_importer import CSVImporter
from src.extraction.metadata_extractor import MetadataExtractor
from src.extraction.statement_extractor import StatementExtractor

# Note: StatementProcessingOrchestrator is imported lazily to avoid circular dependency
from src.services.base import BaseService
from src.services.behaviour_service import BehaviourService
from src.services.statement_service import StatementService
from src.services.transaction_service import TransactionService

UPLOAD_DIR = Path(__file__).parent.parent.parent / "data" / "uploads"


class ImportService(BaseService):
    """Orchestrates statement and CSV import operations.

    Delegates persistence to StatementRepository and TransactionRepository,
    delegates categorization and extraction to dedicated engines, and
    delegates post-upload pipeline to StatementProcessingOrchestrator.
    """

    def __init__(self, db_path: str | None = None) -> None:
        super().__init__(db_path)
        self.statement_service = StatementService(self.db_path)
        self.transaction_service = TransactionService(self.db_path)
        self.behaviour_service = BehaviourService(self.db_path)

    def upload_statement(
        self,
        save_path: str,
        filename: str,
        member: str = "Self",
    ) -> dict[str, Any]:
        """Process a PDF statement upload: extract, categorize, store, validate.

        Args:
            save_path: Path to the saved PDF file.
            filename: Original filename.
            member: Member name for transactions.

        Returns:
            Dict with success, bank, transaction_count, validation_status,
            metadata, log entries, and pipeline_summary.
        """
        log: list[str] = []

        # Check duplicate (fast-path; aligns with existing contract tests).
        if self.statement_service.repo.get_duplicate_check_by_filename(filename):
            return {
                "success": False,
                "error": "File already imported",
                "log": log + ["⚠️ Already imported, skipping"],
            }

        # Shared pipeline: extract → categorize → persist → (optional) orchestrator.
        svc_result = self.import_from_path(str(save_path), member=member)

        # Validate and enrich log (original post-import behaviour).
        val_status = self._validate_statement(
            svc_result["transactions"],
            svc_result.get("metadata", {}),
            log,
            svc_result["statement_id"],
        )
        log.append(f"✅ Saved (Member: {member})")

        pipeline_summary: dict[str, Any] = svc_result.get("pipeline_summary", {})
        completed = [
            k
            for k, v in pipeline_summary.items()
            if v is not None and not k.endswith("_error")
        ]
        if completed:
            log.append(f"✅ Pipeline: {', '.join(completed)}")

        return {
            "success": True,
            "bank": svc_result["bank"],
            "transaction_count": len(svc_result["transactions"]),
            "validation_status": val_status,
            "metadata": svc_result.get("metadata", {}),
            "log": log,
            # M08: additive key surfaced for caller visibility.
            "pipeline_summary": pipeline_summary,
        }

    def import_from_path(
        self,
        pdf_path: str,
        member: str = "Self",
        run_orchestrator: bool = True,
    ) -> dict[str, Any]:
        """Shared PDF-statement pipeline: extract → categorize → persist → (optionally) trigger post-upload intelligence.

        This is the single canonical ingestion entrypoint for PDF statements.
        HTTP handlers and the CLI both route through here (M09-D12).

        Args:
            pdf_path: Absolute or relative path to the PDF file.
            member: Member name assigned to imported transactions.
            run_orchestrator: When ``True`` (default) the post-upload
                intelligence pipeline runs after persist; when ``False``
                the CLI path stays lightweight per D12.

        Returns:
            Dict with ``bank``, ``transactions``, ``statement_id``,
            ``metadata``, and optionally ``pipeline_summary``.
        """
        # Extract
        extractor = StatementExtractor(pdf_path)
        data = extractor.extract()
        bank = data.get("bank", "Unknown")
        transactions = data.get("transactions", [])

        # Categorize
        for txn in transactions:
            amount_paise = int(txn.get("amount_paise") or 0)
            amount_float = amount_paise / 100.0 if amount_paise else 0.0
            cat, subcat = categorize(txn.get("description", ""), amount_float)
            txn["category"] = cat
            txn["subcategory"] = subcat
            txn["member"] = member

        # Insert
        period = data.get("statement_period", {})
        statement_id = self.statement_service.repo.insert_statement(
            bank=bank,
            file_name=Path(pdf_path).name,
            period_from=period.get("from", ""),
            period_to=period.get("to", ""),
        )
        self.transaction_service.repo.insert_transactions(statement_id, transactions)

        # Metadata
        metadata: dict[str, Any] = {}
        try:
            meta_extractor = MetadataExtractor(pdf_path, bank=bank)
            metadata = meta_extractor.extract()
            self.statement_service.repo.update_statement_metadata(
                statement_id, metadata
            )
        except Exception:
            pass  # metadata is best-effort; callers handle gracefully.

        # Invalidate behaviour cache (shared invariant).
        from src.engines.behaviour_engine.core import invalidate_behavior_cache

        invalidate_behavior_cache()

        # Optional post-upload pipeline (M09-D12: default True, CLI may opt-out).
        pipeline_summary: dict[str, Any] = {}
        if run_orchestrator:
            try:
                from src.orchestration.statement_orchestrator import (
                    StatementProcessingOrchestrator,
                )

                orchestrator = StatementProcessingOrchestrator()
                pipeline_summary = orchestrator.process_after_upload(statement_id)
            except Exception:
                pass  # pipeline failure must never abort the import.

        return {
            "bank": bank,
            "transactions": transactions,
            "statement_id": statement_id,
            "metadata": metadata,
            "pipeline_summary": pipeline_summary,
        }

    def _validate_statement(
        self,
        transactions: list[dict[str, Any]],
        metadata: dict[str, Any],
        log: list[str],
        statement_id: int,
    ) -> str:
        """Validate transaction totals against metadata total due.

        Returns the validation status string.
        """
        total_due = metadata.get("total_amount_due")
        if not total_due or total_due <= 0:
            self.statement_service.repo.update_validation_status(
                statement_id, "no_metadata", 0.0
            )
            log.append("⚠️ Validation: total due not found")
            return "no_metadata"

        total_due_paise = int(round(total_due * 100))
        debit_sum_paise = sum(
            int(t.get("amount_paise") or 0)
            for t in transactions
            if t.get("type") == "debit"
        )
        credit_sum_paise = sum(
            int(t.get("amount_paise") or 0)
            for t in transactions
            if t.get("type") == "credit"
        )
        net_paise = debit_sum_paise - credit_sum_paise
        diff_paise = abs(net_paise - total_due_paise)
        diff_rupees = diff_paise / 100.0

        if diff_paise < 100:
            val_status = "exact_match"
            log.append("✅ Validation: exact match")
        elif diff_paise < 5000:
            val_status = "close_match"
            log.append(f"⚠️ Validation: close match (₹{diff_rupees:.2f} off)")
        else:
            val_status = "mismatch"
            log.append(f"❌ Validation: mismatch (₹{diff_rupees:.2f} off)")

        self.statement_service.repo.update_validation_status(
            statement_id, val_status, round(diff_rupees, 2)
        )
        return val_status

    def import_csv(
        self,
        save_path: str,
        mapping: dict[str, Any],
        member: str = "Self",
    ) -> dict[str, Any]:
        """Execute a CSV/Excel import using the provided column mapping.

        Args:
            save_path: Path to the saved file.
            mapping: Column mapping from the client.
            member: Member name for imported transactions.

        Returns:
            Dict with success, count, skipped, and errors.
        """
        importer = CSVImporter(str(save_path))
        transactions, warnings = importer.import_transactions(mapping)

        if not transactions:
            return {
                "success": False,
                "error": "No valid transactions found",
                "warnings": warnings,
            }

        inserted = self.transaction_service.repo.insert_csv_transactions(
            transactions=transactions,
            member=member,
            source="csv",
            bank=mapping.get("bank", "Manual Import"),
            file_name=Path(save_path).name,
        )

        from src.engines.behaviour_engine.core import invalidate_behavior_cache

        invalidate_behavior_cache()

        return {
            "success": True,
            "count": inserted,
            "skipped": len(transactions) - inserted,
            "errors": warnings,
        }

    def detect_import_format(self, save_path: str) -> dict[str, Any]:
        """Detect the CSV/Excel format and return column metadata.

        Args:
            save_path: Path to the saved file.

        Returns:
            Dict with filename, columns, sample_rows, detected_mapping,
            row_count, date_format, and skip_rows.
        """
        from pathlib import Path as PathLib

        filename = PathLib(save_path).name
        importer = CSVImporter(str(save_path))
        detected = importer.detect_format()

        return {
            "filename": filename,
            "columns": detected.get("columns", []),
            "sample_rows": detected.get("sample_rows", []),
            "detected_mapping": detected.get("detected_mapping", {}),
            "row_count": detected.get("row_count", 0),
            "date_format": detected.get("date_format", "%d/%m/%Y"),
            "skip_rows": detected.get("skip_rows", 0),
        }
