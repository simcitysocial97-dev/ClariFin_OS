import os
import sys

workflows = [
    ".github/workflows/quality.yml",
    ".github/workflows/backend.yml",
    ".github/workflows/mutation.yml",
    ".github/workflows/golden.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/frontend-build.yml",
    ".github/workflows/frontend.yml",
    ".github/workflows/full-validation.yml",
    ".github/workflows/nightly-property-tests.yml",
    ".github/workflows/playwright.yml",
]

problems = []

for wf in workflows:
    with open(wf) as f:
        content = f.read()
    lines = content.splitlines()
    for i, line in enumerate(lines, 1):
        import re

        matches = re.findall(r"backend/[\w/._-]+", line)
        for match in matches:
            path = match.replace('"', "").replace('"', "")
            if "." in path or "$" in path:
                continue
            if "." in os.path.basename(path) or path.endswith("/"):
                if not os.path.exists(path):
                    problems.append(f"{wf}:{i}: {path} does not exist")

if problems:
    print("PATH PROBLEMS:")
    for p in problems:
        print(f"  {p}")
    sys.exit(1)
else:
    print("All referenced paths exist")
