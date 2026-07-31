"""Metadata scanner — loads existing generated artifacts as canonical sources.

Reads (does NOT duplicate):
- ``backend/tests/generated/capability-registry.yaml`` — canonical capability registry
- ``backend/tests/generated/dependency-map.json`` — generated dependency graph
- ``backend/tests/generated/verification-matrix.json`` — verification matrix
- ``backend/tests/generated/mutation-registry.json`` — mutation targets
- ``backend/tests/generated/risk-map.json`` — risk classifications
- ``backend/tests/generated/verification-summary.json`` — combined verification summary
- ``backend/tests/generated/architectural-coverage.json`` — architectural coverage
- ``backend/tests/generated/verification-evidence.json`` — verification evidence
- ``backend/requirements.txt`` and ``backend/requirements-frozen.txt`` — dependencies
- ``frontend/package.json`` — frontend dependencies

Creates nodes for capabilities and generated artifacts, plus edges from
capabilities to their components (engines, services, routers, repositories,
tables) — using the registry as the canonical source.
"""

from __future__ import annotations


from runtime.foundation.repository.scanner.base import BaseScanner, ScanResult


class MetadataScanner(BaseScanner):
    """Load existing generated artifacts and create capability nodes + edges."""

    def scan(self) -> ScanResult:
        result = ScanResult()

        self._scan_capability_registry(result)
        self._scan_generated_artifacts(result)
        self._scan_dependency_graph(result)
        self._scan_requirements(result)
        self._scan_package_json(result)

        return result

    def _scan_capability_registry(self, result: ScanResult) -> None:
        """Load capability-registry.yaml and create capability nodes + edges."""
        registry = self.safe_read_yaml(
            self.generated_dir / "capability-registry.yaml"
        )
        if registry is None:
            return

        # Mark the registry file itself as a generated artifact node
        result.add_node(
            node_type="generated_artifact",
            name="capability-registry.yaml",
            path="backend/tests/generated/capability-registry.yaml",
            source="generated:capability-registry",
            properties={
                "capability_count": len(registry.get("capabilities", [])),
            },
        )

        for cap in registry.get("capabilities", []):
            cap_id = cap.get("id", "")
            if not cap_id:
                continue

            cap_node_id = f"capability:{cap_id}"
            result.add_node(
                node_type="capability",
                name=cap.get("name", cap_id),
                path="backend/tests/generated/capability-registry.yaml",
                source="generated:capability-registry",
                node_id=cap_node_id,
                properties={
                    "id": cap_id,
                    "description": cap.get("description", ""),
                    "criticality": cap.get("criticality", "unknown"),
                    "risk": cap.get("risk", "unknown"),
                    "failure_impact": cap.get("failure_impact", ""),
                    "dependencies": cap.get("dependencies", []),
                },
            )

            # Edges: capability implements/owns components
            for engine in cap.get("engines", []):
                result.add_edge(
                    source_id=cap_node_id,
                    target_id=f"module:{engine}",
                    relationship="implements",
                    confidence=1.0,
                    evidence="capability_registry.engines",
                )

            for service in cap.get("services", []):
                result.add_edge(
                    source_id=cap_node_id,
                    target_id=f"module:{service}",
                    relationship="implements",
                    confidence=1.0,
                    evidence="capability_registry.services",
                )

            for router in cap.get("routers", []):
                result.add_edge(
                    source_id=cap_node_id,
                    target_id=f"module:{router}",
                    relationship="implements",
                    confidence=1.0,
                    evidence="capability_registry.routers",
                )

            for repo in cap.get("repositories", []):
                result.add_edge(
                    source_id=cap_node_id,
                    target_id=f"module:{repo}",
                    relationship="implements",
                    confidence=1.0,
                    evidence="capability_registry.repositories",
                )

            # Database tables
            for table in cap.get("tables", []):
                result.add_node(
                    node_type="database_table",
                    name=table,
                    path="backend/src/db.py",
                    source="generated:capability-registry",
                    node_id=f"database_table:{table}",
                    properties={
                        "capability": cap_id,
                    },
                )
                result.add_edge(
                    source_id=cap_node_id,
                    target_id=f"database_table:{table}",
                    relationship="owns",
                    confidence=0.9,
                    evidence="capability_registry.tables",
                )

            # Capability dependencies
            for dep in cap.get("dependencies", []):
                result.add_edge(
                    source_id=cap_node_id,
                    target_id=f"capability:{dep}",
                    relationship="depends_on",
                    confidence=0.9,
                    evidence="capability_registry.dependencies",
                )

    def _scan_generated_artifacts(self, result: ScanResult) -> None:
        """Create nodes for all generated artifacts in backend/tests/generated/."""
        if not self.generated_dir.exists():
            return

        for artifact_file in sorted(self.generated_dir.iterdir()):
            if not artifact_file.is_file():
                continue
            if artifact_file.suffix not in (".json", ".yaml", ".yml"):
                continue

            rel = self.rel_path(artifact_file, self.backend_dir)
            result.add_node(
                node_type="generated_artifact",
                name=artifact_file.name,
                path=rel,
                source="filesystem:backend/tests/generated",
                properties={
                    "size_bytes": artifact_file.stat().st_size,
                },
            )

    def _scan_dependency_graph(self, result: ScanResult) -> None:
        """Load dependency-map.json and create edges from the generated graph."""
        dep_map = self.safe_read_json(self.generated_dir / "dependency-map.json")
        if dep_map is None:
            return

        result.add_node(
            node_type="generated_artifact",
            name="dependency-map.json",
            path="backend/tests/generated/dependency-map.json",
            source="generated:dependency-map",
            properties={
                "generated_at": dep_map.get("generated_at", ""),
                "edge_count": len(dep_map.get("edges", [])),
            },
        )

        for edge in dep_map.get("edges", []):
            source_id = f"{edge.get('source_type', 'module')}:{edge.get('source', '')}"
            target_id = f"{edge.get('target_type', 'module')}:{edge.get('target', '')}"
            result.add_edge(
                source_id=source_id,
                target_id=target_id,
                relationship=edge.get("relationship", "depends_on"),
                confidence=edge.get("confidence", 0.5),
                evidence=edge.get("evidence", "dependency_map"),
            )

    def _scan_requirements(self, result: ScanResult) -> None:
        """Load backend requirements files."""
        for req_file in ("requirements.txt", "requirements-frozen.txt"):
            req_path = self.backend_dir / req_file
            if not req_path.exists():
                continue

            content = self.safe_read(req_path)
            if content is None:
                continue

            rel = self.rel_path(req_path, self.repo_root)
            deps = [
                line.strip()
                for line in content.splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
            result.add_node(
                node_type="requirements",
                name=req_file,
                path=rel,
                source="filesystem:backend",
                properties={
                    "dependencies": deps,
                    "dependency_count": len(deps),
                },
            )

    def _scan_package_json(self, result: ScanResult) -> None:
        """Load frontend package.json for dependency metadata."""
        pkg = self.safe_read_json(self.frontend_dir / "package.json")
        if pkg is None:
            return

        rel = "frontend/package.json"
        deps = {
            **pkg.get("dependencies", {}),
            **pkg.get("devDependencies", {}),
        }
        result.add_node(
            node_type="package_json",
            name="package.json",
            path=rel,
            source="filesystem:frontend",
            properties={
                "name": pkg.get("name", ""),
                "version": pkg.get("version", ""),
                "scripts": pkg.get("scripts", {}),
                "dependency_count": len(deps),
            },
        )
