#!/usr/bin/env python3
"""
Debug script for Windows 500 Internal Server Error issues
"""
import sys
import os
import requests
import sqlite3
import json
from pathlib import Path

def test_ollama_connection():
    """Test if Ollama is accessible"""
    print("🔍 Testing Ollama connection...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print("✅ Ollama is running")
            print(f"Available models: {[model['name'] for model in models.get('models', [])]}")
            
            # Test if llama3.1:8b is available
            model_names = [model['name'] for model in models.get('models', [])]
            if 'llama3.1:8b' in model_names:
                print("✅ llama3.1:8b model is available")
            else:
                print("❌ llama3.1:8b model NOT found")
                print("Available models:", model_names)
            
            return True
        else:
            print(f"❌ Ollama responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama (is 'ollama serve' running?)")
        return False
    except Exception as e:
        print(f"❌ Ollama connection error: {e}")
        return False

def test_database():
    """Test database creation and access"""
    print("\n🔍 Testing database...")
    try:
        db_path = "dear_me.db"
        if os.path.exists(db_path):
            print(f"✅ Database file exists: {os.path.abspath(db_path)}")
        else:
            print(f"ℹ️  Database file doesn't exist yet: {os.path.abspath(db_path)}")
        
        # Test database connection
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"✅ Database connection successful")
        print(f"Tables: {[table[0] for table in tables]}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_file_paths():
    """Test file path access"""
    print("\n🔍 Testing file paths...")
    try:
        # Test prompts directory
        prompts_dir = Path("prompts")
        if prompts_dir.exists():
            print("✅ Prompts directory exists")
            
            # List some prompt files
            prompt_files = list(prompts_dir.rglob("*.txt"))
            print(f"Found {len(prompt_files)} prompt files")
            
            # Test reading a specific prompt
            guided_en = prompts_dir / "guided" / "guide_en.txt"
            if guided_en.exists():
                with open(guided_en, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"✅ Can read guided prompt file ({len(content)} chars)")
            else:
                print("❌ guided/guide_en.txt not found")
        else:
            print("❌ Prompts directory not found")
            
        return True
    except Exception as e:
        print(f"❌ File path error: {e}")
        return False

def test_python_packages():
    """Test required Python packages from requirements.txt"""
    print("\n🔍 Testing Python packages...")
    
    # Read requirements.txt
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.readlines()
    except FileNotFoundError:
        print("❌ requirements.txt not found")
        return False
    
    # Parse package names
    required_packages = []
    for line in requirements:
        line = line.strip()
        if line and not line.startswith('#'):
            # Extract package name (before == or [ )
            package_name = line.split('==')[0].split('[')[0]
            required_packages.append(package_name)
    
    print(f"Found {len(required_packages)} packages in requirements.txt")
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {missing_packages}")
        print("Run: pip install -r requirements.txt")
        print("Or individually: pip install " + " ".join(missing_packages))
        return False
    return True

def test_backend_api():
    """Test if backend API is responding"""
    print("\n🔍 Testing backend API...")
    try:
        response = requests.get("http://localhost:8001/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Backend API is running")
            return True
        else:
            print(f"❌ Backend API responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend API (is it running?)")
        return False
    except Exception as e:
        print(f"❌ Backend API error: {e}")
        return False

def main():
    print("=" * 50)
    print("🔧 Dear Me - Windows Debug Tool")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Platform: {sys.platform}")
    print()
    
    results = []
    results.append(("Ollama", test_ollama_connection()))
    results.append(("Database", test_database()))
    results.append(("File Paths", test_file_paths()))
    results.append(("Python Packages", test_python_packages()))
    results.append(("Backend API", test_backend_api()))
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<15} {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 All tests passed! The issue might be in the application logic.")
        print("Check the backend console output for specific error messages.")
    else:
        print("⚠️  Some tests failed. Fix the failing components first.")
        
    print("\n💡 Next steps:")
    print("1. Fix any failing tests above")
    print("2. Check backend console output for detailed error messages")
    print("3. Try running: python main.py and look for error details")

if __name__ == "__main__":
    main()