# runtime/generated/m9-c42.21-population-probe.py
#
# M9-C42.21 / M21.2 — deterministic mutation POPULATION identification probe.
#
# Uses mutmut 3.7.0's own generation building blocks (the exact code path that
# `mutmut run` executes to generate the population: copy_src_dir →
# copy_also_copy_files → setup_source_paths → store_lines_covered_by_tests →
# create_mutants) WITHOUT running any tests. After generation, the complete
# mutant population is read from mutmut's cache exactly like
# `collect_source_file_mutation_data` (used by `mutmut results`) reads it.
#
# Forensic measurement tooling only — no production code, no gates, no tests.
#
# Usage (repo root, .venv python):
#   .venv/bin/python runtime/generated/m9-c42.21-population-probe.py <engine>
#
# Output: runtime/generated/m9-c42.21/m9-c42.21-population-<engine>.json

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
OUT_DIR = REPO_ROOT / "runtime" / "generated" / "m9-c42.21"

sys.path.insert(0, str(REPO_ROOT))

from runtime.foundation.verification.mutation_contract import (  # noqa: E402
    ENGINE_SELECTION,
    write_backend_mutmut_config,
)


def main() -> int:
    engine = sys.argv[1]
    if engine not in ENGINE_SELECTION:
        print(f"unknown engine: {engine}", file=sys.stderr)
        return 2

    os.environ["MUTANT_UNDER_TEST"] = "mutant_generation"
    os.chdir(BACKEND_DIR)

    config_file = BACKEND_DIR / "pyproject.toml"
    original_text: str | None = None
    try:
        sha_before = hashlib.sha256(config_file.read_bytes()).hexdigest()
        original_text = write_backend_mutmut_config(engine, config_file)

        for stale in (BACKEND_DIR / "mutants", BACKEND_DIR / ".mutmut-cache"):
            if stale.exists():
                shutil.rmtree(stale)

        # mutmut 3.7.0 generation building blocks (same path as `mutmut run`)
        from mutmut.__main__ import (
            Config,
            SourceFileMutationData,
            copy_also_copy_files,
            copy_src_dir,
            create_mutants,
            makedirs,
            setup_source_paths,
            store_lines_covered_by_tests,
            walk_mutatable_files,
        )

        Config.ensure_loaded()
        makedirs(Path("mutants"), exist_ok=True)

        t0 = time.monotonic()
        copy_src_dir()
        copy_also_copy_files()
        setup_source_paths()
        store_lines_covered_by_tests()
        stats = create_mutants(max_children=4)
        gen_seconds = round(time.monotonic() - t0, 2)

        files: dict[str, dict] = {}
        all_names: list[str] = []
        for path in walk_mutatable_files():
            data = SourceFileMutationData(path=path)
            data.load()
            names = sorted(data.exit_code_by_key.keys())
            all_names.extend(names)
            files[str(path)] = {
                "mutants": len(names),
                "functions": sorted(set(n.rpartition("__mutmut_")[0] for n in names)),
                "mutant_names": names,
            }

        all_names_sorted = sorted(all_names)
        fingerprint = hashlib.sha256("\n".join(all_names_sorted).encode()).hexdigest()

        record = {
            "title": f"M9-C42.21 population identity — {engine}",
            "generated_at": datetime.now(UTC).isoformat(),
            "engine": engine,
            "probe": "mutmut 3.7.0 generation building blocks (create_mutants), no tests executed",
            "source_paths": ENGINE_SELECTION[engine].source_paths,
            "test_selection": ENGINE_SELECTION[engine].test_selection,
            "generation_stats": {
                "files_mutated": stats.mutated,
                "files_ignored": stats.ignored,
                "files_unmodified": stats.unmodified,
                "seconds": gen_seconds,
            },
            "population": {
                "mutants_generated": len(all_names_sorted),
                "per_file": {
                    k: {
                        "mutants": v["mutants"],
                        "functions": v["functions"],
                    }
                    for k, v in sorted(files.items())
                },
            },
            "population_fingerprint_sha256": fingerprint,
            "config_sha256_before_run": sha_before,
            "unexecuted_population": True,
        }
        # full name list kept separately (can be large)
        record["population"]["mutant_names"] = all_names_sorted

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out = OUT_DIR / f"m9-c42.21-population-{engine}.json"
        out.write_text(json.dumps(record, indent=2) + "\n")
        print(
            f"{engine}: {len(all_names_sorted)} mutants, {stats.mutated} files mutated, "
            f"fp={fingerprint[:16]} -> {out.name}"
        )
        return 0
    finally:
        if original_text is not None:
            config_file.write_text(original_text)
        sha_after = hashlib.sha256(config_file.read_bytes()).hexdigest()
        if original_text is not None and hashlib.sha256(
            original_text.encode()
        ).hexdigest() != sha_after:
            print(f"CONFIG RESTORE MISMATCH for {engine}", file=sys.stderr)
            return 3
        for stale in (BACKEND_DIR / "mutants", BACKEND_DIR / ".mutmut-cache"):
            if stale.exists():
                shutil.rmtree(stale)


if __name__ == "__main__":
    raise SystemExit(main())
