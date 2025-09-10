#!/bin/bash
# Dear Me - Automated Setup Script (macOS/Linux)

set -e  # Exit on any error

echo "🌟 Dear Me - Automated Setup"
echo "============================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command_exists python3; then
    echo "❌ Python 3 not found. Please install from https://www.python.org/"
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js not found. Please install from https://nodejs.org/"
    exit 1
fi

if ! command_exists ollama; then
    echo "❌ Ollama not found. Please install from https://ollama.ai/"
    exit 1
fi

echo "✅ All prerequisites found"

# Setup Ollama
echo ""
echo "🤖 Setting up AI models..."
if ollama list | grep -q "llama3.1:8b"; then
    echo "✅ Llama 3.1 model already downloaded"
else
    echo "📥 Downloading Llama 3.1 model (this may take a few minutes)..."
    ollama pull llama3.1:8b
fi

echo "🚀 Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!
sleep 3

# Setup Backend
echo ""
echo "🔧 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "📦 Installing backend dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo "🚀 Starting backend server..."
python main.py &
BACKEND_PID=$!
cd ..
sleep 3

# Setup Frontend
echo ""
echo "🎨 Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

echo "🚀 Starting frontend server..."
npm start &
FRONTEND_PID=$!
cd ..

# Wait a bit for everything to start
sleep 5

echo ""
echo "🎉 Setup complete!"
echo "📱 Your app should open automatically at: http://localhost:3000"
echo "📚 API docs available at: http://localhost:8001/docs"
echo ""
echo "💡 Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "👋 Shutting down Dear Me..."
    kill $OLLAMA_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Set trap to cleanup on Ctrl+C
trap cleanup INT

# Keep script running
while true; do
    sleep 60
    echo "✅ All services running..."
done