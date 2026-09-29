#!/usr/bin/env bash
# M9-C42.14 Phase 0 — Forensic Baseline for Process Lifecycle (fixed)

set -euo pipefail

REPO_ROOT="/home/vasantha/AI-Projects/ClariFin_OS"
cd "$REPO_ROOT"

echo "============================================================"
echo "  M9-C42.14 Phase 0 — Process Lifecycle Forensic Baseline"
echo "============================================================"

# Test 1: Parent -> Child -> Grandchild creation with current executor
echo ""
echo "Test 1: Process tree creation (shell=True)"
echo "----------------------------------------"
.venv/bin/python3 << 'PYEOF'
import subprocess
import time
import os

# Start a process that spawns grandchildren
cmd = 'bash -c "echo SHELL_PID=$$; python3 -c \\"import subprocess, time; p=subprocess.Popen([\\'sleep\\', \\'10\\']); print(f\\'GRANDCHILD_PID={p.pid}\\'); time.sleep(15)\\""'
proc = subprocess.Popen(cmd, shell=True)
print(f'PARENT_PID={proc.pid}')
time.sleep(1)
# Check process tree
import subprocess as sp
result = sp.run(['ps', '--ppid', str(proc.pid), '-o', 'pid,cmd'], capture_output=True, text=True)
print(f'Children of {proc.pid}:')
print(result.stdout)
PYEOF

# Test 2: SIGTERM propagation with current executor
echo ""
echo "Test 2: SIGTERM propagation (current behavior)"
echo "----------------------------------------"
.venv/bin/python3 << 'PYEOF'
import subprocess
import time
import os
import signal

cmd = 'bash -c "echo SHELL_PID=$$; python3 -c \\"import subprocess, time, signal; p=subprocess.Popen([\\'sleep\\', \\'30\\']); print(f\\'GRANDCHILD_PID={p.pid}\\'); signal.pause()\\""'
proc = subprocess.Popen(cmd, shell=True)
print(f'PARENT_PID={proc.pid}')
time.sleep(1)
print('Sending SIGTERM to parent shell...')
proc.terminate()
try:
    proc.wait(timeout=3)
    print(f'Parent exited with: {proc.returncode}')
except subprocess.TimeoutExpired:
    print('Parent did not exit in 3s - killing')
    proc.kill()
    proc.wait()

# Check if grandchild survived
import subprocess as sp
result = sp.run(['pgrep', '-f', 'sleep 30'], capture_output=True, text=True)
if result.stdout.strip():
    print(f'ORPHANED GRANDCHILDREN: {result.stdout.strip()}')
else:
    print('No orphaned grandchildren')
PYEOF

# Test 3: Timeout handling with current executor
echo ""
echo "Test 3: Timeout handling (current behavior)"
echo "----------------------------------------"
.venv/bin/python3 << 'PYEOF'
import subprocess
import time
import os

cmd = 'bash -c "echo SHELL_PID=$$; python3 -c \\"import subprocess, time; p=subprocess.Popen([\\'sleep\\', \\'30\\']); print(f\\'GRANDCHILD_PID={p.pid}\\'); time.sleep(60)\\""'
proc = subprocess.Popen(cmd, shell=True)
print(f'PARENT_PID={proc.pid}')
time.sleep(1)
print('Simulating timeout kill (proc.kill())...')
proc.kill()
try:
    proc.wait(timeout=3)
    print(f'Parent exited with: {proc.returncode}')
except subprocess.TimeoutExpired:
    print('Parent kill failed')

# Check if grandchild survived
import subprocess as sp
result = sp.run(['pgrep', '-f', 'sleep 30'], capture_output=True, text=True)
if result.stdout.strip():
    print(f'ORPHANED GRANDCHILDREN after timeout kill: {result.stdout.strip()}')
else:
    print('No orphaned grandchildren')
PYEOF

# Test 4: Current executor behavior
echo ""
echo "Test 4: Current executor timeout behavior"
echo "----------------------------------------"
.venv/bin/python3 << 'PYEOF'
import sys
sys.path.insert(0, '/home/vasantha/AI-Projects/ClariFin_OS')
from runtime.foundation.verification.executor import Executor
from pathlib import Path

executor = Executor(repo_root=Path('/home/vasantha/AI-Projects/ClariFin_OS'))
# Execute a command that spawns grandchildren and times out
result = executor.execute('bash -c "echo SHELL_PID=$$; python3 -c \\"import subprocess, time; p=subprocess.Popen([\\'sleep\\', \\'30\\']); print(f\\'GRANDCHILD_PID={p.pid}\\'); time.sleep(60)\\""', task_id='timeout-test', max_retries=0)
print(f'Exit code: {result.exit_code}')
print(f'Status: {result.status}')
print(f'Duration: {result.duration_seconds}s')

# Check for orphans
import subprocess as sp
result = sp.run(['pgrep', '-f', 'sleep 30'], capture_output=True, text=True)
if result.stdout.strip():
    print(f'ORPHANED GRANDCHILDREN: {result.stdout.strip()}')
else:
    print('No orphaned grandchildren')
PYEOF

# Test 5: Process group membership
echo ""
echo "Test 5: Process group membership (current)"
echo "----------------------------------------"
.venv/bin/python3 << 'PYEOF'
import subprocess
import time
import os

cmd = 'bash -c "echo SHELL_PID=$$; echo SHELL_PGID=$(ps -o pgid= $$); python3 -c \\"import os; print(f\\'PYTHON_PGID={os.getpgrp()}\\'); import time; time.sleep(10)\\""'
proc = subprocess.Popen(cmd, shell=True)
time.sleep(0.5)
import subprocess as sp
result = sp.run(['ps', '-o', 'pid,ppid,pgid,cmd', '-p', str(proc.pid)], capture_output=True, text=True)
print('Parent process group:')
print(result.stdout)
PYEOF

echo ""
echo "============================================================"
echo "  Baseline Complete"
echo "============================================================"