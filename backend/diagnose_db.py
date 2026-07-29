import os
from pathlib import Path

print("--- SEARCHING FOR DIRECT DATABASE PATH INITIALIZATIONS ---")
search_paths = ["src"]
keywords = ["sqlite3.connect", "FinanceDB(", "database.db", "finance.db", "db_path"]

for path_str in search_paths:
    base_path = Path(path_str)
    for file_path in base_path.rglob("*.py"):
        try:
            content = file_path.read_text(encoding="utf-8")
            for line_num, line in enumerate(content.splitlines(), 1):
                if any(kw in line for kw in keywords):
                    print(f"{file_path}:{line_num} -> {line.strip()}")
        except Exception as e:
            pass
