"""
M9-C57 — Survivor enrichment linking mutants to financial concepts.

Takes a survivor catalog (JSON produced by a mutation run) and enriches
each surviving mutant with:

  * financial concept (from FINANCIAL_CONCEPTS)
  * at-risk invariant (from the concept's invariant list)
  * suggested test name (derived from mutation operator + invariant)
  * suggested assertion (the FINANCIAL_INVARIANTS remediation pattern)

Output is a list of ``EnrichedSurvivor`` records suitable for downstream
diagnostic and test-generation tooling.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# ---------------------------------------------------------------------------
# Public data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EnrichedSurvivor:
    """A survivor enriched with financial-domain context."""

    original_survivor: dict[str, Any]
    concept_id: str
    concept_domain: str
    at_risk_invariant: str
    suggested_test_name: str
    suggested_assertion: str

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.original_survivor,
            "concept_id": self.concept_id,
            "concept_domain": self.concept_domain,
            "at_risk_invariant": self.at_risk_invariant,
            "suggested_test_name": self.suggested_test_name,
            "suggested_assertion": self.suggested_assertion,
        }


# ---------------------------------------------------------------------------
# Operator-to-test mapping heuristics
# ---------------------------------------------------------------------------

_OPERATOR_TEST_HINTS: dict[str, str] = {
    " arithmetic ": "test_arithmetic_boundaries",
    " conditionals ": "test_condition_guard",
    " boolean ": "test_boolean_logic",
    " return ": "test_return_value",
    " operator ": "test_operator_correctness",
    " slice ": "test_slice_bounds",
    " keyword ": "test_keyword_argument",
    " math ": "test_math_precision",
    "cmp": "test_comparison",
    "bool": "test_boolean",
    "ret": "test_return",
}


def _suggest_test_from_operator(
    mutmut_operator: str,
    concept_id: str,
    invariant_id: str,
) -> str:
    """Derive a descriptive test name from the mutation operator."""
    op_lower = mutmut_operator.lower() if mutmut_operator else ""

    # Check operator hints first
    for key, hint in _OPERATOR_TEST_HINTS.items():
        if key in op_lower:
            return f"test_{concept_id}_{hint}_{invariant_id}"

    # Fallback: combine concept + invariant into a meaningful name
    safe_op = mutmut_operator.replace(" ", "_").replace("-", "_")[:20]
    safe_concept = concept_id.replace("-", "_")
    safe_inv = invariant_id.replace("-", "_")
    return f"test_{safe_concept}_{safe_op}_{safe_inv}_survivor"


# ---------------------------------------------------------------------------
# SurvivorEnricher
# ---------------------------------------------------------------------------


class SurvivorEnricher:
    """Enrich a survivor catalog with financial-concept context."""

    def __init__(self) -> None:
        from runtime.foundation.verification.semantics.concepts import (  # noqa: PLC0415
            FINANCIAL_CONCEPTS,
        )
        from runtime.foundation.verification.semantics.assertions import (  # noqa: PLC0415
            FINANCIAL_INVARIANTS,
        )

        self._concepts = FINANCIAL_CONCEPTS
        self._invariants = FINANCIAL_INVARIANTS

    # -- public API --------------------------------------------------------

    def enrich(self, survivor_catalog_path: str | Path) -> list[EnrichedSurvivor]:
        """Load a survivor catalog JSON and return enriched records.

        Parameters
        ----------
        survivor_catalog_path : str | Path
            Path to the JSON file produced by ``verify.py mutation`` or
            ``build_survivor_intel``.  Expected schema: top-level dict with
            a ``survivors`` list; each entry has ``source_file``,
            ``mutation_type``, and optionally ``component``.
        """
        path = Path(survivor_catalog_path)
        if not path.exists():
            return []

        try:
            catalog = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

        survivors = catalog.get("survivors", [])
        if not survivors:
            # Try top-level entries directly (some catalogs use "entries")
            survivors = catalog.get("entries", [])

        enriched: list[EnrichedSurvivor] = []
        for surv in survivors:
            enriched.append(self._enrich_one(surv))

        return enriched

    def enrich_batch(
        self,
        survivor_records: list[dict[str, Any]],
    ) -> list[EnrichedSurvivor]:
        """Enrich an in-memory list of survivor dicts."""
        return [self._enrich_one(s) for s in survivor_records]

    # -- internals ---------------------------------------------------------

    def _enrich_one(self, survivor: dict[str, Any]) -> EnrichedSurvivor:
        """Enrich a single survivor record."""
        source_file = survivor.get("source_file", "")
        component = survivor.get("component", "")
        mutation_type = survivor.get("mutation_type", "") or survivor.get("category", "")
        original_expression = survivor.get("original_expression", "")
        mutated_expression = survivor.get("mutated_expression", "")

        concept = self._find_concept(source_file, component)
        concept_id = concept.concept_id if concept else "unknown"
        concept_domain = concept.domain if concept else "unknown"

        invariant = self._find_at_risk_invariant(concept, mutation_type)
        invariant_id = invariant.invariant_id if invariant else "unknown"

        suggested_test = self._suggest_test(
            mutation_type,
            concept_id,
            invariant_id,
            original_expression,
            mutated_expression,
        )
        suggested_assertion = invariant.remediation_pattern if invariant else ""

        return EnrichedSurvivor(
            original_survivor=survivor,
            concept_id=concept_id,
            concept_domain=concept_domain,
            at_risk_invariant=invariant_id,
            suggested_test_name=suggested_test,
            suggested_assertion=suggested_assertion,
        )

    def _find_concept(
        self,
        source_file: str,
        component: str = "",
    ) -> Any | None:
        """Look up the financial concept matching *source_file*."""
        if not source_file:
            return None

        source_norm = source_file.replace("\\", "/")

        for concept in self._concepts.values():
            impl = concept.implemented_in
            if not impl:
                continue
            impl_norm = impl.replace("\\", "/")

            # Exact match
            if source_norm == impl_norm:
                return concept
            # Directory prefix match
            if source_norm.startswith(impl_norm):
                return concept
            # Component-based match (e.g. "loan_engine" → concepts in loan_engine/)
            if component and component in impl_norm:
                return concept

        return None

    def _find_at_risk_invariant(
        self,
        concept: Any | None,
        mutation_type: str,
    ) -> Any | None:
        """Return the most relevant invariant for the given concept/operator."""
        if not concept:
            return None

        inv_ids = list(concept.invariants)
        if not inv_ids:
            return None

        # Prefer invariants whose remediation mentions something related to
        # the mutation type (heuristic).
        mut_lower = mutation_type.lower()
        for inv_id in inv_ids:
            inv = self._invariants.get(inv_id)
            if inv and mut_lower in inv.description.lower():
                return inv

        # Fall back to the first invariant.
        first_id = inv_ids[0]
        return self._invariants.get(first_id)

    def _suggest_test(
        self,
        mutmut_operator: str,
        concept_id: str,
        invariant_id: str,
        original_expr: str,
        mutated_expr: str,
    ) -> str:
        """Build a suggested test name and assertion string."""
        test_name = _suggest_test_from_operator(
            mutmut_operator, concept_id, invariant_id
        )
        assertion = self._invariants.get(invariant_id)
        if assertion:
            assertion_str = (
                f"assert_not_equal({assertion.implemented_in!r}, "
                f"{mutmut_operator!r})  # {assertion.description}"
            )
        else:
            assertion_str = (
                f"# Verify invariant {invariant_id} against mutation "
                f"{mutmut_operator!r} in {concept_id}"
            )
        return f"{test_name}  # assert: {assertion_str}"


# ---------------------------------------------------------------------------
# CLI helper
# ---------------------------------------------------------------------------


def run_enrich_cli(argv: list[str] | None = None) -> int:
    """verify.py strengthen enrich-survivors — CLI entry point."""
    import argparse  # noqa: PLC0415

    parser = argparse.ArgumentParser(
        prog="verify.py strengthen enrich-survivors",
        description="Enrich survivor catalog with financial-concept context.",
    )
    parser.add_argument(
        "--catalog",
        default=str(
            REPO_ROOT
            / "backend"
            / "tests"
            / "generated"
            / "mutation"
            / "mutation-survivor-intel.json"
        ),
        help="Path to the survivor catalog JSON.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Optional output path for enriched JSON (defaults to stdout).",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON.")
    args = parser.parse_args(argv or [])

    enricher = SurvivorEnricher()
    results = enricher.enrich(args.catalog)

    if not results:
        print(f"No survivors enriched from {args.catalog}")
        return 0

    output_data = [r.to_dict() for r in results]

    if args.json or args.out:
        text = json.dumps(output_data, indent=2)
        if args.out:
            Path(args.out).write_text(text + "\n", encoding="utf-8")
            print(f"Wrote {len(results)} enriched records to {args.out}")
        else:
            print(text)
        return 0

    for rec in results:
        orig = rec.original_survivor
        print(f"# {orig.get('survivor_id', '?')}")
        print(f"  concept           : {rec.concept_id} ({rec.concept_domain})")
        print(f"  at_risk_invariant : {rec.at_risk_invariant}")
        print(f"  suggested_test    : {rec.suggested_test_name}")
        print(f"  suggested_assertion: {rec.suggested_assertion}")
        print()

    return 0


__all__ = [
    "EnrichedSurvivor",
    "SurvivorEnricher",
    "run_enrich_cli",
]
