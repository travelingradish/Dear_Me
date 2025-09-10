#!/usr/bin/env python3
"""
Test conversation quality improvements.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8001"

def test_improved_conversation():
    """Test the improved conversation flow"""
    print("🎭 Testing Improved Conversation Quality...")
    
    # Register/login
    register_data = {
        "username": "conv_test_user",
        "email": "conv_test@example.com", 
        "password": "testpass123"
    }
    
    try:
        # Try register, fallback to login
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ Registered new test user")
        else:
            login_data = {"email": "conv_test@example.com", "password": "testpass123"}
            response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code != 200:
                print(f"❌ Login failed: {response.text}")
                return False
            token = response.json()["access_token"]
            print("✅ Logged in with existing user")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Start a guided diary session
        session_data = {"language": "en"}
        print("🚀 Starting guided diary session with single LLM architecture...")
        
        response = requests.post(f"{BASE_URL}/guided-diary/start", json=session_data, headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to start session: {response.text}")
            return False
        
        session_result = response.json()
        session_id = session_result["session_id"]
        print(f"✅ Started session {session_id}")
        print(f"Initial message: {session_result['initial_message']}")
        
        # Test the problematic conversation flow
        test_messages = [
            "I am feeling OK.",
            "Not much. Have to travel back to Australia this evening. It's a long flight. I'm a bit stressed",
            "Because the flight is very long."
        ]
        
        print("\n📝 Testing conversation flow:")
        for i, user_message in enumerate(test_messages, 1):
            print(f"\n--- Turn {i} ---")
            print(f"User: {user_message}")
            
            message_data = {"message": user_message}
            response = requests.post(f"{BASE_URL}/guided-diary/{session_id}/message", 
                                   json=message_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                assistant_response = result["response"]
                print(f"Assistant: {assistant_response}")
                
                # Analyze response quality
                analyze_response_quality(user_message, assistant_response, i)
            else:
                print(f"❌ Message failed: {response.text}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def analyze_response_quality(user_message, assistant_response, turn_number):
    """Analyze the quality of the assistant's response"""
    
    # Check for repetitive phrases
    repetitive_phrases = ["that sounds", "sounds like", "what made", "what's making"]
    repetition_count = sum(1 for phrase in repetitive_phrases if phrase.lower() in assistant_response.lower())
    
    # Check for echoing user's words
    user_words = set(user_message.lower().split())
    assistant_words = set(assistant_response.lower().split())
    echo_percentage = len(user_words & assistant_words) / len(user_words) if user_words else 0
    
    # Check response length and variety
    response_length = len(assistant_response.split())
    
    print(f"  📊 Quality Analysis:")
    print(f"     Repetitive phrases: {repetition_count} {'❌' if repetition_count > 1 else '✅'}")
    print(f"     Word echo rate: {echo_percentage:.0%} {'❌' if echo_percentage > 0.4 else '✅'}")
    print(f"     Response length: {response_length} words {'✅' if 15 <= response_length <= 40 else '❌'}")
    
    # Specific checks for this conversation
    if turn_number == 1 and "OK" in user_message:
        if "OK" in assistant_response and assistant_response.count("OK") > 1:
            print(f"     ❌ Over-echoing 'OK'")
        else:
            print(f"     ✅ Natural response to 'OK'")
    
    if turn_number == 2 and "long flight" in user_message:
        if assistant_response.lower().count("long") > 1:
            print(f"     ❌ Repetitive use of 'long'")
        else:
            print(f"     ✅ Varied language about flight")

if __name__ == "__main__":
    success = test_improved_conversation()
    if success:
        print("\n🎉 Conversation quality test completed!")
    else:
        print("\n❌ Conversation quality test failed")
    sys.exit(0 if success else 1)