#!/usr/bin/env python3
"""
Dear Me - Automated Setup Script
Handles all setup tasks automatically
"""

import os
import subprocess
import sys
import time
import platform
from pathlib import Path

def run_command(command, description, cwd=None, background=False):
    """Run a command with error handling"""
    print(f"📦 {description}...")
    try:
        if background:
            if platform.system() == "Windows":
                subprocess.Popen(command, shell=True, cwd=cwd, creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(command, shell=True, cwd=cwd)
            time.sleep(2)  # Give it time to start
            return True
        else:
            result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Error: {result.stderr}")
                return False
            print(f"✅ {description} completed")
            return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_prerequisites():
    """Check if required software is installed"""
    print("🔍 Checking prerequisites...")
    
    # Check Python
    try:
        import sys
        python_version = sys.version_info
        if python_version.major < 3 or python_version.minor < 10:
            print("❌ Python 3.10+ required")
            return False
        print("✅ Python version OK")
    except:
        print("❌ Python not found")
        return False
    
    # Check Node.js
    if not run_command("node -v", "Checking Node.js"):
        print("❌ Node.js not found. Please install from https://nodejs.org/")
        return False
    
    # Check Ollama
    if not run_command("ollama --version", "Checking Ollama"):
        print("❌ Ollama not found. Please install from https://ollama.ai/")
        return False
    
    return True

def setup_ollama():
    """Setup Ollama models"""
    print("\n🤖 Setting up AI models...")
    
    # Check if model is already downloaded
    result = subprocess.run("ollama list", shell=True, capture_output=True, text=True)
    if "llama3.1:8b" in result.stdout:
        print("✅ Llama 3.1 model already downloaded")
    else:
        if not run_command("ollama pull llama3.1:8b", "Downloading Llama 3.1 model (this may take a few minutes)"):
            return False
    
    # Start Ollama server in background
    print("🚀 Starting Ollama server...")
    run_command("ollama serve", "Starting Ollama server", background=True)
    return True

def setup_backend():
    """Setup backend"""
    print("\n🔧 Setting up backend...")
    
    backend_path = Path("backend")
    if not backend_path.exists():
        print("❌ Backend directory not found")
        return False
    
    # Create virtual environment if it doesn't exist
    venv_path = backend_path / "venv"
    if not venv_path.exists():
        if not run_command("python -m venv venv", "Creating virtual environment", cwd="backend"):
            return False
    
    # Install dependencies
    if platform.system() == "Windows":
        pip_cmd = "venv\\Scripts\\pip.exe install -r requirements.txt"
        python_cmd = "venv\\Scripts\\python.exe main.py"
    else:
        pip_cmd = "venv/bin/pip install -r requirements.txt"
        python_cmd = "venv/bin/python main.py"
    
    if not run_command(pip_cmd, "Installing backend dependencies", cwd="backend"):
        return False
    
    # Start backend server in background
    print("🚀 Starting backend server...")
    run_command(python_cmd, "Starting backend server", cwd="backend", background=True)
    return True

def setup_frontend():
    """Setup frontend"""
    print("\n🎨 Setting up frontend...")
    
    frontend_path = Path("frontend")
    if not frontend_path.exists():
        print("❌ Frontend directory not found")
        return False
    
    # Install dependencies
    if not run_command("npm install", "Installing frontend dependencies", cwd="frontend"):
        return False
    
    # Start frontend server in background
    print("🚀 Starting frontend server...")
    run_command("npm start", "Starting frontend server", cwd="frontend", background=True)
    return True

def main():
    """Main setup function"""
    print("🌟 Dear Me - Automated Setup")
    print("=" * 40)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Please install missing prerequisites and try again")
        return
    
    # Setup everything
    if not setup_ollama():
        print("\n❌ Ollama setup failed")
        return
    
    if not setup_backend():
        print("\n❌ Backend setup failed")
        return
    
    if not setup_frontend():
        print("\n❌ Frontend setup failed")
        return
    
    print("\n🎉 Setup complete!")
    print("📱 Your app should open automatically at: http://localhost:3000")
    print("📚 API docs available at: http://localhost:8001/docs")
    print("\n💡 To stop all services, close this window or press Ctrl+C")
    
    # Keep the script running so background processes don't die
    try:
        while True:
            time.sleep(60)
            print("✅ All services running...")
    except KeyboardInterrupt:
        print("\n👋 Shutting down Dear Me...")

if __name__ == "__main__":
    main()