#!/usr/bin/env python3
"""
Debug the guided diary flow to see where structured data gets lost.
"""

import requests
import sys
import json
from datetime import datetime

BASE_URL = "http://localhost:8001"

def test_with_session_checks():
    """Test with session status checks after each message"""
    print("🔍 Debugging Guided Diary Flow...")
    
    # Login
    login_data = {"email": "calendar_test@example.com", "password": "testpass123"}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return False
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Logged in")
    
    # Start new session
    print("\n🚀 Starting new guided diary session...")
    session_data = {"language": "en", "model": "llama3.1:8b"}
    
    response = requests.post(f"{BASE_URL}/guided-diary/start", json=session_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to start session: {response.text}")
        return False
    
    session_result = response.json()
    session_id = session_result["session_id"]
    print(f"✅ Started session {session_id}")
    
    def check_session_status():
        """Check and print current session status"""
        response = requests.get(f"{BASE_URL}/guided-diary/{session_id}", headers=headers)
        if response.status_code == 200:
            session_info = response.json()
            print(f"  📊 Session status:")
            print(f"     Phase: {session_info.get('current_phase', 'None')}")
            print(f"     Intent: {session_info.get('current_intent', 'None')}")
            print(f"     Complete: {session_info.get('is_complete', False)}")
            
            structured_data = session_info.get('structured_data', {})
            print(f"     Structured data: {json.dumps(structured_data, indent=8)}")
            return structured_data
        else:
            print(f"  ❌ Failed to get session status: {response.text}")
            return {}
    
    # Check initial status
    print("\n📊 Initial session status:")
    check_session_status()
    
    # Send messages and check status after each
    test_messages = [
        ("ASK_MOOD", "I'm feeling excited but nervous about returning to Australia tonight from my Sri Lanka trip."),
        ("ASK_ACTIVITIES", "I spent time today reflecting on our family's housing situation and future plans."),
        ("ASK_CHALLENGES_WINS", "The biggest challenge is finding an affordable house near good schools and my work."),
        ("ASK_GRATITUDE", "I'm grateful for this travel experience and quality time to think about what we need."),
        ("ASK_HOPE", "I hope we can find the perfect home for our growing children soon."),
    ]
    
    for i, (expected_intent, message) in enumerate(test_messages, 1):
        print(f"\n--- Turn {i} ({expected_intent}) ---")
        print(f"Sending: {message}")
        
        message_data = {"message": message, "model": "llama3.1:8b"}
        response = requests.post(f"{BASE_URL}/guided-diary/{session_id}/message", 
                               json=message_data, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Message failed: {response.text}")
            continue
        
        result = response.json()
        print(f"Response: {result.get('response', 'No response')[:100]}...")
        print(f"Current intent: {result.get('current_intent', 'None')}")
        print(f"Structured data in response: {result.get('structured_data', {})}")
        
        # Check session status after message
        structured_data = check_session_status()
        
        # Validate that structured data is being accumulated
        if i == 1:  # After first message (mood)
            if 'mood' not in structured_data or not structured_data['mood']:
                print("❌ Mood not captured in structured data!")
            else:
                print("✅ Mood captured successfully")
        
        elif i == 2:  # After second message (activities)
            if 'activities' not in structured_data or not structured_data['activities']:
                print("❌ Activities not captured in structured data!")
            else:
                print("✅ Activities captured successfully")
                
            if 'mood' not in structured_data or not structured_data['mood']:
                print("❌ Previous mood data lost!")
            else:
                print("✅ Previous mood data preserved")
    
    # Generate diary
    print(f"\n📝 Generating diary...")
    message_data = {"message": "I'm ready to generate my diary now.", "model": "llama3.1:8b"}
    response = requests.post(f"{BASE_URL}/guided-diary/{session_id}/message", 
                           json=message_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Final diary generated:")
        diary = result.get('final_diary', result.get('composed_diary', 'No diary'))
        print("=" * 50)
        print(diary)
        print("=" * 50)
        
        # Final session check
        print(f"\n📊 Final session status:")
        final_data = check_session_status()
        
        return True
    else:
        print(f"❌ Diary generation failed: {response.text}")
        return False

if __name__ == "__main__":
    test_with_session_checks()