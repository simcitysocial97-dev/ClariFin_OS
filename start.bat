@echo off
chcp 65001 >nul

REM ============================================================================
REM  ClariFin OS - canonical startup entry point for Windows.
REM ============================================================================
REM
REM  This is a thin wrapper with no logic of its own: it delegates to the same
REM  canonical launcher used by start.sh, reached through WSL2. Windows and
REM  Unix therefore share ONE startup implementation and one set of URLs.
REM
REM  Usage:
REM    start.bat                      Start the full application (canonical)
REM    start.bat stop                 Canonical shutdown
REM    start.bat console              Platform Console only (independent)
REM    start.bat status ^| health ^| logs ^| check-env ^| restart
REM    start.bat platform-status      Platform API readiness only
REM    start.bat help                 Full command list
REM
REM  The WSL distribution is taken from the WSL_DISTRO_NAME environment
REM  variable, falling back to Ubuntu. Override it by setting WSL_DISTRO_NAME.
REM ============================================================================

echo ═══════════════════════════════════════════════════════════
echo   ClariFin OS
echo   Canonical launcher: scripts/launch.sh (via WSL2)
echo ═══════════════════════════════════════════════════════════
echo.

set "SCRIPT_DIR=%~dp0"

REM Locate the WSL distribution hosting the repository.
set "WSL_DISTRO=%WSL_DISTRO_NAME%"
if "%WSL_DISTRO%"=="" set "WSL_DISTRO=Ubuntu"

REM Convert the Windows script directory to a WSL-accessible POSIX path.
REM wslpath -a yields an absolute POSIX path (forward slashes, e.g.
REM /mnt/c/Users/...). An empty result means no usable distro was found.
set "WSL_SCRIPT_DIR="
for /f "delims=" %%i in ('wsl -d "%WSL_DISTRO%" wslpath -a "%SCRIPT_DIR%" 2^>nul ^| findstr /V "^$"') do set "WSL_SCRIPT_DIR=%%i"

if "%WSL_SCRIPT_DIR%"=="" (
    echo [ERROR] Could not resolve a WSL path from "%SCRIPT_DIR%".
    echo         WSL did not return a path for distribution "%WSL_DISTRO%".
    echo         Install WSL2, or set WSL_DISTRO_NAME to your distribution.
    echo.
    pause
    exit /b 1
)

echo [INFO] WSL path : %WSL_SCRIPT_DIR%
echo [INFO] Distro   : %WSL_DISTRO%
echo.

REM Build the POSIX launcher path. wslpath already returns forward slashes;
REM appending a Windows-style "\scripts\launch.sh" here would produce a path
REM bash cannot resolve, so join with a literal forward slash.
set "LAUNCHER=%WSL_SCRIPT_DIR%/scripts/launch.sh"

REM Forward arguments when present, otherwise default to `start`, so that
REM "start.bat stop" stops the application rather than starting it again.
if "%~1"=="" (
    wsl -d "%WSL_DISTRO%" bash "%LAUNCHER%" start
) else (
    wsl -d "%WSL_DISTRO%" bash "%LAUNCHER%" %*
)

set "EXITCODE=%ERRORLEVEL%"

REM The launcher tears down everything it started, including on Ctrl+C, so no
REM Windows-side cleanup is required.
echo.
if "%EXITCODE%"=="0" (
    echo [OK] Done.
) else (
    echo [ERROR] The launcher exited with code %EXITCODE%.
)
exit /b %EXITCODE%