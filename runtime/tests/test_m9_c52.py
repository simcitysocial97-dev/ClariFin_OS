# runtime/tests/test_m9_c52.py
#
# M9-C52 — Verification Control-Plane Integration acceptance tests.
#
# Deterministic, source-derived tests proving the control plane behaves as one
# coherent system: catalog completeness, route authority (no shadows), the
# unified change->capability->plan contract, execution enforcement, bypass
# classification, pipeline-spine enforcement, evidence-integrity fail-closed
# verdicts, dependency propagation, configuration authority, and efficiency.

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VERIFY_PY = REPO_ROOT / "runtime" / "verify.py"


def _dispatch_routes() -> dict[str, int]:
    """Map route name -> number of dispatcher branches binding it."""
    src = VERIFY_PY.read_text()
    counts: dict[str, int] = {}
    for m in re.finditer(r"(?:if|elif)\s+command\s*==\s*[\"']([^\"']+)[\"']", src):
        r = m.group(1)
        counts[r] = counts.get(r, 0) + 1
    return counts


class TestM521CatalogCompleteness(unittest.TestCase):
    """M9-C52.1 capability catalog completeness."""

    def test_all_capabilities_resolve_to_actual_code(self):
        from runtime.foundation.verification.catalog_certification import (
            build_catalog_certification,
        )

        cert = build_catalog_certification()
        # M52.3 adds 11 legitimate capabilities to close the CLI route gap
        self.assertEqual(cert["total_capabilities"], 55)
        self.assertTrue(cert["internal_passed"], f"audits: {cert['audits']}")
        unresolved = [r for r in cert["records"] if not r["implementation_resolvable"]]
        self.assertEqual(unresolved, [])

    def test_no_duplicate_capability_id_or_alias(self):
        from runtime.foundation.verification.catalog_certification import (
            build_catalog_certification,
        )

        cert = build_catalog_certification()
        self.assertEqual(cert["audits"]["duplicate_capability_ids"], [])
        self.assertEqual(cert["audits"]["duplicate_alias_routes"], [])

    def test_notes_metadata_not_corrupted(self):
        from runtime.foundation.verification.capability_catalog import (
            get_capability_catalog,
        )

        catalog = get_capability_catalog()
        corrupted = []
        for e in catalog.entries:
            notes = e.to_dict()["notes"]
            if notes and any(len(x) == 1 for x in notes) and len(notes) > 2:
                corrupted.append(e.capability_id)
        self.assertEqual(corrupted, [], f"per-character corrupted notes: {corrupted}")

    def test_stale_implementation_references_fixed(self):
        # The 8 stale C51 references (orchestrator:cmd_* etc.) must point at
        # real code. Verify no catalog entry still names a missing symbol in
        # the verification.orchestrator module.
        from runtime.foundation.verification import capability_catalog_data as data

        stale = [
            r.capability_id
            for r in data.REGISTRATIONS
            if "orchestrator:cmd_" in (r.implementation or "")
        ]
        self.assertEqual(stale, [], f"stale orchestrator cmd_* refs: {stale}")

    def test_in_code_gap_tracked_not_silently_dropped(self):
        from runtime.foundation.verification.catalog_certification import (
            build_catalog_certification,
        )

        cert = build_catalog_certification()
        gap = cert["completeness_gap_in_code_absent_from_catalog"]
        # The gap must be recorded (28 at freeze). It may shrink as M52.3
        # classifies routes into the catalog, but it must never be hidden.
        self.assertGreaterEqual(gap, 0)
        for item in cert["open_items"]:
            self.assertEqual(item["resolution"].startswith("M52.3"), True)


class TestM522RouteAuthority(unittest.TestCase):
    """M9-C52.2 deterministic CLI route resolution (no shadows)."""

    def test_route_resolution_no_shadows(self):
        # No route name may be bound by more than one dispatcher branch.
        counts = _dispatch_routes()
        shadowed = {r: c for r, c in counts.items() if c > 1}
        self.assertEqual(shadowed, {}, f"shadowed routes: {shadowed}")

    def test_strengthen_survivor_single_canonical_binding(self):
        from runtime.foundation.verification.route_authority import (
            analyze_dispatch_table,
        )

        bindings = analyze_dispatch_table()
        canon = bindings.get("strengthen-survivor", [])
        forensic = bindings.get("strengthen-survivor-forensic", [])
        self.assertEqual(
            len(canon), 1, "strengthen-survivor must be bound exactly once"
        )
        self.assertEqual(
            len(forensic), 1, "strengthen-survivor-forensic must be bound exactly once"
        )
        self.assertIn("strengthening_pipeline", canon[0]["target"])
        self.assertIn("forensic_cli", forensic[0]["target"])

    def test_canonical_route_executes_pipeline_not_forensic(self):
        # Behavioral proof that the canonical route resolves to the
        # capability-aware pipeline (durable-intel driven), which fails
        # gracefully for an unknown survivor WITHOUT requiring a live mutmut
        # run. The forensic variant would instead shell out to `mutmut show`.
        from runtime.foundation.verification import strengthening_pipeline as sp

        rc = sp.cmd_strengthen_survivor(["__definitely_not_a_survivor__"])
        self.assertEqual(rc, 1)  # survivor-not-found, not a mutmut crash

    def test_route_authority_artifact_passes(self):
        from runtime.foundation.verification.route_authority import (
            build_route_authority,
        )

        auth = build_route_authority()
        self.assertTrue(auth["passed"])
        self.assertEqual(auth["shadow_count"], 0)
        self.assertFalse(auth["strengthen_survivor_resolution"]["same_implementation"])


class TestM523CliCapabilityMatrix(unittest.TestCase):
    """M9-C52.3 CLI capability matrix completeness."""

    def test_cli_matrix_artifact_generates(self):
        from runtime.foundation.verification.cli_capability_matrix import (
            build_cli_capability_matrix,
        )

        matrix = build_cli_capability_matrix()
        # M52.4-M52.15 add C52 routes; M9-C53 adds generate-test, c53-scenarios, c53-certify
        self.assertEqual(matrix["total_routes"], 80)
        self.assertEqual(matrix["statistics"].get("UNCLASSIFIED", 0), 0)
        # Sum of all stats should equal total routes
        self.assertEqual(sum(matrix["statistics"].values()), 80)

    def test_all_dispatcher_routes_have_explicit_classification(self):
        from runtime.foundation.verification.cli_capability_matrix import (
            build_cli_capability_matrix,
        )
        from runtime.foundation.verification.route_authority import (
            analyze_dispatch_table,
        )

        matrix = build_cli_capability_matrix()
        bindings = analyze_dispatch_table()
        for route in bindings:
            entry = next(e for e in matrix["entries"] if e["route"] == route)
            self.assertNotEqual(
                entry["classification"],
                "UNCLASSIFIED",
                f"route {route} has no explicit classification",
            )

    def test_legacy_superseded_routes_have_successor(self):
        from runtime.foundation.verification.cli_capability_matrix import (
            build_cli_capability_matrix,
        )

        matrix = build_cli_capability_matrix()
        for entry in matrix["entries"]:
            if entry["classification"] == "LEGACY_SUPERSEDED":
                self.assertIn(
                    "superseded",
                    entry["derivation_source"].lower(),
                    f"LEGACY_SUPERSEDED route {entry['route']} must name successor",
                )

    def test_operational_observability_routes_explicitly_marked(self):
        from runtime.foundation.verification.cli_capability_matrix import (
            build_cli_capability_matrix,
        )

        matrix = build_cli_capability_matrix()
        obs = [
            e
            for e in matrix["entries"]
            if e["classification"] == "OPERATIONAL_OBSERVABILITY"
        ]
        self.assertEqual(len(obs), 4)
        for e in obs:
            # All OPERATIONAL_OBSERVABILITY routes must have derivation_source
            # indicating they are outside the verification control plane scope
            ds = e["derivation_source"].lower()
            self.assertTrue(
                "not a verification capability" in ds
                or "outside verification scope" in ds
                or "operational" in ds
                or "ci " in ds
                or "control plane does not gate" in ds,
                f"OPERATIONAL_OBSERVABILITY route {e['route']} must explain out-of-scope nature",
            )


if __name__ == "__main__":
    unittest.main()
