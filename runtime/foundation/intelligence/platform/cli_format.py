"""Canonical CLI formatter — Program 14.1.

Formats the canonical intelligence outputs for the ``affected``, ``diagnose``,
``repair`` and ``risk`` commands. This replaces the legacy
``runtime/foundation/intelligence/formatter.py`` which formatted the
pre-14.0 dataclasses. Output is produced from canonical ``platform`` objects
only; no selection or inference happens here.
"""

from __future__ import annotations

import sys

from runtime.foundation.intelligence.platform.blast import BlastRadius
from runtime.foundation.intelligence.platform.change import ChangeIntelligence
from runtime.foundation.intelligence.platform.optimizer import VerificationPlanIntel
from runtime.foundation.intelligence.platform.repair import RepairPlan
from runtime.foundation.intelligence.platform.risk import EngineeringRisk

__all__ = [
    "format_affected",
    "format_diagnostic",
    "format_repair",
    "format_risk",
]


def _color(code: int, text: str) -> str:
    if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text


def _bold(t: str) -> str:
    return _color(1, t)


def _cyan(t: str) -> str:
    return _color(36, t)


def _yellow(t: str) -> str:
    return _color(33, t)


def _green(t: str) -> str:
    return _color(32, t)


def _red(t: str) -> str:
    return _color(31, t)


def format_affected(blast: BlastRadius, plan: VerificationPlanIntel) -> str:
    lines: list[str] = [_bold("Affected Tests (provider-resolved)"), ""]
    if blast.verification:
        lines.append(_cyan(f"Provider-recorded tests ({len(blast.verification)})"))
        for ref in blast.verification:
            lines.append(f"  {ref.key}")
        lines.append("")
    if plan.selected:
        lines.append(_cyan("Verification units selected"))
        for unit in plan.selected:
            lines.append(f"  {_yellow(unit.id)} — {unit.command}")
        lines.append("")
    if plan.skipped:
        lines.append(_cyan("Verification skipped (justified)"))
        for skipped in plan.skipped:
            lines.append(f"  {skipped.id} — {skipped.reason}")
        lines.append("")
    lines.append(f"Total affected entities: {len(blast.all_impacted)}")
    return "\n".join(lines)


def format_diagnostic(
    change: ChangeIntelligence,
    blast: BlastRadius,
    risk: EngineeringRisk,
    repair: RepairPlan,
) -> str:
    lines: list[str] = [_bold("Developer Diagnostic"), ""]
    lines.append(_cyan("Changed files"))
    for f in change.changeset.files:
        lines.append(f"  {f.path} ({f.status})")
    lines.append("")

    lines.append(_cyan("Ownership (provider-resolved)"))
    for ref in change.owning_engines:
        lines.append(f"  {ref.ref}")
    if change.unmapped_paths:
        lines.append(_yellow("  Unmapped (no provider owner):"))
        for p in change.unmapped_paths:
            lines.append(f"    {p}")
    lines.append("")

    lines.append(_cyan("Blast radius"))
    counts = blast.kinds()
    for kind, count in sorted(counts.items()):
        lines.append(f"  {kind}: {count}")
    lines.append(f"  direct: {len(blast.direct)}  indirect: {len(blast.indirect)}")
    lines.append("")

    lines.append(_cyan("Risk"))
    lines.append(f"  Level: {_red(risk.overall_level)}  Score: {risk.overall_score}")
    lines.append(f"  Confidence: {risk.confidence}")
    lines.append("")

    if repair.defects:
        lines.append(_cyan(f"Repair backlog ({len(repair.defects)} defect(s))"))
        for item in repair.items[:5]:
            first = item["repair_order"][0]["target"] if item["repair_order"] else "?"
            lines.append(f"  {_yellow(item['defect_id'])} -> {first}")
        lines.append("")

    return "\n".join(lines)


def format_repair(repair: RepairPlan) -> str:
    lines: list[str] = [_bold("Repair Intelligence"), ""]
    if not repair.defects:
        lines.append("No defects recorded (runtime-defects.json / normalized-issues.json empty).")
        return "\n".join(lines)
    for item in repair.items:
        lines.append(_cyan(item["defect_id"]))
        lines.append(f"  Root cause: {item['root_cause']['summary']}")
        lines.append(f"  Confidence: {item['confidence']}")
        if item["repair_order"]:
            lines.append("  Order:")
            for step in item["repair_order"][:5]:
                lines.append(f"    {step['step']}. {step['target']} ({step['path'] or 'engine'})")
        if item["verification_order"]:
            lines.append("  Verify:")
            for vo in item["verification_order"]:
                lines.append(f"    {vo['step']}. {vo['action']}")
        lines.append("")
    return "\n".join(lines)


def format_risk(risk: EngineeringRisk) -> str:
    lines: list[str] = [_bold("Engineering Risk"), ""]
    level_color = (
        _green if risk.overall_level == "Low"
        else _yellow if risk.overall_level == "Medium"
        else _red
    )
    lines.append(f"Overall: {level_color(risk.overall_level)} (score {risk.overall_score})")
    lines.append(f"Confidence: {risk.confidence}")
    lines.append("")
    for dim in risk.dimensions:
        d_color = (
            _green if dim.level == "Low" else _yellow if dim.level == "Medium" else _red
        )
        lines.append(f"  {dim.name}: {d_color(dim.level)} ({dim.score})")
        for ev in dim.evidence[:2]:
            lines.append(f"    - {ev}")
    lines.append("")
    return "\n".join(lines)
