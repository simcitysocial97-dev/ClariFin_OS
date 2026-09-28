@echo off
chcp 65001 >nul

REM ClariFin OS - Personal Finance MVP v1.0.0
REM One-Click Launch Script for Windows (WSL2 delegation)
REM ==========================================

echo ═══════════════════════════════════════════════════════════
echo   ClariFin OS - Personal Finance MVP v1.0.0
echo ═══════════════════════════════════════════════════════════
echo.

REM Get script directory (Windows path)
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check Python prerequisites (must be available in WSL, not required locally)
python --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Python check skipped (local environment optional — running via WSL2)
)

REM Check Node.js prerequisite similarly
node --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Node.js check skipped (local environment optional — running via WSL2)
)

echo [INFO] Starting ClariFin OS via WSL2 (canonical repository launcher)...
echo.

REM Locate WSL distribution (try common defaults; user may override WSL_DISTRO).
REM The Windows+WSL2 architecture deploys the canonical runtime inside WSL; this
REM launcher bridges from Windows to that single environment.
set "WSL_DISTRO=%WSL_DISTRO_NAME%"
if "%WSL_DISTRO%"=="" set "WSL_DISTRO=Ubuntu"

REM Convert the Windows script directory to a WSL-accessible path.
REM wslpath -a prefers an absolute path and fails if no distro is accessible.
for /f "delims=" %%i in ('wsl -d "%WSL_DISTRO%" wslpath -a "%SCRIPT_DIR%" ^| findstr /V "^$"') do set "WSL_SCRIPT_DIR=%%i"
if "%WSL_SCRIPT_DIR%"=="" (
    echo [ERROR] Could not resolve WSL path from %SCRIPT_DIR%.
    echo        Ensure WSL is installed and the default distribution is accessible.
    pause
    exit /b 1
)

echo [INFO] WSL path: %WSL_SCRIPT_DIR%
echo [INFO] Distro:   %WSL_DISTRO%
echo.

REM Delegate to the canonical launcher via WSL. This preserves the WSL process
REM lifecycle (background backend + foreground frontend serve).
wsl -d "%WSL_DISTRO%" bash "%WSL_SCRIPT_DIR%\scripts\launch.sh" start

REM If we reach here (user exited), clean up. Windows-side tasks are handled
REM inside WSL by the launcher; nothing else to kill here.
echo.
echo [OK] Goodbye!
timeout /t 2 >nul
pause >nul
