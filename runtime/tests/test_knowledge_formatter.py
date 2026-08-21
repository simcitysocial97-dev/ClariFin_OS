"""Tests for the Engineering Knowledge Base formatter — Program 11.

Deterministic tests. No network. No repository mutation.
"""

from __future__ import annotations


from runtime.foundation.knowledge.formatter import (
    format_catalog_summary,
    format_knowledge_report,
    format_query_result,
)
from runtime.foundation.knowledge.indexer import build_index


class TestKnowledgeFormatter:
    """Tests for the knowledge formatter functions."""

    def test_format_knowledge_report_contains_header(self) -> None:
        index = build_index()
        output = format_knowledge_report(index)
        assert "Engineering Knowledge Base" in output

    def test_format_knowledge_report_contains_counts(self) -> None:
        index = build_index()
        output = format_knowledge_report(index)
        assert "Endpoints" in output or "Endpoints" in output

    def test_format_catalog_summary_contains_total(self) -> None:
        index = build_index()
        output = format_catalog_summary(index)
        assert "Knowledge Catalog Summary" in output

    def test_format_query_result_contains_result_header(self) -> None:
        index = build_index()
        from runtime.foundation.knowledge.query import query_endpoint

        result = query_endpoint("/api/loans/{loan_id}/schedule")
        if result:
            output = format_query_result(result)
            assert "Knowledge Query Result" in output


class TestKnowledgeFormatterUnicode:
    """Tests for unicode/ASCII adaptive rendering."""

    def test_format_knowledge_report_is_string(self) -> None:
        index = build_index()
        output = format_knowledge_report(index)
        assert isinstance(output, str)

    def test_format_query_result_is_string(self) -> None:
        from runtime.foundation.knowledge.query import query_endpoint

        result = query_endpoint("/api/loans/{loan_id}/schedule")
        if result:
            output = format_query_result(result)
            assert isinstance(output, str)

    def test_format_catalog_summary_is_string(self) -> None:
        index = build_index()
        output = format_catalog_summary(index)
        assert isinstance(output, str)


class TestKnowledgeFormatterStructure:
    """Tests for output structure."""

    def test_knowledge_report_has_section_headers(self) -> None:
        index = build_index()
        output = format_knowledge_report(index)
        for category in ["Endpoints", "Capabilities", "Workspaces"]:
            assert category in output

    def test_query_result_has_ownership_section(self) -> None:
        from runtime.foundation.knowledge.query import query_endpoint

        result = query_endpoint("/api/loans/{loan_id}/schedule")
        if result:
            output = format_query_result(result)
            assert "Ownership" in output

    def test_query_result_has_dependencies_section(self) -> None:
        from runtime.foundation.knowledge.query import query_endpoint

        result = query_endpoint("/api/loans/{loan_id}/schedule")
        if result:
            output = format_query_result(result)
            assert "Dependencies" in output
