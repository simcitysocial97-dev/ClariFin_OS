"""Markdown Reporter

Generates human-readable markdown reports from audit results.
"""

from datetime import datetime
from typing import List
from reports.base_reporter import BaseReporter
from core.models import AuditResult, Finding, AuditStatus

class MarkdownReporter(BaseReporter):
    """Markdown report generator."""

    def render(self, audit_result: AuditResult) -> str:
        """Render audit result as markdown."""
        report = self._generate_header(audit_result)
        report += self._generate_executive_summary(audit_result)
        report += self._generate_metrics_section(audit_result)
        report += self._generate_findings_section(audit_result)
        report += self._generate_conclusion(audit_result)
        return report

    def save_to_file(self, audit_result: AuditResult, filename: str) -> None:
        """Save the rendered report to a file."""
        report_content = self.render(audit_result)
        with open(filename, 'w') as f:
            f.write(report_content)
        print(f"✅ Report saved to: {filename}")

    def _generate_header(self, audit_result: AuditResult) -> str:
        """Generate report header."""
        return f"""# {audit_result.audit_name}

"""

    def _generate_executive_summary(self, audit_result: AuditResult) -> str:
        """Generate executive summary section."""
        status_emoji = "✅" if audit_result.status == AuditStatus.PASS else "⚠️" if audit_result.status == AuditStatus.WARNING else "🔴"
        status_text = audit_result.status.value

        return f"""## Executive Summary

**Audit Status**: {status_emoji} {status_text}
**Generated**: {audit_result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**Total Findings**: {len(audit_result.findings)}

{self._get_status_description(audit_result)}

---

"""

    def _get_status_description(self, audit_result: AuditResult) -> str:
        """Get status-specific description."""
        if audit_result.status == AuditStatus.PASS:
            return "All checks passed. Financial data appears consistent and complete."
        elif audit_result.status == AuditStatus.WARNING:
            return "Some issues detected that require attention but no critical failures."
        else:
            return "Critical issues detected that require immediate action."

    def _generate_metrics_section(self, audit_result: AuditResult) -> str:
        """Generate metrics section."""
        metrics = audit_result.metrics
        if not metrics:
            return ""

        metrics_section = "## Key Metrics\n\n"

        for metric_name, metric_value in metrics.items():
            if isinstance(metric_value, (int, float)):
                metrics_section += f"- **{metric_name}**: {metric_value:,}\n"
            elif isinstance(metric_value, str):
                metrics_section += f"- **{metric_name}**: {metric_value}\n"
            else:
                metrics_section += f"- **{metric_name}**: {str(metric_value)}\n"

        metrics_section += "\n---\n\n"
        return metrics_section

    def _generate_findings_section(self, audit_result: AuditResult) -> str:
        """Generate findings section."""
        if not audit_result.findings:
            return "## Findings\n\nNo findings reported.\n\n---\n\n"

        findings_section = "## Detailed Findings\n\n"

        # Group findings by severity
        critical_findings = [f for f in audit_result.findings if f.severity == "CRITICAL"]
        high_findings = [f for f in audit_result.findings if f.severity == "HIGH"]
        medium_findings = [f for f in audit_result.findings if f.severity == "MEDIUM"]
        low_findings = [f for f in audit_result.findings if f.severity == "LOW"]

        if critical_findings:
            findings_section += self._format_findings_group("🔴 CRITICAL", critical_findings)
        if high_findings:
            findings_section += self._format_findings_group("🟡 HIGH", high_findings)
        if medium_findings:
            findings_section += self._format_findings_group("🟠 MEDIUM", medium_findings)
        if low_findings:
            findings_section += self._format_findings_group("🔵 LOW", low_findings)

        findings_section += "---\n\n"
        return findings_section

    def _format_findings_group(self, severity_label: str, findings: List[Finding]) -> str:
        """Format a group of findings with the same severity."""
        group_content = f"### {severity_label} Findings ({len(findings)})\n\n"

        for i, finding in enumerate(findings, 1):
            group_content += f"**{i}. {finding.description}**\n"
            if finding.details:
                group_content += f"   - *Details*: {self._format_details(finding.details)}\n"
            group_content += "\n"

        return group_content

    def _format_details(self, details: dict) -> str:
        """Format finding details."""
        detail_items = []
        for key, value in details.items():
            if key != "type":  # Skip the type field as it's internal
                detail_items.append(f"{key}: {value}")
        return ", ".join(detail_items)

    def _generate_conclusion(self, audit_result: AuditResult) -> str:
        """Generate conclusion section."""
        conclusion = "## Conclusion & Recommendations\n\n"

        if audit_result.status == AuditStatus.PASS:
            conclusion += "🎉 **EXCELLENT**: All audit checks passed. The financial data is consistent and complete.\n"
            conclusion += "- No immediate action required\n"
            conclusion += "- Continue regular monitoring\n"
        elif audit_result.status == AuditStatus.WARNING:
            conclusion += "⚠️ **ATTENTION REQUIRED**: Some issues were detected that should be reviewed.\n"
            conclusion += "- Review the findings above and address as appropriate\n"
            conclusion += "- Monitor trends over time\n"
            conclusion += "- Consider implementing automated corrections where possible\n"
        else:
            conclusion += "🔴 **CRITICAL ACTION REQUIRED**: Significant issues detected that need immediate attention.\n"
            conclusion += "- Address critical findings immediately\n"
            conclusion += "- Review data integrity and import processes\n"
            conclusion += "- Consider running a full data validation\n"

        conclusion += "\n---\n\n"
        conclusion += f"**Audit Completed**: {audit_result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        conclusion += f"**Status**: {audit_result.status.value}\n"

        return conclusion