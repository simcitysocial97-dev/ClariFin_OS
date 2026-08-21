"""Professional terminal formatter — Program 11.

Adaptive Unicode/ASCII. Readable hierarchy. No JSON dumps.
"""

from __future__ import annotations

import sys
from typing import Any

from runtime.foundation.knowledge.models import (
    KnowledgeIndex,
    QueryResult,
    RelationshipChain,
)


def _supports_unicode() -> bool:
    if not hasattr(sys.stdout, "isatty"):
        return False
    if not sys.stdout.isatty():
        return False
    encoding = getattr(sys.stdout, "encoding", "ascii")
    if not encoding:
        return False
    try:
        "─│├┬┴◆●■□".encode(encoding)
        return True
    except (UnicodeEncodeError, LookupError):
        return False


_USE_UNICODE = _supports_unicode()

if _USE_UNICODE:
    _H = "─"
    _V = "│"
    _TL = "┌"
    _TR = "┐"
    _BL = "└"
    _BR = "┘"
    _TJ = "┬"
    _BJ = "┴"
    _LR = "├"
    _CR = "┤"
    _X = "┼"
else:
    _H = "-"
    _V = "|"
    _TL = "+"
    _TR = "+"
    _BL = "+"
    _BR = "+"
    _TJ = "+"
    _BJ = "+"
    _LR = "+"
    _CR = "+"
    _X = "+"


def _pad(text: str, width: int, align: str = "left") -> str:
    text = str(text)
    if align == "right":
        return text.rjust(width)
    return text.ljust(width)


def _truncate(text: str, width: int) -> str:
    text = str(text)
    if len(text) > width:
        return text[: width - 1] + "…"
    return text


def _terminal_width() -> int:
    try:
        import shutil

        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def format_knowledge_report(index: KnowledgeIndex) -> str:
    """Format a KnowledgeIndex as a professional terminal report."""
    lines: list[str] = []
    width = _terminal_width()

    # Header
    lines.append(_TL + _H * (width - 2) + _TR)
    title = "Engineering Knowledge Base"
    lines.append(_V + _pad(title, width - 2) + _V)
    lines.append(_BL + _H * (width - 2) + _BR)
    lines.append("")

    # Summary
    lines.append(f"Indexed at: {index.indexed_at}")
    lines.append(f"Source artifacts: {len(index.source_artifacts)}")
    lines.append("")

    # Category counts table
    count_headers = ["Category", "Count"]
    count_rows = [
        ["Endpoints", str(len(index.endpoints))],
        ["Capabilities", str(len(index.capabilities))],
        ["Mappers", str(len(index.mappers))],
        ["ViewModels", str(len(index.view_models))],
        ["Workspaces", str(len(index.workspaces))],
        ["Components", str(len(index.components))],
        ["GraphRenderers", str(len(index.graph_renderers))],
        ["VerificationProfiles", str(len(index.verification_profiles))],
        ["IntegrityRules", str(len(index.integrity_rules))],
        ["RuntimeArtifacts", str(len(index.runtime_artifacts))],
        ["Documentation", str(len(index.documentation))],
    ]
    lines.append(_render_table(count_headers, count_rows))
    lines.append("")

    # Detail sections
    if index.endpoints:
        lines.append(_section("Endpoints"))
        ep_headers = ["Method", "Path", "References"]
        ep_rows = []
        for ep in index.endpoints:
            ref_count = len(ep.references)
            ep_rows.append([ep.method, ep.path, str(ref_count)])
        lines.append(_render_table(ep_headers, ep_rows))
        lines.append("")

    if index.capabilities:
        lines.append(_section("Capabilities"))
        cap_headers = ["Name", "References"]
        cap_rows = []
        for cap in index.capabilities:
            name = getattr(cap, "name", str(cap))
            ref_count = len(getattr(cap, "references", {}))
            cap_rows.append([name, str(ref_count)])
        lines.append(_render_table(cap_headers, cap_rows))
        lines.append("")

    if index.mappers:
        lines.append(_section("Mappers"))
        mp_headers = ["Name", "References"]
        mp_rows = [[mp.name, str(len(mp.references))] for mp in index.mappers]
        lines.append(_render_table(mp_headers, mp_rows))
        lines.append("")

    if index.view_models:
        lines.append(_section("ViewModels"))
        vm_headers = ["Name", "References"]
        vm_rows = [[vm.name, str(len(vm.references))] for vm in index.view_models]
        lines.append(_render_table(vm_headers, vm_rows))
        lines.append("")

    if index.workspaces:
        lines.append(_section("Workspaces"))
        ws_headers = ["Name", "References"]
        ws_rows = [[ws.name, str(len(ws.references))] for ws in index.workspaces]
        lines.append(_render_table(ws_headers, ws_rows))
        lines.append("")

    if index.components:
        lines.append(_section("Components"))
        comp_headers = ["Name", "References"]
        comp_rows = [
            [comp.name, str(len(comp.references))] for comp in index.components
        ]
        lines.append(_render_table(comp_headers, comp_rows))
        lines.append("")

    if index.integrity_rules:
        lines.append(_section("Integrity Rules"))
        rule_headers = ["Rule ID", "Category", "Severity"]
        rule_rows = []
        for rule in index.integrity_rules:
            cat = rule.references.get("category", "")
            sev = rule.references.get("severity", "")
            rule_rows.append([rule.rule_id, cat, sev])
        lines.append(_render_table(rule_headers, rule_rows))
        lines.append("")

    if index.documentation:
        lines.append(_section("Documentation"))
        doc_headers = ["Title", "Path"]
        doc_rows = [[doc.title, doc.path] for doc in index.documentation]
        lines.append(_render_table(doc_headers, doc_rows))
        lines.append("")

    # Footer
    lines.append(_TL + _H * (width - 2) + _TR)
    total = (
        len(index.endpoints)
        + len(index.capabilities)
        + len(index.mappers)
        + len(index.view_models)
        + len(index.workspaces)
        + len(index.components)
        + len(index.graph_renderers)
        + len(index.verification_profiles)
        + len(index.integrity_rules)
        + len(index.runtime_artifacts)
        + len(index.documentation)
    )
    lines.append(
        _V
        + _pad(
            f"Knowledge Base operational — {total} total entries",
            width - 2,
        )
        + _V
    )
    lines.append(_BL + _H * (width - 2) + _BR)

    return "\n".join(lines)


def format_query_result(result: QueryResult | None) -> str:
    """Format a QueryResult as a professional terminal report."""
    if result is None:
        return "No matching entry found."

    lines: list[str] = []
    width = _terminal_width()

    lines.append(_TL + _H * (width - 2) + _TR)
    lines.append(_V + _pad("Knowledge Query Result", width - 2) + _V)
    lines.append(_BL + _H * (width - 2) + _BR)
    lines.append("")

    # Entry info - handle different entry types
    entry = result.entry
    if hasattr(entry, "path") and hasattr(entry, "method"):
        lines.append(f"Path: {entry.path}")
        lines.append(f"Method: {entry.method}")
        lines.append("Category: endpoint")
    elif hasattr(entry, "rule_id"):
        lines.append(f"Rule ID: {entry.rule_id}")
        lines.append("Category: integrity_rule")
    elif hasattr(entry, "name"):
        lines.append(f"ID: {entry.id if hasattr(entry, 'id') else entry.name}")
        lines.append(f"Name: {entry.name}")
        lines.append(
            f"Category: {entry.category if hasattr(entry, 'category') else 'unknown'}"
        )
    lines.append("")

    # Ownership
    if result.ownership:
        lines.append(_bold("Ownership"))
        for key, value in result.ownership.items():
            lines.append(f"  {key}: {value}")
        lines.append("")

    # Dependencies
    if result.dependencies:
        lines.append(_bold("Dependencies"))
        for dep in result.dependencies:
            lines.append(f"  • {dep}")
        lines.append("")

    # Verification profile
    if result.verification_profile:
        lines.append(f"Verification Profile: {result.verification_profile}")
        lines.append("")

    # Integrity rules
    if result.integrity_rules:
        lines.append(_bold("Integrity Rules"))
        for rule in result.integrity_rules:
            lines.append(f"  • {rule}")
        lines.append("")

    # Documentation references
    if result.documentation_references:
        lines.append(_bold("Documentation References"))
        for doc in result.documentation_references:
            lines.append(f"  • {doc}")
        lines.append("")

    # Related artifacts
    if result.related_artifacts:
        lines.append(_bold("Related Runtime Artifacts"))
        for art in result.related_artifacts:
            lines.append(f"  • {art}")
        lines.append("")

    # Footer
    lines.append(_TL + _H * (width - 2) + _TR)

    return "\n".join(lines)


def format_catalog_summary(index: KnowledgeIndex) -> str:
    """Format a compact catalog summary."""
    lines: list[str] = []
    width = _terminal_width()

    lines.append(_TL + _H * (width - 2) + _TR)
    lines.append(_V + _pad("Knowledge Catalog Summary", width - 2) + _V)
    lines.append(_BL + _H * (width - 2) + _BR)
    lines.append("")

    total = (
        len(index.endpoints)
        + len(index.capabilities)
        + len(index.mappers)
        + len(index.view_models)
        + len(index.workspaces)
        + len(index.components)
        + len(index.graph_renderers)
        + len(index.verification_profiles)
        + len(index.integrity_rules)
        + len(index.runtime_artifacts)
        + len(index.documentation)
    )

    lines.append(f"Total indexed entities: {total}")
    lines.append(f"Indexed at: {index.indexed_at}")
    lines.append("")

    headers = ["Category", "Count"]
    rows = [
        ["Endpoints", str(len(index.endpoints))],
        ["Capabilities", str(len(index.capabilities))],
        ["Mappers", str(len(index.mappers))],
        ["ViewModels", str(len(index.view_models))],
        ["Workspaces", str(len(index.workspaces))],
        ["Components", str(len(index.components))],
        ["GraphRenderers", str(len(index.graph_renderers))],
        ["VerificationProfiles", str(len(index.verification_profiles))],
        ["IntegrityRules", str(len(index.integrity_rules))],
        ["RuntimeArtifacts", str(len(index.runtime_artifacts))],
        ["Documentation", str(len(index.documentation))],
    ]
    lines.append(_render_table(headers, rows))

    lines.append("")
    lines.append(_TL + _H * (width - 2) + _TR)

    return "\n".join(lines)


def format_relationship_chains(chains: list[RelationshipChain]) -> str:
    """Format relationship chains as a terminal report."""
    lines: list[str] = []
    width = _terminal_width()

    lines.append(_TL + _H * (width - 2) + _TR)
    lines.append(_V + _pad("Relationship Chains", width - 2) + _V)
    lines.append(_BL + _H * (width - 2) + _BR)
    lines.append("")

    if not chains:
        lines.append("No relationships found.")
        lines.append("")
        lines.append(_TL + _H * (width - 2) + _TR)
        return "\n".join(lines)

    headers = [
        "Source",
        "Source Type",
        "Target",
        "Target Type",
        "Relationship",
        "Depth",
    ]
    rows = [
        [
            c.source,
            c.source_type,
            c.target,
            c.target_type,
            c.relationship,
            str(c.depth),
        ]
        for c in chains
    ]
    lines.append(_render_table(headers, rows))
    lines.append("")
    lines.append(_TL + _H * (width - 2) + _TR)

    return "\n".join(lines)


def _render_table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return ""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            if idx < len(col_widths):
                col_widths[idx] = max(col_widths[idx], len(str(cell)))

    terminal_width = _terminal_width()
    total = sum(col_widths) + (len(col_widths) - 1) * 3 + 2
    if total > terminal_width and col_widths:
        overflow = total - terminal_width
        max_width = max(col_widths)
        if max_width > 10:
            reduce = min(overflow // len(col_widths) + 1, max_width - 10)
            col_widths = [max(10, w - reduce) for w in col_widths]

    header_line = _TL + _H * (sum(col_widths) + (len(col_widths) - 1) * 3) + _TR
    result: list[str] = [header_line]

    header_cells = [_pad(_truncate(h, w), w) for h, w in zip(headers, col_widths)]
    result.append(_V + " " + " ".join(header_cells) + " " + _V)

    sep = _LR + _H * (sum(col_widths) + (len(col_widths) - 1) * 3) + _CR
    result.append(sep)

    for row in rows:
        cells = [_pad(_truncate(str(c), w), w) for c, w in zip(row, col_widths)]
        result.append(_V + " " + " ".join(cells) + " " + _V)

    footer_line = _BL + _H * (sum(col_widths) + (len(col_widths) - 1) * 3) + _BR
    result.append(footer_line)
    return "\n".join(result)


def _bold(text: str) -> str:
    return _color(1, text)


def _color(code: int, text: str) -> str:
    if not _USE_UNICODE:
        return str(text)
    return f"\033[{code}m{text}\033[0m"


def _section(title: str) -> str:
    width = _terminal_width()
    if _USE_UNICODE:
        return f"\n{_TL}{_H * (width - 2)}{_TR}\n{_V} {_pad(title, width - 4)} {_V}\n{_BL}{_H * (width - 2)}{_BR}\n"
    return f"\n+{'-' * (width - 2)}+\n| {_pad(title, width - 4)} |\n+{'-' * (width - 2)}+\n"
