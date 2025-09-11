@echo off
setlocal enabledelayedexpansion

echo.
echo *** Dear Me - Automated Setup ***
echo =================================
echo Starting your AI-powered journaling app...
echo.

echo [INFO] Starting Ollama server...
start "Ollama Server" ollama serve
timeout /t 3 >nul

echo [INFO] Setting up backend...
cd backend

echo [INFO] Creating Python virtual environment...
if not exist "venv" (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

echo [INFO] Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies
    pause
    exit /b 1
)

echo [INFO] Starting backend server...
start "Backend Server" cmd /c "cd /d "%cd%" && call venv\Scripts\activate.bat && python main.py"
cd ..

echo [INFO] Setting up frontend...
cd frontend

if not exist "node_modules" (
    echo [INFO] Installing frontend dependencies...
    npm install
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install frontend dependencies
        cd ..
        pause
        exit /b 1
    )
)

echo [INFO] Starting frontend server...
start "Frontend Server" cmd /c "cd /d "%cd%" && npm start"
cd ..

timeout /t 5 >nul

echo.
echo [SUCCESS] Setup complete!
echo [INFO] Opening Dear Me app...
start http://localhost:3000
echo.
echo [INFO] Your app should be running at: http://localhost:3000
echo [INFO] API docs at: http://localhost:8001/docs
echo.
echo [INFO] Press any key to exit (services will keep running)...
pause