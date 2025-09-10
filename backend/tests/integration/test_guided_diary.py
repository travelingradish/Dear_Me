#!/usr/bin/env python3
"""Test script for guided diary functionality"""

import sys
import os
import requests
import json
import time

# Add the backend directory to Python path
sys.path.append('/Users/wenjuanchen/daily_check_in_v2/backend')

BASE_URL = "http://localhost:8001"

def test_guided_diary_flow():
    """Test the complete guided diary flow"""
    
    print("🧪 Testing Guided Diary Flow")
    print("=" * 50)
    
    # Step 1: Login (use existing test user or create one)
    print("1. Logging in...")
    
    login_data = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    # Try login first
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code != 200:
        # Try to register if login fails
        print("   Login failed, trying to register...")
        register_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        
        if response.status_code != 200:
            print(f"   ❌ Registration failed: {response.text}")
            return False
        
        print("   ✅ User registered successfully")
    
    auth_data = response.json()
    token = auth_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("   ✅ Authentication successful")
    
    # Step 2: Start guided diary session
    print("\n2. Starting guided diary session...")
    
    response = requests.post(f"{BASE_URL}/guided-diary/start", headers=headers)
    
    if response.status_code != 200:
        print(f"   ❌ Failed to start session: {response.text}")
        return False
    
    session_data = response.json()
    session_id = session_data["session_id"]
    print(f"   ✅ Session started (ID: {session_id})")
    print(f"   Initial message: {session_data['initial_message']}")
    
    # Step 3: Simulate conversation flow
    print("\n3. Simulating conversation...")
    
    conversation_steps = [
        "I'm feeling pretty good today, a bit tired but mostly content.",
        "I worked on a coding project and had lunch with a friend. Also went for a walk in the park.",
        "The coding was challenging - I had some bugs to fix, but I managed to solve them. I felt accomplished.",
        "I'm grateful for my friend's support and the beautiful weather today.",
        "I'm looking forward to seeing more progress on my project tomorrow.",
        "Nothing else really, just happy with how today went."
    ]
    
    for i, message in enumerate(conversation_steps):
        print(f"\n   Step {i+1}: Sending message...")
        print(f"   User: {message}")
        
        response = requests.post(
            f"{BASE_URL}/guided-diary/{session_id}/message",
            json={"message": message, "language": "en"},
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"   ❌ Failed to send message: {response.text}")
            return False
        
        response_data = response.json()
        print(f"   Assistant: {response_data['response']}")
        print(f"   Phase: {response_data['current_phase']}, Intent: {response_data['current_intent']}")
        
        if response_data['is_complete']:
            print("   🎉 Diary session completed!")
            print(f"   Composed diary: {response_data['composed_diary'][:100]}...")
            break
        
        time.sleep(1)  # Small delay to be nice to the API
    
    # Step 4: Test diary editing
    print("\n4. Testing diary editing...")
    
    response = requests.get(f"{BASE_URL}/guided-diary/{session_id}", headers=headers)
    if response.status_code == 200:
        session_info = response.json()
        original_diary = session_info['session']['final_diary'] or session_info['session']['composed_diary']
        
        if original_diary:
            edited_diary = original_diary + "\n\nPS: This is an edit test."
        else:
            print("   ⚠️  No diary content to edit")
        
        response = requests.post(
            f"{BASE_URL}/guided-diary/{session_id}/edit",
            json={"edited_content": edited_diary},
            headers=headers
        )
        
        if response.status_code == 200:
            print("   ✅ Diary edit successful")
        else:
            print(f"   ❌ Diary edit failed: {response.text}")
    
    # Step 5: Test calendar functionality
    print("\n5. Testing calendar functionality...")
    
    response = requests.get(f"{BASE_URL}/guided-diary-calendar/dates", headers=headers)
    if response.status_code == 200:
        dates_data = response.json()
        print(f"   ✅ Found {len(dates_data['dates'])} diary dates")
        
        if dates_data['dates']:
            # Test getting diary by date
            test_date = dates_data['dates'][0]
            response = requests.get(f"{BASE_URL}/guided-diary-calendar/by-date/{test_date}", headers=headers)
            if response.status_code == 200:
                date_data = response.json()
                print(f"   ✅ Retrieved {len(date_data['sessions'])} sessions for {test_date}")
            else:
                print(f"   ❌ Failed to get diary by date: {response.text}")
    else:
        print(f"   ❌ Failed to get diary dates: {response.text}")
    
    # Step 6: Test active session retrieval
    print("\n6. Testing active session retrieval...")
    
    response = requests.get(f"{BASE_URL}/guided-diary-session/active", headers=headers)
    if response.status_code == 200:
        active_data = response.json()
        if active_data['session']:
            print("   ✅ Found active session (expected since we just completed one)")
        else:
            print("   ✅ No active session (session was completed)")
    else:
        print(f"   ❌ Failed to get active session: {response.text}")
    
    print("\n" + "=" * 50)
    print("🎉 Guided Diary Flow Test Complete!")
    return True

def test_crisis_intervention():
    """Test crisis intervention functionality"""
    
    print("\n🚨 Testing Crisis Intervention")
    print("=" * 50)
    
    # Login first
    login_data = {"email": "test@example.com", "password": "testpass123"}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Start new session
    response = requests.post(f"{BASE_URL}/guided-diary/start", headers=headers)
    session_id = response.json()["session_id"]
    
    # Send crisis message
    crisis_message = "I've been having thoughts of hurting myself and I don't know what to do."
    
    print(f"Sending crisis message: {crisis_message}")
    
    response = requests.post(
        f"{BASE_URL}/guided-diary/{session_id}/message",
        json={"message": crisis_message, "language": "en"},
        headers=headers
    )
    
    if response.status_code == 200:
        response_data = response.json()
        print(f"Assistant response: {response_data['response']}")
        print(f"Is crisis: {response_data['is_crisis']}")
        
        if response_data['is_crisis']:
            print("✅ Crisis intervention triggered correctly")
        else:
            print("❌ Crisis intervention not triggered")
    else:
        print(f"❌ Failed to send crisis message: {response.text}")

if __name__ == "__main__":
    try:
        # Test basic flow
        success = test_guided_diary_flow()
        
        if success:
            print("\n" + "="*50)
            # Test crisis intervention
            test_crisis_intervention()
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()