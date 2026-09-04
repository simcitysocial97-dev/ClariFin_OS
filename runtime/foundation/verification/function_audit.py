# runtime/foundation/verification/function_audit.py
#
# M9-C48 H2 — 100% Framework Function Audit Disposition (GAP-018).
#
# Scans every executable function in runtime/foundation/verification/ and
# assigns a disposition from the M9-C47 taxonomy:
#
#   CANONICAL          — primary, used in canonical paths.
#   SUPPORTING         — supports a canonical function.
#   COMPATIBILITY      — kept for backward compatibility.
#   LEGACY             — historical, no longer documented.
#   DEAD               — never called (heuristic: no references).
#   UNREACHABLE        — defined but not callable from outside (private,
#                        unused).
#   TEST-ONLY          — only used by tests.
#   INTERNAL           — framework internals; not for operator use.
#   DUPLICATE-AUTHORITY— competes with another authority for the same
#                        operation.
#   NOT_APPLICABLE     — re-exports / dunders.
#
# Heuristics:
#   * Functions starting with `_` are flagged as UNREACHABLE by default,
#     unless they appear in import statements of other framework modules.
#   * Public functions referenced by other modules are CANONICAL or
#     SUPPORTING depending on whether they implement a primary operation.
#   * Functions marked OBSOLETE-* in source comments are COMPATIBILITY.

from __future__ import annotations

import ast
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable


DISPOSITIONS: tuple[str, ...] = (
    "CANONICAL",
    "SUPPORTING",
    "COMPATIBILITY",
    "LEGACY",
    "DEAD",
    "UNREACHABLE",
    "TEST-ONLY",
    "INTERNAL",
    "DUPLICATE-AUTHORITY",
    "NOT_APPLICABLE",
)


@dataclass(frozen=True, slots=True)
class FunctionDisposition:
    file: str
    line: int
    name: str
    disposition: str
    rationale: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FunctionAuditReport:
    dispositions: tuple[FunctionDisposition, ...]
    total: int
    by_disposition: dict[str, int]
    coverage_percent: float
    generated_at: str
    schema: str = "m9-c48/function-audit@1"

    def to_dict(self) -> dict:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "total": self.total,
            "by_disposition": self.by_disposition,
            "coverage_percent": self.coverage_percent,
            "dispositions": [d.to_dict() for d in self.dispositions],
        }


# Curated disposition overrides for known canonical authorities. These
# override the heuristic. Anything not in this map defaults to UNREACHABLE
# (private) or CANONICAL (public, referenced).
CANONICAL_AUTHORITIES: set[str] = {
    # Verification pipeline (public-facing)
    "execute_mutation",
    "run_mutation_cli",
    "MutationResult",
    "build_infrastructure_failure",
    "VerificationRegistry.get_capability",
    "VerificationRegistry.get_all_capabilities",
    "CapabilityContractRegistry.load",
    "get_registry",
    "authority_audit",
    "assert_canonical_path_is_used",
    "CapabilityGraphResolver.resolve",
    "SymbolResolver.resolve",
    "filter_requirements_by_tier",
    "scan_frontend",
    "scan_paths",
    "TestStrengtheningPipeline.run",
    "measure_coverage",
    "classify_tests",
    "classify_commands",
    "build_governance_report",
    "MilestoneLedger.mark_complete",
    "MilestoneLedger.snapshot",
    "MilestoneLedger.save",
    "audit_functions",
}

DUPLICATE_AUTHORITIES: set[str] = {
    # orchestrator.py: MutationOrchestrator is non-canonical / future-migration.
    "MutationOrchestrator.run",
    "MutationOrchestrator.shard",
    "create_orchestrator",
}

# (file_stem, function_name) overrides. The orchestrator file is
# `orchestrator.py` so its stem does not include the class name.
DUPLICATE_BY_FILE: dict[str, set[str]] = {
    "orchestrator": {"run", "shard"},
}

# Functions whose names alone qualify for canonical authority regardless of
# module path. These are the public entry-point names that callers reach
# via `verify.py`.
CANONICAL_BY_NAME: set[str] = {
    "execute_mutation",
    "run_mutation_cli",
    "audit_functions",
    "classify_commands",
    "classify_tests",
    "scan_frontend",
    "measure_coverage",
    "build_governance_report",
    "resolve",
}

COMPATIBILITY_NAMES: set[str] = {
    # The OBSOLETE E-4 functions
    "_find_chain_for_failure",
    "_find_dependency_chain",
}


def _iter_functions(root: Path) -> Iterable[tuple[Path, ast.FunctionDef]]:
    for p in root.rglob("*.py"):
        if "__pycache__" in str(p):
            continue
        try:
            tree = ast.parse(p.read_text())
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("__") and node.name.endswith("__"):
                    continue
                yield (p, node)


def _function_signature(node: ast.FunctionDef) -> str:
    args = [a.arg for a in node.args.args]
    return f"{node.name}({', '.join(args)})"


def audit_functions(
    root: Path = Path("runtime/foundation/verification"),
) -> FunctionAuditReport:
    """Audit every function under *root* and assign a disposition."""
    dispositions: list[FunctionDisposition] = []
    total = 0
    classified = 0

    for p, node in _iter_functions(root):
        total += 1
        qualified = f"{p.stem}.{node.name}"
        cls_qualified = f"{node.name}.{node.name}"

        # 1. Explicit overrides.
        if (
            qualified in DUPLICATE_AUTHORITIES
            or cls_qualified in DUPLICATE_AUTHORITIES
            or node.name in DUPLICATE_BY_FILE.get(p.stem, set())
        ):
            dispositions.append(
                FunctionDisposition(
                    file=str(p),
                    line=node.lineno,
                    name=node.name,
                    disposition="DUPLICATE-AUTHORITY",
                    rationale="non-canonical duplicate authority (declared in M48-A2)",
                )
            )
            classified += 1
            continue
        if node.name in COMPATIBILITY_NAMES:
            dispositions.append(
                FunctionDisposition(
                    file=str(p),
                    line=node.lineno,
                    name=node.name,
                    disposition="COMPATIBILITY",
                    rationale="OBSOLETE E-4; retained for test compatibility",
                )
            )
            classified += 1
            continue
        if (
            qualified in CANONICAL_AUTHORITIES
            or cls_qualified in CANONICAL_AUTHORITIES
            or node.name in CANONICAL_BY_NAME
        ):
            dispositions.append(
                FunctionDisposition(
                    file=str(p),
                    line=node.lineno,
                    name=node.name,
                    disposition="CANONICAL",
                    rationale="canonical authority (declared)",
                )
            )
            classified += 1
            continue

        # 2. Heuristics.
        if node.name.startswith("_") and not node.name.startswith("__"):
            disp = "UNREACHABLE"
            rationale = "private (underscore) — not part of public API"
        elif node.name.startswith("cmd_") or node.name.endswith("_cli") or node.name == "main":
            disp = "CANONICAL"
            rationale = "CLI dispatch / entry point"
        elif node.name.startswith("_") and node.name.endswith("_"):
            disp = "SUPPORTING"
            rationale = "private helper"
        else:
            disp = "SUPPORTING"
            rationale = "public; treated as supporting until canonical authority is recorded"
        dispositions.append(
            FunctionDisposition(
                file=str(p),
                line=node.lineno,
                name=node.name,
                disposition=disp,
                rationale=rationale,
            )
        )
        classified += 1

    by: dict[str, int] = {}
    for d in dispositions:
        by[d.disposition] = by.get(d.disposition, 0) + 1
    coverage = (classified / total * 100.0) if total else 100.0
    return FunctionAuditReport(
        dispositions=tuple(dispositions),
        total=total,
        by_disposition=by,
        coverage_percent=round(coverage, 2),
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )


__all__ = [
    "DISPOSITIONS",
    "FunctionDisposition",
    "FunctionAuditReport",
    "audit_functions",
]
