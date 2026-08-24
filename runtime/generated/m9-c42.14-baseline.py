#!/usr/bin/env python3
"""M9-C42.14 Phase 0 — Forensic Baseline for Process Lifecycle (simplified, no shell quoting)"""

import subprocess
import time
import os
import signal
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

def test_1_process_tree():
    """Test 1: Parent -> Child -> Grandchild creation WITHOUT shell=True"""
    print_header("Test 1: Process tree creation (no shell, direct subprocess)")
    
    # Direct subprocess chain: python -> python (grandchild)
    proc = subprocess.Popen([PYTHON, str(GRANDCHILD_FILE)])
    print(f'PARENT_PID={proc.pid}')
    time.sleep(1.5)
    
    result = subprocess.run(['ps', '--ppid', str(proc.pid), '-o', 'pid,cmd'], capture_output=True, text=True)
    print(f'Children of {proc.pid}:')
    print(result.stdout)
    
    orphans = check_orphans()
    if orphans:
        print(f'Grandchild found: {orphans}')
    
    proc.terminate()
    proc.wait(timeout=3)

def test_2_shell_tree():
    """Test 2: Process tree creation WITH shell=True"""
    print_header("Test 2: Process tree creation (with shell=True)")
    
    cmd = f'{PYTHON} {GRANDCHILD_FILE}'
    proc = subprocess.Popen(cmd, shell=True)
    print(f'SHELL_PID={proc.pid}')
    time.sleep(1.5)
    
    result = subprocess.run(['ps', '--ppid', str(proc.pid), '-o', 'pid,cmd'], capture_output=True, text=True)
    print(f'Children of shell {proc.pid}:')
    print(result.stdout)
    
    orphans = check_orphans()
    if orphans:
        print(f'Grandchild found: {orphans}')
    
    proc.terminate()
    proc.wait(timeout=3)

def test_3_sigterm_shell():
    """Test 3: SIGTERM to shell leaves orphans"""
    print_header("Test 3: SIGTERM to shell=True process")
    
    cmd = f'{PYTHON} {GRANDCHILD_FILE}'
    proc = subprocess.Popen(cmd, shell=True)
    print(f'SHELL_PID={proc.pid}')
    time.sleep(1.5)
    
    orphans_before = check_orphans()
    print(f'Grandchildren before signal: {orphans_before}')
    
    print('Sending SIGTERM to shell...')
    proc.terminate()
    try:
        proc.wait(timeout=3)
        print(f'Shell exited with: {proc.returncode}')
    except subprocess.TimeoutExpired:
        print('Shell did not exit in 3s - killing')
        proc.kill()
        proc.wait()

    orphans_after = check_orphans()
    if orphans_after:
        print(f'ORPHANED GRANDCHILDREN: {orphans_after}')
    else:
        print('No orphaned grandchildren')

def test_4_timeout_kill():
    """Test 4: Timeout kill (proc.kill()) leaves orphans"""
    print_header("Test 4: Timeout kill (proc.kill())")
    
    cmd = f'{PYTHON} {GRANDCHILD_FILE}'
    proc = subprocess.Popen(cmd, shell=True)
    print(f'SHELL_PID={proc.pid}')
    time.sleep(1.5)
    
    orphans_before = check_orphans()
    print(f'Grandchildren before kill: {orphans_before}')
    
    print('Simulating timeout kill (proc.kill())...')
    proc.kill()
    try:
        proc.wait(timeout=3)
        print(f'Shell exited with: {proc.returncode}')
    except subprocess.TimeoutExpired:
        print('Shell kill failed')

    orphans_after = check_orphans()
    if orphans_after:
        print(f'ORPHANED GRANDCHILDREN after timeout kill: {orphans_after}')
    else:
        print('No orphaned grandchildren')

def test_5_executor():
    """Test 5: Current executor behavior"""
    print_header("Test 5: Current executor timeout behavior")
    
    executor = Executor(repo_root=REPO_ROOT)
    # Use shell=True command like the executor does
    cmd = f'{PYTHON} {GRANDCHILD_FILE}'
    result = executor.execute(cmd, task_id='timeout-test', max_retries=0)
    print(f'Exit code: {result.exit_code}')
    print(f'Status: {result.status}')
    print(f'Duration: {result.duration_seconds}s')

    orphans = check_orphans()
    if orphans:
        print(f'ORPHANED GRANDCHILDREN: {orphans}')
    else:
        print('No orphaned grandchildren')

def test_6_process_group():
    """Test 6: Process group membership"""
    print_header("Test 6: Process group membership (shell=True)")
    
    cmd = f'{PYTHON} -c "import os; print(f\'PYTHON_PGID={os.getpgrp()}\'); import time; time.sleep(10)"'
    proc = subprocess.Popen(cmd, shell=True)
    time.sleep(0.5)
    result = subprocess.run(['ps', '-o', 'pid,ppid,pgid,cmd', '-p', str(proc.pid)], capture_output=True, text=True)
    print('Shell process group:')
    print(result.stdout)
    
    proc.terminate()
    proc.wait(timeout=3)

if __name__ == '__main__':
    print("============================================================")
    print("  M9-C42.14 Phase 0 — Process Lifecycle Forensic Baseline")
    print("============================================================")
    
    test_1_process_tree()
    test_2_shell_tree()
    test_3_sigterm_shell()
    test_4_timeout_kill()
    test_5_executor()
    test_6_process_group()
    
    print("\n============================================================")
    print("  Baseline Complete")
    print("============================================================")