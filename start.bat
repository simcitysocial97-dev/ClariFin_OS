@echo off
chcp 65001 >nul

REM ClariFin OS - Personal Finance MVP v1.0.0
REM One-Click Launch Script for Windows
REM ==========================================

echo ═══════════════════════════════════════════════════════════
echo   ClariFin OS - Personal Finance MVP v1.0.0
echo ═══════════════════════════════════════════════════════════
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed
    echo Please install Node.js 18 or higher from https://nodejs.org
    pause
    exit /b 1
)

echo [INFO] Starting Backend Server...
cd backend

REM Check if virtual environment exists, create if not
if not exist "venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies if needed
if not exist "venv\installed" (
    echo [INFO] Installing Python dependencies...
    pip install -q -r requirements.txt
    type nul > venv\installed
)

REM Start backend in background
echo [OK] Backend starting on http://localhost:8000
start "ClariFin Backend" cmd /c "uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload"
cd ..

REM Wait for backend to be ready
echo [INFO] Waiting for backend to be ready...
timeout /t 5 /nobreak >nul

REM Check if backend is responding
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8000/docs' -UseBasicParsing -TimeoutSec 2; exit 0 } catch { exit 1 }"
if errorlevel 1 (
    echo [WARNING] Backend may not be ready yet, continuing anyway...
) else (
    echo [OK] Backend is ready!
)

echo.
echo [INFO] Starting Frontend...
cd frontend

REM Install dependencies if needed
if not exist "node_modules" (
    echo [INFO] Installing Node.js dependencies...
    call npm install
)

REM Build frontend for production
echo [INFO] Building frontend...
call npm run build

REM Start frontend
echo [OK] Frontend starting on http://localhost:3000
start "ClariFin Frontend" cmd /c "npx serve@latest out -p 3000 -s"
cd ..

echo.
echo ═══════════════════════════════════════════════════════════
echo [OK] ClariFin OS is running!
echo.
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo.
echo Press any key to stop all services...
echo ═══════════════════════════════════════════════════════════

pause >nul

REM Kill all node and python processes started by this script
echo [INFO] Shutting down ClariFin OS...
taskkill /F /FI "WINDOWTITLE eq ClariFin Backend" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq ClariFin Frontend" >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1

echo [OK] Goodbye!
timeout /t 2 >nul
