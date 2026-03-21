@echo off
REM Dear Me - One-Click Desktop Launcher (Windows)
REM Double-click or run from command prompt
REM This launcher starts all services and opens the app in your browser

setlocal enabledelayedexpansion

REM Color codes using batch (limited - using simple prefixes instead)
set "CHECK=✓"
set "ERROR=✗"

REM Get script directory
set "SCRIPT_DIR=%~dp0"
REM Remove trailing backslash and go up one level to project root
for %%A in ("%SCRIPT_DIR:~0,-1%") do set "APP_DIR=%%~dpA"

REM Virtual environment path
set "VENV_DIR=%APP_DIR%backend\venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"

echo.
echo ================================
echo  Dear Me - One-Click Launcher
echo ================================
echo.

REM [1/5] Verify virtual environment exists
echo [1/5] Checking virtual environment...

if not exist "%VENV_DIR%" (
    echo ✗ Virtual environment not found!
    echo.
    echo Please run: powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%install_dependencies.ps1"
    echo.
    pause
    exit /b 1
)

echo ✓ Virtual environment found

REM [2/5] Free up ports (8001 and 3000)
echo.
echo [2/5] Checking for port conflicts...

REM Kill any existing processes using these ports
for /f "tokens=5" %%A in ('netstat -ano ^| findstr ":8001 " ^| findstr "LISTENING"') do (
    taskkill /PID %%A /F >nul 2>&1
)

for /f "tokens=5" %%A in ('netstat -ano ^| findstr ":3000 " ^| findstr "LISTENING"') do (
    taskkill /PID %%A /F >nul 2>&1
)

echo ✓ Ports cleared

REM [3/5] Check Ollama service
echo.
echo [3/5] Setting up Ollama...

set "OLLAMA_READY=0"
for /l %%A in (1,1,15) do (
    powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:11434/' -TimeoutSec 1 -ErrorAction Stop | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
    if !errorlevel! equ 0 (
        set "OLLAMA_READY=1"
        goto :OLLAMA_READY
    )
    timeout /t 2 /nobreak >nul 2>&1
)

:OLLAMA_READY
if !OLLAMA_READY! equ 1 (
    echo ✓ Ollama service is running
) else (
    echo ✗ Ollama service not responding
    echo.
    echo Ollama needs to be running before Dear Me can start.
    echo Please install Ollama from https://ollama.ai
    echo.
    pause
    exit /b 1
)

REM Check if model is downloaded
powershell -Command "try { $models = & ollama list; if ($models | Select-String 'llama3.1:8b') { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1

if !errorlevel! equ 0 (
    echo ✓ Model is downloaded
) else (
    echo ⚠ Model not found. Downloading llama3.1:8b (this will take 15-20 minutes)...
    call ollama pull llama3.1:8b
    if !errorlevel! neq 0 (
        echo ✗ Model download failed
        echo You can download manually: ollama pull llama3.1:8b
        pause
        exit /b 1
    )
)

REM [4/5] Start backend
echo.
echo [4/5] Starting backend server...

cd /d "%APP_DIR%backend"

start "DearMe-Backend" /MIN cmd /c "%VENV_PYTHON% main.py"

REM Wait for backend to be ready
set "BACKEND_READY=0"
for /l %%A in (1,1,60) do (
    powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8001/' -TimeoutSec 1 -ErrorAction Stop | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
    if !errorlevel! equ 0 (
        set "BACKEND_READY=1"
        goto :BACKEND_READY
    )
    timeout /t 1 /nobreak >nul 2>&1
)

:BACKEND_READY
if !BACKEND_READY! equ 1 (
    echo ✓ Backend ready at http://localhost:8001
) else (
    echo ✗ Backend failed to start
    echo.
    echo Check %APP_DIR%backend\dear_me.db for database issues
    pause
    exit /b 1
)

REM [5/5] Start frontend (http.server on pre-built frontend)
echo.
echo [5/5] Starting frontend server...

cd /d "%APP_DIR%frontend\build"

start "DearMe-Frontend" /MIN cmd /c "%VENV_PYTHON% -m http.server 3000"

REM Wait for frontend to be ready
set "FRONTEND_READY=0"
for /l %%A in (1,1,15) do (
    powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:3000' -TimeoutSec 1 -ErrorAction Stop | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
    if !errorlevel! equ 0 (
        set "FRONTEND_READY=1"
        goto :FRONTEND_READY
    )
    timeout /t 1 /nobreak >nul 2>&1
)

:FRONTEND_READY
if !FRONTEND_READY! equ 1 (
    echo ✓ Frontend ready
) else (
    echo ✗ Frontend failed to start
    pause
    exit /b 1
)

REM Get local IP for WiFi access
for /f "tokens=2 delims=: " %%A in ('ipconfig ^| find "IPv4"') do set "LOCAL_IP=%%A"

REM Print success banner
echo.
echo ================================
echo  Dear Me is running!
echo ================================
echo.
echo Desktop: http://localhost:3000
echo API Docs: http://localhost:8001/docs

if defined LOCAL_IP (
    echo Phone (same WiFi): http://%LOCAL_IP%:3000
)

echo.
echo Press Ctrl+C or close this window to stop all services
echo.

REM Open browser
timeout /t 1 /nobreak >nul 2>&1
start http://localhost:3000

REM Monitor loop - check every 10 seconds
:MONITOR_LOOP
timeout /t 10 /nobreak >nul 2>&1

REM Check if backend is still running
tasklist | find "python.exe" >nul 2>&1
if !errorlevel! neq 0 (
    echo.
    echo ✗ Backend process stopped unexpectedly
    goto :CLEANUP
)

goto :MONITOR_LOOP

:CLEANUP
echo.
echo Shutting down Dear Me...
taskkill /FI "WINDOWTITLE eq DearMe-Backend" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq DearMe-Frontend" /F >nul 2>&1

echo Done.
pause
exit /b 0
