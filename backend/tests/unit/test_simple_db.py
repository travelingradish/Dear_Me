#!/usr/bin/env python3
"""
Simple database test to verify commits work.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"

def test_simple_session_retrieval():
    """Test if session data persists between API calls"""
    print("🔍 Testing Session Data Persistence...")
    
    # Login
    login_data = {"email": "calendar_test@example.com", "password": "testpass123"}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return False
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Logged in")
    
    # Create a new session
    print("\n🚀 Creating new session...")
    session_data = {"language": "en", "model": "llama3.1:8b"}
    response = requests.post(f"{BASE_URL}/guided-diary/start", json=session_data, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to start session: {response.text}")
        return False
    
    session_result = response.json()
    session_id = session_result["session_id"]
    print(f"✅ Created session {session_id}")
    
    # Check session immediately after creation
    print(f"\n📊 Checking session immediately after creation...")
    response = requests.get(f"{BASE_URL}/guided-diary/{session_id}", headers=headers)
    
    if response.status_code == 200:
        response_data = response.json()
        session_info = response_data.get('session', {})
        print(f"✅ Retrieved session {session_id}")
        print(f"   Phase: {session_info.get('current_phase', 'None')}")
        print(f"   Intent: {session_info.get('current_intent', 'None')}")
        print(f"   Structured data: {session_info.get('structured_data', {})}")
    else:
        print(f"❌ Failed to retrieve session: {response.text}")
        return False
    
    # Send one message
    print(f"\n💬 Sending one message...")
    message_data = {"message": "I'm feeling excited about my trip!", "model": "llama3.1:8b"}
    response = requests.post(f"{BASE_URL}/guided-diary/{session_id}/message", 
                           json=message_data, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Message failed: {response.text}")
        return False
    
    result = response.json()
    print(f"✅ Message sent successfully")
    print(f"   Response intent: {result.get('current_intent', 'None')}")
    print(f"   Response phase: {result.get('current_phase', 'None')}")
    print(f"   Response structured_data: {result.get('structured_data', {})}")
    
    # Wait a moment for any async operations
    time.sleep(1)
    
    # Check session again after message
    print(f"\n📊 Checking session after sending message...")
    response = requests.get(f"{BASE_URL}/guided-diary/{session_id}", headers=headers)
    
    if response.status_code == 200:
        response_data = response.json()
        session_info = response_data.get('session', {})
        print(f"✅ Retrieved session {session_id}")
        print(f"   Phase: {session_info.get('current_phase', 'None')}")
        print(f"   Intent: {session_info.get('current_intent', 'None')}")
        print(f"   Structured data: {session_info.get('structured_data', {})}")
        
        # Compare with the response from the message
        if (session_info.get('current_phase') == result.get('current_phase') and
            session_info.get('current_intent') == result.get('current_intent')):
            print("✅ Session data matches between POST response and GET retrieval")
            return True
        else:
            print("❌ Session data differs between POST response and GET retrieval")
            print(f"   POST: phase={result.get('current_phase')}, intent={result.get('current_intent')}")
            print(f"   GET:  phase={session_info.get('current_phase')}, intent={session_info.get('current_intent')}")
            return False
    else:
        print(f"❌ Failed to retrieve session after message: {response.text}")
        return False

if __name__ == "__main__":
    success = test_simple_session_retrieval()
    if success:
        print("\n🎉 Session persistence test passed!")
    else:
        print("\n❌ Session persistence test failed!")