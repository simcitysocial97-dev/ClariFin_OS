"""Evidence CLI — Command-line interface for evidence collection and verification."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def get_git_info(workspace_root: Path) -> tuple[str, str]:
    """Get current commit SHA and branch name."""
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        sha = os.environ.get("GITHUB_SHA", "unknown")

    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        branch = os.environ.get("GITHUB_REF_NAME", "unknown")

    return sha, branch


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evidence Runtime CLI — Collect and aggregate verification evidence"
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Workspace root directory (default: current directory)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("runtime/generated/evidence/verification-summary.json"),
        help="Output path for verification-summary.json",
    )
    parser.add_argument(
        "--commit",
        type=str,
        help="Git commit SHA (default: auto-detect)",
    )
    parser.add_argument(
        "--branch",
        type=str,
        help="Git branch name (default: auto-detect)",
    )
    parser.add_argument(
        "--status",
        type=str,
        choices=["pass", "fail", "partial"],
        default="partial",
        help="Overall verification status (default: partial)",
    )
    parser.add_argument(
        "--collect-only",
        action="store_true",
        help="Only collect artifacts, don't build verification evidence",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON to stdout instead of writing file",
    )

    args = parser.parse_args()

    # Ensure repo root in sys.path for imports
    repo_root = args.workspace
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    # Import after path setup
    from runtime.system.evidence.api import (
        collect_all_evidence,
        build_verification_evidence,
        write_verification_summary,
    )

    # Get git info
    commit_sha = args.commit
    branch = args.branch
    if not commit_sha or not branch:
        detected_sha, detected_branch = get_git_info(repo_root)
        commit_sha = commit_sha or detected_sha
        branch = branch or detected_branch

    # Collect evidence
    print(f"Collecting evidence from {repo_root}...")
    collection_result = collect_all_evidence(repo_root)

    if args.collect_only:
        if args.json:
            print(collection_result.to_json())
        else:
            output_path = args.output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(collection_result.to_json())
            print(f"Evidence collection written to {output_path}")
        return 0

    # Build verification evidence
    print("Building verification evidence...")
    evidence = build_verification_evidence(
        commit_sha=commit_sha,
        branch=branch,
        artifacts=collection_result.artifacts,
        status=args.status,
    )

    if args.json:
        print(evidence.to_json())
    else:
        output_path = args.output
        write_verification_summary(evidence, output_path)
        print(f"Verification summary written to {output_path}")

    # Print summary
    print("\nVerification Summary:")
    print("  Commit: {}".format(commit_sha[:8]))
    print("  Branch: {}".format(branch))
    print("  Status: {}".format(evidence.status))
    if evidence.coverage:
        print(f"  Coverage: {evidence.coverage.percentage:.1f}%")
    if evidence.mutation:
        print(f"  Mutation Score: {evidence.mutation.score:.1f}%")

    return 0


if __name__ == "__main__":
    sys.exit(main())
