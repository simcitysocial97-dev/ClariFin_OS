# Archive Directory

This directory contains files that have been removed from the active codebase
but preserved for historical reference, rollback, or audit purposes.

## Contents

### program16_analysis.py
Auto-generated analysis dump from Program 16 (Repository Canonicalization).
Large output artifact (~1,749 lines) not imported by any runtime module.
Retained for reference only — the generated artifacts it produced are in
`runtime/generated/`.

### analysis_scripts/
Individual analysis scripts that were previously at the repository root.
These have been superseded by the modular architecture discovery pipeline
in `runtime/foundation/architecture/`. The pipeline loads phase modules
dynamically; if any of these scripts are needed again, restore them to
`runtime/` and register in `runtime/foundation/architecture/discovery.py`.

Scripts in this directory:
- `analyze_architecture.py` — Phase 1: module classification
- `analyze_engine_topology.py` — Phase 2: engine discovery
- `analyze_ownership.py` — Phase 3: ownership graph
- `analyze_execution.py` — Phase 4: runtime call paths
- `analyze_engine_normalization.py` — Phase 5: migration status
- `analyze_knowledge.py` — Phase 6: knowledge reconstruction
- `analyze_artifacts.py` — Phase 7: artifact ownership
- `analyze_gap.py` — Phase 8: certification gap analysis

NOTE: If these scripts are restored, update `runtime/foundation/architecture/discovery.py`
and `runtime/foundation/architecture/sources.py` to reference the new locations.
