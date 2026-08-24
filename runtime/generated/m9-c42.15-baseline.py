#!/usr/bin/env python3
"""M9-C42.15 Phase 0 — Forensic Baseline for External State"""

import os
import subprocess
import sys
import json
import locale
import time
from pathlib import Path

REPO_ROOT = Path('/home/vasantha/AI-Projects/ClariFin_OS')

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_git_fetch_failure():
    """Test 1: Git fetch failure semantics - current behavior"""
    print_header("Test 1: Git fetch failure (F26)")
    
    # Test _merge_base_with_default with network failure simulation
    import sys
    sys.path.insert(0, str(REPO_ROOT))
    from runtime.foundation.verification.orchestrator import _merge_base_with_default
    
    print("Calling _merge_base_with_default()...")
    result = _merge_base_with_default()
    print(f"Result: {result}")
    
    # Check if git fetch failure was silently ignored
    # The current code at orchestrator.py:107-116 silently ignores fetch failures
    print("NOTE: Current code silently ignores git fetch failures (orchestrator.py:114-116)")

def test_locale_tz():
    """Test 2: Locale and TZ determinism (ED7)"""
    print_header("Test 2: Locale/TZ determinism (ED7)")
    
    print(f"locale.getdefaultlocale(): {locale.getdefaultlocale()}")
    print(f"locale.getlocale(): {locale.getlocale()}")
    print(f"os.environ.get('TZ'): {os.environ.get('TZ')}")
    print(f"os.environ.get('LC_ALL'): {os.environ.get('LC_ALL')}")
    print(f"os.environ.get('LANG'): {os.environ.get('LANG')}")
    
    # Test datetime behavior
    import datetime
    dt = datetime.datetime.now()
    print(f"datetime.now(): {dt}")
    print(f"datetime.now().astimezone(): {dt.astimezone()}")
    
    # Test locale-sensitive formatting
    try:
        import locale as loc
        loc.setlocale(loc.LC_TIME, 'C')
        formatted = dt.strftime('%a %b %d %H:%M:%S %Y')
        print(f"C locale formatted: {formatted}")
    except Exception as e:
        print(f"locale test error: {e}")

def test_editable_install_paths():
    """Test 3: Editable install path coupling (F09)"""
    print_header("Test 3: Editable install path coupling (F09)")
    
    # Check where clarinfin-verification is installed
    result = subprocess.run([sys.executable, '-c', 'import clarinfin_verification; print(clarinfin_verification.__file__)'], 
                           capture_output=True, text=True)
    print(f"clarinfin_verification.__file__: {result.stdout.strip()}")
    
    # Check .pth files
    result = subprocess.run([sys.executable, '-c', 'import sys; print([p for p in sys.path if "clarinfin" in p or ".venv" in p])'], 
                           capture_output=True, text=True)
    print(f"sys.path entries: {result.stdout.strip()}")
    
    # Check pip show
    result = subprocess.run(['pip', 'show', 'clarinfin-verification'], capture_output=True, text=True)
    print(f"pip show clarinfin-verification:")
    for line in result.stdout.split('\n'):
        if line.strip():
            print(f"  {line}")

def test_playwright_browsers():
    """Test 4: Playwright browser provisioning (ED6)"""
    print_header("Test 4: Playwright browser provisioning (ED6)")
    
    # Check if browsers are available
    result = subprocess.run(['npx', 'playwright', 'install', '--help'], capture_output=True, text=True, timeout=30)
    print(f"npx playwright install --help: exit={result.returncode}")
    
    # Check cache location
    cache_dir = Path.home() / '.cache' / 'ms-playwright'
    print(f"Playwright cache dir: {cache_dir}")
    if cache_dir.exists():
        for item in cache_dir.iterdir():
            print(f"  {item}")
    else:
        print("  (does not exist)")
    
    # Check if chromium is installed
    result = subprocess.run(['npx', 'playwright', 'install', 'chromium', '--dry-run'], capture_output=True, text=True, timeout=30)
    print(f"playwright install chromium --dry-run: exit={result.returncode}")
    if result.stdout:
        print(f"  stdout: {result.stdout[:200]}")
    if result.stderr:
        print(f"  stderr: {result.stderr[:200]}")

def test_executor_env():
    """Test 5: Executor environment injection"""
    print_header("Test 5: Executor environment (locale/TZ injection)")
    
    sys.path.insert(0, str(REPO_ROOT))
    from runtime.foundation.verification.executor import Executor
    from pathlib import Path
    
    executor = Executor(repo_root=Path('/home/vasantha/AI-Projects/ClariFin_OS'))
    env = executor._exec_env
    
    print(f"TZ in exec_env: {env.get('TZ', 'NOT SET')}")
    print(f"LC_ALL in exec_env: {env.get('LC_ALL', 'NOT SET')}")
    print(f"LANG in exec_env: {env.get('LANG', 'NOT SET')}")
    print(f"PYTHONUNBUFFERED: {env.get('PYTHONUNBUFFERED', 'NOT SET')}")

def test_git_status_in_verification():
    """Test 6: Git operations in verification flow"""
    print_header("Test 6: Git operations in verification flow")
    
    # Test _resolve_base_ref
    import sys
    sys.path.insert(0, str(REPO_ROOT))
    from runtime.foundation.verification.orchestrator import _resolve_base_ref
    
    print("Calling _resolve_base_ref()...")
    result = _resolve_base_ref()
    print(f"Base ref: {result}")

if __name__ == '__main__':
    print("============================================================")
    print("  M9-C42.15 Phase 0 — Forensic Baseline for External State")
    print("============================================================")
    
    test_git_fetch_failure()
    test_locale_tz()
    test_editable_install_paths()
    test_playwright_browsers()
    test_executor_env()
    test_git_status_in_verification()
    
    print("\n============================================================")
    print("  Baseline Complete")
    print("============================================================")