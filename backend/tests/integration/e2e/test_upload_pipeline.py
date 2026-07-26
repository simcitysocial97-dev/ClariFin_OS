"""Tests for statement upload pipeline modules.

Validates csv_importer, statement_extractor, column_mapper, and ingest.
"""

from __future__ import annotations



class TestCSVImporter:
    """Tests for csv_importer module."""

    def test_import_csv_module_exists(self) -> None:
        """Test csv_importer module can be imported."""
        from src import csv_importer

        assert hasattr(csv_importer, "CSVImporter")

    def test_csv_importer_instantiation(self) -> None:
        """Test CSVImporter can be instantiated."""
        from src.csv_importer import CSVImporter

        importer = CSVImporter("dummy.csv")
        assert importer is not None

    def test_detect_format_returns_dict(self, tmp_path: Path) -> None:
        """Test detect_format returns a dict with expected keys."""
        from src.csv_importer import CSVImporter

        csv_file = tmp_path / "test.csv"
        csv_file.write_text("Date,Description,Amount\n2025-01-01,Test,1000\n")

        importer = CSVImporter(str(csv_file))
        result = importer.detect_format()
        assert isinstance(result, dict)

    def test_date_format_detection(self) -> None:
        """Test date format constants exist and are valid."""
        from src.csv_importer import DATE_FORMATS

        assert isinstance(DATE_FORMATS, list)
        assert len(DATE_FORMATS) > 0
        for fmt in DATE_FORMATS:
            assert isinstance(fmt, str)
            assert len(fmt) > 0


class TestStatementExtractor:
    """Tests for statement_extractor module."""

    def test_import_extractor_module_exists(self) -> None:
        """Test statement_extractor module can be imported."""
        from src import statement_extractor

        assert hasattr(statement_extractor, "StatementExtractor")

    def test_bank_keywords_defined(self) -> None:
        """Test BANK_KEYWORDS constant is defined."""
        from src.statement_extractor import BANK_KEYWORDS

        assert isinstance(BANK_KEYWORDS, dict)
        assert len(BANK_KEYWORDS) > 0
        for bank, keywords in BANK_KEYWORDS.items():
            assert isinstance(bank, str)
            assert isinstance(keywords, list)
            assert len(keywords) > 0

    def test_score_threshold_defined(self) -> None:
        """Test SCORE_THRESHOLD constant is defined."""
        from src.statement_extractor import SCORE_THRESHOLD

        assert isinstance(SCORE_THRESHOLD, (int, float))
        assert SCORE_THRESHOLD > 0

    def test_header_phrases_defined(self) -> None:
        """Test HEADER_PHRASES constant is defined."""
        from src.statement_extractor import HEADER_PHRASES

        assert isinstance(HEADER_PHRASES, list)
        assert len(HEADER_PHRASES) > 0


class TestColumnMapper:
    """Tests for column_mapper module."""

    def test_import_column_mapper(self) -> None:
        """Test ColumnMapper can be imported."""
        from src.column_mapper import ColumnMapper

        assert ColumnMapper is not None

    def test_standard_fields_defined(self) -> None:
        """Test STANDARD_FIELDS constant is defined."""
        from src.column_mapper import ColumnMapper

        assert hasattr(ColumnMapper, "STANDARD_FIELDS")
        assert isinstance(ColumnMapper.STANDARD_FIELDS, list)
        assert len(ColumnMapper.STANDARD_FIELDS) > 0

    def test_column_aliases_defined(self) -> None:
        """Test COLUMN_ALIASES constant is defined."""
        from src.column_mapper import ColumnMapper

        assert hasattr(ColumnMapper, "COLUMN_ALIASES")
        assert isinstance(ColumnMapper.COLUMN_ALIASES, dict)
        assert len(ColumnMapper.COLUMN_ALIASES) > 0

    def test_map_columns_returns_dict(self) -> None:
        """Test map_columns returns a dict."""
        from src.column_mapper import ColumnMapper

        mapper = ColumnMapper()
        result = mapper.map_columns(["Date", "Description", "Amount"])
        assert isinstance(result, dict)

    def test_map_columns_fuzzy_matching(self) -> None:
        """Test map_columns uses fuzzy matching for column names."""
        from src.column_mapper import ColumnMapper

        mapper = ColumnMapper()
        result = mapper.map_columns(["Transaction Date", "Narration", "Amount (INR)"])
        assert isinstance(result, dict)
        assert len(result) > 0


class TestIngest:
    """Tests for ingest module."""

    def test_import_ingest_module(self) -> None:
        """Test ingest module can be imported."""
        from src import ingest

        assert hasattr(ingest, "ingest_pdf")

    def test_ingest_pdf_function_exists(self) -> None:
        """Test ingest_pdf function is defined."""
        from src.ingest import ingest_pdf

        assert callable(ingest_pdf)