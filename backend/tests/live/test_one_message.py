#!/usr/bin/env python3
"""
Test one message to see debug output.
"""

import requests

BASE_URL = "http://localhost:8001"

def test_one_message():
    # Login
    login_data = {"email": "calendar_test@example.com", "password": "testpass123"}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Complete existing session
    requests.post(f"{BASE_URL}/guided-diary/9/message", json={"message": "I'm ready to generate my diary now.", "model": "llama3.1:8b"}, headers=headers)
    
    # Create fresh session
    response = requests.post(f"{BASE_URL}/guided-diary/start", json={"language": "en", "model": "llama3.1:8b"}, headers=headers)
    session_id = response.json()["session_id"]
    print(f"Created session {session_id}")
    
    # Send one message
    message_data = {"message": "I'm feeling excited but nervous about my trip!", "model": "llama3.1:8b"}
    response = requests.post(f"{BASE_URL}/guided-diary/{session_id}/message", json=message_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {result.get('response', '')[:100]}...")
        print(f"Structured data: {result.get('structured_data', {})}")
    else:
        print(f"Failed: {response.text}")

if __name__ == "__main__":
    test_one_message()