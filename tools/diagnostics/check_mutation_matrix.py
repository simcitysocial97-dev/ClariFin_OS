import os
import sys

import yaml

# Read mutation workflow
with open(".github/workflows/mutation.yml") as f:
    mutation = yaml.safe_load(f)

# Extract engine matrix
jobs = mutation.get("jobs", {})
matrix_engines = []
for job_name, job in jobs.items():
    strategy = job.get("strategy", {})
    matrix = strategy.get("matrix", {})
    engines = matrix.get("engine", [])
    matrix_engines.extend(engines)

print(f"Engines in matrix: {sorted(matrix_engines)}")

# Find actual engine files in src/engines/
actual_engines = []
engine_dir = os.path.join("backend", "src", "engines")
for f in os.listdir(engine_dir):
    if f.endswith("_engine.py") and not f.startswith("test_"):
        name = f.replace("_engine.py", "")
        actual_engines.append(name)

print(f"Actual engines: {sorted(actual_engines)}")

missing_from_matrix = set(actual_engines) - set(matrix_engines)
extra_in_matrix = set(matrix_engines) - set(actual_engines)

if missing_from_matrix:
    print(f"MISSING from matrix: {missing_from_matrix}")
if extra_in_matrix:
    print(f"EXTRA in matrix (no file): {extra_in_matrix}")

if missing_from_matrix or extra_in_matrix:
    sys.exit(1)
else:
    print("Matrix matches actual engines")
