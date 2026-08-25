# runtime/generated/m9-c42.21-evidence-capture.py
#
# M9-C42.21 / M21.3-M21.6 — per-engine post-run evidence capture.
#
# After `runtime/verify.py mutation --target <engine>` completes, the mutmut
# cache for that engine still exists (it is wiped only at the START of the next
# campaign run). The [tool.mutmut] config, however, has been restored by the
# runner (R2 semantics). Since `mutmut results`/`mutmut show` resolve the
# population through the ACTIVE config, this helper re-installs the engine's
# canonical config (write_backend_mutmut_config — the exact runner seam) while
# evidence is read, then restores the committed config in `finally`. Same
# provenance principle as the runner's R2 architectural fix, applied externally
# so the certified runner is not modified.
#
# Usage (repo root):
#   .venv/bin/python runtime/generated/m9-c42.21-evidence-capture.py <engine> [--summary-copy]
#
# Outputs:
#   runtime/generated/m9-c42.21/raw/<engine>-results.txt      (mutmut results --all true)
#   runtime/generated/m9-c42.21/survivors/<engine>/*.diff     (mutmut show per survivor/timeout/suspicious)
#   runtime/generated/m9-c42.21/raw/<engine>-status-map.json  (parsed name->status)

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
OUT_DIR = REPO_ROOT / "runtime" / "generated" / "m9-c42.21"
SUMMARY = BACKEND_DIR / "tests" / "generated" / "mutation" / "mutation-summary.json"

sys.path.insert(0, str(REPO_ROOT))

from runtime.foundation.verification.mutation_contract import (  # noqa: E402
    ENGINE_SELECTION,
    write_backend_mutmut_config,
)

_LINE = re.compile(r"^\s*(?P<name>\S+)\s*:\s*(?P<status>.+?)\s*$")
CAPTURE_STATUSES = {"survived", "timeout", "suspicious", "not checked", "no tests"}


def main() -> int:
    engine = sys.argv[1]
    copy_summary = "--summary-copy" in sys.argv
    if engine not in ENGINE_SELECTION:
        print(f"unknown engine: {engine}", file=sys.stderr)
        return 2

    mutmut = str(REPO_ROOT / ".venv/bin/mutmut")
    config_file = BACKEND_DIR / "pyproject.toml"
    original_text: str | None = None

    try:
        original_text = write_backend_mutmut_config(engine, config_file)

        res = subprocess.run(
            [mutmut, "results", "--all", "true"],
            cwd=str(BACKEND_DIR),
            capture_output=True,
            text=True,
            timeout=300,
        )
        raw = res.stdout
        (OUT_DIR / "raw").mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "raw" / f"{engine}-results.txt").write_text(raw)

        status_map: dict[str, str] = {}
        for line in raw.splitlines():
            m = _LINE.match(line)
            if m:
                status_map[m.group("name")] = m.group("status").strip().lower()

        (OUT_DIR / "raw" / f"{engine}-status-map.json").write_text(
            json.dumps(
                {
                    "engine": engine,
                    "captured_at": datetime.now(UTC).isoformat(),
                    "total_mutants": len(status_map),
                    "status_counts": _counts(status_map),
                    "mutants": status_map,
                },
                indent=2,
            )
            + "\n"
        )

        surv_dir = OUT_DIR / "survivors" / engine
        surv_dir.mkdir(parents=True, exist_ok=True)
        capture = [n for n, s in status_map.items() if s in CAPTURE_STATUSES]
        for name in sorted(capture):
            try:
                show = subprocess.run(
                    [mutmut, "show", name],
                    cwd=str(BACKEND_DIR),
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                out = show.stdout or show.stderr
            except Exception as exc:  # pragma: no cover
                out = f"CAPTURE ERROR: {exc}"
            safe = name.replace("/", "__").replace("\\", "__")
            (surv_dir / f"{safe}.diff").write_text(
                f"# status: {status_map[name]}\n{out}"
            )

        if copy_summary and SUMMARY.exists():
            dst = OUT_DIR / "summaries" / f"{engine}-mutation-summary.json"
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SUMMARY, dst)

        print(
            f"{engine}: captured {len(status_map)} mutants, "
            f"{len(capture)} survivor/timeout/suspicious/no-tests diffs "
            f"counts={json.dumps(_counts(status_map))}"
        )
        return 0
    finally:
        if original_text is not None:
            config_file.write_text(original_text)


def _counts(status_map: dict[str, str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for s in status_map.values():
        counts[s] = counts.get(s, 0) + 1
    return dict(sorted(counts.items()))


if __name__ == "__main__":
    raise SystemExit(main())
