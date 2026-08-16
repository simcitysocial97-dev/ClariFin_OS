"""Run evidence aggregator from CI artifact directory."""
import sys
from pathlib import Path

sys.path.insert(0, ".")

from runtime.system.evidence.aggregator import EvidenceAggregator


def main():
    evidence_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("evidence")

    summary = EvidenceAggregator.from_artifact_directory(evidence_dir)

    output_dir = Path("runtime/generated/evidence")
    output_dir.mkdir(parents=True, exist_ok=True)

    summary.save(output_dir / "summary.json")
    summary.save_markdown(output_dir / "summary.md")

    print("Evidence summary generated")
    print(f"Overall status: {summary.overall_status}")
    if summary.attention_needed:
        print(f"Items needing attention: {len(summary.attention_needed)}")
    else:
        print("No issues found.")


if __name__ == "__main__":
    main()
