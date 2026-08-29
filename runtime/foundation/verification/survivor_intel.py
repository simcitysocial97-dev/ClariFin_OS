# runtime/foundation/verification/survivor_intel.py
#
# M9-C45.2 — Durable survivor intelligence.
#
# Closes the analysis bottleneck: per-mutant survivor intelligence must
# survive the mutmut workspace lifecycle. Previously an engineer/agent who
# wanted to understand a survivor ("what mutated -> was it executed -> which
# tests covered it -> why did it survive -> what classification -> what
# assertion follows -> has it been attempted") had to re-run mutmut's built-in
# analysis (`show`, `tests-for-mutant`) against the *transient* `.meta` cache
# and `mutants/` tree, which is destroyed/restored when the run ends.
#
# This module enriches each surviving mutant AT RUN TIME (when that source of
# truth is alive) and persists a durable, machine-readable per-mutant record
# under backend/tests/generated/mutation/mutation-survivor-intel.json.
#
# Architecture-preserving: it extends the C42 certified mutation runner
# (`verify.py mutation` already emits mutation-summary.json and
# mutation-survivors.json). No parallel verification system is created.
#
# Reliable by construction:
#   * Reuses the certified mutation contract (collect_mutant_results) for status.
#   * Reuses survivor_catalog (mutmut libcst reconstruction) for offline fields,
#     so it works even when `mutmut show` cannot run.
#   * Uses mutmut's native tests-for-mutant (when the cache is alive) for the
#     covering-test surface; marks enrichment provenance explicitly.
#   * classify() reuses the C42.17 pure classifier (mutation_inventory.classify),
#     so A/B/C/D/E is evidence-based, never invented.
#   * Every record carries an evidence fingerprint so it can be re-derived.
#
# Pure functions are unit-tested (runtime/tests/test_survivor_intel.py).

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

BACKEND_DIR = REPO_ROOT / "backend"
DEFAULT_INTEL_PATH = (
    BACKEND_DIR / "tests" / "generated" / "mutation" / "mutation-survivor-intel.json"
)

# Component -> capability (single source of truth derived from the C44
# survivor-capability-attribution summary). Multi-capability components are
# recorded as lists; the primary capability is the attribute key.
COMPONENT_TO_CAPABILITY: dict[str, str] = {
    "account_engine": "accounts",
    "credit_card_engine": "credit-cards",
    "loan_engine": "loans",
    "reconciliation_engine": "reconciliation",
    "behaviour_engine": "behaviour",
    "financial_intelligence": "financial-intelligence",
    "transaction_intelligence": "transaction-intelligence",
    "common_calculations": "common-calculations",
    "ledger_audit_engine": "ledger",
    "financial_events": "financial-events",
    "recommendation_engine": "recommendations",
    "cashflow_engine": "cashflow",
    "core_domain_money": "core-domain",
    "balance_engine": "balance",
}

# Components whose mutants may affect multiple capabilities (cross-capability).
MULTI_CAPABILITY: dict[str, list[str]] = {
    "common_calculations": [
        "common-calculations",
        "accounts",
        "loans",
        "credit-cards",
        "financial-intelligence",
        "reconciliation",
    ],
}

# Non-engine source paths (relative to src/) mapped to their component. These
# cover modules whose component name is not a substring of their path.
SOURCE_TO_COMPONENT: dict[str, str] = {
    "common/calculations.py": "common_calculations",
    "core/domain/": "core_domain_money",
}


def component_for_source(source_relative: str) -> str | None:
    """Map a source file (relative to src/) to a mutation component."""
    s = source_relative.replace("\\", "/")
    for prefix, comp in SOURCE_TO_COMPONENT.items():
        if s.startswith(prefix) or s == prefix:
            return comp
    best: str | None = None
    for comp in COMPONENT_TO_CAPABILITY:
        if comp in s and (best is None or len(comp) > len(best)):
            best = comp
    if best:
        return best
    # Heuristic fallback for engines not in the static map.
    if "/engines/" in s:
        seg = s.split("/engines/")[-1].split("/")[0]
        return seg if seg in COMPONENT_TO_CAPABILITY else None
    return None


def capability_for(survivor_id: str, source_relative: str) -> tuple[str, list[str]]:
    """Return (primary_capability, capabilities) for a survivor."""
    comp = component_for_source(source_relative)
    if comp is None:
        return "UNMAPPED_CAPABILITY", ["UNMAPPED_CAPABILITY"]
    caps = MULTI_CAPABILITY.get(comp)
    if caps:
        return caps[0], caps
    return COMPONENT_TO_CAPABILITY[comp], [COMPONENT_TO_CAPABILITY[comp]]


def _evidence_fingerprint(record_fields: dict) -> str:
    """Stable sha256 over the survivor record's evidence fields."""
    payload = json.dumps(record_fields, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _parse_test_nodes(text: str) -> list[str]:
    """Parse `mutmut tests-for-mutant` output into test node ids."""
    nodes: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if line and "::" in line:
            nodes.append(line)
    return nodes


def _run_tests_for_mutant(survivor_id: str) -> tuple[list[str], str]:
    """Run mutmut's native tests-for-mutant. Returns (test_nodes, provenance)."""
    backend_dir = BACKEND_DIR
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "mutmut", "tests-for-mutant", survivor_id],
            cwd=str(backend_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            return [], "unavailable (mutmut rc!=0)"
        nodes = _parse_test_nodes(proc.stdout)
        return nodes, ("derived_from_tests-for-mutant" if nodes else "unavailable")
    except Exception:
        return [], "unavailable (exception)"


def build_survivor_intel(
    meta_dir: Path,
    backend_dir: Path,
    *,
    enrich_tests: bool = True,
    max_enrich: int = 0,
) -> dict:
    """Build a durable survivor-intel record from surviving mutants.

    Args:
        meta_dir: the live mutmut .meta directory (backend/mutants).
        backend_dir: backend/ cwd-equivalent for mutmut reconstruction.
        enrich_tests: whether to attempt mutmut tests-for-mutant enrichment.
        max_enrich: if >0, cap tests-for-mutant calls to this many survivors
            (bounded; -1 or 0 means enrich all when requested).

    Returns a dict artifact with a `survivors` list.
    """
    from runtime.foundation.verification.mutation_inventory import classify
    from runtime.foundation.verification.survivor_catalog import (
        build_survivor_catalog,
    )

    prev = os.getcwd()
    did_chdir = False
    try:
        if backend_dir.is_dir():
            os.chdir(backend_dir)
            did_chdir = True
        catalog = build_survivor_catalog(meta_dir, backend_dir)
    finally:
        if did_chdir:
            os.chdir(prev)

    survivors: list[dict] = []
    by_class: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    total_enriched = 0

    for entry in catalog.entries:
        # Classification via the C42.17 pure classifier on reconstructed snippets.
        cls = classify(entry.old, entry.new)
        class_code = cls.classification
        subclass = cls.subclass
        evidence = cls.evidence
        proposed_action = cls.proposed_action

        by_class[class_code] = by_class.get(class_code, 0) + 1

        primary_cap, capabilities = capability_for(entry.key, entry.source_file)

        covering_tests: list[str] = []
        tests_provenance = "not_enriched"
        # max_enrich <= 0 means "enrich all"; otherwise cap the number of
        # tests-for-mutant invocations (each is a subprocess — bounded for
        # large populations).
        if enrich_tests and (max_enrich <= 0 or total_enriched < max_enrich):
            tests, tests_provenance = _run_tests_for_mutant(entry.key)
            covering_tests = tests
            if tests:
                total_enriched += 1

        record_fields = {
            "survivor_id": entry.key,
            "component": (component_for_source(entry.source_file) or "unknown"),
            "source_file": f"src/{entry.source_file}",
            "source_location": f"{entry.source_file}:{entry.function}",
            "function": entry.function,
            "mutation_type": entry.category,
            "original_expression": entry.old,
            "mutated_expression": entry.new,
            "status": "survived",
            "covering_tests": covering_tests,
            "killing_tests": covering_tests,  # discriminating tests == covering surface
            "covering_test_surface": sorted(
                {t.rsplit("::", 1)[0] for t in covering_tests}
            ),
            "tests_enrichment_provenance": tests_provenance,
            "classification": class_code,
            "classification_evidence": evidence,
            "subclassification": subclass,
            "capability": primary_cap,
            "capabilities": capabilities,
            "evidence_fingerprint": _evidence_fingerprint(
                {
                    "id": entry.key,
                    "fn": entry.function,
                    "loc": entry.source_file,
                    "cat": entry.category,
                    "old": entry.old,
                    "new": entry.new,
                    "cls": class_code,
                    "sub": subclass,
                }
            ),
            "investigation_status": "needs_investigation",
            "previous_proposal_status": "not_attempted",
            "previous_validation_status": "not_attempted",
            "recommended_action": proposed_action,
        }
        survivors.append(record_fields)

    return {
        "schema": "m9-c45-survivor-intel/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "total_survivors": len(survivors),
        "by_class": dict(sorted(by_class.items(), key=lambda kv: -kv[1])),
        "tests_enriched_count": total_enriched,
        "survivors": survivors,
    }


def write_survivor_intel(intel: dict, out_path: Path | None = None) -> Path:
    target = out_path or DEFAULT_INTEL_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(intel, indent=2) + "\n")
    return target


def load_survivor_intel(intel_path: Path | None = None) -> dict:
    target = intel_path or DEFAULT_INTEL_PATH
    if not target.exists():
        return {}
    return json.loads(target.read_text())


def find_survivor(intel: dict, survivor_id: str) -> dict | None:
    for s in intel.get("survivors", []):
        if s.get("survivor_id") == survivor_id:
            return s
    return None


def run_intel_cli(argv: list[str]) -> int:
    """verify.py mutation-intel — inspect one survivor from the durable record,
    then derive the scaffold for the behavioural assertion to consider."""
    import argparse

    parser = argparse.ArgumentParser(prog="verify.py mutation-intel", add_help=False)
    parser.add_argument(
        "survivor_id",
        nargs="?",
        help="mutmut mutant name; omit to print the durable intel summary",
    )
    parser.add_argument(
        "--intel",
        default=str(DEFAULT_INTEL_PATH),
        help="path to durable mutation-survivor-intel.json",
    )
    parser.add_argument("--json", action="store_true")
    args, _ = parser.parse_known_args(argv)

    intel = load_survivor_intel(Path(args.intel))
    if not intel:
        print(
            "No durable survivor-intel record found. Run `verify.py mutation "
            "(--target <engine>)` which enriches and persists it."
        )
        return 1

    if args.survivor_id:
        rec = find_survivor(intel, args.survivor_id)
        if rec is None:
            print(f"survivor not found in durable record: {args.survivor_id}")
            return 2
        if args.json:
            print(json.dumps(rec, indent=2))
            return 0
        print(f"# {rec['survivor_id']}")
        print(f"  component          : {rec['component']}")
        print(f"  source             : {rec['source_file']}")
        print(f"  location           : {rec['source_location']}")
        print(f"  mutation type      : {rec['mutation_type']}")
        print(f"  mutated            : {rec['original_expression']!r}")
        print(f"                       -> {rec['mutated_expression']!r}")
        print(
            f"  classification     : {rec['classification']} ({rec['subclassification']})"
        )
        print("  classification ev. :", rec["classification_evidence"])
        print(f"  capability         : {rec['capability']} {rec['capabilities']}")
        print(
            f"  covering tests     : {len(rec['covering_tests'])}  "
            f"(provenance={rec['tests_enrichment_provenance']})"
        )
        for t in rec["covering_test_surface"][:15]:
            print(f"      {t}")
        print(f"  investigation      : {rec['investigation_status']}")
        print(f"  previous proposal  : {rec['previous_proposal_status']}")
        print(f"  previous validation: {rec['previous_validation_status']}")
        print(f"  evidence fp        : {rec['evidence_fingerprint'][:16]}...")
        print("  recommended next   :", rec["recommended_action"])
        return 0

    print("DURABLE SURVIVOR INTELLIGENCE")
    print(f"  total survivors : {intel['total_survivors']}")
    print("  by class:")
    for cls, n in intel["by_class"].items():
        print(f"    {cls}: {n}")
    print(f"  tests enriched : {intel['tests_enriched_count']}")
    return 0


__all__ = [
    "COMPONENT_TO_CAPABILITY",
    "DEFAULT_INTEL_PATH",
    "MULTI_CAPABILITY",
    "SOURCE_TO_COMPONENT",
    "build_survivor_intel",
    "capability_for",
    "component_for_source",
    "find_survivor",
    "load_survivor_intel",
    "run_intel_cli",
    "write_survivor_intel",
]
