#!/usr/bin/env python3

import requests
import json

def test_diary_generation():
    """Test the diary generation endpoint to see the exact error"""

    # First, get a valid token
    auth_url = "http://localhost:8001/auth/login"
    auth_data = {
        "username": "wen@example.com",
        "password": "securepass123"
    }

    print("🔐 Authenticating...")
    auth_response = requests.post(auth_url, json=auth_data)

    if auth_response.status_code != 200:
        print(f"❌ Authentication failed: {auth_response.status_code}")
        print(f"Response: {auth_response.text}")
        return

    token = auth_response.json().get("access_token")
    print(f"✅ Got token: {token[:20]}...")

    # Test diary generation
    diary_url = "http://localhost:8001/diary/generate"
    headers = {"Authorization": f"Bearer {token}"}

    # Sample diary data
    diary_data = {
        "answers": {
            "summary": "Had a great day at the park with family"
        },
        "conversation_history": [
            {"role": "user", "content": "I had a good day"},
            {"role": "assistant", "content": "That's wonderful to hear!"}
        ],
        "language": "en",
        "tone": "casual"
    }

    print("📝 Testing diary generation...")
    diary_response = requests.post(diary_url, json=diary_data, headers=headers)

    print(f"Status Code: {diary_response.status_code}")
    print(f"Response: {diary_response.text}")

    if diary_response.status_code == 500:
        print("❌ 500 Error confirmed!")
    else:
        print("✅ Diary generation worked!")

if __name__ == "__main__":
    test_diary_generation()