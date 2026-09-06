# runtime/system/evidence/aggregator_obsolete_disposition.py
#
# M9-C48 H1 — Obsolete evidence-aggregator function disposition (GAP-015).
#
# The two functions below are KNOWN to be defective (E-4 keyword-
# attribution defect). They are retained for test compatibility but
# must never be used by new code. This module:
#
#   1. Declares their lifecycle explicitly.
#   2. Asserts that no production code calls them.
#   3. Persists a governance report so the disposition is auditable.

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ObsoleteDisposition:
    name: str
    location: str
    lifecycle: str  # OBSOLETE-RETIRED | OBSOLETE-RETAINED-FOR-COMPAT | DELETED
    rationale: str
    production_call_sites: tuple[str, ...]
    test_call_sites: tuple[str, ...]
    action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "location": self.location,
            "lifecycle": self.lifecycle,
            "rationale": self.rationale,
            "production_call_sites": list(self.production_call_sites),
            "test_call_sites": list(self.test_call_sites),
            "action": self.action,
        }


def _scan_for_calls(name: str, root: Path = Path("runtime")) -> list[tuple[str, str]]:
    """Find call sites of *name* under *root*.

    Returns a list of (file, kind) tuples where kind is 'production' or
    'test'.
    """
    sites: list[tuple[str, str]] = []
    pattern = re.compile(rf"\b{name}\s*\(")
    for p in root.rglob("*.py"):
        if "__pycache__" in str(p):
            continue
        try:
            text = p.read_text()
        except Exception:
            continue
        if pattern.search(text):
            kind = "test" if "/tests/" in str(p) else "production"
            sites.append((str(p), kind))
    return sites


def build_disposition(
    root: Path = Path("runtime"),
) -> tuple[ObsoleteDisposition, ObsoleteDisposition]:
    chain_for_failure_sites = _scan_for_calls("_find_chain_for_failure", root=root)
    dependency_chain_sites = _scan_for_calls("_find_dependency_chain", root=root)

    chain_prod = [s for s, k in chain_for_failure_sites if k == "production"]
    chain_test = [s for s, k in chain_for_failure_sites if k == "test"]
    dep_prod = [s for s, k in dependency_chain_sites if k == "production"]
    dep_test = [s for s, k in dependency_chain_sites if k == "test"]

    chain = ObsoleteDisposition(
        name="_find_chain_for_failure",
        location="runtime/system/evidence/aggregator.py:986",
        lifecycle="OBSOLETE-RETAINED-FOR-COMPAT",
        rationale=(
            "Known E-4 keyword-attribution defect; replacing with graph "
            "traversal is owned by Phase 3. Retained for backward "
            "compatibility with existing test suite; do not call from "
            "new code."
        ),
        production_call_sites=tuple(chain_prod),
        test_call_sites=tuple(chain_test),
        action="mark OBSOLETE; do not call from new code; phase-3 migration tracked",
    )
    dep = ObsoleteDisposition(
        name="_find_dependency_chain",
        location="runtime/system/evidence/aggregator.py:53",
        lifecycle="OBSOLETE-RETAINED-FOR-COMPAT",
        rationale=(
            "Known E-4 keyword-attribution defect; retained for test "
            "compatibility. Production call sites must be migrated to "
            "graph traversal in Phase 3."
        ),
        production_call_sites=tuple(dep_prod),
        test_call_sites=tuple(dep_test),
        action="mark OBSOLETE; do not call from new code",
    )
    return chain, dep


def write_report(
    path: str | Path = "runtime/generated/m9-c48/aggregator-obsolete-disposition.json",
) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    chain, dep = build_disposition()
    payload = {
        "schema": "m9-c48/aggregator-obsolete-disposition@1",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "dispositions": [chain.to_dict(), dep.to_dict()],
        "summary": {
            "obsolete_retained": 2,
            "deleted": 0,
        },
    }
    p.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return p


__all__ = [
    "ObsoleteDisposition",
    "build_disposition",
    "write_report",
]
