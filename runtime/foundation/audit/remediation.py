"""Platform Remediation Plan — Program 13.

Generates deterministic repair plan for all root cause clusters.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
REMEDIATION_PATH = REPO_ROOT / "runtime" / "generated" / "platform-remediation.md"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_remediation() -> str:
    lines: list[str] = []
    lines.append("# Engineering Platform Remediation Plan")
    lines.append("")
    lines.append(f"**Generated:** {_now_iso()}")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append("This document provides deterministic repair instructions for all")
    lines.append("certification-blocking root cause clusters identified by the")
    lines.append("Engineering Platform Certification Audit.")
    lines.append("")
    lines.append("## Repair Phases")
    lines.append("")
    lines.append("Repairs must be executed in dependency order. Never repair")
    lines.append("downstream before upstream.")
    lines.append("")

    phases = [
        {
            "phase": 1,
            "name": "Repository Graph Integrity",
            "clusters": ["CLUSTER-REPOSITORY_GRAPH_INTEGRITY"],
            "problems": [
                "Repository index has edge referential integrity violations",
                "Fresh graph build produces 1362 errors",
                "Node and edge counts are inconsistent",
            ],
            "repair_steps": [
                "1. Inspect `runtime/foundation/repository/builder/builder.py` validate() method",
                "2. Fix scanner edge generation to reference valid node IDs",
                "3. Ensure builder.build() completes without errors",
                "4. Verify index.json edge count matches declared count",
            ],
            "files": [
                "runtime/foundation/repository/builder/builder.py",
                "runtime/foundation/repository/scanner/base.py",
                "runtime/generated/repository/index.json",
            ],
            "functions": [
                "RepositoryBuilder.build()",
                "RepositoryBuilder.validate()",
                "BaseScanner.scan()",
            ],
            "tests": [
                "python3 -c 'from runtime.foundation.repository.builder.builder import RepositoryBuilder; b=RepositoryBuilder(); b.build(); print(b.validate().is_valid())'",
            ],
            "verification": "python runtime/verify.py graph",
            "expected_result": "Graph builds cleanly with zero structural errors and complete referential integrity",
        },
        {
            "phase": 2,
            "name": "Cross-Layer Map Completeness",
            "clusters": ["CLUSTER-CROSS_LAYER_COMPLETENESS"],
            "problems": [
                "72 duplicate endpoints across cross-layer chains",
                "16 chains missing capabilities",
                "5 chains missing routers",
            ],
            "repair_steps": [
                "1. Inspect cross-layer map builder",
                "2. Add deduplication pass for endpoints",
                "3. Ensure all chains have complete field population",
                "4. Validate chain completeness before write",
            ],
            "files": [
                "runtime/generated/cross-layer-map.json",
            ],
            "functions": [
                "CrossLayerImpactPlanner.analyze_cross_layer_impact()",
            ],
            "tests": [
                "python3 -c 'import json; m=json.load(open(\"runtime/generated/cross-layer-map.json\")); print(len(m), \"chains\")'",
            ],
            "verification": "python runtime/verify.py graph",
            "expected_result": "All chains have unique endpoints and complete ownership fields",
        },
        {
            "phase": 3,
            "name": "Dependency Graph Integrity",
            "clusters": ["CLUSTER-DEPENDENCY_GRAPH_INTEGRITY"],
            "problems": [
                "194 edges with missing source nodes",
                "525 edges with missing target nodes",
                "1329 structural errors in graph",
                "671 isolated nodes (60% of graph)",
            ],
            "repair_steps": [
                "1. Repair repository graph first (Phase 1 dependency)",
                "2. Rebuild cross-layer map (Phase 2 dependency)",
                "3. Rebuild dependency graph from clean data",
                "4. Verify no isolated nodes remain",
            ],
            "files": [
                "runtime/foundation/repository/graph/graph_service.py",
                "runtime/generated/repository/index.json",
            ],
            "functions": [
                "RepositoryGraphService.load()",
                "RepositoryGraphService.validate()",
            ],
            "tests": [
                "python3 -c 'from runtime.foundation.repository.graph.graph_service import RepositoryGraphService; s=RepositoryGraphService(); print(s.validate())'",
            ],
            "verification": "python runtime/verify.py graph",
            "expected_result": "Graph has zero structural errors, no missing nodes, no isolated nodes",
        },
        {
            "phase": 4,
            "name": "Knowledge Base Data Quality",
            "clusters": ["CLUSTER-KNOWLEDGE_DATA_QUALITY"],
            "problems": [
                "101 broken links in knowledge index",
                "Indexer count mismatch for documentation (saved=131, rebuilt=132)",
            ],
            "repair_steps": [
                "1. Repair cross-layer map (Phase 2 dependency)",
                "2. Rebuild knowledge index from clean artifacts",
                "3. Validate all references are resolvable",
                "4. Verify indexer count consistency",
            ],
            "files": [
                "runtime/foundation/knowledge/indexer.py",
                "runtime/generated/knowledge-index.json",
            ],
            "functions": [
                "KnowledgeIndexer.build_index()",
                "KnowledgeIndexer.validate()",
            ],
            "tests": [
                "python3 -c 'from runtime.foundation.knowledge.indexer import build_index; idx=build_index(); print(idx.total_entries, \"entries\")'",
            ],
            "verification": "python runtime/verify.py knowledge",
            "expected_result": "Zero broken links, indexer count matches rebuilt count",
        },
        {
            "phase": 5,
            "name": "Executor Command Formatting",
            "clusters": ["CLUSTER-EXECUTOR_COMMAND_FORMTING"],
            "problems": [
                "execute_python does not format command correctly",
                "execute_pytest does not format command correctly",
                "execute_vitest does not format command correctly",
                "execute_playwright does not format command correctly",
            ],
            "repair_steps": [
                "1. Inspect each execute_* method in runtime/foundation/verification/executor.py",
                "2. Fix command string formatting",
                "3. Verify commands execute correctly",
            ],
            "files": [
                "runtime/foundation/verification/executor.py",
            ],
            "functions": [
                "Executor.execute_python()",
                "Executor.execute_pytest()",
                "Executor.execute_vitest()",
                "Executor.execute_playwright()",
            ],
            "tests": [
                "python3 -c 'from runtime.foundation.verification.executor import Executor; e=Executor(); print(e.execute_python(\"echo test\"))'",
            ],
            "verification": "python runtime/verify.py quick",
            "expected_result": "All execute_* methods produce correctly formatted commands",
        },
        {
            "phase": 6,
            "name": "Executor Resilience",
            "clusters": ["CLUSTER-EXECUTOR_RESILIENCE"],
            "problems": [
                "No retry logic for failed commands",
                "No cancellation support",
                "No parallel execution support",
            ],
            "repair_steps": [
                "1. Add retry decorator to execute() method",
                "2. Add cancel() method to Executor",
                "3. Add parallel execution support for independent commands",
            ],
            "files": [
                "runtime/foundation/verification/executor.py",
            ],
            "functions": [
                "Executor.execute()",
                "Executor.cancel()",
            ],
            "tests": [
                "python3 -c 'from runtime.foundation.verification.executor import Executor; e=Executor(); print(hasattr(e, \"cancel\"))'",
            ],
            "verification": "python runtime/verify.py quick",
            "expected_result": "Executor supports retry, cancellation, and parallel execution",
        },
        {
            "phase": 7,
            "name": "CLI Completeness",
            "clusters": ["CLUSTER-CLI_COMPLETENESS"],
            "problems": [
                "dashboard command is not implemented",
            ],
            "repair_steps": [
                "1. Implement cmd_dashboard() in runtime/verify.py",
                "2. Register dashboard command in main()",
                "3. Verify command executes without error",
            ],
            "files": [
                "runtime/verify.py",
            ],
            "functions": [
                "cmd_dashboard()",
            ],
            "tests": [
                "python runtime/verify.py dashboard",
            ],
            "verification": "python runtime/verify.py audit",
            "expected_result": "dashboard command is recognized and executes successfully",
        },
        {
            "phase": 8,
            "name": "GitHub Actions Completeness",
            "clusters": ["CLUSTER-GITHUB_ACTIONS_COMPLETENESS"],
            "problems": [
                "verification-runtime workflow missing artifact upload",
                "quality workflow missing artifact upload",
                "backend-verify workflow missing artifact upload",
                "frontend-verify workflow missing artifact upload",
            ],
            "repair_steps": [
                "1. Inspect each workflow in .github/workflows/",
                "2. Add upload-runtime composite action step",
                "3. Verify artifact names are unique",
            ],
            "files": [
                ".github/workflows/verification-runtime.yml",
                ".github/workflows/quality.yml",
                ".github/workflows/backend-verify.yml",
                ".github/workflows/frontend-verify.yml",
            ],
            "functions": [],
            "tests": [
                "python3 .github/scripts/validate_actions.py",
            ],
            "verification": "python runtime/verify.py ci-doctor",
            "expected_result": "All workflows have artifact upload steps and validate successfully",
        },
        {
            "phase": 9,
            "name": "Artifact Organization",
            "clusters": ["CLUSTER-ARTIFACT_ORGANIZATION"],
            "problems": [
                "loan-results.txt exists in 3 locations",
                "mutation-summary.json exists in 3 locations",
                "junit.xml exists in 2 locations",
            ],
            "repair_steps": [
                "1. Consolidate sample artifacts to single canonical location",
                "2. Update sample data references",
                "3. Verify no overwrites occur",
            ],
            "files": [
                "runtime/generated/verification/samples/",
            ],
            "functions": [],
            "tests": [
                "python3 -c 'from pathlib import Path; files=list(Path(\"runtime/generated\").rglob(\"loan-results.txt\")); print(len(files), \"loan-results.txt files\")'",
            ],
            "verification": "python runtime/verify.py audit",
            "expected_result": "No duplicate artifact names in runtime/generated/",
        },
    ]

    lines.append("| Phase | Cluster | Problems | Complexity |")
    lines.append("|-------|---------|----------|------------|")
    for p in phases:
        lines.append(f"| {p['phase']} | {p['name']} | {len(p['problems'])} | varies |")
    lines.append("")

    for p in phases:
        lines.append(f"## Phase {p['phase']}: {p['name']}")
        lines.append("")
        lines.append(f"**Cluster:** {', '.join(p['clusters'])}")
        lines.append("")
        lines.append("### Problems")
        lines.append("")
        for prob in p["problems"]:
            lines.append(f"- {prob}")
        lines.append("")
        lines.append("### Repair Steps")
        lines.append("")
        for step in p["repair_steps"]:
            lines.append(f"- {step}")
        lines.append("")
        lines.append("### Files")
        lines.append("")
        for f in p["files"]:
            lines.append(f"- `{f}`")
        lines.append("")
        if p["functions"]:
            lines.append("### Functions")
            lines.append("")
            for func in p["functions"]:
                lines.append(f"- `{func}`")
            lines.append("")
        lines.append("### Tests")
        lines.append("")
        for t in p["tests"]:
            lines.append(f"```bash\n{t}\n```")
        lines.append("")
        lines.append("### Verification")
        lines.append("")
        lines.append(f"```bash\n{p['verification']}\n```")
        lines.append("")
        lines.append("### Expected Result")
        lines.append("")
        lines.append(p["expected_result"])
        lines.append("")

    lines.append("## Validation Criteria")
    lines.append("")
    lines.append("The platform is certified when:")
    lines.append("")
    lines.append("- [ ] `python runtime/verify.py audit` exits 0 with zero critical and high findings")
    lines.append("- [ ] `python runtime/verify.py graph` exits 0")
    lines.append("- [ ] `python runtime/verify.py knowledge` exits 0")
    lines.append("- [ ] `python runtime/verify.py quick` exits 0")
    lines.append("- [ ] `python runtime/verify.py ci-doctor` exits 0")
    lines.append("- [ ] All GitHub Actions workflows are green")
    lines.append("- [ ] No command hangs or requires manual intervention")
    lines.append("")

    return "\n".join(lines)


def generate_remediation() -> str:
    return _generate_remediation()


def run_remediation() -> str:
    content = _generate_remediation()
    REMEDIATION_PATH.write_text(content, encoding="utf-8")
    return content


if __name__ == "__main__":
    content = run_remediation()
    print(f"Generated remediation plan: {REMEDIATION_PATH}")
    print(f"Length: {len(content)} bytes")
