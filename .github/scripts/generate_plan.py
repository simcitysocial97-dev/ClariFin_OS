"""Generate verification plan from git diff."""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, ".")

from runtime.foundation.verification.planner.plan_models import (
    VerificationPlan,
)


def get_changed_files():
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
        )
    if result.returncode != 0:
        return []
    return [f.strip() for f in result.stdout.splitlines() if f.strip()]


def main():
    changed_files = os.environ.get("CHANGED_FILES", "")
    if changed_files:
        files = [f.strip() for f in changed_files.splitlines() if f.strip()]
    else:
        files = get_changed_files()

    if not files:
        fallback = os.environ.get("GITHUB_CHANGED_FILES", "")
        if fallback:
            files = [f.strip() for f in fallback.splitlines() if f.strip()]

    plan = VerificationPlan.from_changed_files(files, triggered_by="push")

    output_dir = Path("runtime/generated/verification")
    output_dir.mkdir(parents=True, exist_ok=True)
    plan_path = output_dir / "plan.json"
    with open(plan_path, "w") as f:
        f.write(plan.to_json())

    outputs = plan.to_github_outputs()
    gha_output = os.environ.get("GITHUB_OUTPUT")
    if gha_output:
        with open(gha_output, "a") as f:
            for k, v in outputs.items():
                f.write(f"{k}={v}\n")

    print("Verification plan generated successfully")
    print(f"Plan ID: {plan.plan_id}")
    print(f"Plan written to: {plan_path}")
    print(f"Changed files: {len(plan.changed_files)}")
    print(f"Engines affected: {', '.join(plan.impact.engines) or 'none'}")
    print(f"Unit tests: {'YES' if plan.unit_tests.run else 'no'}")
    print(f"Property tests: {'YES' if plan.property_tests.run else 'no'}")
    print(f"Contract tests: {'YES' if plan.contract_tests.run else 'no'}")
    print(f"Mutation: {'YES' if plan.mutation.run else 'no'}")
    print(f"Integration: {'YES' if plan.integration_tests.run else 'no'}")
    print(f"Golden: {'YES' if plan.golden_tests.run else 'no'}")


if __name__ == "__main__":
    main()
