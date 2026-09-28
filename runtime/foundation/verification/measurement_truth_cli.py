# runtime/foundation/verification/measurement_truth_cli.py
#
# M9-C47 Phase 6 — canonical command surface for measurement truth.
#
# `verify.py measurement-truth <record.json> [--json]` answers, explicitly:
#   1. what was requested;
#   2. what actually ran;
#   3. what evidence was produced;
#   4. whether the evidence is authoritative;
#   5. whether certification may consume it;
#   6. what should be run next.
#
# This is ONE canonical read path for coverage and mutation measurement
# truth — existing commands are reused (coverage/mutation measurement emit the
# same record shape via measurement_truth.py).

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from runtime.foundation.verification.measurement_truth import (
    MeasurementTruthRecord,
    classify_completion,
    load_measurement_truth,
    operator_report,
)


def _render_text(report: dict, record: MeasurementTruthRecord) -> str:
    return (
        "=== M9-C47 MEASUREMENT TRUTH ===\n"
        f"RUN_ID           : {record.run_id}\n"
        f"MEASUREMENT_KIND : {record.measurement_kind}\n"
        f"REPO_SHA         : {record.repository_sha}\n"
        "\n"
        "1. WHAT WAS REQUESTED\n"
        f"   command         : {report['requested']['command']}\n"
        f"   requested scope : {report['requested']['requested_scope']}\n"
        f"   mode            : {report['requested']['mode']}\n"
        "\n"
        "2. WHAT ACTUALLY RAN\n"
        f"   actual scope    : {report['actually_ran']['actual_scope']}\n"
        f"   execution status: {report['actually_ran']['execution_status']}\n"
        f"   completion      : {report['actually_ran']['completion_status']}\n"
        f"   failure         : {report['actually_ran']['failure_classification']}\n"
        f"   duration (s)    : {report['actually_ran']['duration_seconds']}\n"
        "\n"
        "3. EVIDENCE PRODUCED\n"
        f"   artifacts       : {', '.join(report['evidence_produced']['artifact_paths']) or '(none)'}\n"
        f"   evidence fp     : {report['evidence_produced']['evidence_fingerprint']}\n"
        f"   survivor evidence: {', '.join(report['evidence_produced']['durable_survivor_evidence']) or '(none)'}\n"
        "\n"
        f"4. AUTHORITATIVE   : {report['is_authoritative']}\n"
        f"5. CERTIFIABLE     : {report['may_certification_consume']}\n"
        f"6. RUN NEXT        : {report['run_next']}\n"
    )


def run_measurement_truth_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="verify.py measurement-truth")
    parser.add_argument("record", help="path to a measurement-truth JSON record")
    parser.add_argument("--json", action="store_true", help="emit machine JSON only")
    args = parser.parse_args(argv)

    path = Path(args.record)
    if not path.is_file():
        print(
            f"record not found: {path} — no measurement truth available",
            file=sys.stderr,
        )
        return 2

    try:
        record = load_measurement_truth(path)
    except Exception as exc:
        print(f"invalid measurement-truth record: {exc}", file=sys.stderr)
        return 2

    report = operator_report(record)
    # Recompute and surface the authoritative completion in the record context.
    record_final_status = classify_completion(record=record)
    report["mutation_score"] = record.mutation_score
    report["coverage_percent"] = record.coverage_result_percent
    report["population"] = record.population.as_dict()
    report["recomputed_completion"] = record_final_status

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(_render_text(report, record))

    certifiable = report["may_certification_consume"]
    return 0 if certifiable else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(run_measurement_truth_cli())
