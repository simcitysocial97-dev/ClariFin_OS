from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from runtime.foundation.audit.models import (
    AuditFinding,
    AuditPriority,
    AuditSeverity,
    AuditStatus,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _f(
    check_id: str,
    name: str,
    status: str,
    severity: str,
    priority: str,
    message: str,
    details: dict[str, Any] = None,
    recommendation: str = "",
) -> AuditFinding:
    return AuditFinding(
        section="knowledge",
        check_id=check_id,
        name=name,
        status=AuditStatus(status),
        severity=AuditSeverity(severity),
        priority=AuditPriority(priority),
        message=message,
        details=details or {},
        recommendation=recommendation,
    )


def audit(repo_root: Path | None = None) -> dict[str, Any]:
    start = time.monotonic()
    repo_root = repo_root or REPO_ROOT
    findings: list[AuditFinding] = []
    metrics: dict[str, Any] = {}

    knowledge_index_path = repo_root / "runtime" / "generated" / "knowledge-index.json"

    if not knowledge_index_path.exists():
        findings.append(
            _f(
                "knowledge-index-exists",
                "Knowledge index file exists",
                "fail",
                "critical",
                "critical",
                f"Knowledge index file not found at {knowledge_index_path}",
                {"path": str(knowledge_index_path)},
                "Run the knowledge indexer to generate the index file",
            )
        )
        all_pass = all(f.status == AuditStatus.PASS for f in findings)
        overall = AuditStatus.PASS if all_pass else AuditStatus.FAIL
        duration = time.monotonic() - start
        return {
            "section": "knowledge",
            "name": "Knowledge Base Audit",
            "status": overall,
            "findings": findings,
            "metrics": metrics,
            "duration_seconds": round(duration, 4),
        }

    try:
        with open(knowledge_index_path, encoding="utf-8") as f:
            index_data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        findings.append(
            _f(
                "knowledge-index-parse",
                "Knowledge index file is valid JSON",
                "fail",
                "critical",
                "critical",
                f"Failed to parse knowledge index: {exc}",
                {"path": str(knowledge_index_path)},
                "Fix the knowledge index file to be valid JSON",
            )
        )
        all_pass = all(f.status == AuditStatus.PASS for f in findings)
        overall = AuditStatus.PASS if all_pass else AuditStatus.FAIL
        duration = time.monotonic() - start
        return {
            "section": "knowledge",
            "name": "Knowledge Base Audit",
            "status": overall,
            "findings": findings,
            "metrics": metrics,
            "duration_seconds": round(duration, 4),
        }

    categories = index_data.get("categories", {})
    counts = index_data.get("counts", {})

    object_type_labels = {
        "endpoints": "Endpoints",
        "capabilities": "Capabilities",
        "workspaces": "Workspaces",
        "integrity_rules": "Rules",
        "documentation": "Documentation",
        "runtime_artifacts": "Artifacts",
    }

    for obj_key, label in object_type_labels.items():
        if obj_key in categories:
            entries = categories[obj_key]
            if len(entries) > 0:
                findings.append(
                    _f(
                        f"indexed-{obj_key}",
                        f"{label} are indexed",
                        "pass",
                        "info",
                        "low",
                        f"{label} category has {len(entries)} entries in the knowledge index",
                        {"count": len(entries), "category": obj_key},
                    )
                )
            else:
                findings.append(
                    _f(
                        f"indexed-{obj_key}",
                        f"{label} are indexed",
                        "fail",
                        "high",
                        "high",
                        f"{label} category has no entries in the knowledge index",
                        {"category": obj_key},
                        f"Add {label.lower()} to the knowledge index",
                    )
                )
        else:
            findings.append(
                _f(
                    f"indexed-{obj_key}",
                    f"{label} are indexed",
                    "fail",
                    "high",
                    "high",
                    f"{label} category is missing from the knowledge index",
                    {"category": obj_key},
                    f"Add {label.lower()} category to the knowledge index",
                )
            )

    references_found = False
    for obj_key, entries in categories.items():
        for entry in entries:
            if isinstance(entry, dict) and "references" in entry:
                refs = entry["references"]
                if isinstance(refs, dict) and len(refs) > 0:
                    references_found = True
                    break
        if references_found:
            break

    if references_found:
        findings.append(
            _f(
                "indexed-references",
                "References are indexed",
                "pass",
                "info",
                "low",
                "Knowledge index contains reference links within entries",
                {"references_present": True},
            )
        )
    else:
        findings.append(
            _f(
                "indexed-references",
                "References are indexed",
                "fail",
                "high",
                "high",
                "Knowledge index does not contain reference links",
                {},
                "Ensure entries include references to related entities",
            )
        )

    broken_links = 0
    for obj_key, entries in categories.items():
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if obj_key == "documentation":
                doc_path = entry.get("path", "")
                if doc_path:
                    full_path = repo_root / doc_path
                    if not full_path.exists():
                        broken_links += 1
            elif obj_key == "runtime_artifacts":
                artifact_path = entry.get("path", "")
                if artifact_path:
                    full_path = repo_root / artifact_path
                    if not full_path.exists():
                        broken_links += 1
            if obj_key in ("documentation", "runtime_artifacts"):
                refs = entry.get("references", {})
                if isinstance(refs, dict):
                    for ref_key, ref_value in refs.items():
                        if ref_key == "source_file" and isinstance(ref_value, str):
                            full_path = repo_root / ref_value
                            if not full_path.exists():
                                broken_links += 1

    if broken_links == 0:
        findings.append(
            _f(
                "broken-links",
                "No broken links found",
                "pass",
                "info",
                "low",
                "All reference links in the knowledge index point to existing files",
                {"broken_links": 0},
            )
        )
    else:
        findings.append(
            _f(
                "broken-links",
                "No broken links found",
                "fail",
                "high",
                "high",
                f"Found {broken_links} broken links in the knowledge index",
                {"broken_links": broken_links},
                "Fix or remove references to non-existent files",
            )
        )

    duplicates_found = 0
    seen_paths: dict[str, list[str]] = {}
    seen_names: dict[str, list[str]] = {}
    for obj_key, entries in categories.items():
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if obj_key == "endpoints":
                path = entry.get("path", "")
                method = entry.get("method", "")
                identifier = f"{method} {path}"
                seen_paths.setdefault(identifier, []).append(obj_key)
            elif obj_key in (
                "capabilities",
                "workspaces",
                "mappers",
                "view_models",
                "components",
            ):
                name = entry.get("name", "")
                seen_names.setdefault(name, []).append(obj_key)
            elif obj_key == "integrity_rules":
                rule_id = entry.get("rule_id", "")
                seen_names.setdefault(rule_id, []).append(obj_key)
            elif obj_key == "runtime_artifacts":
                path = entry.get("path", "")
                seen_paths.setdefault(path, []).append(obj_key)
            elif obj_key == "documentation":
                doc_path = entry.get("path", "")
                seen_paths.setdefault(doc_path, []).append(obj_key)

    for identifier, keys in seen_paths.items():
        if len(keys) > 1:
            duplicates_found += 1
    for name, keys in seen_names.items():
        if len(keys) > 1:
            duplicates_found += 1

    if duplicates_found == 0:
        findings.append(
            _f(
                "duplicates",
                "No duplicate entries found",
                "pass",
                "info",
                "low",
                "No duplicate entries found in the knowledge index",
                {"duplicates": 0},
            )
        )
    else:
        findings.append(
            _f(
                "duplicates",
                "No duplicate entries found",
                "fail",
                "high",
                "high",
                f"Found {duplicates_found} duplicate entries in the knowledge index",
                {"duplicates": duplicates_found},
                "Remove or merge duplicate entries in the knowledge index",
            )
        )

    from runtime.foundation.knowledge.indexer import build_index
    from runtime.foundation.knowledge.query import KnowledgeQueryEngine

    rebuilt_index = build_index()
    rebuilt_counts = {
        "endpoints": len(rebuilt_index.endpoints),
        "capabilities": len(rebuilt_index.capabilities),
        "workspaces": len(rebuilt_index.workspaces),
        "integrity_rules": len(rebuilt_index.integrity_rules),
        "documentation": len(rebuilt_index.documentation),
        "runtime_artifacts": len(rebuilt_index.runtime_artifacts),
    }

    indexer_consistent = True
    for obj_key, expected_count in rebuilt_counts.items():
        saved_count = counts.get(obj_key, 0)
        if saved_count != expected_count:
            indexer_consistent = False
            findings.append(
                _f(
                    f"indexer-consistency-{obj_key}",
                    f"Indexer consistency for {obj_key}",
                    "fail",
                    "high",
                    "high",
                    f"Indexer count mismatch for {obj_key}: saved={saved_count}, rebuilt={expected_count}",
                    {"saved": saved_count, "rebuilt": expected_count},
                    "Rebuild the knowledge index to ensure consistency",
                )
            )

    if indexer_consistent:
        findings.append(
            _f(
                "indexer-consistency",
                "Indexer consistency verified",
                "pass",
                "info",
                "low",
                "Knowledge indexer rebuild produces consistent counts with saved index",
                {"counts_match": True},
            )
        )

    query_engine = KnowledgeQueryEngine()
    query_results = query_engine.query_all()
    if len(query_results) > 0:
        findings.append(
            _f(
                "query-engine-works",
                "Knowledge query engine works",
                "pass",
                "info",
                "low",
                f"KnowledgeQueryEngine.query_all() returned {len(query_results)} results",
                {"query_result_count": len(query_results)},
            )
        )
    else:
        findings.append(
            _f(
                "query-engine-works",
                "Knowledge query engine works",
                "fail",
                "high",
                "high",
                "KnowledgeQueryEngine.query_all() returned no results",
                {},
                "Verify the knowledge catalog is properly initialized",
            )
        )

    total_indexed = sum(counts.values())
    metrics["total_indexed_objects"] = total_indexed
    metrics["endpoints_count"] = counts.get("endpoints", 0)
    metrics["capabilities_count"] = counts.get("capabilities", 0)
    metrics["workspaces_count"] = counts.get("workspaces", 0)
    metrics["rules_count"] = counts.get("integrity_rules", 0)
    metrics["documentation_count"] = counts.get("documentation", 0)
    metrics["artifacts_count"] = counts.get("runtime_artifacts", 0)
    metrics["references_present"] = references_found
    metrics["broken_links"] = broken_links
    metrics["duplicates"] = duplicates_found
    metrics["indexer_consistent"] = indexer_consistent
    metrics["query_results_count"] = len(query_results)

    all_pass = all(f.status == AuditStatus.PASS for f in findings)
    overall = AuditStatus.PASS if all_pass else AuditStatus.FAIL

    duration = time.monotonic() - start

    return {
        "section": "knowledge",
        "name": "Knowledge Base Audit",
        "status": overall,
        "findings": findings,
        "metrics": metrics,
        "duration_seconds": round(duration, 4),
    }
