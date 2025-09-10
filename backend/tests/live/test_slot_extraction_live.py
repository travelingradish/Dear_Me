#!/usr/bin/env python3
"""
Test slot extraction with live API calls.
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_slot_extraction_live():
    """Test slot extraction in a real API conversation"""
    print("🔍 Testing Live Slot Extraction...")
    
    # Login
    login_data = {"email": "calendar_test@example.com", "password": "testpass123"}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return False
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Logged in")
    
    # Create a brand new session
    print("\n🚀 Creating new session...")
    session_data = {"language": "en", "model": "llama3.1:8b"}
    response = requests.post(f"{BASE_URL}/guided-diary/start", json=session_data, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to start session: {response.text}")
        return False
    
    session_result = response.json()
    session_id = session_result["session_id"]
    print(f"✅ Created session {session_id}")
    print(f"   Initial intent: {session_result.get('current_intent', 'None')}")
    
    # Check initial session state
    response = requests.get(f"{BASE_URL}/guided-diary/{session_id}", headers=headers)
    if response.status_code == 200:
        session_data = response.json()['session']
        print(f"   Session state: intent={session_data.get('current_intent')}, phase={session_data.get('current_phase')}")
        print(f"   Initial structured_data: {session_data.get('structured_data', {})}")
    
    # Send messages that match the expected intent flow
    messages = [
        {
            "expected_current_intent": "ASK_MOOD",
            "message": "I'm feeling excited but nervous about returning to Australia tonight from my Sri Lanka trip.",
            "expected_extract": "mood"
        },
        {
            "expected_current_intent": "ASK_ACTIVITIES", 
            "message": "I spent time today reflecting on our family's housing situation and future plans.",
            "expected_extract": "activities"
        },
        {
            "expected_current_intent": "ASK_CHALLENGES_WINS",
            "message": "The biggest challenge is finding an affordable house near good schools and my work.",
            "expected_extract": "challenges"
        },
        {
            "expected_current_intent": "ASK_GRATITUDE",
            "message": "I'm grateful for this travel experience and quality time to think about what we need.",
            "expected_extract": "gratitude"
        },
        {
            "expected_current_intent": "ASK_HOPE",
            "message": "I hope we can find the perfect home for our growing children soon.",
            "expected_extract": "hope"
        }
    ]
    
    for i, msg_data in enumerate(messages, 1):
        print(f"\n--- Turn {i} ---")
        print(f"Expected current intent: {msg_data['expected_current_intent']}")
        print(f"Message: {msg_data['message'][:60]}...")
        print(f"Should extract: {msg_data['expected_extract']}")
        
        # Check current session state before sending message
        response = requests.get(f"{BASE_URL}/guided-diary/{session_id}", headers=headers)
        if response.status_code == 200:
            session_info = response.json()['session']
            current_intent = session_info.get('current_intent')
            print(f"Actual current intent: {current_intent}")
            
            if current_intent != msg_data['expected_current_intent']:
                print(f"⚠️  Intent mismatch! Expected {msg_data['expected_current_intent']}, got {current_intent}")
        
        # Send the message
        message_data = {"message": msg_data['message'], "model": "llama3.1:8b"}
        response = requests.post(f"{BASE_URL}/guided-diary/{session_id}/message", 
                               json=message_data, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Message failed: {response.text}")
            continue
        
        result = response.json()
        print(f"Response: {result.get('response', '')[:80]}...")
        print(f"Next intent: {result.get('current_intent', 'None')}")
        
        # Check if the expected field was extracted
        structured_data = result.get('structured_data', {})
        expected_field = msg_data['expected_extract']
        extracted_value = structured_data.get(expected_field, '')
        
        if extracted_value and extracted_value.strip():
            print(f"✅ {expected_field} extracted: {extracted_value[:50]}...")
        else:
            print(f"❌ {expected_field} NOT extracted! Value: '{extracted_value}'")
            print(f"   Full structured_data: {structured_data}")
    
    # Final check - see if we have a complete structured_data
    print(f"\n📊 Final Session Check...")
    response = requests.get(f"{BASE_URL}/guided-diary/{session_id}", headers=headers)
    if response.status_code == 200:
        session_info = response.json()['session']
        final_data = session_info.get('structured_data', {})
        print(f"Final structured data:")
        for key, value in final_data.items():
            status = "✅" if value and value.strip() else "❌"
            print(f"  {status} {key}: {value[:50] if value else 'EMPTY'}...")
        
        # Check if we have enough data for a meaningful diary
        filled_fields = [k for k, v in final_data.items() if v and v.strip()]
        if len(filled_fields) >= 3:
            print(f"✅ Sufficient data for diary generation ({len(filled_fields)} fields filled)")
            return True
        else:
            print(f"❌ Insufficient data for diary generation ({len(filled_fields)} fields filled)")
            return False
    
    return False

if __name__ == "__main__":
    success = test_slot_extraction_live()
    if success:
        print("\n🎉 Slot extraction test passed!")
    else:
        print("\n❌ Slot extraction test failed!")