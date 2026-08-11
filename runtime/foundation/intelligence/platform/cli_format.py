"""Canonical CLI formatter — Program 14.1.

Formats the canonical intelligence outputs for the ``affected``, ``diagnose``,
``repair`` and ``risk`` commands. This replaces the legacy
``runtime/foundation/intelligence/formatter.py`` which formatted the
pre-14.0 dataclasses. Output is produced from canonical ``platform`` objects
only; no selection or inference happens here.
"""

from __future__ import annotations

import sys

from runtime.foundation.intelligence.platform.attribution import AttributionReport
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
    "format_cross_layer_failure",
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


def format_cross_layer_failure(
    change: ChangeIntelligence,
    blast: BlastRadius,
    plan: VerificationPlanIntel,
    report: AttributionReport,
) -> str:
    """Render the CROSS-LAYER FAILURE diagnostic (VEA-2 Phase 1.5 §18).

    Compresses cascades into clusters and states explicitly which areas the
    change does **not** explain, so an agent knows what not to touch.
    """
    lines: list[str] = [_bold("CROSS-LAYER FAILURE"), ""]

    lines.append(_cyan("Change:"))
    for f in change.changeset.files:
        lines.append(f"  {f.path} ({f.status})")
    lines.append("")

    lines.append(_cyan("Capability:"))
    caps = sorted(
        {
            n.ref.ref
            for n in blast.all_impacted
            if n.ref.kind == "capability"
        }
    )
    for cap in caps or ["(none resolved)"]:
        lines.append(f"  {cap}")
    lines.append("")

    lines.append(_cyan("Impact (predicted downstream files):"))
    for path in report.blast_radius_paths:
        lines.append(f"  {path}")
    lines.append("")

    lines.append(_cyan("Verification:"))
    for unit in plan.selected:
        lines.append(f"  {_yellow(unit.id)} — source={unit.source} kinds={list(unit.impact_kinds)}")
    lines.append("")

    implicated = report.in_blast_radius
    lines.append(_cyan("Failure attribution:"))
    lines.append(
        f"  observed={len(report.attributions)}  "
        f"in-blast-radius={len(implicated)}  "
        f"outside={len(report.outside_blast_radius)}  "
        f"unknown={len(report.unknown)}"
    )
    lines.append("")

    if implicated:
        lines.append(_red("PRIMARY CAUSE — failures the change explains:"))
        for item in implicated:
            lines.append(
                f"  {item.failure.phase}: {item.failure.path} "
                f"({item.matched_entity})"
            )
            if item.failure.diagnostic:
                lines.append(f"      {item.failure.diagnostic}")
        lines.append("")
        lines.append(_cyan("Recommended inspection order:"))
        step = 1
        for f in change.changeset.files:
            lines.append(f"  {step}. {f.path} (source of change)")
            step += 1
        for item in implicated:
            lines.append(f"  {step}. {item.failure.path} (failing consumer)")
            step += 1
        lines.append("")
    else:
        lines.append(_green("NO FAILURE IS ATTRIBUTABLE TO THIS CHANGE."))
        lines.append(
            "  Every observed failure lies outside the blast radius that "
            "justified running these units."
        )
        lines.append(
            "  Do NOT modify the changed files to make this verification green."
        )
        lines.append("")

    outside = report.outside_blast_radius
    if outside:
        lines.append(_yellow("Unrelated / pre-existing (excluded from this change):"))
        by_phase: dict[str, list[str]] = {}
        for item in outside:
            by_phase.setdefault(item.failure.phase, []).append(item.failure.path)
        for phase, paths in sorted(by_phase.items()):
            unique = sorted(set(paths))
            lines.append(f"  {phase}: {len(paths)} diagnostic(s) across {len(unique)} file(s)")
            for path in unique:
                lines.append(f"      {path}")
        lines.append("")

    if report.unknown:
        lines.append(_yellow("Unattributed (insufficient evidence):"))
        for item in report.unknown:
            lines.append(f"  {item.failure.phase}: {item.reason}")
        lines.append("")

    return "\n".join(lines)
