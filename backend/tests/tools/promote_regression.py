#!/usr/bin/env python3
"""Manual promotion utility for golden regressions.

Usage:
    python backend/tests/tools/promote_regression.py \
        --source path/to/minimized_failing_example.py \
        --name cc_cycle_boundary \
        --description "CC payment near billing cycle boundary misclassified"

Copies the JSON snapshot into backend/tests/golden/regressions/<name>.json.
Does NOT run during pytest.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote a minimized failing example into golden regressions")
    parser.add_argument("--source", required=True, help="Path to source JSON snapshot or dict file")
    parser.add_argument("--name", required=True, help="Dataset name (no .json suffix)")
    parser.add_argument("--description", default="", help="Human-readable description")
    args = parser.parse_args()

    source = Path(args.source)
    if not source.exists():
        print(f"Source not found: {source}")
        return 1

    destination_dir = Path(__file__).parent.parent / "golden" / "regressions"
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"{args.name}.json"

    payload = {
        "name": args.name,
        "description": args.description,
        "promoted_from": str(source),
    }
    if source.suffix == ".json":
        data = json.loads(source.read_text())
    else:
        data = {"raw_source": source.read_text()}
    payload["snapshot"] = data

    destination.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(f"Promoted regression dataset: {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())