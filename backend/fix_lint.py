import os
import re


def fix_lint_errors(directory="."):
    total_b904 = 0
    total_e722 = 0

    def b904_replacer(match):
        nonlocal total_b904
        block = match.group(0)

        # If it already has 'from e' or 'from None', skip it
        if re.search(r"\bfrom\s+\w+\s*$", block):
            return block

        # Figure out the exception variable (e.g., 'e' from 'except Exception as e:')
        var_match = re.search(r"except\s+.*?\s+as\s+(\w+):", block)
        var_name = var_match.group(1) if var_match else "None"

        total_b904 += 1
        return block + f" from {var_name}"

    for root, _, files in os.walk(directory):
        if any(ignore in root for ignore in ["venv", ".git", "__pycache__"]):
            continue

        for file in files:
            if not file.endswith(".py"):
                continue

            path = os.path.join(root, file)
            with open(path, encoding="utf-8") as f:
                content = f.read()

            original = content

            # 1. Fix E722: Bare except -> except Exception
            content, e722_count = re.subn(
                r"(\s+)except\s*:", r"\1except Exception:", content
            )
            total_e722 += e722_count

            # 2. Fix B904: Exception chaining (handles both single-line and multi-line raises)
            # This regex captures from `except...:` up to the closing `)` of the `raise` statement.
            pattern = re.compile(
                r"(\bexcept\s+(?:Exception|ImportError|ValueError|ValidationError).*?:\s*\n"
                r"(?:(?!\bexcept\b|\bdef\b|\bclass\b).)*?"
                r"\braise\s+(?:HTTPException|AppError|RuntimeError|AssertionError)\b"
                r"(?:[^)]*?\)))",
                re.DOTALL,
            )
            content = pattern.sub(b904_replacer, content)

            if content != original:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Fixed issues in {path}")

    print(f"\nTotal fixes applied -> B904: {total_b904}, E722: {total_e722}")


if __name__ == "__main__":
    fix_lint_errors()
