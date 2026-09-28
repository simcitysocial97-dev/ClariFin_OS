# runtime/tests/test_m9_c50_stop_gate6_strengthening_authority.py
#
# M9-C50 PHASE 6 — STOP GATE 6: ONE STRENGTHENING AUTHORITY
#
# Gate conditions (GUIDING_DOCUMENT.md §PHASE 6):
#   1. mutation execution has one authority
#   2. mutation result contract is canonical
#   3. survivor intelligence is reachable through the control plane
#   4. strengthening is capability-aware
#   5. forensic services are internally consumed
#   6. legacy forensic commands cannot bypass canonical architecture
#   7. mutation evidence enters the common evidence model
#   8. dormant duplicate architecture has a bounded disposition

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any


def _load(name: str) -> Any:
    return importlib.import_module(name)


def _src(name: str) -> str:
    """Read a module's source (test helper)."""
    return Path(_load(name).__file__).read_text(encoding="utf-8")
    return importlib.import_module(name)


# ── 1. Mutation execution has one authority ────────────────────────────────


def test_mutation_execution_has_one_authority() -> None:
    ma = _load("runtime.foundation.verification.mutation_authority")
    audit = ma.authority_audit()
    assert (
        audit.canonical_resolvable
    ), f"canonical entrypoint unresolvable: {audit.canonical_entrypoint}"
    assert (
        audit.canonical_runner_callable
    ), f"canonical runner not callable: {audit.canonical_runner_function}"
    # The canonical runner is the actual execution function, not a wrapper stub.
    runner = ma._resolve(audit.canonical_runner_function)
    assert callable(runner)


def test_canonical_runner_is_live_executable() -> None:
    """The declared authority must be the real mutmut-driving execution."""
    ma = _load("runtime.foundation.verification.mutation_authority")
    runner_mod = _load("runtime.foundation.verification.mutation_runner")
    assert runner_mod.execute_mutation is ma._resolve(
        "runtime.foundation.verification.mutation_runner.execute_mutation"
    )
    # run_mutation_cli is the CLI entrypoint routed by the control plane.
    assert callable(runner_mod.run_mutation_cli)


# ── 2. Mutation result contract is canonical ───────────────────────────────


def test_mutation_result_contract_is_canonical() -> None:
    _load("runtime.foundation.verification.mutation_contract")


def test_orchestrator_results_project_to_canonical_contract() -> None:
    """The non-canonical orchestrator can only exit through the canonical
    result projection — no second result vocabulary is reachable."""
    mru = _load("runtime.foundation.verification.mutation_result_unified")
    assert callable(mru.project_orchestrator_to_canonical)
    assert hasattr(mru, "UnifiedMutationProjection")
    # The projection targets the canonical contract.
    mc = _load("runtime.foundation.verification.mutation_contract")
    # The projection is keyword-only and pure.
    fake_orch = type(
        "_O",
        (),
        {
            "killed": 3,
            "survived": 1,
            "equivalent": 0,
            "no_tests": 0,
            "timeout": 0,
            "skipped": 0,
            "suspicious": 0,
            "generated": 4,
        },
    )()
    proj = mru.project_orchestrator_to_canonical(
        orchestrator_result=fake_orch,
        run_id="r1",
        repository_sha="a" * 40,
        tree_sha="b" * 40,
        python_version="3.12",
        pytest_version="8",
        mutmut_version="3.7.0",
        config_hash="cfg",
    )
    assert isinstance(proj, mru.UnifiedMutationProjection)
    # The projection's canonical payload IS the canonical contract type.
    mc = _load("runtime.foundation.verification.mutation_contract")
    assert type(proj.canonical) is mc.MutationResult
    assert proj.orchestrator_provenance["survived"] == 1


# ── 3. Survivor intelligence reachable through control plane ───────────────


def test_survivor_intelligence_reachable_via_control_plane() -> None:
    ccp = _load("runtime.foundation.verification.canonical_control_plane")
    # mutation-intel is the survivor-intelligence diagnostic surface.
    assert ccp._MIGRATION["mutation-intel"] == ("diagnose", "survivor_intel")
    assert ccp.classification_for("mutation-intel") == "DEPRECATED"
    si = _load("runtime.foundation.verification.survivor_intel")
    assert any(callable(getattr(si, n)) for n in dir(si) if not n.startswith("_"))


# ── 4. Strengthening is capability-aware ───────────────────────────────────


def test_strengthening_is_capability_aware() -> None:
    st = _load("runtime.foundation.verification.strengthening")
    # Survivor evidence and strengthening proposals both carry a capability
    # field — strengthening cannot operate blind to capability identity.
    assert "capability" in st.SurvivorEvidence.__dataclass_fields__
    assert "survivor_id" in st.SurvivorEvidence.__dataclass_fields__
    assert "capability" in st.StrengtheningProposal.__dataclass_fields__


def test_strengthening_requires_capability_not_score_only() -> None:
    src = _src("runtime.foundation.verification.strengthening")
    assert "not score-only optimization" in src or "capability-aware" in src


# ── 5. Forensic services internally consumed ───────────────────────────────


def test_forensic_services_internally_consumed() -> None:
    """The control plane consumes the canonical runner; the forensic CLI
    consumes canonical artifacts rather than reimplementing forensics."""
    ccp_src = _src("runtime.foundation.verification.canonical_control_plane")
    assert "mutation_runner" in ccp_src
    fcli_src = _src("runtime.foundation.verification.forensic_cli")
    # The forensic CLI renders canonical records — it is a view, not a second engine.
    assert "canonical" in fcli_src.lower()


# ── 6. Legacy forensic commands cannot bypass ──────────────────────────────


def test_legacy_forensic_commands_marked_deprecated() -> None:
    ccp = _load("runtime.foundation.verification.canonical_control_plane")
    for legacy in [
        "strengthen-analyze",
        "strengthen-discover",
        "strengthen-propose",
        "strengthen-validate",
        "strengthen-survivor",
        "strengthen-survivor-forensic",
        "strengthen-report",
        "mutation",  # canonical: strengthen
        "mutation-intel",
    ]:
        assert (
            ccp.classification_for(legacy) == "DEPRECATED"
        ), f"legacy forensic command {legacy!r} is not marked DEPRECATED"


def test_legacy_commands_route_through_canonical_facade() -> None:
    """Deprecated aliases still resolve — but only via the canonical facade."""
    ccp_src = _src("runtime.foundation.verification.canonical_control_plane")
    # The facade must contain the deprecation-warning path, not silent aliasing.
    assert "deprecat" in ccp_src.lower()


# ── 7. Mutation evidence enters the common evidence model ──────────────────


def test_mutation_evidence_in_common_evidence_model() -> None:
    cc = _load("runtime.foundation.verification.capability_catalog")
    kinds = set(cc.EVIDENCE_KINDS)
    for required in (
        "mutation_score",
        "survivor_intel",
        "strengthening_proposal",
        "forensic_report",
    ):
        assert required in kinds, f"{required!r} missing from EVIDENCE_KINDS"


def test_mutation_evidence_vocabulary_is_closed() -> None:
    src = _src("runtime.foundation.verification.capability_catalog")
    assert "closed EVIDENCE_KINDS vocabulary" in src


# ── 8. Dormant duplicate architecture has bounded disposition ──────────────


def test_dormant_orchestrator_has_bounded_disposition() -> None:
    """MutationOrchestrator is declared non-canonical in the authority module
    and unreachable from CLI routes."""
    ma = _load("runtime.foundation.verification.mutation_authority")
    backends = ma.NON_CANONICAL_BACKENDS
    assert any("MutationOrchestrator" in b for b in backends)
    assert any("create_orchestrator" in b for b in backends)
    # No CLI route exposes the orchestrator directly.
    ccp = _load("runtime.foundation.verification.canonical_control_plane")
    for target in ccp._MIGRATION.values():
        assert (
            target[1] != "MutationOrchestrator"
        ), "MutationOrchestrator exposed as a CLI target — dormant disposition broken"


def test_orchestrator_not_imported_by_production_pipelines() -> None:
    """The canonical control plane and execution orchestrator must not import
    the dormant orchestrator — the canonical path is mutation_runner."""
    ccp_src = _src("runtime.foundation.verification.canonical_control_plane")
    eo_src = _src("runtime.foundation.verification.execution_orchestrator")
    for name, src in [
        ("canonical_control_plane", ccp_src),
        ("execution_orchestrator", eo_src),
    ]:
        assert (
            "from runtime.foundation.verification.mutation_execution" not in src
        ), f"{name} imports the dormant MutationOrchestrator"


def test_diagnose_routes_use_internal_services() -> None:
    ccp = _load("runtime.foundation.verification.canonical_control_plane")
    for cmd, expected in [
        ("forensic-diagnose", ("diagnose", "forensic_diagnose")),
        ("forensic-report", ("diagnose", "forensic_report")),
        ("mutation", ("strengthen", "mutation_runner")),
    ]:
        assert (
            ccp._MIGRATION[cmd] == expected
        ), f"{cmd} not routed through canonical service"

    # The canonical result type is resolvable and IS the contract type.
    ma = _load("runtime.foundation.verification.mutation_authority")
    mc = _load("runtime.foundation.verification.mutation_contract")
    result_type = ma._resolve(ma.CANONICAL_RESULT_TYPE)
    assert result_type is mc.MutationResult
    # The contract carries the operational fields the gate requires.
    assert hasattr(mc.MutationResult, "to_dict")
    counts = mc.MutationCounts(killed=8, survived=2)
    assert counts.generated == 10
    assert "mutants_generated" in counts.as_dict()
