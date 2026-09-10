"""
M9-C54 — Local <-> CI semantic equivalence (Q5).

Standalone module that compares local and CI execution across semantic
dimensions without depending on workflow inventory.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class EquivalenceResult(str, Enum):
    EQUIVALENT = "equivalent"
    COMPATIBLE = "compatible_non_identical"
    INCOMPATIBLE = "incompatible"
    STALE = "stale"
    INSUFFICIENT = "insufficient_evidence"


@dataclass(frozen=True, slots=True)
class SemanticEquivalence:
    dimension: str
    local_value: str
    ci_value: str
    result: EquivalenceResult
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "local_value": self.local_value,
            "ci_value": self.ci_value,
            "result": self.result.value,
            "notes": self.notes,
        }


def check_semantic_equivalence(
    local_config: dict[str, Any],
    ci_config: dict[str, Any],
) -> list[SemanticEquivalence]:
    """Compare local and CI execution across semantic dimensions."""
    dimensions = [
        ("repository_sha", "repository SHA"),
        ("configuration", "configuration"),
        ("toolchain", "toolchain"),
        ("command", "command"),
        ("capability", "capability"),
        ("component", "component"),
        ("verification_profile", "verification profile"),
        ("execution_result", "execution result"),
        ("measurement_result", "measurement result"),
        ("artifact_identity", "artifact/evidence identity"),
    ]
    results: list[SemanticEquivalence] = []
    for key, label in dimensions:
        local_val = str(local_config.get(key, ""))
        ci_val = str(ci_config.get(key, ""))
        if not local_val and not ci_val:
            result = EquivalenceResult.INSUFFICIENT
            notes = "no evidence on either side"
        elif not ci_val:
            result = EquivalenceResult.INSUFFICIENT
            notes = "CI evidence missing"
        elif not local_val:
            result = EquivalenceResult.INSUFFICIENT
            notes = "local evidence missing"
        elif local_val == ci_val:
            result = EquivalenceResult.EQUIVALENT
            notes = "identical"
        else:
            result = EquivalenceResult.INCOMPATIBLE
            notes = f"mismatch: local={local_val}, ci={ci_val}"
        results.append(
            SemanticEquivalence(
                dimension=label,
                local_value=local_val,
                ci_value=ci_val,
                result=result,
                notes=notes,
            )
        )
    return results
