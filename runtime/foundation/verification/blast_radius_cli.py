"""
M9-C50 — Blast-Radius CLI Commands.

Operator-facing CLI for inspecting blast-radius results, execution plans,
and minimum-safe verification scope. Extends the existing CLI without
creating a parallel interface.

Commands:
  verify.py blast-radius [--json] [--files FILE...] [--base REF] [--head REF]
  verify.py what-should-i-run [--json] [--files FILE...]
  verify.py execution-plan [--files FILE...] [--json]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def cmd_blast_radius(argv: list[str]) -> int:
    """M9-C50 — Compute and display the blast-radius contract.

    Usage:
        verify.py blast-radius [--json] [--files FILE...] [--base REF] [--head REF]

    If no --files provided, discovers from git working tree.
    If --base and --head provided, discovers from committed range.
    """
    import argparse

    parser = argparse.ArgumentParser(prog="verify.py blast-radius", add_help=False)
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="Explicit changed files (bypass git discovery)",
    )
    parser.add_argument("--base", default=None, help="Base ref for committed range")
    parser.add_argument("--head", default=None, help="Head ref for committed range")
    parser.add_argument("--out", default=None, help="Output file path")
    args = parser.parse_args(argv)

    from runtime.foundation.verification.blast_radius import (
        compute_blast_radius,
        format_blast_radius,
    )

    contract = compute_blast_radius(
        explicit_files=args.files,
        base=args.base,
        head=args.head,
    )

    output = contract.to_json() if args.json else format_blast_radius(contract)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(output)
        print(f"Written to {args.out}")
    else:
        print(output)

    # Persist to generated directory
    gen_dir = REPO_ROOT / "runtime" / "generated" / "m9-c50"
    gen_dir.mkdir(parents=True, exist_ok=True)
    latest = gen_dir / "latest-blast-radius.json"
    latest.write_text(contract.to_json())
    artifact = gen_dir / f"{contract.contract_id}.json"
    artifact.write_text(contract.to_json())

    # Exit non-zero if fail-closed
    return 1 if contract.is_fail_closed else 0


def cmd_what_should_i_run_c50(argv: list[str]) -> int:
    """M9-C50 — Answer 'what should I run?' for a change.

    Usage:
        verify.py what-should-i-run [--json] [--files FILE...] [--base REF] [--head REF]
    """
    import argparse

    parser = argparse.ArgumentParser(prog="verify.py what-should-i-run", add_help=False)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="Explicit changed files (bypass git discovery)",
    )
    parser.add_argument("--base", default=None)
    parser.add_argument("--head", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    from runtime.foundation.verification.blast_radius import compute_blast_radius

    contract = compute_blast_radius(
        explicit_files=args.files,
        base=args.base,
        head=args.head,
    )

    if args.json:
        answer = {
            "changed_files": contract.change_surface.changed_files,
            "directly_affected_capabilities": contract.directly_affected_capabilities,
            "transitively_affected_capabilities": contract.transitively_affected_capabilities,
            "shared_infrastructure_affected_capabilities": contract.shared_infrastructure_affected_capabilities,
            "unmapped_capabilities": contract.unmapped_capabilities,
            "minimum_safe_verification": [
                v.to_dict() for v in contract.minimum_safe_verification
            ],
            "escalation_conditions": [
                e.to_dict() for e in contract.escalation_conditions
            ],
            "is_fail_closed": contract.is_fail_closed,
            "fail_closed_reasons": contract.fail_closed_reasons,
        }
        output = json.dumps(answer, indent=2, default=str)
    else:
        lines = []
        lines.append("=" * 72)
        lines.append("  WHAT SHOULD I RUN? (M9-C50)")
        lines.append("=" * 72)
        lines.append(f"  Changed files: {len(contract.change_surface.changed_files)}")
        lines.append("-" * 72)
        lines.append("  AFFECTED CAPABILITIES:")
        for c in contract.directly_affected_capabilities:
            lines.append(f"    → {c} (directly)")
        for c in contract.transitively_affected_capabilities:
            lines.append(f"    ~ {c} (transitively)")
        for c in contract.shared_infrastructure_affected_capabilities:
            lines.append(f"    ≈ {c} (shared infrastructure)")
        for c in contract.unmapped_capabilities:
            lines.append(f"    ? {c} (UNMAPPED)")
        lines.append("-" * 72)
        lines.append("  MINIMUM SAFE VERIFICATION:")
        if contract.minimum_safe_verification:
            for v in contract.minimum_safe_verification:
                auth = " [AUTHORIZATION REQUIRED]" if v.authorization_required else ""
                lines.append(f"    [{v.surface_kind}] {v.command}{auth}")
        else:
            lines.append("    No mandatory verification required")
        lines.append("-" * 72)
        if contract.escalation_conditions:
            lines.append("  ESCALATION CONDITIONS:")
            for ec in contract.escalation_conditions:
                if ec.triggered:
                    lines.append(f"    ⚠ {ec.description}")
            lines.append("-" * 72)
        lines.append(f"  FAIL-CLOSED: {contract.is_fail_closed}")
        if contract.is_fail_closed:
            for r in contract.fail_closed_reasons:
                lines.append(f"    ✗ {r}")
        lines.append("=" * 72)
        output = "\n".join(lines)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(output)
        print(f"Written to {args.out}")
    else:
        print(output)

    return 1 if contract.is_fail_closed else 0


def cmd_execution_plan_c50(argv: list[str]) -> int:
    """M9-C50 — Generate a C49 ExecutionPlan from blast-radius analysis.

    Usage:
        verify.py execution-plan [--files FILE...] [--json] [--out PATH]
    """
    import argparse

    parser = argparse.ArgumentParser(prog="verify.py execution-plan", add_help=False)
    parser.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="Explicit changed files (bypass git discovery)",
    )
    parser.add_argument("--base", default=None)
    parser.add_argument("--head", default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", default=None)
    parser.add_argument(
        "--authorize",
        nargs="*",
        default=[],
        help="Authorize production-affecting tasks",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan and validate without executing",
    )
    args = parser.parse_args(argv)

    from runtime.foundation.verification.blast_radius import compute_blast_radius
    from runtime.foundation.verification.execution_orchestrator import (
        ExecutionOrchestrator,
        format_plan,
    )

    # First compute blast-radius to understand the change
    contract = compute_blast_radius(
        explicit_files=args.files,
        base=args.base,
        head=args.head,
    )

    # Then build the C49 execution plan
    orch = ExecutionOrchestrator()
    files = args.files
    if not files:
        files = contract.change_surface.changed_files

    if not files:
        print("No files to plan", file=sys.stderr)
        return 1

    plan = orch.build_execution_plan(files)
    output = plan.to_json() if args.json else format_plan(plan)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(output)
        print(f"Written to {args.out}")
    else:
        print(output)

    if not args.dry_run:
        authorize = set(args.authorize or [])
        if "all" in authorize:
            authorize = {t.task_id for t in plan.tasks}
        orch.execute(plan, authorize=authorize, dry_run=True)
        gen_dir = REPO_ROOT / "runtime" / "generated" / "m9-c50"
        gen_dir.mkdir(parents=True, exist_ok=True)
        (gen_dir / "latest-execution-plan.json").write_text(plan.to_json())

    return 1 if contract.is_fail_closed else 0
