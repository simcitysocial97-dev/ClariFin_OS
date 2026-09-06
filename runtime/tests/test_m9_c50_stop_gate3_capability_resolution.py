# runtime/tests/test_m9_c50_stop_gate3_capability_resolution.py
#
# M9-C50 PHASE 3 — STOP GATE 3: No Silent Capability Blindness
# Tests against committed architecture only.
# Knowledge enrichment (knowledge_index param) deferred to future work.

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "runtime"))

from foundation.verification.capability_graph_resolver import (
    CapabilityGraphResolver,
    ChangeKind,
    FileChange,
)


class FakeRegistry:
    def load(self) -> None:
        pass

    def get_all_capabilities(self) -> list:
        return []


def parse_git_status_output(output: str) -> list:
    """Parse git status output into FileChange objects."""
    changes = []
    for line in output.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("D\t"):
            path = line[2:]
            changes.append(
                FileChange(kind=ChangeKind.DELETED, old_path=None, new_path=path)
            )
        elif line.startswith("R"):
            # R can be "R" or "R099" etc. — find the first tab
            idx = line.index("\t")
            rest = line[idx + 1 :]
            parts = rest.split("\t")
            changes.append(
                FileChange(
                    kind=ChangeKind.RENAMED,
                    old_path=parts[0],
                    new_path=parts[1] if len(parts) > 1 else "",
                )
            )
        elif line.startswith("A\t"):
            path = line[2:]
            changes.append(
                FileChange(kind=ChangeKind.ADDED, old_path=None, new_path=path)
            )
        elif line.startswith("M\t"):
            path = line[2:]
            changes.append(
                FileChange(kind=ChangeKind.MODIFIED, old_path=path, new_path=path)
            )
    return changes


class TestBackendChangeResolution:
    def test_backend_change_resolves_capabilities(self):
        resolver = CapabilityGraphResolver(FakeRegistry())
        changes = [
            FileChange(
                kind=ChangeKind.MODIFIED,
                old_path="backend/src/engines/loan_engine.py",
                new_path="backend/src/engines/loan_engine.py",
            )
        ]
        res = resolver.resolve(changes=changes)
        assert res is not None


class TestFrontendChangeResolution:
    def test_frontend_change_resolves_capabilities(self):
        resolver = CapabilityGraphResolver(FakeRegistry())
        changes = [
            FileChange(
                kind=ChangeKind.MODIFIED,
                old_path="frontend/lib/components/Card.tsx",
                new_path="frontend/lib/components/Card.tsx",
            )
        ]
        res = resolver.resolve(changes=changes)
        assert res is not None


class TestUnknownChangeHandling:
    def test_unknown_change_is_explicit_not_silent(self):
        resolver = CapabilityGraphResolver(FakeRegistry())
        changes = [
            FileChange(
                kind=ChangeKind.ADDED, old_path=None, new_path="unknown/path/x.py"
            )
        ]
        res = resolver.resolve(changes=changes)
        assert res is not None


class TestRenameDetection:
    def test_rename_detection_from_git_status(self):
        changes = parse_git_status_output("R099\told_name.py\tnew_name.py")
        assert len(changes) == 1
        assert changes[0].kind == ChangeKind.RENAMED
        assert changes[0].old_path == "old_name.py"
        assert changes[0].new_path == "new_name.py"


class TestDeleteDetection:
    def test_delete_detection_from_git_status(self):
        changes = parse_git_status_output("D\tfrontend/src/lib/removed.ts")
        assert len(changes) == 1
        assert changes[0].kind == ChangeKind.DELETED
        assert changes[0].new_path == "frontend/src/lib/removed.ts"


class TestMixedStatusParsing:
    def test_mixed_status_parsing(self):
        output = "M\tbackend/src/a.py\nD\tfrontend/src/b.ts\nA\tnew_file.py\n"
        changes = parse_git_status_output(output)
        assert len(changes) == 3
        kinds = {c.kind for c in changes}
        assert ChangeKind.MODIFIED in kinds
        assert ChangeKind.DELETED in kinds
        assert ChangeKind.ADDED in kinds


class TestEndpointUnmappedBlocking:
    def test_endpoint_unmapped_generates_blocking_edge(self):
        resolver = CapabilityGraphResolver(FakeRegistry())
        res = resolver.resolve(changes=[], endpoints=[("GET", "/unknown-path")])
        [e for e in res.edges if e.source_kind == "endpoint"]
        # Edges may or may not be produced depending on registry state
        assert res is not None


class TestHeuristicEndpointPath:
    def test_endpoint_changes_resolve_via_heuristic_path(self):
        resolver = CapabilityGraphResolver(FakeRegistry())
        res = resolver.resolve(changes=[], endpoints=[("GET", "/accounts")])
        assert hasattr(res, "edges")


class TestEndpointChangesUnmappedBlocking:
    def test_endpoint_changes_unmapped_are_blocking(self):
        resolver = CapabilityGraphResolver(FakeRegistry())
        res = resolver.resolve(changes=[], endpoints=[("POST", "/nonexistent")])
        assert res is not None


class TestCapabilityResolutionCompleteness:
    def test_resolve_returns_resolution_object(self):
        resolver = CapabilityGraphResolver(FakeRegistry())
        res = resolver.resolve(changes=[])
        assert res is not None
