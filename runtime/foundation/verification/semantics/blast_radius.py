"""
M9-C57 — Financial blast radius analyzer.

Computes the financial-domain impact of changed files by mapping them
to concepts, then resolving transitive downstream dependencies and
collecting all affected invariants.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from runtime.foundation.verification.semantics.concepts import FINANCIAL_CONCEPTS


@dataclass
class FinancialBlastRadius:
    """Result of a financial blast-radius computation."""

    changed_files: list[str]
    affected_concepts: list[str] = field(default_factory=list)
    at_risk_invariants: list[str] = field(default_factory=list)
    cross_domain: bool = False
    cross_domain_details: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "changed_files": list(self.changed_files),
            "affected_concepts": list(self.affected_concepts),
            "at_risk_invariants": list(self.at_risk_invariants),
            "cross_domain": self.cross_domain,
            "cross_domain_details": list(self.cross_domain_details),
        }


class _FinancialBlastRadius:
    """Internal implementation of financial blast-radius analysis."""

    @staticmethod
    def compute_affected_concepts(changed_files: list[str]) -> list[str]:
        """Return concept IDs directly impacted by changed files."""
        affected: set[str] = set()
        for concept in FINANCIAL_CONCEPTS.values():
            if not concept.implemented_in:
                continue
            for f in changed_files:
                # Exact file match
                if f == concept.implemented_in:
                    affected.add(concept.concept_id)
                    break
                # File inside concept directory
                impl_parts = concept.implemented_in.split("/")
                concept_dir = "/".join(impl_parts[:-1])
                if concept_dir and f.startswith(concept_dir + "/"):
                    # Skip generic "backend/src/engines" directory matches;
                    # only match meaningful subdirectories like loan_engine/.
                    if concept_dir in ("backend/src/engines", "backend/src/engines/"):
                        continue
                    affected.add(concept.concept_id)
                    break
        return sorted(affected)

    @staticmethod
    def compute_transitive_closure(
        initial_concepts: list[str],
    ) -> list[str]:
        """Expand to all downstream concepts that depend on the initial set."""
        all_ids = set(FINANCIAL_CONCEPTS.keys())
        queue = list(initial_concepts)
        visited = set(initial_concepts)
        while queue:
            current = queue.pop(0)
            for cid, concept in FINANCIAL_CONCEPTS.items():
                if cid in visited:
                    continue
                if current in concept.depends_on:
                    visited.add(cid)
                    queue.append(cid)
        return sorted(visited)

    @staticmethod
    def compute_at_risk_invariants(concepts: list[str]) -> list[str]:
        """Collect all invariant IDs associated with the given concepts."""
        invariants: set[str] = set()
        for cid in concepts:
            concept = FINANCIAL_CONCEPTS.get(cid)
            if concept:
                invariants.update(concept.invariants)
        return sorted(invariants)

    @staticmethod
    def detect_cross_domain_impacts(concepts: list[str]) -> tuple[bool, list[str]]:
        """Check if affected concepts span multiple domains."""
        domains: set[str] = set()
        details: list[str] = []
        for cid in concepts:
            concept = FINANCIAL_CONCEPTS.get(cid)
            if concept:
                domains.add(concept.domain)
                details.append(f"{cid} ({concept.domain})")
        return len(domains) > 1, details


def compute_financial_blast_radius(changed_files: list[str]) -> FinancialBlastRadius:
    """Compute the financial blast radius for a set of changed files.

    Returns a FinancialBlastRadius with affected concepts, at-risk invariants,
    and cross-domain impact information.
    """
    initial = _FinancialBlastRadius.compute_affected_concepts(changed_files)
    all_concepts = _FinancialBlastRadius.compute_transitive_closure(initial)
    invariants = _FinancialBlastRadius.compute_at_risk_invariants(all_concepts)
    is_cross_domain, details = _FinancialBlastRadius.detect_cross_domain_impacts(all_concepts)

    return FinancialBlastRadius(
        changed_files=changed_files,
        affected_concepts=all_concepts,
        at_risk_invariants=invariants,
        cross_domain=is_cross_domain,
        cross_domain_details=details,
    )
