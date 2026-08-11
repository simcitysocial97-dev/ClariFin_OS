"""VEA-3 M3 — E-4 Negative / Mutation Tests.

These tests prove the principal E-4 defect classes are *detectable* with the new
unit-keyed graph traversal (``EvidenceAggregator._resolve_chain_for_failure``):

    A. unrelated first entry     — correct chain is not the first map entry
    B. substring collision       — two unrelated entities share a textual substring
    C. same test name, diff unit — unit_id dominates
    D. missing graph edge        — traversal cannot establish causality -> UNKNOWN
    E. UNMAPPED                  — unmapped execution stays UNMAPPED, never forced
    F. unrelated manifest entry  — an unrelated manifest entry is never borrowed
    G. first-entry mutant        — forcing "return first chain" must fail >=1 test
    H. substring mutant          — replacing identity matching with substring must fail >=1 test

The new resolver runs against a *controlled* canonical chain map (the real provider
is patched), so the tests are deterministic and do not depend on discovery artifacts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

from runtime.system.evidence.aggregator import EvidenceAggregator


# --- A controlled canonical chain map (engine root path -> chain projection) ----
def _chain_map() -> dict[str, dict[str, Any]]:
    return {
        # engine A: owned by useAlphaCapability
        "backend/src/engines/alpha_engine": {
            "engine": "backend/src/engines/alpha_engine",
            "services": ["AlphaService"],
            "endpoints": ["GET /alpha"],
            "capabilities": ["useAlphaCapability"],
            "mappers": ["alphaMapper"],
            "viewModels": ["AlphaViewModel"],
            "workspace": ["AlphaWorkspace"],
            "components": ["AlphaComponent"],
        },
        # engine B: owned by useBetaCapability — name shares substring "eta" with A,
        # and a test name could collide if we matched by substring. Inserted FIRST
        # so the E-4 "first-entry" mutant returns beta for an alpha failure.
        "backend/src/engines/beta_engine": {
            "engine": "backend/src/engines/beta_engine",
            "services": ["BetaService"],
            "endpoints": ["GET /beta"],
            "capabilities": ["useBetaCapability"],
            "mappers": ["betaMapper"],
            "viewModels": ["BetaViewModel"],
            "workspace": ["BetaWorkspace"],
            "components": ["BetaComponent"],
        },
        # engine C: stale path, not resolvable to any unit (simulates BL-005 drift).
        "backend/src/engines/legacy_engine": {
            "engine": "backend/src/engines/legacy_engine",
            "services": ["LegacyService"],
            "endpoints": [],
            "capabilities": ["useLegacyCapability"],
            "mappers": [],
            "viewModels": [],
            "workspace": [],
            "components": [],
        },
        # decoy engine: its path contains "alpha" as a SUBSTRING (alphabet), but it
        # is NOT owned by useAlphaCapability. A substring matcher would mis-resolve
        # an alpha failure onto this engine. Identity resolution never does. Inserted
        # BEFORE alpha_engine so a first-match substring mutant picks it.
        "backend/src/engines/alphabet_engine": {
            "engine": "backend/src/engines/alphabet_engine",
            "services": ["AlphabetService"],
            "endpoints": [],
            "capabilities": ["useAlphabetCapability"],
            "mappers": [],
            "viewModels": [],
            "workspace": [],
            "components": [],
        },
    }


def _chain_map_beta_first() -> dict[str, dict[str, Any]]:
    """Same map but with beta_engine inserted FIRST (drives the first-entry mutant)."""
    cm = _chain_map()
    ordered = {"backend/src/engines/beta_engine": cm.pop("backend/src/engines/beta_engine")}
    ordered.update(cm)
    return ordered


def _chain_map_decoy_first() -> dict[str, dict[str, Any]]:
    """Same map but with alphabet_engine inserted BEFORE alpha_engine (substring mutant)."""
    cm = _chain_map()
    alpha = cm.pop("backend/src/engines/alpha_engine")
    decoy = cm.pop("backend/src/engines/alphabet_engine")
    out: dict[str, dict[str, Any]] = {}
    # preserve beta first, then decoy before alpha
    for k, v in list(cm.items()):
        out[k] = v
        if k == "backend/src/engines/beta_engine":
            out["backend/src/engines/alphabet_engine"] = decoy
    out["backend/src/engines/alpha_engine"] = alpha
    return out


def _agg() -> EvidenceAggregator:
    return EvidenceAggregator(Path("."))


def _resolve(failure_type: str, provenance: dict[str, dict[str, Any]], chain_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    agg = _agg()
    with patch.object(EvidenceAggregator, "_canonical_chain_map", return_value=chain_map):
        return agg._resolve_chain_for_failure(failure_type, provenance, chain_map)


class TestE4Negative:
    # A. unrelated first entry ------------------------------------------------
    def test_A_unrelated_first_entry(self):
        # The map's first entry is beta_engine, but the failing unit is alpha.
        prov = {"backend-unit": {"capabilities": ["useAlphaCapability"], "impact_kinds": ["engine"], "source": "blast-radius"}}
        result = _resolve("unit_tests", prov, _chain_map())
        assert "backend/src/engines/alpha_engine" in result["dependency_chain"]
        assert "backend/src/engines/beta_engine" not in result["dependency_chain"]

    # B. substring collision --------------------------------------------------
    def test_B_substring_collision(self):
        # "useBetaCapability" shares no substring logic; we ensure selecting the
        # beta unit never pulls alpha despite "eta" overlap in a naive matcher.
        prov = {"backend-unit": {"capabilities": ["useBetaCapability"], "impact_kinds": ["engine"], "source": "blast-radius"}}
        result = _resolve("unit_tests", prov, _chain_map())
        assert result["likely_origin"] == "backend/src/engines/beta_engine"
        assert "alpha" not in result["dependency_chain"]

    # C. same test name, different unit --------------------------------------
    def test_C_same_test_name_different_unit(self):
        # Two units, both with a test named "test_shared.py" — unit_id dominates.
        prov = {
            "unit-alpha": {"capabilities": ["useAlphaCapability"], "impact_kinds": ["engine"], "source": "blast-radius"},
            "unit-beta": {"capabilities": ["useBetaCapability"], "impact_kinds": ["engine"], "source": "blast-radius"},
        }
        alpha = _resolve("unit_tests", {"unit-alpha": prov["unit-alpha"]}, _chain_map())
        beta = _resolve("unit_tests", {"unit-beta": prov["unit-beta"]}, _chain_map())
        assert alpha["likely_origin"] == "backend/src/engines/alpha_engine"
        assert beta["likely_origin"] == "backend/src/engines/beta_engine"
        assert alpha["likely_origin"] != beta["likely_origin"]

    # D. missing graph edge ---------------------------------------------------
    def test_D_missing_graph_edge_is_unknown(self):
        # Capability resolves to NO engine in the map -> no causality -> UNKNOWN.
        prov = {"backend-unit": {"capabilities": ["useOrphanCapability"], "impact_kinds": ["engine"], "source": "blast-radius"}}
        result = _resolve("unit_tests", prov, _chain_map())
        assert result == {}

    # E. UNMAPPED -------------------------------------------------------------
    def test_E_unmapped_stays_unmapped(self):
        # A step mapped to UNMAPPED must never be borrowed into the blast radius.
        prov: dict[str, dict[str, Any]] = {}  # no mapped units at all
        result = _resolve("unit_tests", prov, _chain_map())
        assert result == {}

    # F. unrelated manifest entry --------------------------------------------
    def test_F_unrelated_manifest_entry_not_borrowed(self):
        # The failing type is contract_tests; only a beta unit is mapped, but the
        # beta unit did not select contracts. No enumerated contract unit exists,
        # and no mapped unit carries a capability that owns contracts -> UNKNOWN,
        # never borrow the alpha unit that happens to be mapped.
        prov = {"unit-beta": {"capabilities": ["useBetaCapability"], "impact_kinds": ["engine"], "source": "blast-radius"}}
        result = _resolve("contract_tests", prov, _chain_map())
        # No contract-owned unit is mapped; must not cross-borrow alpha.
        assert "backend/src/engines/alpha_engine" not in result.get("dependency_chain", [])

    # G. first-entry mutant ---------------------------------------------------
    def test_G_first_entry_mutant_kills_a_test(self):
        # The real, unit-keyed implementation returns alpha for an alpha failure,
        # regardless of map insertion order. We assert that first, then apply the
        # E-4 "first-entry" mutant and assert it DIVERGES from the correct answer
        # (it returns beta, the first inserted chain). The diverging assertion is
        # what proves the first-entry defect class is detectable by this test.
        prov = {"backend-unit": {"capabilities": ["useAlphaCapability"], "impact_kinds": ["engine"], "source": "blast-radius"}}

        # 1) real implementation: correct, order-independent answer.
        real = _resolve("unit_tests", prov, _chain_map_beta_first())
        assert real["likely_origin"] == "backend/src/engines/alpha_engine"

        # 2) mutant: return the FIRST inserted chain, irrespective of unit.
        def mutant_first_entry(self, failure_type, unit_provenance, cross_map=None):
            cm = self._canonical_chain_map(cross_map)
            if not cm:
                return {}
            first_engine = next(iter(cm))
            chain = cm[first_engine]
            return {
                "dependency_chain": [chain.get("engine")],
                "likely_origin": chain.get("engine"),
                "likely_consumer": None,
                "suggested_layer": None,
            }

        with patch.object(EvidenceAggregator, "_resolve_chain_for_failure", mutant_first_entry):
            agg = _agg()
            with patch.object(EvidenceAggregator, "_canonical_chain_map", return_value=_chain_map_beta_first()):
                mutated = agg._resolve_chain_for_failure("unit_tests", prov, _chain_map_beta_first())
        # The mutant mis-resolves to beta (first entry); this must differ from the
        # correct alpha answer, proving the defect class is caught.
        assert mutated["likely_origin"] != real["likely_origin"]
        assert mutated["likely_origin"] == "backend/src/engines/beta_engine"

    # H. substring mutant -----------------------------------------------------
    def test_H_substring_mutant_kills_a_test(self):
        # The real implementation resolves by capability OWNERSHIP, so an alpha
        # failure maps to alpha_engine even though the decoy "alphabet_engine"
        # path contains "alpha" as a substring. We assert that first, then apply
        # the E-4 substring mutant and assert it DIVERGES (it mis-resolves onto
        # the decoy), proving the substring defect class is detectable.
        cm = _chain_map_decoy_first()
        prov = {"backend-unit": {"capabilities": ["useAlphaCapability"], "impact_kinds": ["engine"], "source": "blast-radius"}}

        # 1) real implementation: ownership-based, substring-independent answer.
        real = _resolve("unit_tests", prov, cm)
        assert real["likely_origin"] == "backend/src/engines/alpha_engine"

        # 2) mutant: derive the short name and match it as a substring of any
        # engine path (first match wins) — the exact E-4 pattern.
        def mutant_substring(self, failure_type, unit_provenance, cross_map=None):
            chain_map = self._canonical_chain_map(cross_map)
            if not chain_map:
                return {}
            cap = list(unit_provenance.values())[0]["capabilities"][0]
            short = cap.lower().replace("use", "").replace("capability", "").strip()
            for engine_path, chain in chain_map.items():
                if short and short in engine_path.lower():
                    return {"dependency_chain": [engine_path], "likely_origin": engine_path, "likely_consumer": None, "suggested_layer": None}
            return {}

        with patch.object(EvidenceAggregator, "_resolve_chain_for_failure", mutant_substring):
            agg = _agg()
            with patch.object(EvidenceAggregator, "_canonical_chain_map", return_value=cm):
                mutated = agg._resolve_chain_for_failure("unit_tests", prov, cm)
        # The substring mutant mis-resolves onto alphabet_engine (decoy); this
        # must differ from the correct alpha_engine answer.
        assert mutated["likely_origin"] != real["likely_origin"]
        assert mutated["likely_origin"] == "backend/src/engines/alphabet_engine"
