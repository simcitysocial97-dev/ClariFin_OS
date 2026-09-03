"""M9-C56 — Coverage & Mutation Convergence CLI commands.

Exposes convergence intelligence through verify.py:
- convergence-status: Current coverage + mutation state
- coverage-analysis: Per-component coverage breakdown
- mutation-analysis: Per-engine mutation breakdown
- gap-analysis: Classified gap registry
- convergence-plan: Prioritized convergence queue
- threshold-assessment: 80% threshold achievement status
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
C56_DIR = REPO_ROOT / "runtime" / "generated" / "m9-c56"


def _load_json(path: Path) -> dict | None:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def cmd_convergence_status() -> int:
    """Display current convergence status."""
    baseline = _load_json(C56_DIR / "baseline" / "baseline.json")
    recon = _load_json(C56_DIR / "measurement" / "measurement-reconciliation.json")
    gap_reg = _load_json(C56_DIR / "gap-analysis" / "gap-registry.json")

    if not baseline:
        print("C56 baseline not found. Run baseline lock first.", file=sys.stderr)
        return 1

    print("=" * 70)
    print("  M9-C56 — Convergence Status")
    print("=" * 70)

    cov = baseline.get("coverage", {})
    mut = baseline.get("mutation", {})

    print(f"\n  Repository SHA: {baseline.get('repository', {}).get('sha', 'unknown')}")
    print(f"  Baseline: {baseline.get('generated_at', 'unknown')}")

    print(f"\n  --- Coverage ---")
    print(f"  Line coverage:   {cov.get('percent_covered', 0):.2f}%")
    print(f"  Branch coverage: {cov.get('percent_branches_covered', 0):.2f}%")

    print(f"\n  --- Mutation ---")
    print(f"  Overall score:   {mut.get('mutation_score', 'N/A')}%")
    if "engines" in mut:
        for engine, data in mut["engines"].items():
            print(f"    {engine:<25} {data['mutation_score']:>6.1f}% ({data['killed']}/{data['mutants_generated']})")

    print(f"\n  --- Gaps ---")
    if gap_reg:
        print(f"  Total gaps: {gap_reg.get('total_gaps', 0)}")
        print(f"  Actionable: {gap_reg.get('actionable_gaps', 0)}")
        print(f"  Preserved:  {gap_reg.get('preserved_gaps', 0)}")

    gaps = baseline.get("gaps", {})
    print(f"\n  --- Gap to 80% Threshold ---")
    print(f"  Coverage line:   {gaps.get('coverage_line_pct', 0):.2f} pp")
    print(f"  Coverage branch: {gaps.get('coverage_branch_pct', 0):.2f} pp")
    print(f"  Mutation:        {gaps.get('mutation_pct', 0):.2f} pp")

    return 0


def cmd_coverage_analysis() -> int:
    """Display per-component coverage analysis."""
    matrix = _load_json(C56_DIR / "measurement" / "coverage-matrix.json")
    if not matrix:
        print("Coverage matrix not found.", file=sys.stderr)
        return 1

    print("=" * 70)
    print("  M9-C56 — Coverage Analysis")
    print("=" * 70)

    components = matrix.get("components", [])
    print(f"\n  {'Component':<28} {'Files':>5} {'Line%':>6} {'Branch%':>7} {'Stmts':>6} {'Missing':>7}")
    print("  " + "-" * 65)

    for c in sorted(components, key=lambda x: x.get("line_pct") or 0):
        line_s = f"{c['line_pct']:.1f}" if c.get("line_pct") is not None else "N/A"
        branch_s = f"{c['branch_pct']:.1f}" if c.get("branch_pct") is not None else "N/A"
        print(f"  {c['component']:<28} {c['source_files']:>5} {line_s:>6} {branch_s:>7} {c['statements']:>6} {c['missing_lines']:>7}")

    totals = matrix.get("totals", {})
    print("  " + "-" * 65)
    line_pct = totals.get("covered_lines", 0) / max(totals.get("statements", 1), 1) * 100
    print(f"  {'TOTAL':<28} {totals.get('source_files', 0):>5} {line_pct:>6.1f}")

    return 0


def cmd_mutation_analysis() -> int:
    """Display per-engine mutation analysis."""
    matrix = _load_json(C56_DIR / "measurement" / "mutation-matrix.json")
    if not matrix:
        print("Mutation matrix not found.", file=sys.stderr)
        return 1

    print("=" * 70)
    print("  M9-C56 — Mutation Analysis")
    print("=" * 70)

    overall = matrix.get("overall", {})
    print(f"\n  Overall: {overall.get('killed', 0)}/{overall.get('mutants_generated', 0)} killed = {overall.get('score', 0)}%")

    engines = matrix.get("engines", [])
    print(f"\n  {'Engine':<28} {'Killed':>6} {'Survived':>8} {'Total':>6} {'Score%':>7}")
    print("  " + "-" * 60)

    for e in sorted(engines, key=lambda x: x.get("score", 0)):
        print(f"  {e['engine']:<28} {e['killed']:>6} {e['survived']:>8} {e['mutants_generated']:>6} {e['score']:>7.1f}")

    return 0


def cmd_gap_analysis() -> int:
    """Display classified gap registry."""
    reg = _load_json(C56_DIR / "gap-analysis" / "gap-registry.json")
    if not reg:
        print("Gap registry not found.", file=sys.stderr)
        return 1

    print("=" * 70)
    print("  M9-C56 — Gap Analysis")
    print("=" * 70)

    print(f"\n  Total gaps: {reg.get('total_gaps', 0)}")
    print(f"  Actionable: {reg.get('actionable_gaps', 0)}")
    print(f"  Preserved:  {reg.get('preserved_gaps', 0)}")

    by_type = reg.get("by_type", {})
    print(f"\n  --- By Type ---")
    for gap_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"    {gap_type:<30} {count:>3}")

    gaps = reg.get("gaps", [])
    actionable = [g for g in gaps if g.get("gap_type") not in ("EQUIVALENT", "DEFENSIVE")]
    print(f"\n  --- Top Actionable Gaps ---")
    for g in sorted(actionable, key=lambda x: -x.get("survivor_count", 0))[:15]:
        print(f"    {g['gap_id']} {g['component']:<25} {g['production_surface']:<30} surv={g['survivor_count']:>3} [{g['gap_type']}]")

    return 0


def cmd_convergence_plan() -> int:
    """Display prioritized convergence queue."""
    queue = _load_json(C56_DIR / "gap-analysis" / "convergence-queue.json")
    if not queue:
        print("Convergence queue not found.", file=sys.stderr)
        return 1

    print("=" * 70)
    print("  M9-C56 — Convergence Plan")
    print("=" * 70)

    by_priority = queue.get("by_priority", {})
    print(f"\n  Total items: {queue.get('total_items', 0)}")
    for pri, count in by_priority.items():
        print(f"    {pri:<12} {count:>3}")

    items = queue.get("queue", [])
    active = [q for q in items if q.get("priority") not in ("PRESERVE",)]
    print(f"\n  --- Top Priority Items ---")
    for q in active[:20]:
        print(f"    [{q['priority']:>8}] {q['gap_id']} {q['component']:<25} {q['production_surface']:<30} score={q['priority_score']:>6.1f}")

    return 0


def cmd_threshold_assessment() -> int:
    """Assess 80% threshold achievement status."""
    baseline = _load_json(C56_DIR / "baseline" / "baseline.json")
    recon = _load_json(C56_DIR / "measurement" / "measurement-reconciliation.json")

    if not baseline:
        print("C56 baseline not found.", file=sys.stderr)
        return 1

    print("=" * 70)
    print("  M9-C56 — Threshold Assessment (80% Engineering Threshold)")
    print("=" * 70)

    cov = baseline.get("coverage", {})
    mut = baseline.get("mutation", {})

    line_pct = cov.get("percent_covered", 0)
    branch_pct = cov.get("percent_branches_covered", 0)

    print(f"\n  --- Coverage Threshold (≥80%) ---")
    print(f"  Line coverage:   {line_pct:.2f}% {'PASS' if line_pct >= 80 else 'FAIL'} (gap: {80 - line_pct:.2f} pp)")
    print(f"  Branch coverage: {branch_pct:.2f}% {'PASS' if branch_pct >= 80 else 'FAIL'} (gap: {80 - branch_pct:.2f} pp)")

    print(f"\n  --- Mutation Threshold (≥80%) ---")
    if "engines" in mut:
        for engine, data in mut["engines"].items():
            score = data["mutation_score"]
            status = "PASS" if score >= 80 else "FAIL"
            print(f"    {engine:<25} {score:>6.1f}% {status}")

    overall_mut = mut.get("mutation_score", 0)
    print(f"\n  Overall mutation: {overall_mut:.1f}% {'PASS' if overall_mut >= 80 else 'FAIL'}")

    print(f"\n  --- Threshold Decision ---")
    all_pass = line_pct >= 80 and branch_pct >= 80 and overall_mut >= 80
    if all_pass:
        print("  STATE A — THRESHOLD ACHIEVED")
    elif line_pct >= 75 and branch_pct >= 70 and overall_mut >= 75:
        print("  STATE B — SUBSTANTIALLY CONVERGED")
    else:
        print("  STATE C — BELOW THRESHOLD (convergence in progress)")

    return 0


def main(argv: list[str]) -> int:
    """Dispatch C56 convergence commands."""
    if not argv:
        print("C56 command required: convergence-status, coverage-analysis, "
              "mutation-analysis, gap-analysis, convergence-plan, threshold-assessment",
              file=sys.stderr)
        return 1

    command = argv[0]

    if command == "convergence-status":
        return cmd_convergence_status()
    if command == "coverage-analysis":
        return cmd_coverage_analysis()
    if command == "mutation-analysis":
        return cmd_mutation_analysis()
    if command == "gap-analysis":
        return cmd_gap_analysis()
    if command == "convergence-plan":
        return cmd_convergence_plan()
    if command == "threshold-assessment":
        return cmd_threshold_assessment()

    print(f"Unknown C56 command: {command}", file=sys.stderr)
    return 1
