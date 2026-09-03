# runtime/foundation/verification/mutation_execution/cache_report.py
#
# M44.12 — Cache Architecture Report.

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "runtime" / "generated" / "m9-c44"


def build_cache_report() -> dict:
    return {
        "schema": "m9-c44-cache-report/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "cache_location": str((REPO_ROOT / "runtime" / "generated" / "m9-c44" / "cache").relative_to(REPO_ROOT)),
        "cache_key_schema": "canonical_mutant_id (sha256 of revision|file|hash|function|line|operator|orig|mut[:20]))",
        "cache_entry_fields": [
            "canonical_mutant_id",
            "source_file",
            "source_hash",
            "configuration_fingerprint",
            "result_state",
            "execution",
            "discovered_at",
            "last_verified_at",
            "verified",
            "invalidation_reason",
        ],
        "invalidation_rules": {
            "source_changes": "invalidate_all(reason='source_changed') — source hash no longer matches",
            "test_changes": "invalidate_all(reason='test_changed') — test selection fingerprint changed",
            "test_config_changes": "invalidate_all(reason='test_config_changed') — pytest configuration altered",
            "dependency_changes": "invalidate_all(reason='dependency_changed') — pyproject.toml dependencies modified",
            "backend_changes": "invalidate_all(reason='backend_changed') — mutation backend or version changed",
            "policy_changes": "invalidate_all(reason='policy_changed') — timeout/workers/operators changed",
            "timeout_changes": "invalidate_all(reason='timeout_changed') — timeout policy altered",
            "profile_changes": "invalidate_all(reason='profile_changed') — verification profile changed",
            "environment_changes": "invalidate_all(reason='environment_changed') — Python/platform changed",
        },
        "stale_cache_policy": "INVALIDATED rather than silently reused",
        "relationship_to_mutmut_cache": (
            "mutmut's .mutmut-cache is NEVER the source of truth. "
            "It may be used as a discovery hint only. "
            "The canonical cache (this module) is authoritative."
        ),
        "cache_operations": [
            "get(mutant_id, config_fp, source_hash) -> CacheEntry | None",
            "put(candidate, config_fp, result_state, execution, verified) -> None",
            "invalidate(mutant_id, reason) -> None",
            "invalidate_all(reason) -> int",
            "invalidate_by_source(source_file, reason) -> int",
            "clear() -> None",
            "stats() -> dict",
            "get_or_skip(candidate, config_fp, placeholder_state) -> (was_cached, entry)",
        ],
    }


if __name__ == "__main__":
    p = OUTPUT_DIR / "mutation-cache-report.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    report = build_cache_report()
    p.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Cache report: {p}")
