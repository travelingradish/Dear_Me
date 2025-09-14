#!/usr/bin/env python3
"""
Test specific API endpoints that are failing
"""
import requests
import json
import time

def test_auth_flow():
    """Test user registration and login"""
    print("🔍 Testing auth flow...")
    
    base_url = "http://localhost:8001"
    
    # Test registration
    try:
        register_data = {
            "email": "test@example.com",
            "password": "testpass123",
            "ai_character_name": "TestBot"
        }
        
        response = requests.post(f"{base_url}/auth/register", json=register_data)
        print(f"Register status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("✅ Registration successful")
        elif response.status_code == 400:
            print("ℹ️  User might already exist, trying login...")
        else:
            print(f"❌ Registration failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return None
    
    # Test login
    try:
        login_data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        print(f"Login status: {response.status_code}")
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            print("✅ Login successful")
            return token
        else:
            print(f"❌ Login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_guided_diary(token):
    """Test guided diary endpoint"""
    print("\n🔍 Testing guided diary...")
    
    if not token:
        print("❌ No auth token, skipping guided diary test")
        return
    
    base_url = "http://localhost:8001"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Test starting guided diary
        response = requests.post(f"{base_url}/guided-diary/start", headers=headers)
        print(f"Guided diary start status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Guided diary start successful")
            session_data = response.json()
            print(f"Session ID: {session_data.get('session_id')}")
        else:
            print(f"❌ Guided diary start failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Guided diary error: {e}")

def test_llm_conversation(token):
    """Test LLM conversation endpoint"""
    print("\n🔍 Testing LLM conversation...")
    
    if not token:
        print("❌ No auth token, skipping LLM conversation test")
        return
    
    base_url = "http://localhost:8001"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Test LLM conversation
        conversation_data = {
            "user_message": "Hello, how are you?",
            "language": "en"
        }
        
        response = requests.post(f"{base_url}/llmconversation", 
                               json=conversation_data, headers=headers)
        print(f"LLM conversation status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ LLM conversation successful")
            result = response.json()
            print(f"Response length: {len(result.get('response', ''))}")
        else:
            print(f"❌ LLM conversation failed: {response.text}")
            
    except Exception as e:
        print(f"❌ LLM conversation error: {e}")

def main():
    print("=" * 50)
    print("🧪 Dear Me - Endpoint Testing")
    print("=" * 50)
    
    # Wait a moment for backend to be ready
    print("Waiting 2 seconds for backend to be ready...")
    time.sleep(2)
    
    # Test auth flow first
    token = test_auth_flow()
    
    # Test the failing endpoints
    test_guided_diary(token)
    test_llm_conversation(token)
    
    print("\n" + "=" * 50)
    print("📋 RECOMMENDATIONS")
    print("=" * 50)
    print("If tests are failing:")
    print("1. Check if Ollama is running: ollama serve")
    print("2. Check if llama3.1:8b model is downloaded: ollama list") 
    print("3. Check backend console for detailed error messages")
    print("4. Run: python debug_windows.py for comprehensive diagnostics")

if __name__ == "__main__":
    main()