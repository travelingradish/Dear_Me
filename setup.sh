#!/bin/bash
# Dear Me - One-Click Desktop Launcher (macOS)
# This script starts all services and opens the app in your browser
# Double-click "Dear Me.command" on your Desktop to use this

set -e

# Color codes
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Find the script directory (even if symlinked)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Determine absolute path to uv
UV_PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin/uv"
if [ ! -f "$UV_PATH" ]; then
    # Fallback: try to find it in PATH
    UV_PATH=$(command -v uv 2>/dev/null || echo "")
    if [ -z "$UV_PATH" ]; then
        echo -e "${RED}❌ uv not found. Please ensure Python 3.13 with uv is installed.${NC}"
        exit 1
    fi
fi

# Cleanup function - called on exit or Ctrl+C
cleanup() {
    echo -e "\n${YELLOW}👋 Shutting down Dear Me...${NC}"

    # Kill frontend if we started it
    if [ -n "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi

    # Kill backend if we started it
    if [ -n "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi

    # Only kill Ollama if we started it (not if it was already running)
    if [ "$OLLAMA_STARTED_BY_US" = "yes" ] && [ -n "$OLLAMA_PID" ]; then
        kill "$OLLAMA_PID" 2>/dev/null || true
    fi

    exit 0
}

trap cleanup INT TERM

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}🌟 Dear Me - One-Click Launcher${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# [1/5] Check prerequisites
echo -e "${BLUE}[1/5]${NC} Checking prerequisites..."

for cmd in node npm ollama curl; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo -e "${RED}❌ $cmd not found. Please install it first.${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ All prerequisites found${NC}"

# [2/5] Clean up port conflicts
echo ""
echo -e "${BLUE}[2/5]${NC} Checking for port conflicts..."

for port in 8001 3000; do
    # Check if port is in use
    if lsof -Pi ":$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Port $port is in use, attempting to free it...${NC}"
        # Kill the process using the port
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
done

echo -e "${GREEN}✅ Ports cleared${NC}"

# [3/5] Start Ollama
echo ""
echo -e "${BLUE}[3/5]${NC} Setting up Ollama..."

# Check if Ollama is already running
if curl -s http://localhost:11434/ >/dev/null 2>&1; then
    echo -e "${GREEN}♻️  Reusing existing Ollama instance${NC}"
    OLLAMA_STARTED_BY_US="no"
else
    echo -e "🤖 Starting Ollama server..."

    # Ensure model is downloaded
    if ! ollama list 2>/dev/null | grep -q "llama3.1:8b"; then
        echo -e "📥 Downloading llama3.1:8b model (may take a few minutes)..."
        ollama pull llama3.1:8b || {
            echo -e "${RED}❌ Failed to download model${NC}"
            exit 1
        }
    fi

    # Start Ollama in background
    ollama serve >/dev/null 2>&1 &
    OLLAMA_PID=$!
    OLLAMA_STARTED_BY_US="yes"

    # Wait for Ollama to be ready (up to 30 seconds)
    TRIES=0
    until curl -s http://localhost:11434/ >/dev/null 2>&1; do
        TRIES=$((TRIES + 1))
        if [ $TRIES -ge 30 ]; then
            echo -e "${RED}❌ Ollama failed to start (timeout)${NC}"
            cleanup
        fi
        if ! kill -0 "$OLLAMA_PID" 2>/dev/null; then
            echo -e "${RED}❌ Ollama process crashed${NC}"
            cleanup
        fi
        sleep 1
    done
fi

echo -e "${GREEN}✅ Ollama ready${NC}"

# [4/5] Start backend
echo ""
echo -e "${BLUE}[4/5]${NC} Starting backend server..."

cd "$SCRIPT_DIR/backend"

# Setup venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "📦 Creating virtual environment..."
    python3 -m venv venv || {
        echo -e "${RED}❌ Failed to create virtual environment${NC}"
        cleanup
    }
fi

# Install/update dependencies using venv's pip
echo -e "📦 Installing backend dependencies (this may take a minute)..."
venv/bin/pip install -q -r requirements.txt 2>/dev/null || {
    echo -e "${RED}❌ Backend dependency installation failed${NC}"
    cleanup
}

# Start backend using venv's python
venv/bin/python main.py >/dev/null 2>&1 &
BACKEND_PID=$!

# Wait for backend to be ready (up to 60 seconds)
TRIES=0
until curl -s http://localhost:8001/ 2>/dev/null | grep -q "status"; do
    TRIES=$((TRIES + 1))
    if [ $TRIES -ge 60 ]; then
        echo -e "${RED}❌ Backend failed to start (timeout)${NC}"
        cleanup
    fi
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo -e "${RED}❌ Backend process crashed${NC}"
        cleanup
    fi
    sleep 1
done

echo -e "${GREEN}✅ Backend ready at http://localhost:8001${NC}"

# [5/5] Start frontend
echo ""
echo -e "${BLUE}[5/5]${NC} Starting frontend server..."

cd "$SCRIPT_DIR/frontend"

# Install dependencies if needed (silently)
if [ ! -d "node_modules" ]; then
    echo -e "📦 Installing frontend dependencies (this may take a minute)..."
    npm install --silent >/dev/null 2>&1 || {
        echo -e "${RED}❌ Frontend dependency installation failed${NC}"
        cleanup
    }
fi

# Start frontend with BROWSER=none to prevent auto-open (we'll do it manually)
BROWSER=none npm start >/dev/null 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to be ready (up to 120 seconds)
TRIES=0
until curl -s http://localhost:3000 >/dev/null 2>&1; do
    TRIES=$((TRIES + 1))
    if [ $TRIES -ge 120 ]; then
        echo -e "${RED}❌ Frontend failed to start (timeout)${NC}"
        cleanup
    fi
    if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo -e "${RED}❌ Frontend process crashed${NC}"
        cleanup
    fi
    sleep 1
done

echo -e "${GREEN}✅ Frontend ready${NC}"

# Get WiFi IP for mobile access
WIFI_IP=$(route get 8.8.8.8 2>/dev/null | grep interface | awk '{print $2}' | xargs -I {} ipconfig getifaddr {} 2>/dev/null || echo "")

# Print success banner
echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}🎉 Dear Me is running!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "📱 ${BLUE}Desktop:${NC} http://localhost:3000"
echo -e "📚 ${BLUE}API Docs:${NC} http://localhost:8001/docs"

if [ -n "$WIFI_IP" ]; then
    echo -e "📱 ${BLUE}Phone (same WiFi):${NC} http://$WIFI_IP:3000"
fi

echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Open browser
sleep 1
open http://localhost:3000 2>/dev/null || true

# Monitor loop - check every 10 seconds that services are still alive
while true; do
    sleep 10

    # Check if backend is still running
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo -e "${RED}❌ Backend crashed, shutting down...${NC}"
        cleanup
    fi

    # Check if frontend is still running
    if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo -e "${RED}❌ Frontend crashed, shutting down...${NC}"
        cleanup
    fi
done
