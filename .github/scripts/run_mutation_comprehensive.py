#!/usr/bin/env python3
"""
Comprehensive Mutation Test Runner
Generates detailed debug output and always produces summary artifacts.
"""

import subprocess
import sys
import json
import os
from pathlib import Path
from datetime import datetime, timezone

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent / "backend"
MUTATION_OUTPUT_DIR = BACKEND_DIR / "tests" / "generated" / "mutation"
MUTATION_SUMMARY = MUTATION_OUTPUT_DIR / "mutation-summary.json"


def run_mutmut() -> tuple[int, str]:
    """Run mutmut and return (exit_code, output)."""
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    try:
        result = subprocess.run(
            ["python3", "-m", "mutmut", "run"],
            cwd=str(BACKEND_DIR),
            capture_output=True,
            text=True,
            env=env,
            timeout=5400,  # 90 minutes
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 1, "TIMEOUT: Mutation run exceeded 90 minutes"
    except Exception as e:
        return 1, f"ERROR: {e}"


def parse_mutmut_output(output: str) -> dict:
    """Parse mutmut output to extract statistics."""
    stats = {
        "killed": 0,
        "survived": 0,
        "timeout": 0,
        "not_checked": 0,
        "no_tests": 0,
        "total": 0,
    }
    
    for line in output.split('\n'):
        if '🎉' in line and '/' in line:
            # Parse line like: ⠇ 16210/16427  🎉 4418 🫥 7439  ⏰ 38  🤔 0  🙁 4218
            parts = line.split()
            for part in parts:
                if part == '🎉':
                    idx = parts.index(part)
                    if idx + 1 < len(parts):
                        try:
                            stats['killed'] = int(parts[idx + 1])
                        except Exception:
                            pass
                elif part == '🫥':
                    idx = parts.index(part)
                    if idx + 1 < len(parts):
                        try:
                            stats['survived'] = int(parts[idx + 1])
                        except Exception:
                            pass
                elif part == '⏰':
                    idx = parts.index(part)
                    if idx + 1 < len(parts):
                        try:
                            stats['timeout'] = int(parts[idx + 1])
                        except Exception:
                            pass
                elif part == '🤔':
                    idx = parts.index(part)
                    if idx + 1 < len(parts):
                        try:
                            stats['not_checked'] = int(parts[idx + 1])
                        except Exception:
                            pass
                elif part == '🙁':
                    idx = parts.index(part)
                    if idx + 1 < len(parts):
                        try:
                            stats['no_tests'] = int(parts[idx + 1])
                        except Exception:
                            pass
    
    # Calculate total from components
    stats['total'] = stats['killed'] + stats['survived'] + stats['timeout'] + stats['not_checked'] + stats['no_tests']
    
    return stats


def main() -> int:
    """Main entry point."""
    print("=" * 70)
    print("ClariFin OS — Comprehensive Mutation Testing")
    print("=" * 70)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    # Ensure output directory exists
    MUTATION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Run mutmut
    print("Starting mutation test run...")
    exit_code, output = run_mutmut()
    
    # Save full output
    log_file = MUTATION_OUTPUT_DIR / "mutation-run.log"
    log_file.write_text(output)
    print(f"Full log saved to: {log_file}")
    print()
    
    # Parse results
    stats = parse_mutmut_output(output)
    
    # Calculate score
    testable = stats['killed'] + stats['survived']
    score = (stats['killed'] / testable * 100) if testable > 0 else 0
    
    # Generate summary
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mutmut_exit_code": exit_code,
        "killed": stats['killed'],
        "survived": stats['survived'],
        "timeout": stats['timeout'],
        "not_checked": stats['not_checked'],
        "no_tests": stats['no_tests'],
        "total_mutants": stats['total'],
        "testable_mutants": testable,
        "score_percent": round(score, 1),
        "threshold_percent": 80,
        "threshold_met": score >= 80,
        "status": "success" if exit_code == 0 else ("mutation_failure" if exit_code == 2 else "infrastructure_failure"),
        "error_message": output[-2000:] if len(output) > 2000 else output,  # Last 2000 chars for debugging
    }
    
    # Save summary
    with open(MUTATION_SUMMARY, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Summary saved to: {MUTATION_SUMMARY}")
    print()
    
    # Print results
    print("=" * 70)
    print("MUTATION RESULTS")
    print("=" * 70)
    print(f"  Killed      : {stats['killed']}")
    print(f"  Survived    : {stats['survived']}")
    print(f"  Timeout     : {stats['timeout']}")
    print(f"  No Tests    : {stats['no_tests']}")
    print(f"  Total       : {stats['total']}")
    print(f"  Score       : {score:.1f}%")
    print(f"  Threshold   : 80%")
    print(f"  Met         : {'YES' if score >= 80 else 'NO'}")
    print(f"  Exit Code   : {exit_code}")
    print()
    
    # Print error details if any
    if exit_code != 0:
        print("=" * 70)
        print("ERROR DETAILS (last 50 lines of output)")
        print("=" * 70)
        lines = output.strip().split('\n')
        for line in lines[-50:]:
            print(line)
        print()
    
    # Return appropriate exit code
    if exit_code == 0 and score >= 80:
        return 0
    elif exit_code == 2:
        return 2  # Mutation failure
    else:
        return 1  # Infrastructure failure


if __name__ == "__main__":
    sys.exit(main())
