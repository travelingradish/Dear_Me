#!/usr/bin/env python3
"""
Detailed test to understand what's happening in calendar review.
"""

import requests
import sys
import json
from datetime import datetime

BASE_URL = "http://localhost:8001"

def test_detailed_flow():
    """Test with more detailed logging"""
    print("🔍 Detailed Calendar Review Test...")
    
    # Login with existing user
    login_data = {"email": "calendar_test@example.com", "password": "testpass123"}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return False
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Logged in")
    
    # Start fresh session
    print("\n🚀 Starting new guided diary session...")
    session_data = {"language": "en", "model": "llama3.1:8b"}
    
    response = requests.post(f"{BASE_URL}/guided-diary/start", json=session_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to start session: {response.text}")
        return False
    
    session_result = response.json()
    session_id = session_result["session_id"]
    print(f"✅ Started session {session_id}")
    print(f"Initial message: {session_result.get('initial_message', 'None')}")
    print(f"Current intent: {session_result.get('current_intent', 'None')}")
    
    # Complete conversation with detailed logging
    test_messages = [
        "I'm feeling excited but nervous about returning to Australia tonight from my Sri Lanka trip.",
        "I spent time today reflecting on our family's housing situation and future plans.",
        "The biggest challenge is finding an affordable house near good schools and my work.",
        "I'm grateful for this travel experience and quality time to think about what we need.",
        "I hope we can find the perfect home for our growing children soon."
    ]
    
    print("\n💬 Completing conversation with detailed logging...")
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Turn {i} ---")
        print(f"Sending: {message}")
        
        message_data = {"message": message, "model": "llama3.1:8b"}
        response = requests.post(f"{BASE_URL}/guided-diary/{session_id}/message", 
                               json=message_data, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Message failed: {response.text}")
            return False
        
        result = response.json()
        print(f"Response: {result.get('response', 'No response')}")
        print(f"Current phase: {result.get('current_phase', 'None')}")
        print(f"Current intent: {result.get('current_intent', 'None')}")
        print(f"Is complete: {result.get('is_complete', False)}")
        
        if result.get('structured_data'):
            print(f"Structured data: {json.dumps(result['structured_data'], indent=2)}")
        
        if result.get('composed_diary'):
            print(f"Composed diary: {result['composed_diary']}")
        
        if result.get('final_diary'):
            print(f"Final diary: {result['final_diary']}")
            break
    
    # Force diary generation if not complete
    if not result.get('is_complete'):
        print("\n📝 Triggering diary generation...")
        message_data = {"message": "I'm ready to generate my diary now.", "model": "llama3.1:8b"}
        response = requests.post(f"{BASE_URL}/guided-diary/{session_id}/message", 
                               json=message_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Generation result: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Generation failed: {response.text}")
    
    # Check session status
    print(f"\n📊 Final session status:")
    response = requests.get(f"{BASE_URL}/guided-diary/{session_id}", headers=headers)
    if response.status_code == 200:
        session_info = response.json()
        print(f"Session complete: {session_info.get('is_complete', False)}")
        print(f"Final diary exists: {bool(session_info.get('final_diary'))}")
        if session_info.get('final_diary'):
            print(f"Final diary content: {session_info['final_diary']}")
    
    return True

if __name__ == "__main__":
    test_detailed_flow()