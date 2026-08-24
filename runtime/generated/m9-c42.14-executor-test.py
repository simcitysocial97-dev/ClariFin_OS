#!/usr/bin/env python3
"""Test updated executor process group killing"""

import subprocess
import time
import os
import sys

sys.path.insert(0, '/home/vasantha/AI-Projects/ClariFin_OS')
from runtime.foundation.verification.executor import Executor
from pathlib import Path

REPO_ROOT = Path('/home/vasantha/AI-Projects/ClariFin_OS')
PYTHON = sys.executable
GRANDCHILD_FILE = REPO_ROOT / 'runtime' / 'generated' / 'm9-c42-14-grandchild.py'

def check_orphans():
    """Check for orphaned grandchild processes."""
    result = subprocess.run(['pgrep', '-f', GRANDCHILD_FILE.name], capture_output=True, text=True)
    if result.stdout.strip():
        return result.stdout.strip().split()
    return []

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_executor_timeout_kills_tree():
    """Test: Executor with short timeout kills entire process tree"""
    print_header("Test: Executor timeout kills process tree (F19 fix)")
    
    executor = Executor(repo_root=REPO_ROOT, per_step_timeout=2)  # 2 second timeout
    cmd = f'{PYTHON} {GRANDCHILD_FILE}'
    print(f'Command: {cmd}')
    print(f'Timeout: 2 seconds')
    
    result = executor.execute(cmd, task_id='timeout-test', max_retries=0)
    print(f'Exit code: {result.exit_code}')
    print(f'Status: {result.status}')
    print(f'Duration: {result.duration_seconds}s')
    print(f'Classification: {result.classification}')

    orphans = check_orphans()
    if orphans:
        print(f'ORPHANED GRANDCHILDREN: {orphans}')
        print("FAIL: Process group NOT killed")
    else:
        print('No orphaned grandchildren')
        print("PASS: Process group killed successfully")

def test_executor_sigterm_on_cancel():
    """Test: Executor cancel() kills process tree"""
    print_header("Test: Executor cancel() kills process tree")
    
    executor = Executor(repo_root=REPO_ROOT, per_step_timeout=3600)
    cmd = f'{PYTHON} {GRANDCHILD_FILE}'
    print(f'Command: {cmd}')
    
    # Start execution in background thread
    import threading
    result_container = {}
    
    def run_cmd():
        result_container['result'] = executor.execute(cmd, task_id='cancel-test', max_retries=0)
    
    thread = threading.Thread(target=run_cmd)
    thread.start()
    
    # Wait for process to start
    time.sleep(2)
    
    # Check for grandchildren before cancel
    orphans_before = check_orphans()
    print(f'Grandchildren before cancel: {orphans_before}')
    
    # Cancel
    print('Calling executor.cancel()...')
    executor.cancel()
    
    thread.join(timeout=5)
    result = result_container.get('result')
    
    if result:
        print(f'Exit code: {result.exit_code}')
        print(f'Status: {result.status}')
        print(f'Duration: {result.duration_seconds}s')
    
    orphans_after = check_orphans()
    if orphans_after:
        print(f'ORPHANED GRANDCHILDREN after cancel: {orphans_after}')
        print("FAIL: Process group NOT killed on cancel")
    else:
        print('No orphaned grandchildren after cancel')
        print("PASS: Process group killed on cancel")

def check_orphans():
    """Check for orphaned grandchild processes."""
    result = subprocess.run(['pgrep', '-f', 'm9-c42-14-grandchild'], capture_output=True, text=True)
    if result.stdout.strip():
        return result.stdout.strip().split()
    return []

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

if __name__ == '__main__':
    print("============================================================")
    print("  M9-C42.14 — Executor Process Group Killing Tests")
    print("============================================================")
    
    test_executor_timeout_kills_tree()
    test_executor_sigterm_on_cancel()
    
    print("\n============================================================")
    print("  Tests Complete")
    print("============================================================")