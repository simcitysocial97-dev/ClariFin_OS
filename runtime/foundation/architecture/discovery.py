"""The single architecture discovery pipeline — Program 13.2, Phase 2.

Constitutional rule: *there must be exactly one architecture discovery
pipeline; everything else is a consumer.*

This module is that pipeline. It owns the ordered set of discovery phases
established by Program 13.1 and is the only code path allowed to WRITE the
constitutional artifacts under ``runtime/generated/``.

Every other runtime subsystem must read through
:func:`runtime.foundation.architecture.get_architecture`.

Phases (ordered; later phases consume earlier outputs):

    1. inventory       -> architecture-inventory.json
    2. topology        -> engine-topology.json
    3. ownership       -> ownership-graph.json
    4. execution       -> execution-graph.json
    5. normalization   -> engine-normalization.json
    6. knowledge       -> knowledge-reconstruction.json
    7. artifacts       -> artifact-ownership-v2.json
    8. gap             -> certification-gap-analysis.json
"""

from __future__ import annotations

import importlib.util
import io
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_DIR = REPO_ROOT / "runtime"
GENERATED_DIR = RUNTIME_DIR / "generated"


@dataclass(frozen=True, slots=True)
class DiscoveryPhase:
    order: int
    name: str
    module: str
    entry: str
    output: str
    purpose: str


#: The ONE pipeline. No other module may declare discovery phases.
PHASES: tuple[DiscoveryPhase, ...] = (
    DiscoveryPhase(
        1,
        "inventory",
        "analyze_architecture",
        "main",
        "architecture-inventory.json",
        "Classify every module into exactly one canonical node type using imports, "
        "registrations, decorators and execution flow.",
    ),
    DiscoveryPhase(
        2,
        "topology",
        "analyze_engine_topology",
        "main",
        "engine-topology.json",
        "Discover canonical engines (package roots + designated single files) and "
        "their implementation modules, services, routers, repositories, tests.",
    ),
    DiscoveryPhase(
        3,
        "ownership",
        "analyze_ownership",
        "build",
        "ownership-graph.json",
        "Build the evidence-backed ownership hierarchy. Engines own modules; "
        "modules are never ownership roots.",
    ),
    DiscoveryPhase(
        4,
        "execution",
        "analyze_execution",
        "build",
        "execution-graph.json",
        "Build the runtime call path. Execution may traverse implementation "
        "modules; ownership must not.",
    ),
    DiscoveryPhase(
        5,
        "normalization",
        "analyze_engine_normalization",
        "build",
        "engine-normalization.json",
        "Classify engine migration status (canonical / partial / parked / façade / "
        "orphan / implementation-only).",
    ),
    DiscoveryPhase(
        6,
        "knowledge",
        "analyze_knowledge",
        "build",
        "knowledge-reconstruction.json",
        "Reconstruct knowledge entities from the ownership graph (architecture "
        "based, not filesystem based).",
    ),
    DiscoveryPhase(
        7,
        "artifacts",
        "analyze_artifacts",
        "build",
        "artifact-ownership-v2.json",
        "Assign Producer/Owner/Consumers/Stage/Pipeline/Lifecycle/Retention to "
        "every generated artifact.",
    ),
    DiscoveryPhase(
        8,
        "gap",
        "analyze_gap",
        "build",
        "certification-gap-analysis.json",
        "Compare legacy certification results against the canonical model and "
        "classify each finding.",
    ),
)

PHASE_BY_NAME: dict[str, DiscoveryPhase] = {p.name: p for p in PHASES}

#: Artifacts written by this pipeline. Nothing else may write them.
CANONICAL_OUTPUTS: tuple[str, ...] = tuple(p.output for p in PHASES)


def _load_phase_callable(phase: DiscoveryPhase) -> Callable[[], Any]:
    source = RUNTIME_DIR / f"{phase.module}.py"
    if not source.exists():  # pragma: no cover - defensive
        raise FileNotFoundError(f"Discovery phase module missing: {source}")
    spec = importlib.util.spec_from_file_location(
        f"runtime.foundation.architecture._phase_{phase.name}", source
    )
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"Cannot load discovery phase {phase.name} from {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    fn = getattr(module, phase.entry, None)
    if fn is None:  # pragma: no cover - defensive
        raise AttributeError(f"Phase {phase.name} has no entry point {phase.entry}()")
    return fn


def run_discovery(
    phases: list[str] | None = None, quiet: bool = True
) -> list[dict[str, Any]]:
    """Execute the single discovery pipeline and return per-phase results."""
    selected = [PHASE_BY_NAME[n] for n in phases] if phases else list(PHASES)
    results: list[dict[str, Any]] = []
    for phase in sorted(selected, key=lambda p: p.order):
        fn = _load_phase_callable(phase)
        buffer = io.StringIO()
        try:
            if quiet:
                with redirect_stdout(buffer):
                    fn()
            else:
                fn()
            status = "ok"
            error = ""
        except Exception as exc:  # pragma: no cover - surfaced to caller
            status = "error"
            error = f"{type(exc).__name__}: {exc}"
        out_path = GENERATED_DIR / phase.output
        results.append(
            {
                "order": phase.order,
                "phase": phase.name,
                "module": f"runtime/{phase.module}.py",
                "entry": phase.entry,
                "output": f"runtime/generated/{phase.output}",
                "status": status,
                "error": error,
                "output_exists": out_path.exists(),
            }
        )
    return results


def pipeline_manifest() -> dict[str, Any]:
    return {
        "pipeline": "runtime.foundation.architecture.discovery",
        "rule": (
            "Exactly one architecture discovery pipeline exists. Every other "
            "runtime subsystem is a consumer of "
            "runtime.foundation.architecture.get_architecture()."
        ),
        "phases": [
            {
                "order": p.order,
                "name": p.name,
                "implementation": f"runtime/{p.module}.py::{p.entry}",
                "output": f"runtime/generated/{p.output}",
                "purpose": p.purpose,
            }
            for p in PHASES
        ],
    }
