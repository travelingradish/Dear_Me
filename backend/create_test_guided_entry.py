#!/usr/bin/env python3
"""
Create a test guided diary entry for testing delete functionality
"""
import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8001"
TEST_USER_EMAIL = "wen@example.com"  # Change this to your current user email
TEST_USER_PASSWORD = "password123"   # Change this to your password

def create_test_guided_entry():
    # 1. Login to get token
    print("1. Logging in...")
    login_response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    })
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code} - {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✓ Logged in successfully")
    
    # 2. Start guided diary session
    print("2. Starting guided diary session...")
    start_response = requests.post(f"{BASE_URL}/guided-diary/start", 
        json={"language": "en", "model": "llama3.1:8b"}, 
        headers=headers)
    
    if start_response.status_code != 200:
        print(f"Start session failed: {start_response.status_code} - {start_response.text}")
        return
    
    session_data = start_response.json()
    session_id = session_data["session_id"]
    print(f"✓ Started session {session_id}")
    
    # 3. Simulate guided conversation
    test_messages = [
        "I'm feeling pretty good today, energetic and positive.",
        "I went to work, had lunch with colleagues, and took a walk in the evening.",
        "The main challenge was a difficult project deadline, but I managed to complete it on time.",
        "I'm grateful for my supportive team and the beautiful weather today.",
        "I'm hopeful about the new opportunities that might come my way next week.",
        "Nothing else comes to mind right now."
    ]
    
    print("3. Simulating guided conversation...")
    for i, message in enumerate(test_messages):
        print(f"   Sending message {i+1}/{len(test_messages)}: {message[:50]}...")
        
        message_response = requests.post(f"{BASE_URL}/guided-diary/{session_id}/message",
            json={"message": message, "language": "en", "model": "llama3.1:8b"},
            headers=headers)
        
        if message_response.status_code != 200:
            print(f"Message failed: {message_response.status_code} - {message_response.text}")
            return
        
        response_data = message_response.json()
        print(f"   ✓ Response: {response_data['response'][:100]}...")
        
        if response_data.get("is_complete"):
            print(f"✓ Diary session completed after {i+1} messages!")
            print(f"Final diary preview: {response_data.get('final_diary', 'N/A')[:100]}...")
            break
    
    # 4. Trigger final diary generation if not complete
    if not response_data.get("is_complete"):
        print("4. Triggering final diary generation...")
        final_response = requests.post(f"{BASE_URL}/guided-diary/{session_id}/message",
            json={"message": "I'm ready to generate my diary now.", "language": "en", "model": "llama3.1:8b"},
            headers=headers)
        
        if final_response.status_code == 200:
            final_data = final_response.json()
            if final_data.get("is_complete"):
                print("✓ Final diary generated successfully!")
                print(f"Final diary: {final_data.get('final_diary', 'N/A')[:200]}...")
            else:
                print("⚠ Session still not complete, might need more steps")
        else:
            print(f"Final generation failed: {final_response.status_code} - {final_response.text}")
    
    print(f"\n🎉 Test guided diary entry created with session ID: {session_id}")
    print(f"Now you can test deleting this entry in the frontend!")
    print(f"Look for entry 'guided_{session_id}' in today's date ({datetime.now().strftime('%Y-%m-%d')})")

if __name__ == "__main__":
    create_test_guided_entry()