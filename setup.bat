@echo off
REM Dear Me - Automated Setup Script (Windows)

echo 🌟 Dear Me - Automated Setup
echo =============================

REM Check prerequisites
echo 🔍 Checking prerequisites...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install from https://www.python.org/
    pause
    exit /b 1
)

node -v >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js not found. Please install from https://nodejs.org/
    pause
    exit /b 1
)

ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Ollama not found. Please install from https://ollama.ai/
    pause
    exit /b 1
)

echo ✅ All prerequisites found

REM Setup Ollama
echo.
echo 🤖 Setting up AI models...
ollama list | findstr "llama3.1:8b" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📥 Downloading Llama 3.1 model (this may take a few minutes)...
    ollama pull llama3.1:8b
) else (
    echo ✅ Llama 3.1 model already downloaded
)

echo 🚀 Starting Ollama server...
start "Ollama Server" ollama serve
timeout /t 3 >nul

REM Setup Backend
echo.
echo 🔧 Setting up backend...
cd backend

if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

echo 📦 Installing backend dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo 🚀 Starting backend server...
start "Backend Server" cmd /c "venv\Scripts\activate.bat && python main.py"
cd ..
timeout /t 3 >nul

REM Setup Frontend
echo.
echo 🎨 Setting up frontend...
cd frontend

if not exist "node_modules" (
    echo 📦 Installing frontend dependencies...
    npm install
)

echo 🚀 Starting frontend server...
start "Frontend Server" npm start
cd ..

timeout /t 5 >nul

echo.
echo 🎉 Setup complete!
echo 📱 Your app should open automatically at: http://localhost:3000
echo 📚 API docs available at: http://localhost:8001/docs
echo.
echo 💡 Close the terminal windows to stop all services
echo.
pause