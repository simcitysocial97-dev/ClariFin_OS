#!/usr/bin/env python3
"""
ClariFin_OS Environment Validation Script

Checks environment health including:
- Python version (3.12+)
- pip version
- Required system packages (ghostscript, libgl1)
- Required Python packages from requirements.txt
- SQLite version
- Disk space
"""

import sys
import subprocess
import shutil
import sqlite3
import os
from pathlib import Path

def print_header(text):
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}")

def print_check(name, status, details=""):
    symbol = "✅" if status else "❌"
    print(f"  {symbol} {name}")
    if details:
        print(f"     {details}")

def check_python_version():
    version = sys.version_info
    required = (3, 12)
    ok = version >= required
    details = f"Python {version.major}.{version.minor}.{version.micro}"
    if not ok:
        details += f" (requires {required[0]}.{required[1]}+)"
    return ok, details

def check_pip_version():
    try:
        result = subprocess.run(
            ["pip", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        version_line = result.stdout.strip()
        parts = version_line.split()
        version = parts[1] if len(parts) > 1 else "unknown"
        return True, f"pip {version}"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False, "pip not found"

def check_system_package(package):
    """Check if a system package is installed using dpkg or which."""
    # First try 'which' for executables
    if shutil.which(package):
        return True, f"{package} found in PATH"
    
    # Try dpkg for Debian-based systems
    try:
        result = subprocess.run(
            ["dpkg", "-l", package],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and "ii" in result.stdout:
            return True, f"{package} installed via dpkg"
    except FileNotFoundError:
        pass
    
    # Try checking for library files
    common_lib_paths = [
        f"/usr/lib/x86_64-linux-gnu/{package}*",
        f"/usr/lib/{package}*",
    ]
    for path_pattern in common_lib_paths:
        import glob
        if glob.glob(path_pattern):
            return True, f"{package} library found"
    
    return False, f"{package} not found"

def check_ghostscript():
    """Check ghostscript installation."""
    gs_path = shutil.which("gs")
    if gs_path:
        try:
            result = subprocess.run(
                ["gs", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            version = result.stdout.strip()
            return True, f"Ghostscript {version} at {gs_path}"
        except subprocess.CalledProcessError:
            return True, f"Ghostscript found at {gs_path} (version unknown)"
    return False, "Ghostscript not found in PATH"

def check_sqlite_version():
    version = sqlite3.sqlite_version
    return True, f"SQLite {version}"

def check_disk_space():
    try:
        stat = os.statvfs(".")
        free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
        total_gb = (stat.f_blocks * stat.f_frsize) / (1024**3)
        ok = free_gb > 1.0  # Require at least 1GB free
        details = f"{free_gb:.1f} GB free / {total_gb:.1f} GB total"
        if not ok:
            details += " (less than 1GB free)"
        return ok, details
    except Exception as e:
        return False, f"Could not check disk space: {e}"

def check_python_packages():
    """Check if required Python packages are installed."""
    backend_dir = Path(__file__).parent.parent
    requirements_file = backend_dir / "requirements.txt"
    
    if not requirements_file.exists():
        return False, "requirements.txt not found"
    
    # Parse requirements.txt to get package names
    required_packages = []
    with open(requirements_file) as f:
        for line in f:
            line = line.strip()
            # Skip comments, empty lines, and options
            if not line or line.startswith('#') or line.startswith('-'):
                continue
            # Extract package name (before ==, >=, etc., and before [extras])
            # Handle extras like camelot-py[cv]==1.0.9
            if '[' in line:
                line = line.split('[')[0]
            # Extract package name before version specifier
            for sep in ['==', '>=', '<=', '>', '<', '!=', '~=']:
                if sep in line:
                    line = line.split(sep)[0]
                    break
            if line:
                required_packages.append(line.lower())
    
    # Check installed packages
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            check=True
        )
        installed = {}
        for line in result.stdout.strip().split('\n'):
            if '==' in line:
                name, version = line.split('==', 1)
                installed[name.lower()] = version
        
        # Normalize package names (replace hyphens with underscores for comparison)
        installed_normalized = {name.replace('-', '_'): ver for name, ver in installed.items()}
        
        # Special package name mappings (PyPI name -> installed name)
        name_mappings = {
            'pdfminer_six': 'pdfminer.six',  # pdfminer-six -> pdfminer.six
        }
        
        missing = []
        for pkg in required_packages:
            # Normalize package name for comparison
            pkg_normalized = pkg.replace('-', '_')
            # Check if there's a mapping for this package
            if pkg_normalized in name_mappings:
                pkg_normalized = name_mappings[pkg_normalized]
            if pkg_normalized not in installed_normalized:
                missing.append(pkg)
        
        if missing:
            return False, f"Missing packages: {', '.join(missing[:5])}" + (
                f" and {len(missing) - 5} more" if len(missing) > 5 else ""
            )
        return True, f"All {len(required_packages)} required packages installed"
    except subprocess.CalledProcessError as e:
        return False, f"Could not check installed packages: {e}"

def main():
    print_header("ClariFin_OS Environment Doctor")
    
    all_ok = True
    
    # Python version
    print("\n📋 Python Environment")
    ok, details = check_python_version()
    print_check("Python Version", ok, details)
    all_ok = all_ok and ok
    
    ok, details = check_pip_version()
    print_check("pip Version", ok, details)
    all_ok = all_ok and ok
    
    ok, details = check_sqlite_version()
    print_check("SQLite Version", ok, details)
    
    # System packages
    print("\n📋 System Dependencies")
    ok, details = check_ghostscript()
    print_check("Ghostscript", ok, details)
    all_ok = all_ok and ok
    
    # Check for OpenCV dependencies
    ok, details = check_system_package("libgl1")
    print_check("libgl1 (OpenCV dependency)", ok, details)
    
    # Python packages
    print("\n📋 Python Packages")
    ok, details = check_python_packages()
    print_check("Required Packages", ok, details)
    all_ok = all_ok and ok
    
    # Disk space
    print("\n📋 System Resources")
    ok, details = check_disk_space()
    print_check("Disk Space", ok, details)
    all_ok = all_ok and ok
    
    # Summary
    print_header("Summary")
    if all_ok:
        print("  ✅ Environment is healthy and ready for development!")
        print("\n  Next steps:")
        print("    make validate  - Run pipeline validation")
        print("    make test      - Run test suite")
        print("    make run       - Start development server")
    else:
        print("  ❌ Environment has issues that need to be resolved.")
        print("\n  Please install missing dependencies:")
        print("    sudo apt-get install ghostscript libgl1-mesa-glx")
        print("    pip install -r requirements.txt")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
