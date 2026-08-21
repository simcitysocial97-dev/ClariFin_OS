"""
Dependency Growth Intelligence — Program 7C

Tracks growth over time from cross-layer map.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEPENDENCY_GROWTH_PATH = REPO_ROOT / "runtime" / "generated" / "dependency-growth.json"


@dataclass(slots=True)
class DependencyGrowthRecord:
    """Growth metrics for a single dependency category."""

    category: str
    current_count: int = 0
    previous_count: int = 0
    delta: int = 0
    growth_rate: float = 0.0
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "current_count": self.current_count,
            "previous_count": self.previous_count,
            "delta": self.delta,
            "growth_rate": self.growth_rate,
            "timestamp": self.timestamp,
        }


class DependencyGrowthIntelligence:
    """Analyzes cross-layer dependency growth."""

    def __init__(self, cross_layer_map_path: Path | None = None) -> None:
        # Program 13.3: chains come from the architecture provider. A path may
        # still be injected by isolated tests; it is never the runtime default.
        self._cross_layer_map_path = cross_layer_map_path

    def compute(self) -> dict[str, DependencyGrowthRecord]:
        cross_map = self._load_chains()
        if not cross_map:
            return {}

        growth: dict[str, DependencyGrowthRecord] = {}

        for engine_file, chain in cross_map.items():
            categories = {
                "engines": engine_file.count("/"),
                "services": len(chain.get("services", [])),
                "routers": len(chain.get("routers", [])),
                "endpoints": len(chain.get("endpoints", [])),
                "capability_hooks": len(chain.get("capabilities", [])),
                "components": len(chain.get("components", [])),
                "graph_renderers": len(chain.get("graphRenderers", [])),
            }
            for category, count in categories.items():
                if category not in growth:
                    growth[category] = DependencyGrowthRecord(
                        category=category,
                        current_count=count,
                        previous_count=count,
                        delta=0,
                        growth_rate=0.0,
                    )
                else:
                    growth[category].current_count += count

        return growth

    def _load_chains(self) -> dict[str, Any]:
        if self._cross_layer_map_path is not None:
            if not self._cross_layer_map_path.exists():
                return {}
            try:
                with open(self._cross_layer_map_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {}
        try:
            from runtime.foundation.architecture.chains import get_chain_map

            return get_chain_map()
        except Exception:
            return {}

    def save(self, path: Path | None = None) -> None:
        target = path or DEPENDENCY_GROWTH_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        data = {name: record.to_dict() for name, record in self.compute().items()}
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)


def generate_dependency_growth(
    cross_layer_map_path: Path | None = None,
) -> dict[str, Any]:
    intelligence = DependencyGrowthIntelligence(cross_layer_map_path)
    intelligence.save()
    return {name: record.to_dict() for name, record in intelligence.compute().items()}
