#!/usr/bin/env python3
"""
Test calendar functionality for reviewing diary entries.
"""

import requests
import sys
import json
from datetime import datetime

BASE_URL = "http://localhost:8001"

def test_calendar_review():
    """Test the complete flow of diary generation and calendar review"""
    print("📅 Testing Calendar Review Functionality...")
    
    # 1. Register/login
    register_data = {
        "username": "calendar_test_user",
        "email": "calendar_test@example.com", 
        "password": "testpass123"
    }
    
    try:
        # Try register, fallback to login
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ Registered new test user")
        else:
            login_data = {"email": "calendar_test@example.com", "password": "testpass123"}
            response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code != 200:
                print(f"❌ Login failed: {response.text}")
                return False
            token = response.json()["access_token"]
            print("✅ Logged in with existing user")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Start a guided diary session
        print("\n🚀 Starting guided diary session...")
        session_data = {"language": "en", "model": "llama3.1:8b"}
        
        response = requests.post(f"{BASE_URL}/guided-diary/start", json=session_data, headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to start session: {response.text}")
            return False
        
        session_result = response.json()
        session_id = session_result["session_id"]
        print(f"✅ Started session {session_id}")
        
        # 3. Complete a conversation flow to generate diary
        test_messages = [
            "I'm feeling excited to go back to Australia from Sri Lanka!",
            "I spent the day thinking about our family's future and house hunting.",
            "The main challenge is finding an affordable place near good schools.",
            "I'm grateful for this travel experience and time to reflect.",
            "I hope we find the perfect home for our growing family."
        ]
        
        print("\n💬 Completing conversation flow...")
        for i, message in enumerate(test_messages, 1):
            print(f"  Turn {i}: {message[:50]}...")
            
            message_data = {"message": message, "model": "llama3.1:8b"}
            response = requests.post(f"{BASE_URL}/guided-diary/{session_id}/message", 
                                   json=message_data, headers=headers)
            
            if response.status_code != 200:
                print(f"❌ Message failed: {response.text}")
                return False
            
            result = response.json()
            if result.get("is_complete"):
                print(f"✅ Diary generated! Session completed.")
                break
        else:
            # Force completion if not done yet
            print("  Triggering diary generation...")
            message_data = {"message": "I'm ready to generate my diary now.", "model": "llama3.1:8b"}
            response = requests.post(f"{BASE_URL}/guided-diary/{session_id}/message", 
                                   json=message_data, headers=headers)
        
        # 4. Test calendar dates retrieval
        print("\n📅 Testing calendar dates retrieval...")
        response = requests.get(f"{BASE_URL}/guided-diary-calendar/dates", headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to get calendar dates: {response.text}")
            return False
        
        dates_result = response.json()
        print(f"✅ Retrieved calendar dates: {dates_result['dates']}")
        
        if not dates_result['dates']:
            print("⚠️  No dates found - diary might not be completed yet")
            return False
        
        # 5. Test diary retrieval by date
        today_date = datetime.now().strftime('%Y-%m-%d')
        print(f"\n📖 Testing diary retrieval for today ({today_date})...")
        
        response = requests.get(f"{BASE_URL}/guided-diary-calendar/by-date/{today_date}", headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to get diary by date: {response.text}")
            return False
        
        diary_result = response.json()
        sessions = diary_result.get('sessions', [])
        
        if not sessions:
            print("⚠️  No diary sessions found for today")
            return False
        
        print(f"✅ Retrieved {len(sessions)} diary session(s) for today")
        
        # Display the diary content
        for i, session in enumerate(sessions, 1):
            print(f"\n📝 Diary Entry {i}:")
            print("-" * 50)
            diary_content = session.get('final_diary') or session.get('composed_diary', 'No diary content')
            print(diary_content)
            print("-" * 50)
            print(f"Completed at: {session.get('completed_at')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_calendar_review()
    if success:
        print("\n🎉 Calendar review functionality test completed successfully!")
        print("Users can now review their diary entries by clicking calendar dates.")
    else:
        print("\n❌ Calendar review functionality test failed")
    sys.exit(0 if success else 1)